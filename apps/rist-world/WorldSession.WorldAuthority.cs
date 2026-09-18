using System;

namespace RistWorld;

public sealed partial class WorldSession
{
    private string _trustedAuthorityWorldId = "";
    private string _trustedAuthoritySessionToken = "";
    private string _trustedWorldRole = "";
    private WorldClaimPermission _trustedClaimPermission = WorldClaimPermission.Blocked;
    private bool _trustedPlatformOwner;
    private bool _trustedWorldAuthorityLoading;
    private bool _trustedWorldAuthorityResolved;
    private DateTimeOffset _trustedWorldAuthorityRetryAfter = DateTimeOffset.MinValue;

    public string TrustedWorldRole => _trustedWorldRole;
    public WorldClaimPermission TrustedClaimPermission => _trustedClaimPermission;
    public bool TrustedPlatformOwner => _trustedPlatformOwner;

    // Browser role/workspace state is representation only. Worldbuilder capability is
    // granted only after the authenticated AWS authority endpoint confirms either
    // platform-owner authority or a GM/owner membership for the selected world.
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
                && (_trustedPlatformOwner || IsTrustedWorldBuilderRole(_trustedWorldRole));
        }
    }

    public bool CanRequestWorldClaim
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
                && !_trustedPlatformOwner
                && !IsTrustedWorldBuilderRole(_trustedWorldRole)
                && WorldClaimAuthorityPolicy.CanSubmitRequest(_trustedClaimPermission);
        }
    }

    private static bool IsTrustedWorldBuilderRole(string? role) =>
        string.Equals(role, "GM", StringComparison.OrdinalIgnoreCase)
        || string.Equals(role, "owner", StringComparison.OrdinalIgnoreCase);

    private static WorldClaimPermission ParseClaimPermission(string? value)
    {
        var normalized = (value ?? "").Trim().Replace("-", "", StringComparison.Ordinal).Replace("_", "", StringComparison.Ordinal);
        return normalized.ToLowerInvariant() switch
        {
            "restricted" => WorldClaimPermission.Restricted,
            "limited" => WorldClaimPermission.Limited,
            "cooperative" => WorldClaimPermission.Cooperative,
            "releaseownership" => WorldClaimPermission.ReleaseOwnership,
            _ => WorldClaimPermission.Blocked
        };
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
            if (_trustedWorldAuthorityResolved || _trustedWorldAuthorityLoading || _trustedPlatformOwner || _trustedWorldRole.Length > 0)
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
        _trustedClaimPermission = WorldClaimPermission.Blocked;
        _trustedPlatformOwner = false;
        _trustedWorldAuthorityResolved = false;
        Notify();

        try
        {
            var authority = new AwsAuthorityClient(http, auth);
            await authority.InitializeAsync();

            AwsAuthorityClient.AuthorityProfile? profile = null;
            AwsAuthorityClient.Membership? membership = null;
            var receivedAuthority = false;

            try
            {
                profile = await authority.GetProfileAsync();
                receivedAuthority = profile is not null;
            }
            catch
            {
                // A membership response can still authorize a GM if the profile lookup
                // is temporarily unavailable.
            }

            try
            {
                membership = await authority.GetMembershipAsync(worldId);
                receivedAuthority = receivedAuthority || membership is not null;
            }
            catch
            {
                // Platform-owner authority can still authorize the owner if membership
                // lookup is temporarily unavailable.
            }

            if (!receivedAuthority)
                throw new InvalidOperationException("Trusted authority could not be resolved.");

            // Ignore any response that arrived after the authenticated identity/world changed.
            if (!string.Equals(WorldId, worldId, StringComparison.Ordinal)
                || !string.Equals(auth.SessionToken ?? "", sessionToken, StringComparison.Ordinal))
                return;

            _trustedPlatformOwner = profile?.PlatformOwner == true;
            if (membership is not null
                && string.Equals(membership.WorldId, worldId, StringComparison.Ordinal))
            {
                _trustedWorldRole = membership.Role?.Trim() ?? "";
                _trustedClaimPermission = ParseClaimPermission(membership.ClaimPermission);
            }

            _trustedWorldAuthorityResolved = true;
            _trustedWorldAuthorityRetryAfter = DateTimeOffset.UtcNow.AddSeconds(30);
        }
        catch
        {
            // Authority/network uncertainty never becomes permission. Retry later.
            _trustedWorldRole = "";
            _trustedClaimPermission = WorldClaimPermission.Blocked;
            _trustedPlatformOwner = false;
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
        _trustedClaimPermission = WorldClaimPermission.Blocked;
        _trustedPlatformOwner = false;
        _trustedWorldAuthorityLoading = false;
        _trustedWorldAuthorityResolved = false;
        _trustedWorldAuthorityRetryAfter = DateTimeOffset.MinValue;
    }
}
