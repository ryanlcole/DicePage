namespace RistWorld;

public sealed partial class WorldSession
{
    public const int IncludedOwnedWorldSlots = 5; // Public-alpha testing allowance for private/sandbox worlds. The Shaelvien MMO world is excluded below.
    public const int IncludedSurfaceWorldPixels = 2048;

    private bool _commerceProfileLoaded;
    private bool _commercePlatformOwner;
    private int _commerceWorldSlots = IncludedOwnedWorldSlots;
    private int _commerceSurfaceWorldPixels = IncludedSurfaceWorldPixels;
    private HashSet<string> _commerceEntitlements = new(StringComparer.OrdinalIgnoreCase);

    public bool CommerceProfileLoaded => _commerceProfileLoaded;
    public bool HasPlatformCommercialOverride => _commercePlatformOwner || auth.IsOwnerDiscordAccount;
    public int? OwnedWorldSlotLimit => HasPlatformCommercialOverride || HasCommerceEntitlement("worlds.unlimited")
        ? null
        : Math.Max(IncludedOwnedWorldSlots, _commerceWorldSlots);

    // The canonical Shaelvien MMO world is governed by developer authority rather than
    // commercial acreage. Everybody else starts at 2048x2048 and can expand only when
    // the account authority service grants a larger surface entitlement.
    public int? SurfaceWorldPixelLimit =>
        IsGeonaphWorld && HasPlatformCommercialOverride
            ? null
            : HasPlatformCommercialOverride || HasCommerceEntitlement("surface.unlimited")
                ? null
                : Math.Max(IncludedSurfaceWorldPixels, _commerceSurfaceWorldPixels);

    public string SurfaceWorldCommercialLabel =>
        SurfaceWorldPixelLimit is int pixels
            ? $"{pixels}×{pixels} px surface"
            : "Developer-controlled surface";

    public string WorldSlotCommercialLabel =>
        OwnedWorldSlotLimit is int slots
            ? $"{slots} owned world{(slots == 1 ? "" : "s")} included"
            : "Developer-controlled world slots";

    public bool HasCommerceEntitlement(string entitlement) =>
        !string.IsNullOrWhiteSpace(entitlement) && _commerceEntitlements.Contains(entitlement.Trim());

    public async Task RefreshCommercialEntitlementsAsync()
    {
        _commerceProfileLoaded = true;
        _commercePlatformOwner = auth.IsOwnerDiscordAccount;
        _commerceWorldSlots = IncludedOwnedWorldSlots;
        _commerceSurfaceWorldPixels = IncludedSurfaceWorldPixels;
        _commerceEntitlements.Clear();

        if (!IsLoggedIn) return;

        try
        {
            var authority = new AwsAuthorityClient(http, auth);
            await authority.InitializeAsync();
            var profile = await authority.GetProfileAsync();
            if (profile is null) return;

            _commercePlatformOwner = profile.PlatformOwner || auth.IsOwnerDiscordAccount;
            _commerceWorldSlots = Math.Max(IncludedOwnedWorldSlots, profile.WorldSlots ?? IncludedOwnedWorldSlots);
            _commerceSurfaceWorldPixels = Math.Max(IncludedSurfaceWorldPixels, profile.SurfaceWorldPixels ?? IncludedSurfaceWorldPixels);

            foreach (var entitlement in profile.Entitlements ?? [])
                if (!string.IsNullOrWhiteSpace(entitlement))
                    _commerceEntitlements.Add(entitlement.Trim());
        }
        catch
        {
            // Commercial capability fails closed to the included allowance.
            // Existing worlds remain loadable; only new paid-only expansion is denied.
        }
        Notify();
    }

    public int CountOwnedCommercialWorlds(IEnumerable<AccountWorldReference> worlds) =>
        worlds.Count(world =>
            IsSandboxWorldReference(world) &&
            string.Equals(world.Relationship, "owner", StringComparison.OrdinalIgnoreCase));

    public bool CanCreateAdditionalOwnedWorld(IEnumerable<AccountWorldReference> worlds)
    {
        var limit = OwnedWorldSlotLimit;
        return limit is null || CountOwnedCommercialWorlds(worlds) < limit.Value;
    }

    public void RequireWorldCreationEntitlement(IEnumerable<AccountWorldReference> worlds)
    {
        if (CanCreateAdditionalOwnedWorld(worlds)) return;
        throw new InvalidOperationException(
            "Your included private/sandbox world allowance is already in use. Additional worlds require an additional world-slot entitlement.");
    }

    public void RequireSurfaceWorldPixels(int requestedPixels)
    {
        if (requestedPixels <= 0)
            throw new ArgumentOutOfRangeException(nameof(requestedPixels));

        var limit = SurfaceWorldPixelLimit;
        if (limit is null || requestedPixels <= limit.Value) return;

        throw new InvalidOperationException(
            $"This world currently includes a {limit.Value}×{limit.Value} px surface. A larger surface requires a surface-expansion entitlement.");
    }
}
