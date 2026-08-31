using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using Microsoft.JSInterop;

namespace RistWorld;

public sealed class DiscordAuthClient(HttpClient http, IJSRuntime js)
{
    private const string AccountProfileKey = "account/profile.json";
    private const string GuardianRequestKey = "rist.guardian.request";
    private const string GuardianApprovalKey = "rist.guardian.approval";
    private string _apiBaseUrl = "";
    private string? _sessionToken;

    public bool IsConfigured => Uri.TryCreate(_apiBaseUrl, UriKind.Absolute, out _);
    public string OwnerDiscordUserId { get; private set; } = "";
    public AuthProfile? Profile { get; private set; }
    public AccountProfile? Account { get; private set; }
    public GuardianConsentRequest? PendingGuardianRequest { get; private set; }
    public string RistAccountId => Account?.AccountId ?? "";
    public string AccessBand => Account?.ContentAccess?.AccessBand ?? ContentAllowancePolicy.General;
    public IReadOnlyList<string> AllowedContentDescriptors => Account?.ContentAccess?.AllowedDescriptors ?? [];
    public IReadOnlyList<string> GuardianApprovedDescriptors => Account?.ContentAccess?.GuardianApprovedDescriptors ?? [];
    public bool GuardianConsentRequired => AccessBand == ContentAllowancePolicy.Minor && Account?.ContentAccess?.GuardianConsentAtUtc is null;
    public string LastError { get; private set; } = "";
    public bool IsOwnerDiscordAccount => Profile is not null && !string.IsNullOrWhiteSpace(OwnerDiscordUserId) && string.Equals(Profile.UserId, OwnerDiscordUserId, StringComparison.Ordinal);
    internal string? SessionToken => _sessionToken;

    public async Task<AuthProfile?> InitializeAsync()
    {
        LastError = "";
        Account = null;
        PendingGuardianRequest = null;
        try
        {
            var config = await http.GetFromJsonAsync<AuthConfig>("auth-config.json");
            _apiBaseUrl = config?.ApiBaseUrl?.TrimEnd('/') ?? "";
            OwnerDiscordUserId = config?.OwnerDiscordUserId?.Trim() ?? "";
            _sessionToken = await js.InvokeAsync<string?>("ristAuth.captureSession", _apiBaseUrl);
        }
        catch
        {
            Profile = null;
            LastError = "Account service could not be initialized.";
            return null;
        }

        if (!IsConfigured || string.IsNullOrWhiteSpace(_sessionToken))
        {
            Profile = null;
            return null;
        }

        for (var attempt = 0; attempt < 3; attempt++)
        {
            try
            {
                Profile = await SendAsync<AuthProfile>(HttpMethod.Get, "/me");
                if (Profile is not null)
                    return await CompleteAccountAccessAsync();

                await ClearSessionAsync();
                return null;
            }
            catch (HttpRequestException) when (attempt < 2)
            {
                await Task.Delay(350 * (attempt + 1));
            }
            catch (TaskCanceledException) when (attempt < 2)
            {
                await Task.Delay(350 * (attempt + 1));
            }
            catch
            {
                return FailClosedProfileVerification();
            }
        }

        return FailClosedProfileVerification();
    }

