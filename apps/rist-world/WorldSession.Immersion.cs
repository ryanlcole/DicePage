using System.Text.Json;

namespace RistWorld;

public sealed partial class WorldSession
{
    public string ImmersionProfileStorageKey(string regionId, string localId)
    {
        var region = AssetPathSegment((regionId ?? "").Trim());
        var local = AssetPathSegment((localId ?? "").Trim());
        if (region.Length == 0) region = "world";
        if (local.Length == 0) local = "region";
        return $"{WorldStoragePrefix}/immersion/{region}/{local}/profile.json";
    }

    public string ImmersionProfileLocalSaveKey(string regionId, string localId)
        => $"rist.immersion.profile.v1.{WorldId}.{(regionId ?? "").Trim()}.{(localId ?? "").Trim()}";

    public async Task<WorldImmersionProfile?> LoadImmersionProfileAsync(string regionId, string localId)
    {
        if (!HasActiveWorld) return null;
        regionId = (regionId ?? "").Trim();
        localId = (localId ?? "").Trim();

        WorldImmersionProfile? profile = null;
        if (IsLoggedIn)
        {
            try { profile = await auth.DownloadJsonAsync<WorldImmersionProfile>(ImmersionProfileStorageKey(regionId, localId)); }
            catch { }
        }

        if (profile is null)
        {
            try
            {
                var raw = await js.InvokeAsync<string?>("localStorage.getItem", ImmersionProfileLocalSaveKey(regionId, localId));
                if (!string.IsNullOrWhiteSpace(raw))
                    profile = JsonSerializer.Deserialize<WorldImmersionProfile>(raw, MapReadOptions);
            }
            catch { }
        }

        if (profile is null || !string.Equals(profile.WorldId, WorldId, StringComparison.Ordinal))
            return null;
        if (!string.Equals(profile.RegionId ?? "", regionId, StringComparison.Ordinal))
            return null;
        if (!string.Equals(profile.LocalId ?? "", localId, StringComparison.Ordinal))
            return null;
        return profile;
    }

    public async Task<WorldImmersionProfile> SaveImmersionProfileAsync(WorldImmersionProfile profile)
    {
        if (!HasActiveWorld)
            throw new InvalidOperationException("Choose a world before saving an Immersion profile.");
        if (profile is null)
            throw new ArgumentNullException(nameof(profile));
        if (!string.Equals(profile.WorldId, WorldId, StringComparison.Ordinal))
            throw new InvalidOperationException("The Immersion profile does not belong to the active world.");

        var regionId = (profile.RegionId ?? "").Trim();
        var localId = (profile.LocalId ?? "").Trim();
        if (regionId.Length > 0)
        {
            var region = _regions.FirstOrDefault(item => string.Equals(item.RegionId, regionId, StringComparison.Ordinal))
                ?? throw new InvalidOperationException("The selected Region is unavailable.");
            if (!CanEditRegion(region))
                throw new UnauthorizedAccessException("Region edit authority is required to author its Immersion handoff.");
        }
        else if (!HasTrustedWorldBuilderAuthority)
        {
            throw new UnauthorizedAccessException("WorldBuilder authority is required to author a world Immersion profile.");
        }

        if (localId.Length > 0)
        {
            var local = _locals.FirstOrDefault(item =>
                string.Equals(item.LocalId, localId, StringComparison.Ordinal)
                && string.Equals(item.RegionId, regionId, StringComparison.Ordinal));
            if (local is null)
                throw new InvalidOperationException("The selected Local is unavailable.");
        }

        var normalized = profile with
        {
            ProfileId = string.IsNullOrWhiteSpace(profile.ProfileId)
                ? $"immersion-{Guid.NewGuid():N}"
                : profile.ProfileId.Trim(),
            WorldId = WorldId,
            RegionId = regionId,
            LocalId = localId,
            WorldToRegionZoom = Math.Clamp(profile.WorldToRegionZoom, 1.01, 256),
            RegionToLocalZoom = Math.Clamp(
                Math.Max(profile.RegionToLocalZoom, profile.WorldToRegionZoom + 0.01),
                1.02,
                256),
            UpdatedAtUtc = DateTimeOffset.UtcNow
        };

        var json = JsonSerializer.Serialize(normalized, MapWriteOptions);
        await js.InvokeVoidAsync("localStorage.setItem", ImmersionProfileLocalSaveKey(regionId, localId), json);
        if (IsLoggedIn)
            await auth.UploadTextAsync(ImmersionProfileStorageKey(regionId, localId), json, "application/json");
        return normalized;
    }
}

public sealed record WorldImmersionProfile(
    string ProfileId,
    string WorldId,
    string RegionId,
    string LocalId,
    double WorldToRegionZoom,
    double RegionToLocalZoom,
    double FocusX,
    double FocusY,
    string TransitionMode,
    DateTimeOffset UpdatedAtUtc)
{
    public const string Format = "RIST_IMMERSION_PROFILE_V1";
}
