using Microsoft.JSInterop;

namespace RistWorld.Components;

public partial class WorldBuilderStudio
{
    readonly Stack<List<TileItem>> _worldBuilderUndo = new();
    readonly HashSet<int> _selectedPlacedTileIndices = [];

    async Task PersistWorldBuilderAsync()
    {
        await Session.SaveAsync();
        await Session.SaveActiveMapCardAsync(_quickTiles.Select(x => x.Id));
    }

    void PushWorldBuilderUndo()
    {
        _worldBuilderUndo.Push(new List<TileItem>(Session.PlacedTiles));
        while (_worldBuilderUndo.Count > 30)
        {
            var keep = _worldBuilderUndo.Reverse().Take(30).Reverse().ToArray();
            _worldBuilderUndo.Clear();
            foreach (var snapshot in keep) _worldBuilderUndo.Push(snapshot);
        }
    }

    void ClearWorldBuilderSelection() => _selectedPlacedTileIndices.Clear();

    static double FootprintFor(TileItem tile)
    {
        var zoom = Math.Max(tile.PlacementZoom, 1.0 / 1_000_000.0);
        return Math.Clamp(1.0 / zoom, 0.001, 1_000_000.0);
    }

    static string NormalizeTreatment(string? value) => value?.ToLowerInvariant() switch
    {
        "blend" => "blend", "trim" => "crop", "crop" => "crop", _ => "normal"
    };

    static (int Tier, int Layer) SceneAddress(int sceneZ)
    {
        var (tier, layer) = WorldSession.SplitSceneZ(sceneZ);
        return (tier, layer);
    }

    TileItem CreateViewerTile(AtlasTile tile, int column, int row, double footprint, string treatment = "normal")
    {
        footprint = Math.Clamp(footprint, 1.0, WorldSession.GridColumns);
        var x = column / (double)WorldSession.GridColumns;
        var y = row / (double)WorldSession.GridRows;
        var placementZoom = 1.0 / footprint;

        // The GM's raised square construction grid is placement authority. Asset
        // metadata may describe where an asset was authored, but it must never
        // teleport a newly placed tile away from the grid the GM is holding.
        return new TileItem(tile.Id,tile.Name,tile.Image,x,y,tile.SourceWidth,tile.SourceHeight,tile.CropX,tile.CropY,tile.CropWidth,tile.CropHeight,placementZoom)
        {
            CubeX = Session.CubeX, CubeY = Session.CubeY, CubeZ = Session.CubeZ, PlaneIndex = Session.PlaneIndex,
            TierIndex = Session.TierIndex, LayerOffset = Session.LayerOffset,
            RotationQuarterTurns = 0, PlacementTreatment = NormalizeTreatment(treatment),
            AssetKind = tile.AssetKind, AuthoredDepth = tile.AuthoredDepth,
            FrameCount = Math.Max(1, tile.FrameCount), FramesPerSecond = Math.Max(0, tile.FramesPerSecond)
        };
    }

    void AddViewerTile(AtlasTile tile, int column, int row, double footprint = 1, bool upperLayer = false, bool upperTier = false, string treatment = "normal")
    {
        var placed = CreateViewerTile(tile, column, row, footprint, treatment);

        if (upperTier)
        {
            placed = placed with { TierIndex = Session.TierIndex + 1, LayerOffset = Session.LayerOffset };
        }
        else if (upperLayer)
        {
            var address = SceneAddress(Session.SceneZ + 1);
            placed = placed with { TierIndex = address.Tier, LayerOffset = address.Layer };
        }

        // World building deliberately permits unsupported / mid-air placement.
        // The raised GM construction grid is the exact placement plane. Overlap
        // is legal and never infers another layer or gravity/support behavior.
        Session.AddPlacedTileAtGridDepth(placed);
    }

