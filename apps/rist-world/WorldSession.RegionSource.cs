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
        var accountId = WorldOwnerAccountId;
        var userId = auth.Profile?.UserId?.Trim() ?? "";
        var token = auth.SessionToken;
        var region = _regions.FirstOrDefault(item =>
            string.Equals(item.RegionId, (regionId ?? "").Trim(), StringComparison.Ordinal));
        if (region is null || !IsRegionInActiveWorld(region))
            throw new UnauthorizedAccessException("Region deed does not belong to the active world.");

        // Private Sandbox worlds hold the parent map in encrypted user storage,
        // not DynamoDB WORLDSOURCE. Project only the selected tiles in the
        // trusted host before crossing the iframe boundary.
        var privateOwner = await HasOwnedPrivateWorldDescriptorAsync(worldId, accountId);
        if (WorldId != worldId || WorldOwnerAccountId != accountId
            || (auth.Profile?.UserId?.Trim() ?? "") != userId || auth.SessionToken != token)
            throw new UnauthorizedAccessException("Active world or session changed during region load.");

        if (privateOwner)
        {
            var parent = await LoadWorldBuilderSourceAsync();
            if (parent?.State is not { ValueKind: JsonValueKind.Object } parentState)
                throw new InvalidOperationException("Publish the private world map before opening a region.");
            var child = await auth.DownloadJsonAsync<AwsAuthorityClient.WorldSource>(
                $"worlds/{worldId}/region-maps/{region.RegionId}.json");
            if (child is not null && !string.Equals(child.WorldId, worldId, StringComparison.Ordinal))
                throw new UnauthorizedAccessException("Private region state belongs to another world.");
            if (WorldId != worldId || WorldOwnerAccountId != accountId
                || (auth.Profile?.UserId?.Trim() ?? "") != userId || auth.SessionToken != token)
                throw new UnauthorizedAccessException("World or account changed while projecting the private region.");
            var projected = RegionSourceProjector.Project(
                worldId, region.RegionId, region.ParentNodeId, region.TierIndex,
                region.SelectedCells, region.GridShape,
                region.SourceLayerOffsets ?? Enumerable.Range(0, 10),
                parentState, child?.State);
            return new AwsAuthorityClient.WorldSource(worldId, projected,
                child?.UpdatedAtUtc ?? parent.UpdatedAtUtc);
        }

        var authority = await GetClaimAuthorityClientAsync();
        if (WorldId != worldId || WorldOwnerAccountId != accountId
            || (auth.Profile?.UserId?.Trim() ?? "") != userId || auth.SessionToken != token)
            throw new UnauthorizedAccessException("Active world or session changed during region load.");
        return authority is null ? null : await authority.GetRegionSourceAsync(worldId, region.RegionId);
    }

    public async Task<AwsAuthorityClient.WorldSource?> SaveRegionMapLayersAsync(
        string regionId, JsonElement userLayers, JsonElement relativeTiers)
    {
        if (!HasActiveWorld || !IsLoggedIn)
            throw new InvalidOperationException("Choose a world before saving map changes.");
        if (userLayers.ValueKind != JsonValueKind.Array || relativeTiers.ValueKind != JsonValueKind.Array)
            throw new InvalidOperationException("Regional layers and tiers must be arrays.");

        var worldId = WorldId;
        var accountId = WorldOwnerAccountId;
        var token = auth.SessionToken;
        var region = _regions.FirstOrDefault(item =>
            string.Equals(item.RegionId, (regionId ?? "").Trim(), StringComparison.Ordinal));
        if (region is null || !IsRegionInActiveWorld(region) || !CanEditRegion(region))
            throw new UnauthorizedAccessException("Region edit authority is required.");

        var privateOwner = await HasOwnedPrivateWorldDescriptorAsync(worldId, accountId);
        if (WorldId != worldId || WorldOwnerAccountId != accountId || auth.SessionToken != token)
            throw new UnauthorizedAccessException("Active world or account changed while saving region.");

        if (privateOwner)
        {
            var normalized = RegionSourceProjector.NormalizeChild(
                worldId, region.RegionId, region.ParentNodeId, region.TierIndex,
                region.SelectedCells, region.GridShape, userLayers, relativeTiers);
            var source = new AwsAuthorityClient.WorldSource(worldId, normalized, DateTimeOffset.UtcNow.ToString("O"));
            await auth.UploadTextAsync($"worlds/{worldId}/region-maps/{region.RegionId}.json",
                JsonSerializer.Serialize(source, MapWriteOptions), "application/json");
            return source;
        }

        var authority = await GetClaimAuthorityClientAsync();
        if (WorldId != worldId || WorldOwnerAccountId != accountId || auth.SessionToken != token)
            throw new UnauthorizedAccessException("Active world or account changed while saving region.");
        if (authority is null)
            throw new InvalidOperationException("World map database authority is unavailable.");
        return await authority.SaveWorldRegionMapAsync(worldId, region.RegionId, userLayers, relativeTiers);
    }

}