    private async Task<AuthProfile?> CompleteAccountAccessAsync()
    {
        if (Profile is null) return null;
        var intent = (await js.InvokeAsync<string?>("localStorage.getItem", "rist.auth.intent"))?.Trim().ToLowerInvariant() ?? "";

        if (intent == "guardian-consent")
        {
            var request = await ReadLocalAsync<GuardianConsentRequest>(GuardianRequestKey);
            if (request is null || DateTimeOffset.UtcNow - request.RequestedAtUtc > TimeSpan.FromMinutes(30))
            {
                LastError = "The guardian consent request expired. Return to the minor account and request consent again.";
                await ClearGuardianDraftAsync();
                await ClearSessionAsync();
                Profile = null;
                return null;
            }
            if (string.Equals(Profile.UserId, request.ChildUserId, StringComparison.Ordinal))
            {
                LastError = "Guardian consent must use a different adult login from the minor account.";
                await ClearSessionAsync();
                Profile = null;
                return null;
            }
            PendingGuardianRequest = request;
            Account = null;
            LastError = "";
            return Profile;
        }

        AccountProfile? saved;
        try
        {
            saved = await DownloadJsonAsync<AccountProfile>(AccountProfileKey);
        }
        catch (HttpRequestException)
        {
            LastError = "Your RIST profile could not be checked. Please try again.";
            await ClearSessionAsync();
            Profile = null;
            return null;
        }

        if (intent == "signup")
        {
            if (saved is not null)
            {
                LastError = "A RIST profile already exists for this Discord account. Use Log In instead.";
                await ClearAuthIntentAsync();
                await ClearSessionAsync();
                Profile = null;
                return null;
            }

            var alias = (await js.InvokeAsync<string?>("localStorage.getItem", "rist.signup.alias"))?.Trim() ?? "";
            var plan = (await js.InvokeAsync<string?>("localStorage.getItem", "rist.signup.plan"))?.Trim() ?? "player";
            var terms = await js.InvokeAsync<string?>("localStorage.getItem", "rist.signup.termsAccepted");
            if (alias.Length is < 1 or > 32 || !string.Equals(terms, "true", StringComparison.OrdinalIgnoreCase))
            {
                LastError = "Sign-up information is incomplete. Please start Sign Up again.";
                await ClearAuthIntentAsync();
                await ClearSessionAsync();
                Profile = null;
                return null;
            }

            plan = plan == "gm-player" ? "gm-player" : "player";
            var created = new AccountProfile(
                AccountId: Guid.NewGuid().ToString("D"),
                PlayerAlias: alias,
                Plan: plan,
                CreatedAtUtc: DateTimeOffset.UtcNow,
                TermsAcceptedAtUtc: DateTimeOffset.UtcNow,
                TermsVersion: "2026-08-30",
                ContentAccess: ContentAccessSettings.Default);

            try
            {
                await UploadTextAsync(AccountProfileKey, JsonSerializer.Serialize(created), "application/json");
                Account = created;
                await ClearSignupDraftAsync();
                LastError = "";
                return Profile;
            }
            catch
            {
                LastError = "Your RIST profile could not be created. Nothing was charged. Please try again.";
                await ClearSessionAsync();
                Profile = null;
                return null;
            }
        }

        if (saved is null)
        {
            LastError = intent == "login"
                ? "No RIST profile is connected to this Discord account. Choose Sign Up first."
                : "This Discord account does not have a RIST profile yet. Choose Sign Up to create one.";
            await ClearAuthIntentAsync();
            await ClearSessionAsync();
            Profile = null;
            return null;
        }

        saved = await ApplyPendingGuardianApprovalAsync(saved);
        Account = saved;
        await ClearAuthIntentAsync();
        return Profile;
    }

    private AuthProfile? FailClosedProfileVerification()
    {
        Profile = null;
        Account = null;
        PendingGuardianRequest = null;
        LastError = "Your RIST profile could not be verified. Please try again.";
        return null;
    }

    public async Task BeginLoginAsync()
    {
        LastError = "";
        if (!IsConfigured) return;
        await js.InvokeVoidAsync("ristAuth.navigate", _apiBaseUrl + "/auth/login");
    }

    public async Task SetContentAccessAsync(string accessBand, IEnumerable<string> requestedDescriptors, bool ageAttested)
    {
        LastError = "";
        if (Account is null) return;

        accessBand = accessBand switch
        {
            ContentAllowancePolicy.Minor => ContentAllowancePolicy.Minor,
            ContentAllowancePolicy.Adult18 => ContentAllowancePolicy.Adult18,
            ContentAllowancePolicy.Adult21 => ContentAllowancePolicy.Adult21,
            _ => ContentAllowancePolicy.General
        };

        if (accessBand == ContentAllowancePolicy.Adult18 && !ageAttested)
        {
            LastError = "You must certify that you are at least 18 before enabling 18+ content allowances.";
            return;
        }
        if (accessBand == ContentAllowancePolicy.Adult21 && !ageAttested)
        {
            LastError = "You must certify that you are at least 21 before enabling sexual-content allowances.";
            return;
        }

        var previous = Account.ContentAccess ?? ContentAccessSettings.Default;
        var now = DateTimeOffset.UtcNow;
        ContentAccessSettings next;
        if (accessBand == ContentAllowancePolicy.Minor)
        {
            next = new ContentAccessSettings(
                AccessBand: ContentAllowancePolicy.Minor,
                AllowedDescriptors: [],
                SelfAttestedAtUtc: null,
                ConsentVersion: ContentAllowancePolicy.Version,
                GuardianConsentAtUtc: previous.AccessBand == ContentAllowancePolicy.Minor ? previous.GuardianConsentAtUtc : null,
                GuardianConsentVersion: previous.AccessBand == ContentAllowancePolicy.Minor ? previous.GuardianConsentVersion : null,
                GuardianApprovedDescriptors: previous.AccessBand == ContentAllowancePolicy.Minor ? previous.GuardianApprovedDescriptors : []);
        }
        else
        {
            var allowed = ContentAllowancePolicy.Sanitize(accessBand, requestedDescriptors);
            next = new ContentAccessSettings(
                AccessBand: accessBand,
                AllowedDescriptors: allowed.ToArray(),
                SelfAttestedAtUtc: accessBand == ContentAllowancePolicy.General ? null : now,
                ConsentVersion: ContentAllowancePolicy.Version,
                GuardianConsentAtUtc: null,
                GuardianConsentVersion: null,
                GuardianApprovedDescriptors: []);
        }

        await SaveContentAccessAsync(next);
    }

