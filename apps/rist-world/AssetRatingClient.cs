using System.Net.Http.Headers;
using System.Net.Http.Json;

namespace RistWorld;

public sealed class AssetRatingClient(HttpClient http, DiscordAuthClient auth)
{
    private string _apiBaseUrl = "";

    private async Task EnsureConfiguredAsync()
    {
        if (!string.IsNullOrWhiteSpace(_apiBaseUrl)) return;
        var config = await http.GetFromJsonAsync<DiscordAuthClient.AuthConfig>("auth-config.json");
        _apiBaseUrl = config?.ApiBaseUrl?.TrimEnd('/') ?? "";
        if (!Uri.TryCreate(_apiBaseUrl, UriKind.Absolute, out _))
            throw new InvalidOperationException("Asset rating service is not configured.");
    }

    public async Task<AssetRating?> RegisterAsync(string assetId, IEnumerable<string> providerDescriptors, bool explicitGeneral)
        => await SendAsync<AssetRating>(HttpMethod.Post, "/assets/rating/register",
            new RegisterAssetRating(assetId, providerDescriptors.Distinct(StringComparer.Ordinal).ToArray(), explicitGeneral));

    public async Task<AssetRating?> GetAsync(string assetId)
    {
        try
        {
            return await SendAsync<AssetRating>(HttpMethod.Get, "/assets/rating?assetId=" + Uri.EscapeDataString(assetId));
        }
        catch (HttpRequestException ex) when (ex.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            return null;
        }
    }

    public async Task<AssetRatingReportResult?> ReportAsync(string assetId, IEnumerable<string> suggestedDescriptors, bool explicitGeneral)
        => await SendAsync<AssetRatingReportResult>(HttpMethod.Post, "/assets/rating/report",
            new ReportAssetRating(assetId, suggestedDescriptors.Distinct(StringComparer.Ordinal).ToArray(), explicitGeneral));

    private async Task<T?> SendAsync<T>(HttpMethod method, string path, object? body = null)
    {
        await EnsureConfiguredAsync();
        if (string.IsNullOrWhiteSpace(auth.SessionToken))
            throw new InvalidOperationException("Log in to use asset ratings.");

        using var request = new HttpRequestMessage(method, _apiBaseUrl + path);
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", auth.SessionToken);
        if (body is not null) request.Content = JsonContent.Create(body);
        using var response = await http.SendAsync(request);
        if (response.StatusCode == System.Net.HttpStatusCode.Unauthorized)
            throw new InvalidOperationException("Your login expired. Please log in again.");
        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadFromJsonAsync<ApiError>();
            throw new HttpRequestException(error?.Error ?? "Asset rating request failed.", null, response.StatusCode);
        }
        if (response.StatusCode == System.Net.HttpStatusCode.NoContent) return default;
        return await response.Content.ReadFromJsonAsync<T>();
    }

    public sealed record RegisterAssetRating(string AssetId, string[] ProviderDescriptors, bool ExplicitGeneral);
    public sealed record ReportAssetRating(string AssetId, string[] SuggestedDescriptors, bool ExplicitGeneral);
    public sealed record AssetRating(
        string AssetId,
        string[] ProviderDescriptors,
        string[] EffectiveDescriptors,
        int UniqueReportCount,
        bool ManualReviewRequired,
        bool AutoRestricted,
        string RatingVersion);
    public sealed record AssetRatingReportResult(
        string AssetId,
        string[] EffectiveDescriptors,
        int UniqueReportCount,
        bool ManualReviewRequired,
        bool AutoRestricted,
        bool RestrictionChanged);
    private sealed record ApiError(string Error);
}
