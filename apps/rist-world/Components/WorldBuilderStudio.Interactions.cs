using Microsoft.JSInterop;

namespace RistWorld.Components;

public partial class WorldBuilderStudio
{
    readonly Stack<WorldBuilderSnapshot> _worldBuilderUndo = new();
    readonly HashSet<int> _selectedPlacedTileIndices = [];
    string _historyContext = "";
    List<TileItem>? _historyExpected;
    List<RecursiveScopePlacement>? _historyExpectedRecursive;
    string HistoryContext => $"{Session.WorldId}|{Session.ActiveMapCardId}|{Session.Layer}|{Session.CubeX},{Session.CubeY},{Session.CubeZ}|{Session.PlaneIndex}|{Session.TierIndex},{Session.LayerOffset}";
    void ResetWorldBuilderHistory()
    {
        _worldBuilderUndo.Clear();
        ClearWorldBuilderSelection();
        _historyContext = HistoryContext;
        _historyExpected = Session.PlacedTiles.ToList();
        _historyExpectedRecursive = Session.ExportRecursiveScopePlacements();
    }
    void EnsureWorldBuilderHistory()
    {
        if (_historyContext != HistoryContext ||
            (_historyExpected is not null && !_historyExpected.SequenceEqual(Session.PlacedTiles)) ||
            (_historyExpectedRecursive is not null && !_historyExpectedRecursive.SequenceEqual(Session.ExportRecursiveScopePlacements())))
            ResetWorldBuilderHistory();
    }
    bool EditableTile(int index) => Session.CanEditTiles && index >= 0 && index < Session.PlacedTiles.Count &&
        !Session.PlacedTiles[index].Locked &&
        !Session.RecursiveWorldTileLocked(Session.PlacedTiles[index]);

    async Task PersistWorldBuilderAsync()
    {
        _historyExpected = Session.PlacedTiles.ToList();
        _historyExpectedRecursive = Session.ExportRecursiveScopePlacements();
        await Session.SaveAsync();
        await Session.SaveActiveMapCardAsync(_quickTiles.Select(x => x.Id));
    }

