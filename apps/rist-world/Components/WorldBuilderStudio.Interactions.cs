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

    void ClearWorldBuilderSelection()
    {
        _selectedPlacedTileIndices.Clear();
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

        var point = await _zModule.InvokeAsync<double[]?>("viewerGridPoint", _viewerElement, clientX, clientY);
        if (point is null || point.Length < 2) return false;

        var tile = _quickTiles[quickIndex];
        var footprint = Math.Clamp(_tileFootprint, 1, 300);
        var visibleColumns = Math.Min(footprint, WorldSession.GridColumns);
        var visibleRows = Math.Min(footprint, WorldSession.GridRows);
        var maxColumn = Math.Max(0, WorldSession.GridColumns - visibleColumns);
        var maxRow = Math.Max(0, WorldSession.GridRows - visibleRows);
        var column = Math.Clamp((int)Math.Floor(point[0] * WorldSession.GridColumns), 0, maxColumn);
        var row = Math.Clamp((int)Math.Floor(point[1] * WorldSession.GridRows), 0, maxRow);

        Session.StageTile(tile);
        var staged = Session.StagedAssets.LastOrDefault(x => x.Key == $"tile:{tile.Id}");
        if (staged is null) return false;

        PushWorldBuilderUndo();
        ClearWorldBuilderSelection();

        if (_multiPlacement)
        {
            for (var y = 0; y < visibleRows; y++)
            {
                for (var x = 0; x < visibleColumns; x++)
                {
                    Session.PlaceStaged(
                        staged,
                        (column + x) / (double)WorldSession.GridColumns,
                        (row + y) / (double)WorldSession.GridRows,
                        1.0);
                }
            }
        }
        else
        {
            Session.PlaceStaged(
                staged,
                column / (double)WorldSession.GridColumns,
                row / (double)WorldSession.GridRows,
                1.0 / footprint);

            var placedIndex = Session.PlacedTiles.FindLastIndex(x => x.Id == tile.Id);
            if (placedIndex >= 0)
                Session.PlacedTiles[placedIndex] = Session.PlacedTiles[placedIndex] with { PlacementZoom = 1.0 / footprint };
        }

        Session.RemoveStaged(staged.Key);
        Session.Notify();
        return true;
    }

    [JSInvokable]
    public Task<WorldBuilderCommandState> GetWorldBuilderCommandState() =>
        Task.FromResult(new WorldBuilderCommandState(
            _multiPlacement ? "Multi" : "Single",
            _worldBuilderUndo.Count > 0,
            _selectedPlacedTileIndices.Count));
}

public sealed record WorldBuilderCommandState(string PlacementMode, bool CanUndo, int SelectedCount);
