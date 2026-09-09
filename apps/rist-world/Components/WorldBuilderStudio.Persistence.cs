using System.Text.Json;

namespace RistWorld.Components;

public partial class WorldBuilderStudio
{
    const string WorldBuilderUiStorageKey = "rist.worldbuilder.ui.v1";
    bool _uiRestoreStarted;
    bool _uiRestoreComplete;

    protected override void OnAfterRender(bool firstRender)
    {
        if (firstRender && !_uiRestoreStarted)
        {
            _uiRestoreStarted = true;
            _ = RestoreWorldBuilderUiAsync();
            return;
        }

        if (_uiRestoreComplete)
            _ = PersistWorldBuilderUiAsync();
    }

    async Task RestoreWorldBuilderUiAsync()
    {
        try
        {
            var json = await JS.InvokeAsync<string?>("localStorage.getItem", WorldBuilderUiStorageKey);
            if (string.IsNullOrWhiteSpace(json))
            {
                _uiRestoreComplete = true;
                return;
            }

            var state = JsonSerializer.Deserialize<WorldBuilderUiState>(json);
            if (state is null)
            {
                _uiRestoreComplete = true;
                return;
            }

            for (var i = 0; i < 12 && Session.AtlasTiles.Count == 0; i++)
                await Task.Delay(100);

            _quickTiles.Clear();
            foreach (var id in state.QuickTileIds.Distinct(StringComparer.Ordinal).Take(QuickSlotCount))
            {
                var tile = Session.AtlasTiles.FirstOrDefault(x => string.Equals(x.Id, id, StringComparison.Ordinal));
                if (tile is not null) _quickTiles.Add(tile);
            }

            if (Footprints.Contains(state.TileFootprint))
                _tileFootprint = state.TileFootprint;

            if (Modes.Contains(state.ToolMode, StringComparer.Ordinal))
                _toolMode = state.ToolMode;

            _viewerGrid = state.ViewerGrid;
            _zLocked = state.ZLocked;
            _toolsOpen = false;
            _libraryRailOpen = false;
            _loadOpen = false;
            _layerOpen = false;
            _tierOpen = false;
            _publishMode = false;
            _uiRestoreComplete = true;

            await InvokeAsync(StateHasChanged);
            await JS.InvokeVoidAsync("ristWorldBuilderUi.restoreRails");
        }
        catch
        {
            _uiRestoreComplete = true;
        }
    }

    async Task PersistWorldBuilderUiAsync()
    {
        try
        {
            var state = new WorldBuilderUiState(
                _quickTiles.Select(x => x.Id).ToArray(),
                _tileFootprint,
                _toolMode,
                _viewerGrid,
                _zLocked);
            await JS.InvokeVoidAsync("localStorage.setItem", WorldBuilderUiStorageKey, JsonSerializer.Serialize(state));
            await JS.InvokeVoidAsync("ristWorldBuilderUi.captureRails");
        }
        catch { }
    }

    sealed record WorldBuilderUiState(
        string[] QuickTileIds,
        int TileFootprint,
        string ToolMode,
        bool ViewerGrid,
        bool ZLocked);
}
