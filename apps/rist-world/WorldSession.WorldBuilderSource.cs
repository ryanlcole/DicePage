using System.Text.Json;

namespace RistWorld;

public sealed partial class WorldSession
{
    public async Task<AwsAuthorityClient.WorldSource?> LoadWorldBuilderSourceAsync()
    {
        if (!IsLoggedIn || !HasActiveWorld) return null;
        var authority = await GetClaimAuthorityClientAsync();
        return authority is null ? null : await authority.GetWorldSourceAsync(WorldId);
    }

    public async Task<AwsAuthorityClient.WorldSource?> SaveRegionMapLayersAsync(string regionId, JsonElement userLayers)
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

        return await authority.SaveWorldRegionMapAsync(WorldId, region.RegionId, userLayers);
    }

    public async Task<AwsAuthorityClient.WorldSource?> SaveWorldBuilderSourceAsync(JsonElement state)
    {
        if (!HasTrustedWorldBuilderAuthority)
            throw new UnauthorizedAccessException("World Builder authority is required to save the canonical world map.");
        if (!HasActiveWorld)
            throw new InvalidOperationException("Choose a world before saving the shared world source.");
        if (state.ValueKind != JsonValueKind.Object)
            throw new InvalidOperationException("World map state must be an object.");

        if (state.TryGetProperty("worldId", out var stateWorldId))
        {
            var value = stateWorldId.GetString()?.Trim() ?? "";
            if (value.Length > 0 && !string.Equals(value, WorldId, StringComparison.Ordinal))
                throw new InvalidOperationException("World map identity does not match the active world.");
        }

        var authority = await GetClaimAuthorityClientAsync();
        if (authority is null)
            throw new InvalidOperationException("World map database authority is unavailable.");

        return await authority.SaveWorldSourceAsync(WorldId, state);
    }
}
