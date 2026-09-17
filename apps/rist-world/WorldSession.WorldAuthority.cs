using System;

namespace RistWorld;

public sealed partial class WorldSession
{
    private string _trustedAuthorityWorldId = "";
    private string _trustedAuthoritySessionToken = "";
    private string _trustedWorldRole = "";
    private bool _trustedWorldAuthorityLoading;
    private bool _trustedWorldAuthorityResolved;
    private DateTimeOffset _trustedWorldAuthorityRetryAfter = DateTimeOffset.MinValue;

    public string TrustedWorldRole => _trustedWorldRole;

    // Browser role/workspace state is representation only. Worldbuilder capability is
    // granted only after the authenticated AWS authority endpoint confirms membership.
    // Unknown, stale, mismatched, or unavailable authority fails closed.
    public bool HasTrustedWorldBuilderAuthority
    {
        get
        {
            EnsureTrustedWorldAuthorityRequested();
            var sessionToken = auth.SessionToken ?? "";
            return IsLoggedIn
                && HasActiveWorld
                && _trustedWorldAuthorityResolved
                && string.Equals(_trustedAuthorityWorldId, WorldId, StringComparison.Ordinal)
                && string.Equals(_trustedAuthoritySessionToken, sessionToken, StringComparison.Ordinal)
                && string.Equals(_trustedWorldRole, "GM", StringComparison.OrdinalIgnoreCase);
        }
    }

    public async Task RefreshTrustedWorldAuthorityAsync()
    {
        ResetTrustedWorldAuthority();
        await LoadTrustedWorldAuthorityAsync();
    }

    private void EnsureTrustedWorldAuthorityRequested()
    {
        var sessionToken = auth.SessionToken ?? "";
        if (!IsLoggedIn || !HasActiveWorld || string.IsNullOrWhiteSpace(sessionToken))
        {
            if (_trustedWorldAuthorityResolved || _trustedWorldAuthorityLoading || _trustedWorldRole.Length > 0)
                ResetTrustedWorldAuthority();
            return;
        }

        var identityChanged = !string.Equals(_trustedAuthorityWorldId, WorldId, StringComparison.Ordinal)
            || !string.Equals(_trustedAuthoritySessionToken, sessionToken, StringComparison.Ordinal);
        if (identityChanged)
            ResetTrustedWorldAuthority();

        if (_trustedWorldAuthorityLoading)
            return;
        if (_trustedWorldAuthorityResolved && DateTimeOffset.UtcNow < _trustedWorldAuthorityRetryAfter)
            return;

        _ = LoadTrustedWorldAuthorityAsync();
    }

    private async Task LoadTrustedWorldAuthorityAsync()
    {
        var sessionToken = auth.SessionToken ?? "";
        var worldId = WorldId;
        if (!IsLoggedIn || string.IsNullOrWhiteSpace(worldId) || string.IsNullOrWhiteSpace(sessionToken))
            return;

        _trustedWorldAuthorityLoading = true;
        _trustedAuthorityWorldId = worldId;
        _trustedAuthoritySessionToken = sessionToken;
        _trustedWorldRole = "";
        _trustedWorldAuthorityResolved = false;
        Notify();

        try
        {
            var authority = new AwsAuthorityClient(http, auth);
            await authority.InitializeAsync();
            var membership = await authority.GetMembershipAsync(worldId);

            // Ignore any response that arrived after the authenticated identity/world changed.
            if (!string.Equals(WorldId, worldId, StringComparison.Ordinal)
                || !string.Equals(auth.SessionToken ?? "", sessionToken, StringComparison.Ordinal))
                return;

            if (membership is not null
                && string.Equals(membership.WorldId, worldId, StringComparison.Ordinal))
                _trustedWorldRole = membership.Role?.Trim() ?? "";

            _trustedWorldAuthorityResolved = true;
            _trustedWorldAuthorityRetryAfter = DateTimeOffset.UtcNow.AddSeconds(30);
        }
        catch
        {
            // Authority/network uncertainty never becomes permission. Retry later.
            _trustedWorldRole = "";
            _trustedWorldAuthorityResolved = true;
            _trustedWorldAuthorityRetryAfter = DateTimeOffset.UtcNow.AddSeconds(30);
        }
        finally
        {
            _trustedWorldAuthorityLoading = false;
            Notify();
        }
    }

    private void ResetTrustedWorldAuthority()
    {
        _trustedAuthorityWorldId = "";
        _trustedAuthoritySessionToken = "";
        _trustedWorldRole = "";
        _trustedWorldAuthorityLoading = false;
        _trustedWorldAuthorityResolved = false;
        _trustedWorldAuthorityRetryAfter = DateTimeOffset.MinValue;
    }
}
