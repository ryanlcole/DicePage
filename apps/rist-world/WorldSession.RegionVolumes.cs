namespace RistWorld;

public sealed partial class WorldSession
{
    /// <summary>
    /// Applies the vertical portion of a Region's canonical bounded volume.
    /// X/Y remain anchored to the same WorldRegion record; this never creates,
    /// crops, or forks World terrain.
    /// </summary>
    public async Task<WorldRegion> ApplyRegionVolumeAsync(
        string regionId,
        int minTierIndex,
        int maxTierIndex)
    {
        regionId = (regionId ?? string.Empty).Trim();
        var index = _regions.FindIndex(region =>
            string.Equals(region.RegionId, regionId, StringComparison.Ordinal));
        if (index < 0)
            throw new InvalidOperationException("The Region volume could not be found.");

        var region = _regions[index];
        if (!CanEditRegion(region))
            throw new UnauthorizedAccessException("Region edit authority is required to define its volume.");

        var maxAllowedTier = IsGeonaphWorld
            ? Math.Max(0, (MmoParcelMaxHeight - 1) / LayersPerTier)
            : 2;

        minTierIndex = Math.Clamp(minTierIndex, 0, maxAllowedTier);
        maxTierIndex = Math.Clamp(maxTierIndex, 0, maxAllowedTier);
        if (maxTierIndex < minTierIndex)
            (minTierIndex, maxTierIndex) = (maxTierIndex, minTierIndex);

        var visibleTiers = Enumerable.Range(
            minTierIndex,
            (maxTierIndex - minTierIndex) + 1).ToList();
        var fullTierLayers = Enumerable.Range(0, LayersPerTier).ToList();
        var now = DateTimeOffset.UtcNow;

        region = region with
        {
            // TierIndex and SourceLayerOffsets remain populated for older clients,
            // but canonical Z is the semantic authority for the Region volume.
            TierIndex = minTierIndex,
            SourceLayerOffsets = fullTierLayers,
            CanonicalZMin = checked(minTierIndex * LayersPerTier),
            CanonicalZMax = checked((maxTierIndex + 1) * LayersPerTier),
            GridShape = "square",
            ResolutionScope = "REGION",
            ViewAngle = 60,
            VisibleTierIndices = visibleTiers,
            VisibleLayerOffsets = fullTierLayers,
            UpdatedAtUtc = now
        };

        _regions[index] = region;
        _activeRegionId = region.RegionId;
        await SaveRegionsAsync();
        return region;
    }

    /// <summary>
    /// Returns inclusive Tier boundaries derived from canonical Z.
    /// CanonicalZMax is stored as an exclusive layer boundary.
    /// </summary>
    public static (int MinTierIndex, int MaxTierIndex) RegionTierBounds(WorldRegion region)
    {
        var minTier = Math.Max(0, region.CanonicalZMin / LayersPerTier);
        var maxLayerInclusive = Math.Max(region.CanonicalZMin, region.CanonicalZMax - 1);
        var maxTier = Math.Max(minTier, maxLayerInclusive / LayersPerTier);
        return (minTier, maxTier);
    }
}
