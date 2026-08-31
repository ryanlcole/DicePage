namespace RistWorld;

public sealed partial class WorldSession
{
    static readonly HashSet<string> AssetRailTypes = new(StringComparer.OrdinalIgnoreCase)
    {
        "all","cards","tokens","minis","rolling-stock","pawns","tiles","terrain","bits"
    };

    public string PublicAssetType { get; private set; } = "all";

    public IReadOnlyList<int> AvailableTierIndices
    {
        get
        {
            var tiers = _terrainByAddress.Keys
                .Concat(_piecesByAddress.Keys)
                .Where(x => x.CubeX == CubeX && x.CubeY == CubeY && x.CubeZ == CubeZ && x.PlaneIndex == PlaneIndex)
                .Select(x => x.TierIndex)
                .Append(TierIndex);

            if (!IsLoggedIn) tiers = tiers.Concat(Enumerable.Range(0, GuestTierCount));
            return tiers.Distinct().Order().ToArray();
        }
    }

    public IReadOnlyList<int> AvailableLayerOffsets
    {
        get
        {
            return _terrainByAddress.Keys
                .Concat(_piecesByAddress.Keys)
                .Where(x => x.CubeX == CubeX && x.CubeY == CubeY && x.CubeZ == CubeZ && x.PlaneIndex == PlaneIndex && x.TierIndex == TierIndex)
                .Select(x => x.LayerOffset)
                .Append(LayerOffset)
                .Append(0)
                .Where(x => x >= 0 && x < LayersPerTier)
                .Distinct()
                .Order()
                .ToArray();
        }
    }

    public bool CanAddTier => IsLoggedIn || AvailableTierIndices.Any(x => x < GuestTierCount - 1);
    public bool CanAddLayer => AvailableLayerOffsets.Count < LayersPerTier;

    public void SetPublicAssetType(string type)
    {
        var normalized = string.IsNullOrWhiteSpace(type) ? "all" : type.Trim().ToLowerInvariant();
        if (!AssetRailTypes.Contains(normalized) || PublicAssetType == normalized) return;
        PublicAssetType = normalized;
        Notify();
    }

    public void NavigateToTier(int tierIndex)
    {
        if (!IsLoggedIn) tierIndex = Math.Clamp(tierIndex, 0, GuestTierCount - 1);
        if (tierIndex == TierIndex) return;
        StoreCurrentSpatialPage();
        TierIndex = tierIndex;
        LayerOffset = 0;
        TouchCurrentSpatialPage();
        LoadCurrentSpatialPage();
        Notify();
    }

    public void NavigateToLayer(int layerOffset)
    {
        var next = Math.Clamp(layerOffset, 0, LayersPerTier - 1);
        if (next == LayerOffset) return;
        StoreCurrentSpatialPage();
        LayerOffset = next;
        TouchCurrentSpatialPage();
        LoadCurrentSpatialPage();
        Notify();
    }

    public void AddTier()
    {
        var known = AvailableTierIndices;
        var next = known.Count == 0 ? 0 : checked(known.Max() + 1);
        if (!IsLoggedIn)
        {
            var missing = Enumerable.Range(0, GuestTierCount).FirstOrDefault(x => !known.Contains(x), -1);
            if (missing < 0) return;
            next = missing;
        }
        StoreCurrentSpatialPage();
        TierIndex = next;
        LayerOffset = 0;
        TouchCurrentSpatialPage();
        LoadCurrentSpatialPage();
        Notify();
    }

    public void AddLayer()
    {
        var known = AvailableLayerOffsets;
        var next = Enumerable.Range(0, LayersPerTier).FirstOrDefault(x => !known.Contains(x), -1);
        if (next < 0) return;
        StoreCurrentSpatialPage();
        LayerOffset = next;
        TouchCurrentSpatialPage();
        LoadCurrentSpatialPage();
        Notify();
    }

    void TouchCurrentSpatialPage()
    {
        var address = CurrentSpatialAddress;
        if (!_terrainByAddress.ContainsKey(address)) _terrainByAddress[address] = [];
        if (!_piecesByAddress.ContainsKey(address)) _piecesByAddress[address] = [];
    }
}