    async Task<(int Column,int Row)?> ViewerCell(double clientX, double clientY, double footprint)
    {
        if (_zModule is null) return null;
        var point = await _zModule.InvokeAsync<double[]?>("viewerGridPoint", _viewerElement, clientX, clientY);
        if (point is null || point.Length < 2) return null;
        var visibleColumns = Math.Min(footprint, WorldSession.GridColumns);
        var visibleRows = Math.Min(footprint, WorldSession.GridRows);
        var maxColumn = Math.Max(0, (int)Math.Floor(WorldSession.GridColumns - visibleColumns));
        var maxRow = Math.Max(0, (int)Math.Floor(WorldSession.GridRows - visibleRows));
        return (Math.Clamp((int)Math.Floor(point[0]*WorldSession.GridColumns),0,maxColumn),Math.Clamp((int)Math.Floor(point[1]*WorldSession.GridRows),0,maxRow));
    }

    [JSInvokable] public Task<int[]> TogglePlacedTileSelection(int index,bool additive){if(index<0||index>=Session.PlacedTiles.Count)return Task.FromResult(_selectedPlacedTileIndices.Order().ToArray());if(!additive)_selectedPlacedTileIndices.Clear();if(!_selectedPlacedTileIndices.Add(index)&&additive)_selectedPlacedTileIndices.Remove(index);return Task.FromResult(_selectedPlacedTileIndices.Order().ToArray());}

    [JSInvokable] public async Task<bool> UndoWorldBuilderFromJs(){if(_worldBuilderUndo.Count==0)return false;var previous=_worldBuilderUndo.Pop();Session.PlacedTiles.Clear();Session.PlacedTiles.AddRange(previous);ClearWorldBuilderSelection();Session.Notify();await PersistWorldBuilderAsync();return true;}

    [JSInvokable] public async Task<int[]> RemoveSelectedTilesFromJs(){if(_selectedPlacedTileIndices.Count==0)return Array.Empty<int>();PushWorldBuilderUndo();foreach(var index in _selectedPlacedTileIndices.Where(i=>i>=0&&i<Session.PlacedTiles.Count).OrderDescending())Session.PlacedTiles.RemoveAt(index);ClearWorldBuilderSelection();Session.Notify();await PersistWorldBuilderAsync();return Array.Empty<int>();}

    [JSInvokable]
    public async Task<bool> PlaceQuickTileFromJs(int quickIndex,double clientX,double clientY)
    {
        if(quickIndex<0||quickIndex>=_quickTiles.Count||_zModule is null||_libraryRailOpen)return false;
        var asset=_quickTiles[quickIndex];

        // Tile Size is an instruction for the NEXT placement. The selected 1²/2²/4²/...
        // footprint wins over catalog defaults so every asset behaves like a physical tile
        // the GM chose to place inside that many construction-grid squares.
        var footprint=Math.Clamp((double)_tileFootprint,1.0,WorldSession.GridColumns);
        var cell=await ViewerCell(clientX,clientY,footprint);if(cell is null)return false;
        PlacementChoice choice;try{choice=await JS.InvokeAsync<PlacementChoice>("ristPlacement.consume");}catch{choice=new(false,false,"normal");}
        PushWorldBuilderUndo();ClearWorldBuilderSelection();AddViewerTile(asset,cell.Value.Column,cell.Value.Row,footprint,choice.UpperLayer,choice.UpperTier,NormalizeTreatment(choice.Treatment));Session.Notify();await PersistWorldBuilderAsync();return true;
    }

