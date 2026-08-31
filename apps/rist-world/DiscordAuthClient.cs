using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using Microsoft.JSInterop;

namespace RistWorld;

public sealed class DiscordAuthClient(HttpClient http, IJSRuntime js)
{
    private const string AccountProfileKey = "account/profile.json";
    private string _apiBaseUrl = "";
    private string? _sessionToken;

    public bool IsConfigured => Uri.TryCreate(_apiBaseUrl, UriKind.Absolute, out _);
    public string OwnerDiscordUserId { get; private set; } = "";
    public AuthProfile? Profile { get; private set; }
    public AccountProfile? Account { get; private set; }
    public string RistAccountId => Account?.AccountId ?? "";
    public bool Age21Verified => Profile?.Age21Verified == true;
    public bool AgeVerificationAvailable => Profile?.AgeVerificationAvailable == true;
    public string LastError { get; private set; } = "";
    public bool IsOwnerDiscordAccount => Profile is not null && !string.IsNullOrWhiteSpace(OwnerDiscordUserId) && string.Equals(Profile.UserId, OwnerDiscordUserId, StringComparison.Ordinal);
    internal string? SessionToken => _sessionToken;

    public async Task<AuthProfile?> InitializeAsync()
    {
        LastError = "";
        Account = null;
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
            catch (HttpRequestException)
            {
                return FailClosedProfileVerification();
            }
            catch (TaskCanceledException)
            {
                return FailClosedProfileVerification();
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
        AccountProfile? saved = null;
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
                TermsVersion: "2026-08-30");

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

        Account = saved;
        await ClearAuthIntentAsync();
        return Profile;
    }

    private AuthProfile? FailClosedProfileVerification()
    {
        Profile = null;
        Account = null;
        LastError = "Your RIST profile could not be verified. Please try again.";
        return null;
    }

    public async Task BeginLoginAsync()
    {
        LastError = "";
        if (!IsConfigured) return;
        await js.InvokeVoidAsync("ristAuth.navigate", _apiBaseUrl + "/auth/login");
    }

    public async Task BeginAgeVerificationAsync()
    {
        LastError = "";
        if (!IsConfigured || string.IsNullOrWhiteSpace(_sessionToken))
        {
            LastError = "Log in before verifying age access.";
            return;
        }

        try
        {
            var result = await SendAsync<AgeVerificationStart>(HttpMethod.Post, "/age/start");
            if (result?.Verified == true)
            {
                await RefreshProfileAsync();
                return;
            }
            if (string.IsNullOrWhiteSpace(result?.Url))
            {
                LastError = "Age verification is not available yet.";
                return;
            }
            await js.InvokeVoidAsync("ristAuth.navigate", result.Url);
        }
        catch
        {
            LastError = "Age verification could not be started. Please try again.";
        }
    }

    public async Task<AuthProfile?> RefreshProfileAsync()
    {
        if (!IsConfigured || string.IsNullOrWhiteSpace(_sessionToken)) return Profile;
        try
        {
            Profile = await SendAsync<AuthProfile>(HttpMethod.Get, "/me");
            return Profile;
        }
        catch
        {
            return Profile;
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
        LastError = "";
        await ClearSignupDraftAsync();
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

    private async Task ClearSignupDraftAsync()
    {
        await js.InvokeVoidAsync("localStorage.removeItem", "rist.signup.alias");
        await js.InvokeVoidAsync("localStorage.removeItem", "rist.signup.plan");
        await js.InvokeVoidAsync("localStorage.removeItem", "rist.signup.termsAccepted");
        await ClearAuthIntentAsync();
    }

    private async Task ClearAuthIntentAsync()
        => await js.InvokeVoidAsync("localStorage.removeItem", "rist.auth.intent");

    private async Task ClearSessionAsync()
    {
        _sessionToken = null;
        await js.InvokeVoidAsync("ristAuth.clearSession");
    }

    public sealed record AuthConfig(string ApiBaseUrl, string? OwnerDiscordUserId = null);
    public sealed record AuthProfile(string UserId, string DisplayName, string StoragePrefix, bool Age21Verified = false, bool AgeVerificationAvailable = false);
    public sealed record AccountProfile(string AccountId, string PlayerAlias, string Plan, DateTimeOffset CreatedAtUtc, DateTimeOffset TermsAcceptedAtUtc, string TermsVersion);
    public sealed record AgeVerificationStart(string? Url, bool Verified = false);
    public sealed record UploadRequest(string Key, string ContentType);
    public sealed record PresignedPost(string Url, Dictionary<string,string> Fields);
    public sealed record DownloadResponse(string Url);
    public sealed record StorageItem(string Key, long Size, DateTimeOffset LastModified);
    public sealed record StorageList(List<StorageItem> Items, bool Truncated);
}
