namespace RistWorld;

public sealed partial class WorldSession
{
    static double TileFootprintWidth(TileItem tile)=>Math.Clamp(1.0/Math.Max(tile.PlacementZoom,1.0/300.0),1,GridColumns)/GridColumns;
    static double TileFootprintHeight(TileItem tile)=>Math.Clamp(1.0/Math.Max(tile.PlacementZoom,1.0/300.0),1,GridRows)/GridRows;

    static bool TilesOverlap(TileItem a,TileItem b)
    {
        var aw=TileFootprintWidth(a);var ah=TileFootprintHeight(a);
        var bw=TileFootprintWidth(b);var bh=TileFootprintHeight(b);
        return a.X < b.X+bw && a.X+aw > b.X && a.Y < b.Y+bh && a.Y+ah > b.Y;
    }

    IEnumerable<TileItem> TerrainInCurrentTier()
    {
        var stored=_terrainByAddress
            .Where(pair=>pair.Key.CubeX==CubeX&&pair.Key.CubeY==CubeY&&pair.Key.CubeZ==CubeZ&&pair.Key.PlaneIndex==PlaneIndex&&pair.Key.TierIndex==TierIndex)
            .SelectMany(pair=>pair.Value);
        return stored;
    }

    /// <summary>
    /// Adds terrain to the current tier. Overlapping terrain naturally stacks onto
    /// the next available layer. A forced upper placement always starts at least one
    /// layer above the current focus. Stacking never crosses into another tier.
    /// </summary>
    public void AddPlacedTileStacked(TileItem tile,bool forceUpper=false)
    {
        StoreCurrentSpatialPage();

        var candidate=tile with
        {
            CubeX=CubeX,CubeY=CubeY,CubeZ=CubeZ,PlaneIndex=PlaneIndex,TierIndex=TierIndex,
            LayerOffset=Math.Clamp(LayerOffset,0,LayersPerTier-1)
        };

        var overlapping=TerrainInCurrentTier().Where(existing=>TilesOverlap(candidate,existing)).ToList();
        var targetLayer=LayerOffset;
        if(overlapping.Count>0)targetLayer=Math.Max(targetLayer,overlapping.Max(existing=>existing.LayerOffset)+1);
        if(forceUpper)targetLayer=Math.Max(targetLayer,LayerOffset+1);
        targetLayer=Math.Clamp(targetLayer,0,LayersPerTier-1);

        var target=new SpatialAddress(CubeX,CubeY,CubeZ,PlaneIndex,TierIndex,targetLayer);
        var placed=candidate with{LayerOffset=targetLayer};
        var terrain=_terrainByAddress.TryGetValue(target,out var existingTerrain)?existingTerrain.ToList():[];
        terrain.Add(placed);
        _terrainByAddress[target]=terrain;

        LoadCurrentSpatialPage();
        Notify();
    }

    public void AddPlacedTileAtLayerDelta(TileItem tile,int layerDelta)
    {
        StoreCurrentSpatialPage();
        var targetLayer=Math.Clamp(LayerOffset+layerDelta,0,LayersPerTier-1);
        var target=new SpatialAddress(CubeX,CubeY,CubeZ,PlaneIndex,TierIndex,targetLayer);
        var placed=tile with
        {
            CubeX=CubeX,CubeY=CubeY,CubeZ=CubeZ,PlaneIndex=PlaneIndex,TierIndex=TierIndex,LayerOffset=targetLayer
        };
        var terrain=_terrainByAddress.TryGetValue(target,out var existingTerrain)?existingTerrain.ToList():[];
        terrain.Add(placed);
        _terrainByAddress[target]=terrain;
        LoadCurrentSpatialPage();
        Notify();
    }
}
