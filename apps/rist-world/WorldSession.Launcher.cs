using System.Text.Json;

namespace RistWorld;

public sealed partial class WorldSession
{
    private const string LauncherIntentKey = "rist.launch.intent";
    private const string LauncherSettingsKey = "rist.launch.settings";

    /// <summary>
    /// Applies the authenticated launcher's one-shot startup choice after the
    /// normal session/world initialization has completed. A plain Play handoff
    /// always enters Shaelvien MMO as a Roleplayer. World/campaign creation is
    /// intentionally handled inside the game rather than by authentication.
    /// </summary>
    public async Task ApplyLauncherStartupAsync()
    {
        var intent = await js.InvokeAsync<string?>("sessionStorage.getItem", LauncherIntentKey);
        var settingsJson = await js.InvokeAsync<string?>("sessionStorage.getItem", LauncherSettingsKey);
        var isPlay = string.Equals(intent, "play", StringComparison.OrdinalIgnoreCase);
        var isNew = string.Equals(intent, "new", StringComparison.OrdinalIgnoreCase);
        var isLoad = string.Equals(intent, "load", StringComparison.OrdinalIgnoreCase);

        // This method also runs during ordinary restored/direct game sessions.
        // Launcher defaults must never overwrite an already-restored world unless
        // the launcher explicitly handed off a supported one-shot intent.
        if (!isPlay && !isNew && !isLoad)
        {
            if (!string.IsNullOrWhiteSpace(settingsJson))
                await js.InvokeVoidAsync("sessionStorage.removeItem", LauncherSettingsKey);
            return;
        }

        var (role, domain) = isPlay
            ? ("Roleplayer", "Shaelvien MMO")
            : ParseLauncherSettings(settingsJson);

        // Consume browser handoff keys before mutating world state so refreshes or
        // later initialization cannot replay a partially applied startup command.
        await js.InvokeVoidAsync("sessionStorage.removeItem", LauncherIntentKey);
        await js.InvokeVoidAsync("sessionStorage.removeItem", LauncherSettingsKey);

        if (isNew)
        {
            // Legacy compatibility only. New world/campaign creation now belongs
            // inside the authenticated game rather than the login launcher.
            ResetToCanonicalOrigin();
        }

        RestoreOperatingMode(string.Equals(domain, "RIST", StringComparison.OrdinalIgnoreCase) ? "sandbox" : "mmo");
        ApplyUserMode(string.Equals(role, "GameMaster", StringComparison.OrdinalIgnoreCase) ? "GameMaster" : "Player");

        // Legacy compatibility only. Existing old launcher links can still expose
        // the current load controls without making Load Campaign part of sign-in.
        if (isLoad)
        {
            LoadMenuOpen = true;
            SaveMenuOpen = false;
        }

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