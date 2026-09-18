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

    public async Task<Membership?> GetMembershipAsync(string worldId)
        => await SendAsync<Membership>(HttpMethod.Get, "/world/membership?worldId=" + Uri.EscapeDataString(worldId));

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
        response.EnsureSuccessStatusCode();
        if (response.StatusCode == System.Net.HttpStatusCode.NoContent) return default;
        return await response.Content.ReadFromJsonAsync<T>();
    }

    public sealed record AuthorityConfig(string ApiBaseUrl, string RealtimeUrl);
    public sealed record AuthorityProfile(
        string UserId,
        string DisplayName,
        bool PlatformOwner,
        List<string>? Entitlements = null,
        int? WorldSlots = null,
        int? SurfaceWorldPixels = null);
    public sealed record Membership(string? WorldId, string Role, string ClaimPermission = "Blocked");

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
