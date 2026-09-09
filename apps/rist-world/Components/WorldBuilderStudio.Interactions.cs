using Microsoft.JSInterop;

namespace RistWorld.Components;

public partial class WorldBuilderStudio
{
    readonly Stack<List<TileItem>> _worldBuilderUndo = new();
    readonly HashSet<int> _selectedPlacedTileIndices = [];
    bool _multiPlacement;

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

    static int FootprintFor(TileItem tile)
    {
        var zoom = Math.Max(tile.PlacementZoom, 1.0 / 300.0);
        return Math.Clamp((int)Math.Round(1.0 / zoom), 1, 300);
    }

    TileItem CreateViewerTile(AtlasTile tile, int column, int row, int footprint, string treatment = "normal")
    {
        var x = column / (double)WorldSession.GridColumns;
        var y = row / (double)WorldSession.GridRows;
        var placementZoom = 1.0 / Math.Max(footprint, 1);

        return new TileItem(
            tile.Id,
            tile.Name,
            tile.Image,
            x,
            y,
            tile.SourceWidth,
            tile.SourceHeight,
            tile.CropX,
            tile.CropY,
            tile.CropWidth,
            tile.CropHeight,
            placementZoom)
        {
            CubeX = Session.CubeX,
            CubeY = Session.CubeY,
            CubeZ = Session.CubeZ,
            PlaneIndex = Session.PlaneIndex,
            TierIndex = Session.TierIndex,
            LayerOffset = Session.LayerOffset,
            RotationQuarterTurns = 0,
            PlacementTreatment = NormalizeTreatment(treatment)
        };
    }

    static string NormalizeTreatment(string? value) => value?.ToLowerInvariant() switch
    {
        "blend" => "blend",
        "crop" => "crop",
        _ => "normal"
    };

    void AddViewerTile(AtlasTile tile, int column, int row, int footprint = 1, bool upperLayer = false, string treatment = "normal")
    {
        var placed = CreateViewerTile(tile, column, row, footprint, treatment);
        Session.AddPlacedTileStacked(placed, upperLayer);
    }

    async Task<(int Column,int Row)?> ViewerCell(double clientX, double clientY, int footprint)
    {
        if (_zModule is null) return null;
        var point = await _zModule.InvokeAsync<double[]?>("viewerGridPoint", _viewerElement, clientX, clientY);
        if (point is null || point.Length < 2) return null;
        var visibleColumns = Math.Min(footprint, WorldSession.GridColumns);
        var visibleRows = Math.Min(footprint, WorldSession.GridRows);
        var maxColumn = Math.Max(0, WorldSession.GridColumns - visibleColumns);
        var maxRow = Math.Max(0, WorldSession.GridRows - visibleRows);
        var column = Math.Clamp((int)Math.Floor(point[0] * WorldSession.GridColumns), 0, maxColumn);
        var row = Math.Clamp((int)Math.Floor(point[1] * WorldSession.GridRows), 0, maxRow);
        return (column,row);
    }

    [JSInvokable]
    public Task<string> TogglePlacementModeFromJs()
    {
        _multiPlacement = !_multiPlacement;
        return Task.FromResult(_multiPlacement ? "Multi" : "Single");
    }

    [JSInvokable]
    public Task<int[]> TogglePlacedTileSelection(int index, bool additive)
    {
        if (index < 0 || index >= Session.PlacedTiles.Count)
            return Task.FromResult(_selectedPlacedTileIndices.Order().ToArray());

        if (!additive) _selectedPlacedTileIndices.Clear();
        if (!_selectedPlacedTileIndices.Add(index) && additive)
            _selectedPlacedTileIndices.Remove(index);

        return Task.FromResult(_selectedPlacedTileIndices.Order().ToArray());
    }

    [JSInvokable]
    public Task<bool> UndoWorldBuilderFromJs()
    {
        if (_worldBuilderUndo.Count == 0) return Task.FromResult(false);
        var previous = _worldBuilderUndo.Pop();
        Session.PlacedTiles.Clear();
        Session.PlacedTiles.AddRange(previous);
        ClearWorldBuilderSelection();
        Session.Notify();
        return Task.FromResult(true);
    }

    [JSInvokable]
    public Task<int[]> RemoveSelectedTilesFromJs()
    {
        if (_selectedPlacedTileIndices.Count == 0)
            return Task.FromResult(Array.Empty<int>());

        PushWorldBuilderUndo();
        foreach (var index in _selectedPlacedTileIndices.Where(i => i >= 0 && i < Session.PlacedTiles.Count).OrderDescending())
            Session.PlacedTiles.RemoveAt(index);

        ClearWorldBuilderSelection();
        Session.Notify();
        return Task.FromResult(Array.Empty<int>());
    }

