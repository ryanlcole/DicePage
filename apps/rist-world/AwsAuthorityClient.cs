using System.Text.Json;
using System.Net.Http.Headers;
using System.Net.Http.Json;

namespace RistWorld;

public sealed class AwsAuthorityClient(HttpClient http, DiscordAuthClient auth)
{
    private string _apiBaseUrl = "";
    private string _realtimeUrl = "";

    public bool IsConfigured => Uri.TryCreate(_apiBaseUrl, UriKind.Absolute, out _);
    public string RealtimeUrl => _realtimeUrl;

    public async Task InitializeAsync()
    {
        try
        {
            var cfg = await http.GetFromJsonAsync<AuthorityConfig>("authority-config.json");
            _apiBaseUrl = cfg?.ApiBaseUrl?.TrimEnd('/') ?? "";
            _realtimeUrl = cfg?.RealtimeUrl?.TrimEnd('/') ?? "";
        }
        catch
        {
            _apiBaseUrl = "";
            _realtimeUrl = "";
        }
    }

    public async Task<AuthorityProfile?> GetProfileAsync()
        => await SendAsync<AuthorityProfile>(HttpMethod.Get, "/authority/me");

    public async Task<WorldToken?> CompleteProfileAsync(string accountId, string playerAlias)
        => await SendAsync<WorldToken>(HttpMethod.Post, "/authority/profile-complete", new { accountId, playerAlias });

    public async Task<List<WorldToken>?> GetWorldTokensAsync()
        => await SendAsync<List<WorldToken>>(HttpMethod.Get, "/authority/world-tokens");

    public async Task<CommerceSummary?> GetCommerceSummaryAsync()
        => await SendAsync<CommerceSummary>(HttpMethod.Get, "/authority/commerce");

    public async Task<List<CommerceInvite>?> GetCommerceInvitesAsync()
        => await SendAsync<List<CommerceInvite>>(HttpMethod.Get, "/authority/commerce/invites");

    public async Task<CommerceInvite?> CreateCommerceInviteAsync(
        string planId,
        int expiresInDays,
        int tokenQuantity = 0,
        string label = "")
        => await SendAsync<CommerceInvite>(
            HttpMethod.Post,
            "/authority/commerce/invites",
            new { planId, expiresInDays, tokenQuantity, label });

    public async Task<CommerceRedeemResult?> RedeemCommerceInviteAsync(string code)
        => await SendAsync<CommerceRedeemResult>(
            HttpMethod.Post,
            "/authority/commerce/invites/redeem",
            new { code });

    public async Task<CommerceInvite?> RevokeCommerceInviteAsync(string inviteId)
        => await SendAsync<CommerceInvite>(
            HttpMethod.Post,
            "/authority/commerce/invites/revoke",
            new { inviteId });

    public async Task<CommerceGrant?> GrantCommerceAccessAsync(
        string targetUserId,
        string planId,
        int expiresInDays,
        string source = "complimentary",
        string label = "")
        => await SendAsync<CommerceGrant>(
            HttpMethod.Post,
            "/authority/commerce/grants",
            new { targetUserId, planId, expiresInDays, source, label });

    public async Task<CommerceGrant?> RevokeCommerceGrantAsync(string targetUserId, string grantId)
        => await SendAsync<CommerceGrant>(
            HttpMethod.Post,
            "/authority/commerce/grants/revoke",
            new { targetUserId, grantId });

    public async Task<List<WorldToken>?> MintCommerceTokensAsync(
        string targetUserId,
        int quantity,
        string source = "complimentary",
        string reference = "")
        => await SendAsync<List<WorldToken>>(
            HttpMethod.Post,
            "/authority/commerce/tokens/mint",
            new { targetUserId, quantity, source, reference });

    public async Task<List<MmoParcel>?> GetMmoParcelsAsync(string worldId)
        => await SendAsync<List<MmoParcel>>(HttpMethod.Get,
            "/world/parcels?worldId=" + Uri.EscapeDataString(worldId));

    public async Task<MmoParcel?> ClaimMmoParcelAsync(string worldId, int cellIndex, string displayName, string tokenId = "")
        => await SendAsync<MmoParcel>(HttpMethod.Post, "/world/parcels/claim", new { worldId, cellIndex, displayName, tokenId });

    public async Task<ParcelDelegationUpdate?> DelegateMmoParcelAsync(string worldId, string parcelId, string userId, string permission)
        => await SendAsync<ParcelDelegationUpdate>(HttpMethod.Post, "/world/parcels/delegate",
            new { worldId, parcelId, userId, permission });

