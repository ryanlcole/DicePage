namespace RistWorld;

public sealed partial class WorldSession
{
    // AuthenticatedWorld establishes the Discord/AWS account before the launcher hub
    // is rendered. Adopt that already-verified identity here so launcher-only surfaces
    // (especially My Worlds / WorldGate) do not behave like an anonymous visitor until
    // a gameplay workspace happens to initialize the full WorldSession.
    public string AuthenticationProvider { get; private set; } = "";
    public DateTimeOffset? AuthenticationExpiresAtUtc { get; private set; }

    public void AdoptAuthentication(DiscordAuthClient.AuthProfile? profile)
    {
        IsLoggedIn = profile is not null;
        DiscordDisplayName = profile?.DisplayName ?? "";
        AuthenticationProvider = profile?.AuthProvider ?? "";
        AuthenticationExpiresAtUtc = profile is not null && profile.SessionExpiresAt > 0
            ? DateTimeOffset.FromUnixTimeSeconds(profile.SessionExpiresAt)
            : null;

        if (!IsLoggedIn)
            Role = "PC";

        PrivateStorageStatus = IsLoggedIn
            ? "Private AWS storage ready."
            : auth.IsConfigured
                ? "Log in with Discord to use private storage."
                : "Discord login is awaiting AWS deployment.";

        Notify();
    }
}
