namespace RistWorld;

public sealed partial class WorldSession
{
    public const int LayersPerTier = 5;
    public const int GuestTierCount = 2;

    readonly Dictionary<SpatialAddress,List<TileItem>> _terrainByAddress = [];
    readonly Dictionary<SpatialAddress,List<PieceItem>> _piecesByAddress = [];

    public int CubeX { get; private set; }
    public int CubeY { get; private set; }
    public int CubeZ { get; private set; }
    public WorldCubeRole CubeRole { get; private set; } = WorldCubeRole.GameMaster;
    public int PlaneIndex { get; private set; }
    public int TierIndex { get; private set; }
    public int LayerOffset { get; private set; }
    public int LayerZ => LayerOffset;
    public int SceneZ => checked((TierIndex * LayersPerTier) + LayerOffset);
    public int LocalZ => SceneZ;
    public bool IsSeaLevel => SceneZ == 0;
    public bool IsGianaph => CubeRole == WorldCubeRole.Developer && CubeX == 0 && CubeY == 0 && CubeZ == 0;
    public string WorldCoordinateLabel => $"Cube {CubeX},{CubeY},{CubeZ} • Plane {PlaneIndex} • Tier {TierIndex} • Layer {LayerZ} • z={SceneZ}";

    SpatialAddress CurrentSpatialAddress => new(CubeX,CubeY,CubeZ,PlaneIndex,TierIndex,LayerOffset);

    public List<NpcBoundaryExchange> NpcBoundaryExchanges { get; private set; } = [];

    public void MoveTier(int delta)
    {
        if (delta == 0) return;
        var next=checked(TierIndex+delta);
        if(!IsLoggedIn)next=Math.Clamp(next,0,GuestTierCount-1);
        if(next==TierIndex)return;
        StoreCurrentSpatialPage();
        TierIndex = next;
        LayerOffset = 0;
        LoadCurrentSpatialPage();
        Notify();
    }

    public void MovePlane(int delta)
    {
        if (delta == 0 || !IsLoggedIn) return;
        StoreCurrentSpatialPage();
        PlaneIndex = checked(PlaneIndex + delta);
        LoadCurrentSpatialPage();
        Notify();
    }

    public void MoveLayer(int delta)
    {
        if (delta == 0) return;
        var targetZ = checked(SceneZ + delta);
        if(!IsLoggedIn)targetZ=Math.Clamp(targetZ,0,(GuestTierCount*LayersPerTier)-1);
        var nextTier=FloorDiv(targetZ, LayersPerTier);
        var nextLayer=targetZ-(nextTier*LayersPerTier);
        if(nextTier==TierIndex&&nextLayer==LayerOffset)return;
        StoreCurrentSpatialPage();
        TierIndex = nextTier;
        LayerOffset = nextLayer;
        LoadCurrentSpatialPage();
        Notify();
    }

    public void SetLayerOffset(int offset)
    {
        var next=Math.Clamp(offset,0,LayersPerTier-1);
        if(next==LayerOffset)return;
        StoreCurrentSpatialPage();
        LayerOffset=next;
        LoadCurrentSpatialPage();
        Notify();
    }

    public void SetWorldCube(int x, int y, int z, WorldCubeRole role)
    {
        if(!IsLoggedIn)return;
        if(x==CubeX&&y==CubeY&&z==CubeZ&&role==CubeRole)return;
        StoreCurrentSpatialPage();
        CubeX = x;
        CubeY = y;
        CubeZ = z;
        CubeRole = role;
        LoadCurrentSpatialPage();
        Notify();
    }

    void StoreCurrentSpatialPage()
    {
        var address=CurrentSpatialAddress;
        var terrain=PlacedTiles.Select(tile=>tile with
        {
            CubeX=address.CubeX,
            CubeY=address.CubeY,
            CubeZ=address.CubeZ,
            PlaneIndex=address.PlaneIndex,
            TierIndex=address.TierIndex,
            LayerOffset=address.LayerOffset
        }).ToList();
        var pieces=Pieces.Select(piece=>piece with
        {
            CubeX=address.CubeX,
            CubeY=address.CubeY,
            CubeZ=address.CubeZ,
            PlaneIndex=address.PlaneIndex,
            TierIndex=address.TierIndex,
            LayerOffset=address.LayerOffset
        }).ToList();
        _terrainByAddress[address]=terrain;
        _piecesByAddress[address]=pieces;
        PlacedTiles=terrain;
        Pieces=pieces;
    }

