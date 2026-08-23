using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using Microsoft.JSInterop;

namespace RistWorld;

public sealed class DiscordAuthClient(HttpClient http, IJSRuntime js)
{
    private string _apiBaseUrl = "";
    private string? _sessionToken;

    public bool IsConfigured => Uri.TryCreate(_apiBaseUrl, UriKind.Absolute, out _);
    public AuthProfile? Profile { get; private set; }

    public async Task<AuthProfile?> InitializeAsync()
    {
        try
        {
            var config = await http.GetFromJsonAsync<AuthConfig>("auth-config.json");
            _apiBaseUrl = config?.ApiBaseUrl?.TrimEnd('/') ?? "";
            _sessionToken = await js.InvokeAsync<string?>("ristAuth.captureSession", _apiBaseUrl);
            if (!IsConfigured || string.IsNullOrWhiteSpace(_sessionToken)) return null;
            Profile = await SendAsync<AuthProfile>(HttpMethod.Get, "/me");
            if (Profile is null) await ClearSessionAsync();
            return Profile;
        }
        catch
        {
            await ClearSessionAsync();
            return null;
        }
    }

    public async Task BeginLoginAsync()
    {
        if (!IsConfigured) return;
        await js.InvokeVoidAsync("ristAuth.navigate", _apiBaseUrl + "/auth/login");
    }

    public async Task LogoutAsync()
    {
        if (IsConfigured && !string.IsNullOrWhiteSpace(_sessionToken))
        {
            try { await SendAsync<object>(HttpMethod.Post, "/auth/logout"); } catch { }
        }
        Profile = null;
        await ClearSessionAsync();
    }

    public async Task DeleteAccountAsync()
    {
        if (IsConfigured && !string.IsNullOrWhiteSpace(_sessionToken))
            await SendAsync<object>(HttpMethod.Post, "/account/delete");
        Profile = null;
        await ClearSessionAsync();
    }

    public async Task UploadTextAsync(string key, string text, string contentType)
    {
        var request = new UploadRequest(key, contentType);
        var post = await SendAsync<PresignedPost>(HttpMethod.Post, "/storage/upload", request)
            ?? throw new InvalidOperationException("Private upload could not be prepared.");
        using var form = new MultipartFormDataContent();
        foreach (var field in post.Fields) form.Add(new StringContent(field.Value), field.Key);
        var bytes = new ByteArrayContent(Encoding.UTF8.GetBytes(text));
        bytes.Headers.ContentType = MediaTypeHeaderValue.Parse(contentType);
        form.Add(bytes, "file", Path.GetFileName(key));
        using var result = await http.PostAsync(post.Url, form);
        result.EnsureSuccessStatusCode();
    }

    public async Task<StorageList?> ListAsync(string prefix = "maps/")
        => await SendAsync<StorageList>(HttpMethod.Get, "/storage/list?prefix=" + Uri.EscapeDataString(prefix));

    public async Task<string?> DownloadUrlAsync(string key)
        => (await SendAsync<DownloadResponse>(HttpMethod.Get, "/storage/download?key=" + Uri.EscapeDataString(key)))?.Url;

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

    private async Task ClearSessionAsync()
    {
        _sessionToken = null;
        await js.InvokeVoidAsync("ristAuth.clearSession");
    }

    public sealed record AuthConfig(string ApiBaseUrl);
    public sealed record AuthProfile(string UserId, string DisplayName, string StoragePrefix);
    public sealed record UploadRequest(string Key, string ContentType);
    public sealed record PresignedPost(string Url, Dictionary<string,string> Fields);
    public sealed record DownloadResponse(string Url);
    public sealed record StorageItem(string Key, long Size, DateTimeOffset LastModified);
    public sealed record StorageList(List<StorageItem> Items, bool Truncated);
}