    void PushWorldBuilderUndo()
    {
        EnsureWorldBuilderHistory();
        _worldBuilderUndo.Push(new WorldBuilderSnapshot(
            new List<TileItem>(Session.PlacedTiles),
            Session.ExportRecursiveScopePlacements()));
        while (_worldBuilderUndo.Count > 30)
        {
            var keep = _worldBuilderUndo.Take(30).Reverse().ToArray();
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

        // New Worldbuilder content starts on RIST_RECURSIVE_SCOPE_V1. Tier is
        // projected to legacy TierIndex only so the existing renderer can show
        // parallax while it is replaced. Visual Layer never enters LayerOffset.
        return new TileItem(tile.Id,tile.Name,tile.Image,x,y,tile.SourceWidth,tile.SourceHeight,tile.CropX,tile.CropY,tile.CropWidth,tile.CropHeight,placementZoom)
        {
            CubeX = Session.CubeX, CubeY = Session.CubeY, CubeZ = Session.CubeZ, PlaneIndex = Session.PlaneIndex,
            TierIndex = Session.TierIndex, LayerOffset = 0,
            RotationQuarterTurns = 0, PlacementTreatment = NormalizeTreatment(treatment),
            AssetKind = tile.AssetKind, AuthoredDepth = tile.AuthoredDepth,
            FrameCount = Math.Max(1, tile.FrameCount), FramesPerSecond = Math.Max(0, tile.FramesPerSecond),
            PlacementId = $"tile-{Guid.NewGuid():N}",
            TypeId = tile.TypeId,
            GroupId = tile.GroupId,
            ShaepId = Session.ResolveShaepId(tile)
        };
    }

    void AddViewerTile(AtlasTile tile, int column, int row, double footprint = 1, bool upperLayer = false, bool upperTier = false, string treatment = "normal")
    {
        var placed = CreateViewerTile(tile, column, row, footprint, treatment);

        if (upperTier)
            placed = placed with { TierIndex = Session.TierIndex + 1, LayerOffset = 0 };

        // "Upper Layer" is now a GIMP-style composition request. It deliberately
        // does not alter legacy Z. Automatic overlap layering is calculated by the
        // recursive WORLD bridge after the tile has a stable placement identity.
        Session.AddPlacedTileAtGridDepth(placed);
        var index = Session.PlacedTiles.FindIndex(item =>
            string.Equals(item.PlacementId, placed.PlacementId, StringComparison.Ordinal));
        if (index >= 0)
            Session.RegisterNewWorldTilePlacement(index, forceFront: upperLayer);
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

    [JSInvokable] public Task<int[]> TogglePlacedTileSelection(int index,bool additive){EnsureWorldBuilderHistory();if(index<0||index>=Session.PlacedTiles.Count)return Task.FromResult(_selectedPlacedTileIndices.Order().ToArray());if(!additive)_selectedPlacedTileIndices.Clear();if(!_selectedPlacedTileIndices.Add(index)&&additive)_selectedPlacedTileIndices.Remove(index);return Task.FromResult(_selectedPlacedTileIndices.Order().ToArray());}

    [JSInvokable]
    public async Task<bool> UndoWorldBuilderFromJs()
    {
        EnsureWorldBuilderHistory();
        if(!Session.CanEditTiles||_worldBuilderUndo.Count==0)return false;
        var previous=_worldBuilderUndo.Pop();
        Session.PlacedTiles.Clear();
        Session.PlacedTiles.AddRange(previous.Tiles);
        Session.ImportRecursiveScopePlacements(previous.RecursivePlacements);
        ClearWorldBuilderSelection();
        Session.Notify();
        await PersistWorldBuilderAsync();
        return true;
    }

    [JSInvokable]
    public async Task<int[]> RemoveSelectedTilesFromJs()
    {
        EnsureWorldBuilderHistory();
        var removable=_selectedPlacedTileIndices.Where(EditableTile).OrderDescending().ToArray();
        if(removable.Length==0)return Array.Empty<int>();
        PushWorldBuilderUndo();
        var removed=removable.Select(index=>Session.PlacedTiles[index]).ToList();
        foreach(var index in removable)Session.PlacedTiles.RemoveAt(index);
        foreach(var tile in removed)Session.RemoveRecursiveWorldPlacement(tile);
        ClearWorldBuilderSelection();
        Session.Notify();
        await PersistWorldBuilderAsync();
        return Array.Empty<int>();
    }

    [JSInvokable]
    public async Task<bool> PlaceQuickTileFromJs(int quickIndex,double clientX,double clientY)
    {
        if(!Session.CanEditTiles||quickIndex<0||quickIndex>=_quickTiles.Count||_zModule is null||_libraryRailOpen)return false;
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
        EnsureWorldBuilderHistory();
        if(!EditableTile(index))return _selectedPlacedTileIndices.Order().ToArray();
        var tile=Session.PlacedTiles[index];
        var canonical=Session.HasRecursiveWorldPlacement(tile);
        var cell=await ViewerCell(clientX,clientY,FootprintFor(tile));if(cell is null)return _selectedPlacedTileIndices.Order().ToArray();
        var moved=tile with
        {
            X=cell.Value.Column/(double)WorldSession.GridColumns,
            Y=cell.Value.Row/(double)WorldSession.GridRows,
            PlacementTreatment=NormalizeTreatment(treatment)
        };

        if(upperTier)
        {
            moved=moved with
            {
                TierIndex=tile.TierIndex+1,
                LayerOffset=canonical?0:tile.LayerOffset
            };
        }
        else if(upperLayer && !canonical)
        {
            // Legacy content retains its historical SceneZ behavior until it is
            // deliberately migrated. New recursive content never takes this path.
            var address=SceneAddress(WorldSession.SceneZOf(tile)+1);
            moved=moved with { TierIndex=address.Tier,LayerOffset=address.Layer };
        }

        ClearWorldBuilderSelection();_selectedPlacedTileIndices.Add(index);
        if(Session.IsPureStateNoOp(tile,moved) && !(canonical && upperLayer))
            return _selectedPlacedTileIndices.Order().ToArray();

        PushWorldBuilderUndo();
        Session.PlacedTiles[index]=moved;
        if(canonical)
            Session.SyncRecursiveWorldTile(moved.PlacementId, bringForward: upperLayer);
        Session.RecordPureStateCommit();
        Session.Notify();
        await PersistWorldBuilderAsync();
        return _selectedPlacedTileIndices.Order().ToArray();
    }

    [JSInvokable] public Task<int[]> MovePlacedTileFromJs(int index,double clientX,double clientY)=>MovePlacedTileCore(index,clientX,clientY,false,false,"normal");

    [JSInvokable]
    public Task<int[]> MovePlacedTileWithPlacementFromJs(int index,double clientX,double clientY,bool upperLayer,bool upperTier,string treatment)=>
        MovePlacedTileCore(index,clientX,clientY,upperLayer,upperTier,treatment);

    [JSInvokable] public async Task<int[]> RotateSelectedTilesFromJs(){EnsureWorldBuilderHistory();if(!_selectedPlacedTileIndices.Any(EditableTile))return Array.Empty<int>();PushWorldBuilderUndo();foreach(var index in _selectedPlacedTileIndices.Where(EditableTile)){var tile=Session.PlacedTiles[index];Session.PlacedTiles[index]=tile with {RotationQuarterTurns=(tile.RotationQuarterTurns+1)%4};}Session.Notify();await PersistWorldBuilderAsync();return _selectedPlacedTileIndices.Order().ToArray();}

    [JSInvokable]
    public async Task<int[]> ResizeSelectedTilesFromJs()
    {
        EnsureWorldBuilderHistory();
        if(!_selectedPlacedTileIndices.Any(EditableTile))return Array.Empty<int>();
        var footprint=Math.Clamp((double)_tileFootprint,1.0,WorldSession.GridColumns);
        var changes=new List<(int Index,TileItem Tile)>();
        foreach(var index in _selectedPlacedTileIndices.Where(EditableTile))
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
    [JSInvokable] public Task<WorldBuilderCommandState> GetWorldBuilderCommandState(){EnsureWorldBuilderHistory();return Task.FromResult(new WorldBuilderCommandState("Single",Session.CanEditTiles&&_worldBuilderUndo.Count>0,_selectedPlacedTileIndices.Count));}

    sealed record WorldBuilderSnapshot(
        List<TileItem> Tiles,
        List<RecursiveScopePlacement> RecursivePlacements);
}

public sealed record PlacementChoice(bool UpperLayer,bool UpperTier,string Treatment);
public sealed record WorldBuilderCommandState(string PlacementMode,bool CanUndo,int SelectedCount);
public sealed record WorldBuilderTileVisual(int Index,int RotationQuarterTurns,int TierIndex,int LayerOffset);
