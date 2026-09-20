using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text;

namespace RistWorld;

public sealed partial class WorldSession
{
    public const string WorldDeletionConfirmationPhrase = "I Approve The Loss Of All Data For This World.";

    public static string NormalizeWorldDeletionConfirmation(string? value)
    {
        var normalized = (value ?? "").Normalize(NormalizationForm.FormKC).Replace('\u00A0', ' ');
        return string.Join(" ", normalized.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries));
    }

    public static bool WorldDeletionConfirmationMatches(string? value) =>
        string.Equals(NormalizeWorldDeletionConfirmation(value), WorldDeletionConfirmationPhrase, StringComparison.Ordinal);

    public bool CanDeleteWorld(AccountWorldReference? world) =>
        world is not null &&
        string.Equals(world.Relationship, "owner", StringComparison.OrdinalIgnoreCase) &&
        !string.Equals(world.WorldId, GeonaphWorldId, StringComparison.Ordinal);

    public async Task DeleteWorldAsync(AccountWorldReference world, string confirmation)
    {
        if (!IsLoggedIn)
            throw new InvalidOperationException("Log in before deleting a world.");
        if (world is null || string.IsNullOrWhiteSpace(world.WorldId))
            throw new InvalidOperationException("Choose a valid world to delete.");
        if (!CanDeleteWorld(world))
            throw new InvalidOperationException(string.Equals(world.WorldId, GeonaphWorldId, StringComparison.Ordinal)
                ? "Endemar is canonical and cannot be deleted from the world chooser."
                : "Only a world owner may delete that world.");
        if (!WorldDeletionConfirmationMatches(confirmation))
            throw new InvalidOperationException("The deletion approval phrase must match exactly.");
        confirmation = WorldDeletionConfirmationPhrase;

        var sessionToken = auth.SessionToken;
        if (string.IsNullOrWhiteSpace(sessionToken))
            throw new InvalidOperationException("Your authenticated session is not available. Sign in again before deleting a world.");

        var config = await http.GetFromJsonAsync<WorldDeletionAuthConfig>("auth-config.json");
        var apiBaseUrl = config?.ApiBaseUrl?.TrimEnd('/') ?? "";
        if (!Uri.TryCreate(apiBaseUrl, UriKind.Absolute, out _))
            throw new InvalidOperationException("World deletion service is not configured.");

        using var request = new HttpRequestMessage(HttpMethod.Post, apiBaseUrl + "/world/delete");
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", sessionToken);
        request.Content = JsonContent.Create(new
        {
            worldId = world.WorldId,
            confirmation
        });

        using var response = await http.SendAsync(request);
        var payload = await response.Content.ReadAsStringAsync();
        if (!response.IsSuccessStatusCode)
            throw new InvalidOperationException(ReadWorldDeletionError(payload, response.ReasonPhrase));

        // Browser persistence is part of the deleted world's data too.
        await js.InvokeVoidAsync("localStorage.removeItem", $"{SaveKey}.{world.WorldId}");
        await js.InvokeVoidAsync("localStorage.removeItem", $"{OceanResetMarkerKey}.{world.WorldId}");

        if (string.Equals(WorldId, world.WorldId, StringComparison.Ordinal))
        {
            // Clear every in-memory spatial page before releasing the active identity so
            // deleted world data cannot survive in the running browser session.
            ResetToCanonicalOrigin();
            _worldId = "";
            _worldDisplayName = "";
            _activeWorldRelationship = "";
            MapName = "Shaelvien";
            _persistedTruth.Clear();
            PrivateStorageStatus = "World deleted.";
            Notify();
        }
    }

    static string ReadWorldDeletionError(string payload, string? fallback)
    {
        if (!string.IsNullOrWhiteSpace(payload))
        {
            try
            {
                using var document = JsonDocument.Parse(payload);
                if (document.RootElement.TryGetProperty("error", out var error))
                {
                    var message = error.GetString();
                    if (!string.IsNullOrWhiteSpace(message)) return message;
                }
            }
            catch (JsonException)
            {
                // Fall through to the HTTP reason below.
            }
        }

        return string.IsNullOrWhiteSpace(fallback) ? "World deletion failed." : $"World deletion failed: {fallback}";
    }

    sealed record WorldDeletionAuthConfig(string ApiBaseUrl);
}