    public async Task<List<ParcelDelegation>?> GetMmoParcelDelegationsAsync(string worldId, string parcelId)
        => await SendAsync<List<ParcelDelegation>>(HttpMethod.Get,
            "/world/parcels/delegations?worldId=" + Uri.EscapeDataString(worldId) +
            "&parcelId=" + Uri.EscapeDataString(parcelId));

    public async Task<Membership?> GetMembershipAsync(string worldId)
        => await SendAsync<Membership>(HttpMethod.Get, "/world/membership?worldId=" + Uri.EscapeDataString(worldId));

    public async Task<bool> SetClaimPermissionAsync(string worldId, string userId, string claimPermission)
    {
        var result = await SendAsync<ClaimPermissionUpdate>(
            HttpMethod.Post,
            "/world/membership/claim-permission",
            new { worldId, userId, claimPermission });
        return result?.Ok == true;
    }

    public async Task<WorldEntity?> GetEntityAsync(string worldId, string entityId)
        => await SendAsync<WorldEntity>(HttpMethod.Get, "/world/entity?worldId=" + Uri.EscapeDataString(worldId) + "&entityId=" + Uri.EscapeDataString(entityId));

    public async Task<WorldEntity?> MutateAsync(string worldId, string entityId, string action, object payload, long expectedVersion, string? ownerUserId = null)
        => await SendAsync<WorldEntity>(HttpMethod.Post, "/world/mutate", new { worldId, entityId, action, payload, expectedVersion, ownerUserId });

    public async Task<RealtimeTicket?> CreateRealtimeTicketAsync(string worldId)
        => await SendAsync<RealtimeTicket>(HttpMethod.Post, "/realtime/ticket", new { worldId });

    public async Task<WorldClaimRequest?> SubmitClaimRequestAsync(WorldClaimRequestCreate request)
        => await SendAsync<WorldClaimRequest>(HttpMethod.Post, "/world/claims/request", request);

    public async Task<List<WorldClaimRequest>?> GetClaimRequestsAsync(string worldId, string status = "pending")
        => await SendAsync<List<WorldClaimRequest>>(HttpMethod.Get,
            "/world/claims?worldId=" + Uri.EscapeDataString(worldId) + "&status=" + Uri.EscapeDataString(status));

    public async Task<WorldClaimRequest?> DecideClaimRequestAsync(WorldClaimDecision decision)
        => await SendAsync<WorldClaimRequest>(HttpMethod.Post, "/world/claims/decision", decision);

    public async Task<WorldSource?> GetWorldSourceAsync(string worldId)
        => await SendAsync<WorldSource>(HttpMethod.Get,
            "/world/source?worldId=" + Uri.EscapeDataString(worldId));

    public async Task<WorldSource?> SaveWorldSourceAsync(string worldId, JsonElement state)
        => await SendAsync<WorldSource>(HttpMethod.Post, "/world/source", new { worldId, state });

    public async Task<WorldSource?> SaveWorldRegionMapAsync(string worldId, string regionId, JsonElement userLayers)
        => await SendAsync<WorldSource>(HttpMethod.Post, "/world/source/region", new { worldId, regionId, userLayers });

    public async Task<List<WorldRegion>?> GetRegionsAsync(string worldId)
        => await SendAsync<List<WorldRegion>>(HttpMethod.Get,
            "/world/regions?worldId=" + Uri.EscapeDataString(worldId));

    public async Task<WorldRegion?> SaveRegionAsync(string worldId, WorldRegion region)
        => await SendAsync<WorldRegion>(HttpMethod.Post, "/world/regions", new { worldId, region });

    private async Task<T?> SendAsync<T>(HttpMethod method, string path, object? body = null)
    {
        if (!IsConfigured) return default;
        var token = auth.SessionToken;
        if (string.IsNullOrWhiteSpace(token)) return default;
        using var request = new HttpRequestMessage(method, _apiBaseUrl + path);
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        if (body is not null) request.Content = JsonContent.Create(body);
        using var response = await http.SendAsync(request);
        if (response.StatusCode is System.Net.HttpStatusCode.Unauthorized or System.Net.HttpStatusCode.Forbidden) return default;
        if (!response.IsSuccessStatusCode)
        {
            var message = $"Authority request failed ({(int)response.StatusCode} {response.ReasonPhrase}).";
            try
            {
                var payload = await response.Content.ReadFromJsonAsync<AuthorityError>();
                if (!string.IsNullOrWhiteSpace(payload?.Error)) message = payload.Error.Trim();
            }
            catch { }
            throw new HttpRequestException(message, null, response.StatusCode);
        }
        if (response.StatusCode == System.Net.HttpStatusCode.NoContent) return default;
        return await response.Content.ReadFromJsonAsync<T>();
    }