    public async Task BeginGuardianConsentAsync(IEnumerable<string> requestedDescriptors)
    {
        LastError = "";
        if (Account is null || Profile is null || AccessBand != ContentAllowancePolicy.Minor)
        {
            LastError = "Guardian consent can only be requested from a minor account.";
            return;
        }

        var request = new GuardianConsentRequest(
            ChildUserId: Profile.UserId,
            ChildAccountId: Account.AccountId,
            ChildAlias: Account.PlayerAlias,
            RequestedDescriptors: requestedDescriptors.Distinct(StringComparer.Ordinal).Where(id => ContentAllowancePolicy.Descriptors.Any(d => d.Id == id)).ToArray(),
            RequestedAtUtc: DateTimeOffset.UtcNow,
            ConsentVersion: ContentAllowancePolicy.Version);

        await WriteLocalAsync(GuardianRequestKey, request);
        await js.InvokeVoidAsync("localStorage.setItem", "rist.auth.intent", "guardian-consent");
        if (IsConfigured && !string.IsNullOrWhiteSpace(_sessionToken))
        {
            try { await SendAsync<object>(HttpMethod.Post, "/auth/logout"); } catch { }
        }
        Profile = null;
        Account = null;
        PendingGuardianRequest = null;
        await ClearSessionOnlyAsync();
        await js.InvokeVoidAsync("ristAuth.navigate", _apiBaseUrl + "/auth/login");
    }

    public async Task ApproveGuardianConsentAsync(bool adultAttested)
    {
        LastError = "";
        if (PendingGuardianRequest is null || Profile is null) return;
        if (!adultAttested)
        {
            LastError = "The parent or guardian must certify that they are an adult and consent to the requested access.";
            return;
        }

        var approval = new GuardianConsentApproval(
            ChildUserId: PendingGuardianRequest.ChildUserId,
            ChildAccountId: PendingGuardianRequest.ChildAccountId,
            GuardianUserId: Profile.UserId,
            ApprovedDescriptors: PendingGuardianRequest.RequestedDescriptors,
            ConsentedAtUtc: DateTimeOffset.UtcNow,
            ConsentVersion: ContentAllowancePolicy.Version);
        await WriteLocalAsync(GuardianApprovalKey, approval);
        await js.InvokeVoidAsync("localStorage.removeItem", GuardianRequestKey);

        if (IsConfigured && !string.IsNullOrWhiteSpace(_sessionToken))
        {
            try { await SendAsync<object>(HttpMethod.Post, "/auth/logout"); } catch { }
        }
        Profile = null;
        Account = null;
        PendingGuardianRequest = null;
        await ClearAuthIntentAsync();
        await ClearSessionOnlyAsync();
        LastError = "Guardian consent recorded. The minor can now log back in to apply the approved content allowances.";
    }

    public async Task DenyGuardianConsentAsync()
    {
        await ClearGuardianDraftAsync();
        if (IsConfigured && !string.IsNullOrWhiteSpace(_sessionToken))
        {
            try { await SendAsync<object>(HttpMethod.Post, "/auth/logout"); } catch { }
        }
        Profile = null;
        Account = null;
        PendingGuardianRequest = null;
        await ClearSessionOnlyAsync();
        LastError = "Guardian consent was not granted. Mature content remains blocked.";
    }

    public bool CampaignContentAllowed(IEnumerable<string> campaignDescriptors)
        => Account is not null && ContentAllowancePolicy.CampaignAllowed(
            AccessBand,
            AllowedContentDescriptors,
            campaignDescriptors,
            GuardianApprovedDescriptors);