    void LoadCurrentSpatialPage()
    {
        PlacedTiles=_terrainByAddress.TryGetValue(CurrentSpatialAddress,out var tiles)
            ? tiles.ToList()
            : [];
        Pieces=_piecesByAddress.TryGetValue(CurrentSpatialAddress,out var pieces)
            ? pieces.ToList()
            : [];
    }

    List<TileItem> ExportSpatialTerrain()
    {
        StoreCurrentSpatialPage();
        return _terrainByAddress.Values.SelectMany(x=>x).ToList();
    }

    List<PieceItem> ExportSpatialPieces()
    {
        StoreCurrentSpatialPage();
        return _piecesByAddress.Values.SelectMany(x=>x).ToList();
    }

    void ImportSpatialContent(IEnumerable<TileItem>? tiles,IEnumerable<PieceItem>? pieces)
    {
        _terrainByAddress.Clear();
        _piecesByAddress.Clear();
        foreach(var group in (tiles??[]).GroupBy(tile=>new SpatialAddress(
            tile.CubeX,
            tile.CubeY,
            tile.CubeZ,
            tile.PlaneIndex,
            tile.TierIndex,
            Math.Clamp(tile.LayerOffset,0,LayersPerTier-1))))
        {
            _terrainByAddress[group.Key]=group.Select(tile=>tile with{LayerOffset=group.Key.LayerOffset}).ToList();
        }
        foreach(var group in (pieces??[]).GroupBy(piece=>new SpatialAddress(
            piece.CubeX,
            piece.CubeY,
            piece.CubeZ,
            piece.PlaneIndex,
            piece.TierIndex,
            Math.Clamp(piece.LayerOffset,0,LayersPerTier-1))))
        {
            _piecesByAddress[group.Key]=group.Select(piece=>piece with{LayerOffset=group.Key.LayerOffset}).ToList();
        }
        if(!IsLoggedIn)
        {
            foreach(var key in _terrainByAddress.Keys.Where(x=>x.PlaneIndex!=0||x.TierIndex<0||x.TierIndex>=GuestTierCount).ToList())_terrainByAddress.Remove(key);
            foreach(var key in _piecesByAddress.Keys.Where(x=>x.PlaneIndex!=0||x.TierIndex<0||x.TierIndex>=GuestTierCount).ToList())_piecesByAddress.Remove(key);
            PlaneIndex=0;
            TierIndex=Math.Clamp(TierIndex,0,GuestTierCount-1);
        }
        LoadCurrentSpatialPage();
    }

    public bool TryExchangeNpcAcrossBoundary(
        string incomingNpcId,
        string outgoingNpcId,
        int fromCubeX,
        int fromCubeY,
        int fromCubeZ,
        int toCubeX,
        int toCubeY,
        int toCubeZ)
    {
        if (string.IsNullOrWhiteSpace(incomingNpcId) || string.IsNullOrWhiteSpace(outgoingNpcId)) return false;
        if (string.Equals(incomingNpcId, outgoingNpcId, StringComparison.Ordinal)) return false;

        NpcBoundaryExchanges.Add(new NpcBoundaryExchange(
            Guid.NewGuid().ToString("N"),
            incomingNpcId.Trim(),
            outgoingNpcId.Trim(),
            fromCubeX,
            fromCubeY,
            fromCubeZ,
            toCubeX,
            toCubeY,
            toCubeZ,
            DateTimeOffset.UtcNow));
        Notify();
        return true;
    }

    void ResetTopologyToCanonicalOrigin()
    {
        CubeX = 0;
        CubeY = 0;
        CubeZ = 0;
        CubeRole = WorldCubeRole.GameMaster;
        PlaneIndex = 0;
        TierIndex = 0;
        LayerOffset = 0;
        _terrainByAddress.Clear();
        _piecesByAddress.Clear();
        NpcBoundaryExchanges = [];
    }

    static int FloorDiv(int value, int divisor)
    {
        var quotient = value / divisor;
        var remainder = value % divisor;
        if (remainder != 0 && ((remainder < 0) != (divisor < 0))) quotient--;
        return quotient;
    }

    readonly record struct SpatialAddress(int CubeX,int CubeY,int CubeZ,int PlaneIndex,int TierIndex,int LayerOffset);
}