    async Task<int[]> MovePlacedTileCore(int index,double clientX,double clientY,bool upperLayer,bool upperTier,string treatment)
    {
        if(index<0||index>=Session.PlacedTiles.Count)return _selectedPlacedTileIndices.Order().ToArray();
        var tile=Session.PlacedTiles[index];var cell=await ViewerCell(clientX,clientY,FootprintFor(tile));if(cell is null)return _selectedPlacedTileIndices.Order().ToArray();
        var moved=tile with
        {
            X=cell.Value.Column/(double)WorldSession.GridColumns,
            Y=cell.Value.Row/(double)WorldSession.GridRows,
            PlacementTreatment=NormalizeTreatment(treatment)
        };
        if(upperTier)
            moved=moved with { TierIndex=tile.TierIndex+1,LayerOffset=tile.LayerOffset };
        else if(upperLayer)
        {
            var address=SceneAddress(WorldSession.SceneZOf(tile)+1);
            moved=moved with { TierIndex=address.Tier,LayerOffset=address.Layer };
        }

        ClearWorldBuilderSelection();_selectedPlacedTileIndices.Add(index);
        if(Session.IsPureStateNoOp(tile,moved))return _selectedPlacedTileIndices.Order().ToArray();

        PushWorldBuilderUndo();
        Session.PlacedTiles[index]=moved;Session.RecordPureStateCommit();Session.Notify();await PersistWorldBuilderAsync();return _selectedPlacedTileIndices.Order().ToArray();
    }

    [JSInvokable] public Task<int[]> MovePlacedTileFromJs(int index,double clientX,double clientY)=>MovePlacedTileCore(index,clientX,clientY,false,false,"normal");

    [JSInvokable]
    public Task<int[]> MovePlacedTileWithPlacementFromJs(int index,double clientX,double clientY,bool upperLayer,bool upperTier,string treatment)=>
        MovePlacedTileCore(index,clientX,clientY,upperLayer,upperTier,treatment);

    [JSInvokable] public async Task<int[]> RotateSelectedTilesFromJs(){if(_selectedPlacedTileIndices.Count==0)return Array.Empty<int>();PushWorldBuilderUndo();foreach(var index in _selectedPlacedTileIndices.Where(i=>i>=0&&i<Session.PlacedTiles.Count)){var tile=Session.PlacedTiles[index];Session.PlacedTiles[index]=tile with {RotationQuarterTurns=(tile.RotationQuarterTurns+1)%4};}Session.Notify();await PersistWorldBuilderAsync();return _selectedPlacedTileIndices.Order().ToArray();}

    [JSInvokable]
    public async Task<int[]> ResizeSelectedTilesFromJs()
    {
        if(_selectedPlacedTileIndices.Count==0)return Array.Empty<int>();
        var footprint=Math.Clamp((double)_tileFootprint,1.0,WorldSession.GridColumns);
        var changes=new List<(int Index,TileItem Tile)>();
        foreach(var index in _selectedPlacedTileIndices.Where(i=>i>=0&&i<Session.PlacedTiles.Count))
        {
            var tile=Session.PlacedTiles[index];
            var resized=tile with {PlacementZoom=1.0/footprint};
            if(!Session.IsPureStateNoOp(tile,resized))changes.Add((index,resized));
        }
        if(changes.Count==0)return _selectedPlacedTileIndices.Order().ToArray();
        PushWorldBuilderUndo();
        foreach(var change in changes)Session.PlacedTiles[change.Index]=change.Tile;
        Session.RecordPureStateCommit(changes.Count);Session.Notify();await PersistWorldBuilderAsync();return _selectedPlacedTileIndices.Order().ToArray();
    }

    [JSInvokable] public async Task<WorldBuilderTileVisual[]> GetWorldBuilderTileVisuals(){var visuals=Session.PlacedTiles.Select((tile,index)=>new WorldBuilderTileVisual(index,tile.RotationQuarterTurns,tile.TierIndex,tile.LayerOffset)).ToArray();try{await JS.InvokeVoidAsync("ristDepth.set",visuals);}catch{}return visuals;}
    [JSInvokable] public Task<WorldBuilderCommandState> GetWorldBuilderCommandState()=>Task.FromResult(new WorldBuilderCommandState("Single",_worldBuilderUndo.Count>0,_selectedPlacedTileIndices.Count));
}

public sealed record PlacementChoice(bool UpperLayer,bool UpperTier,string Treatment);
public sealed record WorldBuilderCommandState(string PlacementMode,bool CanUndo,int SelectedCount);
public sealed record WorldBuilderTileVisual(int Index,int RotationQuarterTurns,int TierIndex,int LayerOffset);