    private async Task<AccountProfile> ApplyPendingGuardianApprovalAsync(AccountProfile saved)
    {
        var approval = await ReadLocalAsync<GuardianConsentApproval>(GuardianApprovalKey);
        if (approval is null) return saved;
        if (DateTimeOffset.UtcNow - approval.ConsentedAtUtc > TimeSpan.FromHours(24))
        {
            await js.InvokeVoidAsync("localStorage.removeItem", GuardianApprovalKey);
            return saved;
        }
        if (Profile is null || !string.Equals(Profile.UserId, approval.ChildUserId, StringComparison.Ordinal) || !string.Equals(saved.AccountId, approval.ChildAccountId, StringComparison.Ordinal))
            return saved;

        var approved = approval.ApprovedDescriptors.Distinct(StringComparer.Ordinal).Where(id => ContentAllowancePolicy.Descriptors.Any(d => d.Id == id)).ToArray();
        var nextAccess = new ContentAccessSettings(
            AccessBand: ContentAllowancePolicy.Minor,
            AllowedDescriptors: approved,
            SelfAttestedAtUtc: null,
            ConsentVersion: ContentAllowancePolicy.Version,
            GuardianConsentAtUtc: approval.ConsentedAtUtc,
            GuardianConsentVersion: approval.ConsentVersion,
            GuardianApprovedDescriptors: approved);
        var updated = saved with { ContentAccess = nextAccess };
        await UploadTextAsync(AccountProfileKey, JsonSerializer.Serialize(updated), "application/json");
        await js.InvokeVoidAsync("localStorage.removeItem", GuardianApprovalKey);
        return updated;
    }

    private async Task SaveContentAccessAsync(ContentAccessSettings settings)
    {
        if (Account is null) return;
        try
        {
            var updated = Account with { ContentAccess = settings, NsfwAccessEnabled = false, Age21AttestedAtUtc = null, NsfwAttestationVersion = null };
            await UploadTextAsync(AccountProfileKey, JsonSerializer.Serialize(updated), "application/json");
            Account = updated;
        }
        catch
        {
            LastError = "Content allowance preferences could not be saved. Please try again.";
        }
    }

    public async Task LogoutAsync()
    {
        if (IsConfigured && !string.IsNullOrWhiteSpace(_sessionToken))
        {
            try { await SendAsync<object>(HttpMethod.Post, "/auth/logout"); } catch { }
        }
        Profile = null;
        Account = null;
        PendingGuardianRequest = null;
        LastError = "";
        await ClearAuthIntentAsync();
        await ClearSessionAsync();
    }

    public async Task DeleteAccountAsync()
    {
        if (IsConfigured && !string.IsNullOrWhiteSpace(_sessionToken))
            await SendAsync<object>(HttpMethod.Post, "/account/delete");
        Profile = null;
        Account = null;
        PendingGuardianRequest = null;
        LastError = "";
        await ClearSignupDraftAsync();
        await ClearGuardianDraftAsync();
        await ClearSessionAsync();
    }

    public async Task UploadTextAsync(string key, string text, string contentType)
        => await UploadBytesAsync(key, Encoding.UTF8.GetBytes(text), contentType);

    public async Task UploadBytesAsync(string key, byte[] bytes, string contentType)
    {
        var request = new UploadRequest(key, contentType);
        var post = await SendAsync<PresignedPost>(HttpMethod.Post, "/storage/upload", request)
            ?? throw new InvalidOperationException("Private upload could not be prepared.");
        using var form = new MultipartFormDataContent();
        foreach (var field in post.Fields) form.Add(new StringContent(field.Value), field.Key);
        var body = new ByteArrayContent(bytes);
        body.Headers.ContentType = MediaTypeHeaderValue.Parse(contentType);
        form.Add(body, "file", Path.GetFileName(key));
        using var result = await http.PostAsync(post.Url, form);
        result.EnsureSuccessStatusCode();
    }

    public async Task<StorageList?> ListAsync(string prefix = "maps/")
        => await SendAsync<StorageList>(HttpMethod.Get, "/storage/list?prefix=" + Uri.EscapeDataString(prefix));

    public async Task<string?> DownloadUrlAsync(string key)
        => (await SendAsync<DownloadResponse>(HttpMethod.Get, "/storage/download?key=" + Uri.EscapeDataString(key)))?.Url;