    [JSInvokable]
    public async Task<bool> PlaceQuickTileFromJs(int quickIndex, double clientX, double clientY)
    {
        if (quickIndex < 0 || quickIndex >= _quickTiles.Count || _zModule is null || _libraryRailOpen)
            return false;

        var footprint = Math.Clamp(_tileFootprint, 1, 300);
        var cell = await ViewerCell(clientX, clientY, footprint);
        if (cell is null) return false;

        PlacementChoice choice;
        try { choice = await JS.InvokeAsync<PlacementChoice>("ristPlacement.consume"); }
        catch { choice = new(false, "normal"); }
        var treatment = NormalizeTreatment(choice.Treatment);
        var tile = _quickTiles[quickIndex];
        var visibleColumns = Math.Min(footprint, WorldSession.GridColumns);
        var visibleRows = Math.Min(footprint, WorldSession.GridRows);

        PushWorldBuilderUndo();
        ClearWorldBuilderSelection();

        if (_multiPlacement)
        {
            for (var y = 0; y < visibleRows; y++)
                for (var x = 0; x < visibleColumns; x++)
                    AddViewerTile(tile, cell.Value.Column + x, cell.Value.Row + y, 1, choice.UpperLayer, treatment);
        }
        else
        {
            AddViewerTile(tile, cell.Value.Column, cell.Value.Row, footprint, choice.UpperLayer, treatment);
        }

        Session.Notify();
        return true;
    }

    [JSInvokable]
    public async Task<int[]> MovePlacedTileFromJs(int index, double clientX, double clientY)
    {
        if (index < 0 || index >= Session.PlacedTiles.Count) return _selectedPlacedTileIndices.Order().ToArray();
        var tile = Session.PlacedTiles[index];
        var footprint = FootprintFor(tile);
        var cell = await ViewerCell(clientX, clientY, footprint);
        if (cell is null) return _selectedPlacedTileIndices.Order().ToArray();

        PushWorldBuilderUndo();
        Session.PlacedTiles[index] = tile with
        {
            X = cell.Value.Column / (double)WorldSession.GridColumns,
            Y = cell.Value.Row / (double)WorldSession.GridRows
        };
        ClearWorldBuilderSelection();
        _selectedPlacedTileIndices.Add(index);
        Session.Notify();
        return _selectedPlacedTileIndices.Order().ToArray();
    }

    [JSInvokable]
    public Task<int[]> RotateSelectedTilesFromJs()
    {
        if (_selectedPlacedTileIndices.Count == 0) return Task.FromResult(Array.Empty<int>());
        PushWorldBuilderUndo();
        foreach (var index in _selectedPlacedTileIndices.Where(i => i >= 0 && i < Session.PlacedTiles.Count))
        {
            var tile = Session.PlacedTiles[index];
            Session.PlacedTiles[index] = tile with { RotationQuarterTurns = (tile.RotationQuarterTurns + 1) % 4 };
        }
        Session.Notify();
        return Task.FromResult(_selectedPlacedTileIndices.Order().ToArray());
    }

    [JSInvokable]
    public Task<int[]> ResizeSelectedTilesFromJs()
    {
        if (_selectedPlacedTileIndices.Count == 0) return Task.FromResult(Array.Empty<int>());
        PushWorldBuilderUndo();
        var footprint = Math.Clamp(_tileFootprint, 1, 300);
        var visible = Math.Min(footprint, Math.Min(WorldSession.GridColumns, WorldSession.GridRows));
        foreach (var index in _selectedPlacedTileIndices.Where(i => i >= 0 && i < Session.PlacedTiles.Count))
        {
            var tile = Session.PlacedTiles[index];
            var column = Math.Clamp((int)Math.Round(tile.X * WorldSession.GridColumns), 0, Math.Max(0, WorldSession.GridColumns - visible));
            var row = Math.Clamp((int)Math.Round(tile.Y * WorldSession.GridRows), 0, Math.Max(0, WorldSession.GridRows - visible));
            Session.PlacedTiles[index] = tile with
            {
                X = column / (double)WorldSession.GridColumns,
                Y = row / (double)WorldSession.GridRows,
                PlacementZoom = 1.0 / footprint
            };
        }
        Session.Notify();
        return Task.FromResult(_selectedPlacedTileIndices.Order().ToArray());
    }

    [JSInvokable]
    public async Task<WorldBuilderTileVisual[]> GetWorldBuilderTileVisuals()
    {
        var visuals=Session.PlacedTiles.Select((tile,index) => new WorldBuilderTileVisual(index, tile.RotationQuarterTurns, tile.TierIndex, tile.LayerOffset)).ToArray();
        try{await JS.InvokeVoidAsync("ristDepth.set",visuals);}catch{}
        return visuals;
    }

    [JSInvokable]
    public Task<WorldBuilderCommandState> GetWorldBuilderCommandState() =>
        Task.FromResult(new WorldBuilderCommandState(
            _multiPlacement ? "Multi" : "Single",
            _worldBuilderUndo.Count > 0,
            _selectedPlacedTileIndices.Count));
}

public sealed record PlacementChoice(bool UpperLayer, string Treatment);
public sealed record WorldBuilderCommandState(string PlacementMode, bool CanUndo, int SelectedCount);
public sealed record WorldBuilderTileVisual(int Index, int RotationQuarterTurns, int TierIndex, int LayerOffset);
