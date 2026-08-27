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
    public sealed record AuthorityProfile(string UserId, string DisplayName, bool PlatformOwner);
    public sealed record Membership(string? WorldId, string Role);
    public sealed record WorldEntity(string WorldId, string EntityId, long Version, Dictionary<string, object>? State, bool Missing = false);
    public sealed record RealtimeTicket(string Ticket, long ExpiresAt);
}
