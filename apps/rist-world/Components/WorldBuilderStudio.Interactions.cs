using Microsoft.JSInterop;

namespace RistWorld.Components;

public partial class WorldBuilderStudio
{
    readonly Stack<List<TileItem>> _worldBuilderUndo = new();
    readonly HashSet<int> _selectedPlacedTileIndices = [];

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

    bool HasLayerSupport(TileItem tile, int layerOffset, int ignoreIndex = -1)
    {
        // Layer 1 (offset 0) is the base surface of every tier. Higher layers
        // require overlapping support from the immediately lower layer in the
        // same cube/plane/tier. A tier itself is an independent elevation band.
        if (layerOffset <= 0) return true;
        for (var i = 0; i < Session.PlacedTiles.Count; i++)
        {
            if (i == ignoreIndex) continue;
            var support = Session.PlacedTiles[i];
            if (support.CubeX != tile.CubeX || support.CubeY != tile.CubeY || support.CubeZ != tile.CubeZ ||
                support.PlaneIndex != tile.PlaneIndex || support.TierIndex != tile.TierIndex ||
                support.LayerOffset != layerOffset - 1)
                continue;
            if (Overlaps(tile, support)) return true;
        }
        return false;
    }

    int ResolveSupportedLayer(TileItem tile, int requestedLayer, int ignoreIndex = -1)
    {
        var layer = Math.Max(0, requestedLayer);
        while (layer > 0 && !HasLayerSupport(tile, layer, ignoreIndex)) layer--;
        return layer;
    }

    TileItem CreateViewerTile(AtlasTile tile, int column, int row, double footprint, string treatment = "normal")
    {
        var x = column / (double)WorldSession.GridColumns;
        var y = row / (double)WorldSession.GridRows;
        var placementZoom = 1.0 / Math.Max(footprint, 0.001);

        return new TileItem(tile.Id,tile.Name,tile.Image,x,y,tile.SourceWidth,tile.SourceHeight,tile.CropX,tile.CropY,tile.CropWidth,tile.CropHeight,placementZoom)
        {
            CubeX = Session.CubeX, CubeY = Session.CubeY, CubeZ = Session.CubeZ, PlaneIndex = Session.PlaneIndex,
            TierIndex = Session.TierIndex, LayerOffset = Session.LayerOffset, RotationQuarterTurns = 0,
            PlacementTreatment = NormalizeTreatment(treatment)
        };
    }

    static string NormalizeTreatment(string? value) => value?.ToLowerInvariant() switch
    {
        "blend" => "blend", "trim" => "crop", "crop" => "crop", _ => "normal"
    };