    public sealed record AuthorityConfig(string ApiBaseUrl, string RealtimeUrl);
    public sealed record AuthorityError(string Error);
    public sealed record AuthorityProfile(
        string UserId,
        string DisplayName,
        bool PlatformOwner,
        List<string>? Entitlements = null,
        int? WorldSlots = null,
        int? SurfaceWorldPixels = null);

    public sealed record WorldToken(
        string TokenId,
        string TokenClass,
        string Status,
        string HolderUserId,
        string PurchasedWorldId = "",
        string ParcelId = "",
        string BindingHash = "",
        string CreatedAtUtc = "",
        string SpentAtUtc = "",
        string Source = "",
        string SourceReference = "");

    public sealed record CommerceSummary(
        List<string>? Entitlements = null,
        List<CommercePlan>? Plans = null,
        List<CommerceGrant>? Grants = null,
        List<WorldToken>? Tokens = null,
        int UnspentTokenCount = 0);

    public sealed record CommercePlan(
        string PlanId,
        string DisplayName,
        int MonthlyUsdCents,
        List<string>? Entitlements = null);

    public sealed record CommerceGrant(
        string GrantId,
        string PlanId,
        List<string>? Entitlements = null,
        string Source = "",
        string Label = "",
        string InviteId = "",
        string CreatedAtUtc = "",
        long ExpiresAtEpoch = 0,
        string RevokedAtUtc = "");

    public sealed record CommerceInvite(
        string InviteId,
        string PlanId,
        string Label = "",
        int TokenQuantity = 0,
        string Status = "",
        string CreatedAtUtc = "",
        long ExpiresAtEpoch = 0,
        string RedeemedAtUtc = "",
        string RedeemedUserId = "",
        string RedeemedGrantId = "",
        string RevokedAtUtc = "",
        string Code = "",
        string RedeemUrl = "");

    public sealed record CommerceRedeemResult(
        bool Ok,
        bool AlreadyRedeemed,
        string GrantId,
        string PlanId,
        int TokenQuantity = 0);

    public sealed record MmoParcel(
        string ParcelId,
        string WorldId,
        string RegionId,
        string DisplayName,
        string OwnerUserId,
        int CellIndex,
        int Column,
        int Row,
        int PixelWidth,
        int PixelHeight,
        int MaxHeight,
        string BindingHash = "",
        string ClaimedAtUtc = "",
        string EffectivePermission = "None");

    public sealed record ParcelDelegation(
        string ParcelId,
        string UserId,
        string Permission,
        string UpdatedAtUtc = "");

    public sealed record ParcelDelegationUpdate(
        bool Ok,
        string ParcelId,
        string UserId,
        string Permission);

    public sealed record Membership(string? WorldId, string Role, string ClaimPermission = "Blocked");
    public sealed record ClaimPermissionUpdate(bool Ok, string ClaimPermission);
    public sealed record WorldSource(string WorldId, JsonElement? State, string UpdatedAtUtc = "");

    public sealed record WorldClaimRequestCreate(
        string WorldId,
        string RequesterUserId,
        string RequesterDisplayName,
        string Workspace,
        int TierIndex,
        List<int> SelectedCells,
        List<int> SourceLayerOffsets,
        string GridShape,
        string RequestedResourceId = "",
        string RequestedName = "");

    public sealed record WorldClaimRequest(
        string RequestId,
        string WorldId,
        string RequesterUserId,
        string RequesterDisplayName,
        string Workspace,
        int TierIndex,
        List<int> SelectedCells,
        List<int> SourceLayerOffsets,
        string GridShape,
        string Status,
        string Permission,
        DateTimeOffset CreatedAtUtc,
        DateTimeOffset UpdatedAtUtc,
        string ApprovedResourceId = "",
        string Note = "",
        string RequestedName = "");

    public sealed record WorldClaimDecision(
        string WorldId,
        string RequestId,
        string Permission,
        List<int>? ApprovedCells = null,
        List<int>? ApprovedLayerOffsets = null,
        string ApprovedResourceId = "",
        string Note = "",
        string WrittenApproval = "");

    public sealed record WorldEntity(string WorldId, string EntityId, long Version, Dictionary<string, object>? State, bool Missing = false, string OwnerUserId = "");
    public sealed record RealtimeTicket(string Ticket, long ExpiresAt);
}
