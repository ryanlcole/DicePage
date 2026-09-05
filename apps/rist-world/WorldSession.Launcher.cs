using System.Text.Json;

namespace RistWorld;

public sealed partial class WorldSession
{
    private const string LauncherIntentKey = "rist.launch.intent";
    private const string LauncherSettingsKey = "rist.launch.settings";

    /// <summary>
    /// Applies the launcher's one-shot startup choice after the normal world
    /// initialization has completed. /Play owns account/profile flow and launch
    /// intent; /Game owns world state. Direct game sessions remain untouched.
    /// </summary>
    public async Task ApplyLauncherStartupAsync()
    {
        var intent = await js.InvokeAsync<string?>("sessionStorage.getItem", LauncherIntentKey);
        var settingsJson = await js.InvokeAsync<string?>("sessionStorage.getItem", LauncherSettingsKey);
        var isNew = string.Equals(intent, "new", StringComparison.OrdinalIgnoreCase);
        var isLoad = string.Equals(intent, "load", StringComparison.OrdinalIgnoreCase);
        var isPreview = string.Equals(intent, "preview", StringComparison.OrdinalIgnoreCase);

        if (!isNew && !isLoad && !isPreview)
        {
            if (!string.IsNullOrWhiteSpace(settingsJson))
                await js.InvokeVoidAsync("sessionStorage.removeItem", LauncherSettingsKey);
            return;
        }

        var (role, domain) = isPreview
            ? ("Roleplayer", "RIST Sandbox")
            : ParseLauncherSettings(settingsJson);

        // Consume handoff keys first so refreshes cannot replay a partially
        // applied command.
        await js.InvokeVoidAsync("sessionStorage.removeItem", LauncherIntentKey);
        await js.InvokeVoidAsync("sessionStorage.removeItem", LauncherSettingsKey);

        if (isNew)
            ResetToCanonicalOrigin();

        RestoreOperatingMode(IsSandboxDomain(domain) ? "sandbox" : "mmo");
        ApplyUserMode(string.Equals(role, "GameMaster", StringComparison.OrdinalIgnoreCase) ? "GameMaster" : "Player");

        // Preview is deliberately read-only because unauthenticated sessions
        // never gain IsLoggedIn/private-storage authority.
        if (isLoad && IsLoggedIn)
        {
            LoadMenuOpen = true;
            SaveMenuOpen = false;
        }

        Notify();
    }

    private static bool IsSandboxDomain(string? domain) =>
        string.Equals(domain, "RIST", StringComparison.OrdinalIgnoreCase) ||
        string.Equals(domain, "RIST Sandbox", StringComparison.OrdinalIgnoreCase) ||
        string.Equals(domain, "Sandbox", StringComparison.OrdinalIgnoreCase);

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
                IsSandboxDomain(domain) ? "RIST Sandbox" : "Shaelvien MMO"
            );
        }
        catch (JsonException)
        {
            return ("Roleplayer", "Shaelvien MMO");
        }
    }
}
