using System.Text.Json;

namespace RistWorld.Components;

public partial class WorldBuilderStudio
{
    const string WorldBuilderUiStorageKey = "rist.worldbuilder.ui.v1";
    static readonly int[] PersistedFootprints = [1, 2, 4, 8, 16, 30];
    bool _uiRestoreStarted;
    bool _uiRestoreComplete;
    bool _worldBuilderPersistBusy;
    bool _worldBuilderPersistAgain;

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

            if (PersistedFootprints.Contains(state.TileFootprint))
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
        if (_worldBuilderPersistBusy)
        {
            _worldBuilderPersistAgain = true;
            return;
        }

        _worldBuilderPersistBusy = true;
        try
        {
            do
            {
                _worldBuilderPersistAgain = false;
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

                    // World Builder edits must survive iOS/Safari suspension. Save the
                    // canonical world snapshot locally after each rendered edit instead
                    // of relying only on the 30-second timer. This never performs an AWS
                    // upload; WorldSession.SaveAsync writes only the scoped local save.
                    if (_autoSave)
                        await Session.SaveAsync();
                }
                catch { }
            }
            while (_worldBuilderPersistAgain);
        }
        finally
        {
            _worldBuilderPersistBusy = false;
        }
    }

    sealed record WorldBuilderUiState(
        string[] QuickTileIds,
        int TileFootprint,
        string ToolMode,
        bool ViewerGrid,
        bool ZLocked);
}