    public async Task<T?> DownloadJsonAsync<T>(string key)
    {
        var url = await DownloadUrlAsync(key);
        if (string.IsNullOrWhiteSpace(url)) return default;
        using var response = await http.GetAsync(url);
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound) return default;
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<T>();
    }

    private async Task<T?> SendAsync<T>(HttpMethod method, string path, object? body = null)
    {
        using var request = new HttpRequestMessage(method, _apiBaseUrl + path);
        if (!string.IsNullOrWhiteSpace(_sessionToken))
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _sessionToken);
        if (body is not null)
            request.Content = JsonContent.Create(body);
        using var response = await http.SendAsync(request);
        if (response.StatusCode == System.Net.HttpStatusCode.Unauthorized) return default;
        response.EnsureSuccessStatusCode();
        if (response.StatusCode == System.Net.HttpStatusCode.NoContent) return default;
        return await response.Content.ReadFromJsonAsync<T>();
    }

    private async Task<T?> ReadLocalAsync<T>(string key)
    {
        try
        {
            var raw = await js.InvokeAsync<string?>("localStorage.getItem", key);
            return string.IsNullOrWhiteSpace(raw) ? default : JsonSerializer.Deserialize<T>(raw);
        }
        catch { return default; }
    }

    private async Task WriteLocalAsync<T>(string key, T value)
        => await js.InvokeVoidAsync("localStorage.setItem", key, JsonSerializer.Serialize(value));

    private async Task ClearSignupDraftAsync()
    {
        await js.InvokeVoidAsync("localStorage.removeItem", "rist.signup.alias");
        await js.InvokeVoidAsync("localStorage.removeItem", "rist.signup.plan");
        await js.InvokeVoidAsync("localStorage.removeItem", "rist.signup.termsAccepted");
        await ClearAuthIntentAsync();
    }

    private async Task ClearGuardianDraftAsync()
    {
        await js.InvokeVoidAsync("localStorage.removeItem", GuardianRequestKey);
        await js.InvokeVoidAsync("localStorage.removeItem", GuardianApprovalKey);
        await ClearAuthIntentAsync();
    }

    private async Task ClearAuthIntentAsync()
        => await js.InvokeVoidAsync("localStorage.removeItem", "rist.auth.intent");

    private async Task ClearSessionOnlyAsync()
    {
        _sessionToken = null;
        await js.InvokeVoidAsync("ristAuth.clearSession");
    }

    private async Task ClearSessionAsync() => await ClearSessionOnlyAsync();

    public sealed record AuthConfig(string ApiBaseUrl, string? OwnerDiscordUserId = null);
    public sealed record AuthProfile(string UserId, string DisplayName, string StoragePrefix, bool Age21Verified = false, bool AgeVerificationAvailable = false);
    public sealed record AccountProfile(
        string AccountId,
        string PlayerAlias,
        string Plan,
        DateTimeOffset CreatedAtUtc,
        DateTimeOffset TermsAcceptedAtUtc,
        string TermsVersion,
        bool NsfwAccessEnabled = false,
        DateTimeOffset? Age21AttestedAtUtc = null,
        string? NsfwAttestationVersion = null,
        ContentAccessSettings? ContentAccess = null);
    public sealed record ContentAccessSettings(
        string AccessBand,
        string[] AllowedDescriptors,
        DateTimeOffset? SelfAttestedAtUtc,
        string ConsentVersion,
        DateTimeOffset? GuardianConsentAtUtc,
        string? GuardianConsentVersion,
        string[] GuardianApprovedDescriptors)
    {
        public static ContentAccessSettings Default => new(ContentAllowancePolicy.General, [], null, ContentAllowancePolicy.Version, null, null, []);
    }
    public sealed record GuardianConsentRequest(string ChildUserId, string ChildAccountId, string ChildAlias, string[] RequestedDescriptors, DateTimeOffset RequestedAtUtc, string ConsentVersion);
    public sealed record GuardianConsentApproval(string ChildUserId, string ChildAccountId, string GuardianUserId, string[] ApprovedDescriptors, DateTimeOffset ConsentedAtUtc, string ConsentVersion);
    public sealed record UploadRequest(string Key, string ContentType);
    public sealed record PresignedPost(string Url, Dictionary<string,string> Fields);
    public sealed record DownloadResponse(string Url);
    public sealed record StorageItem(string Key, long Size, DateTimeOffset LastModified);
    public sealed record StorageList(List<StorageItem> Items, bool Truncated);
}
