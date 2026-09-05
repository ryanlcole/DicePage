using System.Text.Json;

namespace RistWorld;

public sealed partial class WorldSession
{
    private const string LauncherIntentKey = "rist.launch.intent";
    private const string LauncherSettingsKey = "rist.launch.settings";

    /// <summary>
    /// Applies the authenticated launcher's one-shot startup choices after the
    /// normal session/world initialization has completed. Saved map metadata may
    /// not override the role/domain explicitly selected for this launch.
    /// </summary>
    public async Task ApplyLauncherStartupAsync()
    {
        var intent = await js.InvokeAsync<string?>("sessionStorage.getItem", LauncherIntentKey);
        var settingsJson = await js.InvokeAsync<string?>("sessionStorage.getItem", LauncherSettingsKey);
        var isNew = string.Equals(intent, "new", StringComparison.OrdinalIgnoreCase);
        var isLoad = string.Equals(intent, "load", StringComparison.OrdinalIgnoreCase);

        // This method also runs during ordinary restored/direct game sessions.
        // Launcher defaults must never overwrite an already-restored world unless
        // the launcher explicitly handed off a New/Load Campaign intent.
        if (!isNew && !isLoad)
        {
            // Clear any orphaned settings payload so a partial/stale handoff can
            // never become authoritative during a later session initialization.
            if (!string.IsNullOrWhiteSpace(settingsJson))
                await js.InvokeVoidAsync("sessionStorage.removeItem", LauncherSettingsKey);
            return;
        }

        if (isNew)
        {
            // Start a clean in-memory world without destroying the user's
            // previous checkpoint merely because they selected New Campaign.
            ResetToCanonicalOrigin();
        }

        var (role, domain) = ParseLauncherSettings(settingsJson);
        RestoreOperatingMode(string.Equals(domain, "RIST", StringComparison.OrdinalIgnoreCase) ? "sandbox" : "mmo");
        ApplyUserMode(string.Equals(role, "GameMaster", StringComparison.OrdinalIgnoreCase) ? "GameMaster" : "Player");

        // Load Campaign has already been restored by InitializeAsync. Opening the
        // existing load menu makes the intent visible and preserves the current
        // local/private checkpoint controls rather than inventing a second store.
        if (isLoad)
        {
            LoadMenuOpen = true;
            SaveMenuOpen = false;
        }

        await js.InvokeVoidAsync("sessionStorage.removeItem", LauncherIntentKey);
        await js.InvokeVoidAsync("sessionStorage.removeItem", LauncherSettingsKey);
        Notify();
    }

    private static (string Role, string Domain) ParseLauncherSettings(string? json)
    {
        if (string.IsNullOrWhiteSpace(json))
            return ("Roleplayer", "Shaelvien MMO");

        try
        {
            using var doc = JsonDocument.Parse(json);
            var root = doc.RootElement;
            var role = root.TryGetProperty("role", out var roleNode) ? roleNode.GetString() : null;
            var domain = root.TryGetProperty("domain", out var domainNode) ? domainNode.GetString() : null;
            return (
                string.Equals(role, "GameMaster", StringComparison.OrdinalIgnoreCase) ? "GameMaster" : "Roleplayer",
                string.Equals(domain, "RIST", StringComparison.OrdinalIgnoreCase) ? "RIST" : "Shaelvien MMO"
            );
        }
        catch (JsonException)
        {
            return ("Roleplayer", "Shaelvien MMO");
        }
    }
}
