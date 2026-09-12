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

    static bool Overlaps(TileItem a, TileItem b)
    {
        var aw = Math.Min(FootprintFor(a), WorldSession.GridColumns) / WorldSession.GridColumns;
        var ah = Math.Min(FootprintFor(a), WorldSession.GridRows) / WorldSession.GridRows;
        var bw = Math.Min(FootprintFor(b), WorldSession.GridColumns) / WorldSession.GridColumns;
        var bh = Math.Min(FootprintFor(b), WorldSession.GridRows) / WorldSession.GridRows;
        const double epsilon = 1e-9;
        return a.X < b.X + bw - epsilon && a.X + aw > b.X + epsilon &&
               a.Y < b.Y + bh - epsilon && a.Y + ah > b.Y + epsilon;
    }

    bool SameStructuralSpace(TileItem a, TileItem b) =>
        a.CubeX == b.CubeX && a.CubeY == b.CubeY && a.CubeZ == b.CubeZ &&
        a.PlaneIndex == b.PlaneIndex && a.TierIndex == b.TierIndex;

    bool HasLayerSupport(TileItem tile, int layerOffset, int ignoreIndex = -1)
    {
        if (layerOffset <= 0) return true;
        for (var i = 0; i < Session.PlacedTiles.Count; i++)
        {
            if (i == ignoreIndex) continue;
            var support = Session.PlacedTiles[i];
            if (!SameStructuralSpace(tile, support) || support.LayerOffset != layerOffset - 1)
                continue;
            if (Overlaps(tile, support)) return true;
        }
        return false;
    }

    int ResolveSupportedLayer(TileItem tile, int requestedLayer, int ignoreIndex = -1)
    {
        var layer = Math.Clamp(requestedLayer, 0, WorldSession.LayersPerTier - 1);
        while (layer > 0 && !HasLayerSupport(tile, layer, ignoreIndex)) layer--;
        return layer;
    }

    int NextSupportedLayerAt(TileItem tile, int ignoreIndex = -1)
    {
        var highest = -1;
        for (var i = 0; i < Session.PlacedTiles.Count; i++)
        {
            if (i == ignoreIndex) continue;
            var other = Session.PlacedTiles[i];
            if (!SameStructuralSpace(tile, other) || !Overlaps(tile, other)) continue;
            highest = Math.Max(highest, other.LayerOffset);
        }
        return ResolveSupportedLayer(tile, Math.Max(1, highest + 1), ignoreIndex);
    }

    TileItem CreateViewerTile(AtlasTile tile, int column, int row, double footprint, string treatment = "normal")
    {
        if (tile.DefaultFootprint > 0) footprint = tile.DefaultFootprint;
        var x = column / (double)WorldSession.GridColumns;
        var y = row / (double)WorldSession.GridRows;
        var placementZoom = 1.0 / Math.Max(footprint, 0.001);

        return new TileItem(tile.Id,tile.Name,tile.Image,x,y,tile.SourceWidth,tile.SourceHeight,tile.CropX,tile.CropY,tile.CropWidth,tile.CropHeight,placementZoom)
        {
            CubeX = Session.CubeX, CubeY = Session.CubeY, CubeZ = Session.CubeZ, PlaneIndex = Session.PlaneIndex,
            TierIndex = tile.AuthoredDepth ? tile.DefaultTierIndex : Session.TierIndex,
            LayerOffset = tile.AuthoredDepth ? tile.DefaultLayerOffset : Session.LayerOffset,
            RotationQuarterTurns = 0, PlacementTreatment = NormalizeTreatment(treatment),
            AssetKind = tile.AssetKind, AuthoredDepth = tile.AuthoredDepth,
            FrameCount = Math.Max(1, tile.FrameCount), FramesPerSecond = Math.Max(0, tile.FramesPerSecond)
        };
    }

    static string NormalizeTreatment(string? value) => value?.ToLowerInvariant() switch
    {
        "blend" => "blend", "trim" => "crop", "crop" => "crop", _ => "normal"
    };

    void AddViewerTile(AtlasTile tile, int column, int row, double footprint = 1, bool upperLayer = false, bool upperTier = false, string treatment = "normal")
    {
        var placed = CreateViewerTile(tile, column, row, footprint, treatment);
        if (placed.AuthoredDepth && !upperLayer && !upperTier)
        {
            Session.PlacedTiles.Add(placed);
            return;
        }
        if (upperTier)
        {
            placed = placed with { TierIndex = Session.TierIndex + 1, LayerOffset = 0 };
            Session.AddPlacedTileStacked(placed, false);
            return;
        }
        if (upperLayer)
        {
            placed = placed with { LayerOffset = NextSupportedLayerAt(placed) };
            Session.AddPlacedTileStacked(placed, false);
            return;
        }
        placed = placed with { LayerOffset = ResolveSupportedLayer(placed, Session.LayerOffset) };
        Session.AddPlacedTileStacked(placed, false);
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
        var footprint=asset.DefaultFootprint>0?Math.Clamp((double)asset.DefaultFootprint,1.0,WorldSession.GridColumns):Math.Clamp((double)_tileFootprint,1.0,WorldSession.GridColumns);var cell=await ViewerCell(clientX,clientY,footprint);if(cell is null)return false;
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
            moved=moved with { TierIndex=tile.TierIndex+1,LayerOffset=0 };
        else if(upperLayer)
            moved=moved with { LayerOffset=NextSupportedLayerAt(moved,index) };
        else if (!tile.AuthoredDepth)
            moved=moved with { LayerOffset=ResolveSupportedLayer(moved,moved.LayerOffset,index) };

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
            if (!tile.AuthoredDepth) resized=resized with {LayerOffset=ResolveSupportedLayer(resized,resized.LayerOffset,index)};
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
