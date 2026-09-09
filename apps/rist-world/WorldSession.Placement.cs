namespace RistWorld;

public sealed partial class WorldSession
{
    public void AddPlacedTileAtSceneDelta(TileItem tile, int sceneDelta)
    {
        if (sceneDelta == 0)
        {
            PlacedTiles.Add(tile with
            {
                CubeX = CubeX,
                CubeY = CubeY,
                CubeZ = CubeZ,
                PlaneIndex = PlaneIndex,
                TierIndex = TierIndex,
                LayerOffset = LayerOffset
            });
            Notify();
            return;
        }

        StoreCurrentSpatialPage();
        var targetZ = checked(SceneZ + sceneDelta);
        if (!IsLoggedIn)
            targetZ = Math.Clamp(targetZ, 0, (GuestTierCount * LayersPerTier) - 1);

        var nextTier = FloorDiv(targetZ, LayersPerTier);
        var nextLayer = targetZ - (nextTier * LayersPerTier);
        var address = new SpatialAddress(CubeX, CubeY, CubeZ, PlaneIndex, nextTier, nextLayer);
        if (!_terrainByAddress.TryGetValue(address, out var terrain))
        {
            terrain = [];
            _terrainByAddress[address] = terrain;
        }

        terrain.Add(tile with
        {
            CubeX = CubeX,
            CubeY = CubeY,
            CubeZ = CubeZ,
            PlaneIndex = PlaneIndex,
            TierIndex = nextTier,
            LayerOffset = nextLayer
        });
        Notify();
    }
}