    void AddViewerTile(AtlasTile tile, int column, int row, double footprint = 1, bool upperLayer = false, bool upperTier = false, string treatment = "normal")
    {
        var placed = CreateViewerTile(tile, column, row, footprint, treatment);
        if (upperTier)
        {
            // Tier is independent structural elevation: it does not require a
            // filled layer stack beneath it and begins on that tier's base layer.
            placed = placed with { TierIndex = Session.TierIndex + 1, LayerOffset = 0 };
            Session.AddPlacedTileStacked(placed, false);
            return;
        }
        if (upperLayer)
        {
            var requested = Math.Max(1, Session.LayerOffset + 1);
            placed = placed with { LayerOffset = ResolveSupportedLayer(placed, requested) };
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

    [JSInvokable] public async Task<bool> UndoWorldBuilderFromJs(){if(_worldBuilderUndo.Count==0)return false;var previous=_worldBuilderUndo.Pop();Session.PlacedTiles.Clear();Session.PlacedTiles.AddRange(previous);ClearWorldBuilderSelection();Session.Notify();await Session.SaveAsync();return true;}

    [JSInvokable] public async Task<int[]> RemoveSelectedTilesFromJs(){if(_selectedPlacedTileIndices.Count==0)return Array.Empty<int>();PushWorldBuilderUndo();foreach(var index in _selectedPlacedTileIndices.Where(i=>i>=0&&i<Session.PlacedTiles.Count).OrderDescending())Session.PlacedTiles.RemoveAt(index);ClearWorldBuilderSelection();Session.Notify();await Session.SaveAsync();return Array.Empty<int>();}

    [JSInvokable]
    public async Task<bool> PlaceQuickTileFromJs(int quickIndex,double clientX,double clientY)
    {
        if(quickIndex<0||quickIndex>=_quickTiles.Count||_zModule is null||_libraryRailOpen)return false;
        var footprint=Math.Clamp((double)_tileFootprint,1.0,WorldSession.GridColumns);var cell=await ViewerCell(clientX,clientY,footprint);if(cell is null)return false;
        PlacementChoice choice;try{choice=await JS.InvokeAsync<PlacementChoice>("ristPlacement.consume");}catch{choice=new(false,false,"normal");}
        PushWorldBuilderUndo();ClearWorldBuilderSelection();AddViewerTile(_quickTiles[quickIndex],cell.Value.Column,cell.Value.Row,footprint,choice.UpperLayer,choice.UpperTier,NormalizeTreatment(choice.Treatment));Session.Notify();await Session.SaveAsync();return true;
    }

    [JSInvokable]
    public async Task<int[]> MovePlacedTileFromJs(int index,double clientX,double clientY)
    {
        if(index<0||index>=Session.PlacedTiles.Count)return _selectedPlacedTileIndices.Order().ToArray();
        var tile=Session.PlacedTiles[index];var cell=await ViewerCell(clientX,clientY,FootprintFor(tile));if(cell is null)return _selectedPlacedTileIndices.Order().ToArray();
        PushWorldBuilderUndo();
        var moved=tile with { X=cell.Value.Column/(double)WorldSession.GridColumns,Y=cell.Value.Row/(double)WorldSession.GridRows };
        // Moving a layered tile off its support degrades only that tile to the
        // highest valid lower layer. Tier elevation remains unchanged.
        moved=moved with { LayerOffset=ResolveSupportedLayer(moved,moved.LayerOffset,index) };
        Session.PlacedTiles[index]=moved;ClearWorldBuilderSelection();_selectedPlacedTileIndices.Add(index);Session.Notify();await Session.SaveAsync();return _selectedPlacedTileIndices.Order().ToArray();
    }

    [JSInvokable] public async Task<int[]> RotateSelectedTilesFromJs(){if(_selectedPlacedTileIndices.Count==0)return Array.Empty<int>();PushWorldBuilderUndo();foreach(var index in _selectedPlacedTileIndices.Where(i=>i>=0&&i<Session.PlacedTiles.Count)){var tile=Session.PlacedTiles[index];Session.PlacedTiles[index]=tile with {RotationQuarterTurns=(tile.RotationQuarterTurns+1)%4};}Session.Notify();await Session.SaveAsync();return _selectedPlacedTileIndices.Order().ToArray();}
    [JSInvokable] public async Task<int[]> ResizeSelectedTilesFromJs(){if(_selectedPlacedTileIndices.Count==0)return Array.Empty<int>();PushWorldBuilderUndo();var footprint=Math.Clamp((double)_tileFootprint,1.0,WorldSession.GridColumns);foreach(var index in _selectedPlacedTileIndices.Where(i=>i>=0&&i<Session.PlacedTiles.Count)){var tile=Session.PlacedTiles[index];var resized=tile with {PlacementZoom=1.0/footprint};resized=resized with {LayerOffset=ResolveSupportedLayer(resized,resized.LayerOffset,index)};Session.PlacedTiles[index]=resized;}Session.Notify();await Session.SaveAsync();return _selectedPlacedTileIndices.Order().ToArray();}
    [JSInvokable] public async Task<WorldBuilderTileVisual[]> GetWorldBuilderTileVisuals(){var visuals=Session.PlacedTiles.Select((tile,index)=>new WorldBuilderTileVisual(index,tile.RotationQuarterTurns,tile.TierIndex,tile.LayerOffset)).ToArray();try{await JS.InvokeVoidAsync("ristDepth.set",visuals);}catch{}return visuals;}
    [JSInvokable] public Task<WorldBuilderCommandState> GetWorldBuilderCommandState()=>Task.FromResult(new WorldBuilderCommandState("Single",_worldBuilderUndo.Count>0,_selectedPlacedTileIndices.Count));
}

public sealed record PlacementChoice(bool UpperLayer,bool UpperTier,string Treatment);
public sealed record WorldBuilderCommandState(string PlacementMode,bool CanUndo,int SelectedCount);
public sealed record WorldBuilderTileVisual(int Index,int RotationQuarterTurns,int TierIndex,int LayerOffset);
