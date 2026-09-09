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

    IEnumerable<TileItem> TerrainInCurrentPlane()
    {
        return _terrainByAddress
            .Where(pair=>pair.Key.CubeX==CubeX&&pair.Key.CubeY==CubeY&&pair.Key.CubeZ==CubeZ&&pair.Key.PlaneIndex==PlaneIndex)
            .SelectMany(pair=>pair.Value);
    }

    int ClampPlacementSceneZ(int sceneZ)=>IsLoggedIn?sceneZ:Math.Clamp(sceneZ,0,MaxGuestSceneZ);

    void StorePlacedAtSceneZ(TileItem tile,int sceneZ)
    {
        var targetSceneZ=ClampPlacementSceneZ(sceneZ);
        var (tier,layer)=SplitSceneZ(targetSceneZ);
        var target=new SpatialAddress(CubeX,CubeY,CubeZ,PlaneIndex,tier,layer);
        var placed=tile with
        {
            CubeX=CubeX,CubeY=CubeY,CubeZ=CubeZ,PlaneIndex=PlaneIndex,
            TierIndex=tier,LayerOffset=layer
        };
        var terrain=_terrainByAddress.TryGetValue(target,out var existingTerrain)?existingTerrain.ToList():[];
        terrain.Add(placed);
        _terrainByAddress[target]=terrain;
    }

    /// <summary>
    /// Adds terrain on the canonical Z axis. Overlap determines the next free
    /// scene Z naturally; crossing a layer boundary rolls into the next tier.
    /// Tier is therefore derived from stacking rather than chosen independently.
    /// </summary>
    public void AddPlacedTileStacked(TileItem tile,bool forceUpper=false)
    {
        StoreCurrentSpatialPage();

        var candidate=tile with
        {
            CubeX=CubeX,CubeY=CubeY,CubeZ=CubeZ,PlaneIndex=PlaneIndex,
            TierIndex=TierIndex,LayerOffset=LayerOffset
        };

        var currentSceneZ=SceneZ;
        var overlapping=TerrainInCurrentPlane().Where(existing=>TilesOverlap(candidate,existing)).ToList();
        var targetSceneZ=currentSceneZ;
        if(overlapping.Count>0)
            targetSceneZ=Math.Max(targetSceneZ,overlapping.Max(SceneZOf)+1);
        if(forceUpper)
            targetSceneZ=Math.Max(targetSceneZ,currentSceneZ+1);

        StorePlacedAtSceneZ(candidate,targetSceneZ);
        LoadCurrentSpatialPage();
        Notify();
    }

    public void AddPlacedTileAtLayerDelta(TileItem tile,int layerDelta)
    {
        StoreCurrentSpatialPage();
        StorePlacedAtSceneZ(tile,checked(SceneZ+layerDelta));
        LoadCurrentSpatialPage();
        Notify();
    }
}
