using System.Net.Http.Headers;
using System.Net.Http.Json;

namespace RistWorld;

/// <summary>
/// Human-authenticated operator projection for the server-side external-AI defensive runtime.
/// It exposes no external-agent authentication path.
/// </summary>
public sealed class ExternalAiOperatorClient(HttpClient http, DiscordAuthClient auth)
{
    private string _apiBaseUrl = "";

    public bool IsConfigured => Uri.TryCreate(_apiBaseUrl, UriKind.Absolute, out _);
    public bool OwnerReleased { get; private set; }

    public async Task InitializeAsync()
    {
        try
        {
            var cfg = await http.GetFromJsonAsync<ExternalAiOperatorConfig>("external-ai-config.json");
            _apiBaseUrl = cfg?.ApiBaseUrl?.TrimEnd('/') ?? "";
            OwnerReleased = cfg?.OwnerReleased == true;
        }
        catch
        {
            _apiBaseUrl = "";
            OwnerReleased = false;
        }
    }

    public Task<ExternalAiOperatorStatus?> GetStatusAsync(string worldId, string cubeId, string zoneId)
        => SendAsync<ExternalAiOperatorStatus>(
            HttpMethod.Get,
            "/external-ai/status?worldId=" + Uri.EscapeDataString(worldId) +
            "&cubeId=" + Uri.EscapeDataString(cubeId) +
            "&zoneId=" + Uri.EscapeDataString(zoneId));

    public Task<LifeReplenishmentResponse?> ReplenishLifeAsync(
        string worldId,
        string cubeId,
        string zoneId,
        string agentId,
        int tokens,
        string authorityReference)
        => SendAsync<LifeReplenishmentResponse>(HttpMethod.Post, "/external-ai/life/replenish", new
        {
            worldId,
            cubeId,
            zoneId,
            agentId,
            tokens,
            authorityReference
        });

    public Task<Dictionary<string, object>?> ReviewNpcAsync(
        string worldId,
        string cubeId,
        string zoneId,
        string submissionId,
        NpcSubmissionStatus decision,
        string? notes = null,
        string? canonicalNpcId = null)
        => SendAsync<Dictionary<string, object>>(HttpMethod.Post, "/external-ai/npc/review", new
        {
            worldId,
            cubeId,
            zoneId,
            submissionId,
            decision = decision.ToString(),
            notes,
            canonicalNpcId
        });

    private async Task<T?> SendAsync<T>(HttpMethod method, string path, object? body = null)
    {
        if (!IsConfigured) return default;
        var token = auth.SessionToken;
        if (string.IsNullOrWhiteSpace(token)) return default;

        using var request = new HttpRequestMessage(method, _apiBaseUrl + path);
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        if (body is not null) request.Content = JsonContent.Create(body);
        using var response = await http.SendAsync(request);
        if (response.StatusCode is System.Net.HttpStatusCode.Unauthorized or System.Net.HttpStatusCode.Forbidden)
            return default;
        response.EnsureSuccessStatusCode();
        if (response.StatusCode == System.Net.HttpStatusCode.NoContent) return default;
        return await response.Content.ReadFromJsonAsync<T>();
    }

    public sealed record ExternalAiOperatorConfig(string ApiBaseUrl, bool OwnerReleased);
    public sealed record ExternalAiOperatorStatus(
        bool OwnerReleased,
        int MinimumHumans,
        int MaximumExternalAi,
        string WorldId,
        string CubeId,
        string ZoneId,
        IReadOnlyList<Dictionary<string, object>> Items);
    public sealed record LifeReplenishmentResponse(
        int TokensAdded,
        int LifeTokens,
        bool CanAct,
        bool InfrastructureLimitsChanged);
}
