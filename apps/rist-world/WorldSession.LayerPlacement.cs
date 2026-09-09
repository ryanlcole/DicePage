namespace RistWorld;

public sealed partial class WorldSession
{
    /// <summary>
    /// Places terrain at a layer offset relative to the layer currently being viewed
    /// without changing the viewer's current tier/layer. A delta of +1 means the
    /// immediately adjacent upper layer, not the next tier.
    /// </summary>
    public void AddPlacedTileAtLayerDelta(TileItem tile, int layerDelta)
    {
        StoreCurrentSpatialPage();

        var targetSceneZ = checked(SceneZ + layerDelta);
        if (!IsLoggedIn)
            targetSceneZ = Math.Clamp(targetSceneZ, 0, (GuestTierCount * LayersPerTier) - 1);

        var targetTier = FloorDiv(targetSceneZ, LayersPerTier);
        var targetLayer = targetSceneZ - (targetTier * LayersPerTier);
        var target = new SpatialAddress(CubeX, CubeY, CubeZ, PlaneIndex, targetTier, targetLayer);

        var placed = tile with
        {
            CubeX = CubeX,
            CubeY = CubeY,
            CubeZ = CubeZ,
            PlaneIndex = PlaneIndex,
            TierIndex = targetTier,
            LayerOffset = targetLayer
        };

        if (!_terrainByAddress.TryGetValue(target, out var terrain))
            terrain = [];
        else
            terrain = terrain.ToList();

        terrain.Add(placed);
        _terrainByAddress[target] = terrain;

        // Keep the user on the layer they were editing. The newly placed tile is
        // intentionally invisible until they navigate to its target layer.
        LoadCurrentSpatialPage();
        Notify();
    }
}
