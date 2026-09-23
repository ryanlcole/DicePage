using System.Text.Json;

namespace RistWorld;

// Region-specific source projection is separate from private WorldBuilder
// source persistence. Both share the canonical world/session authority.
public sealed partial class WorldSession
{
    public async Task<AwsAuthorityClient.WorldSource?> LoadRegionSourceAsync(string regionId)
    {
        if (!HasActiveWorld || !IsLoggedIn) return null;
        var worldId = WorldId;
        var userId = auth.Profile?.UserId?.Trim() ?? "";
        var token = auth.SessionToken;
        var region = _regions.FirstOrDefault(item =>
            string.Equals(item.RegionId, (regionId ?? "").Trim(), StringComparison.Ordinal));
        if (region is null || !IsRegionInActiveWorld(region))
            throw new UnauthorizedAccessException("Region deed does not belong to the active world.");
        var authority = await GetClaimAuthorityClientAsync();
        if (WorldId != worldId || (auth.Profile?.UserId?.Trim() ?? "") != userId || auth.SessionToken != token)
            throw new UnauthorizedAccessException("Active world or session changed during region load.");
        return authority is null ? null : await authority.GetRegionSourceAsync(worldId, region.RegionId);
    }

    public async Task<AwsAuthorityClient.WorldSource?> SaveRegionMapLayersAsync(string regionId, JsonElement userLayers, JsonElement relativeTiers)
    {
        if (!HasActiveWorld)
            throw new InvalidOperationException("Choose a world before saving map changes.");
        if (userLayers.ValueKind != JsonValueKind.Array)
            throw new InvalidOperationException("Region map layers must be an array.");

        var region = _regions.FirstOrDefault(item =>
            string.Equals(item.RegionId, (regionId ?? "").Trim(), StringComparison.Ordinal));
        if (region is null || !CanEditRegion(region))
            throw new UnauthorizedAccessException("Region edit authority is required to save this part of the world map.");

        var authority = await GetClaimAuthorityClientAsync();
        if (authority is null)
            throw new InvalidOperationException("World map database authority is unavailable.");

        return await authority.SaveWorldRegionMapAsync(WorldId, region.RegionId, userLayers, relativeTiers);
    }

}
