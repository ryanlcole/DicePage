namespace RistWorld.Components;

/// <summary>
/// Bridges the general Asset Library's legacy staging contract into the World
/// Builder quick-slot contract. AssetLibrary is shared outside World Builder,
/// so it continues to stage selected tiles through WorldSession. While the
/// World Builder's general Library rail is open, those staged tiles are
/// immediately promoted to the same visible quick slots used by sprite assets.
/// This keeps one placement path for regular image tiles and sprite tiles.
/// </summary>
public partial class WorldBuilderStudio
{
    bool _assetLibraryBridgeBusy;
    bool _assetLibraryBridgeScheduled;

    protected override void OnInitialized()
    {
        // Do not keep the builder alive through the long-lived WorldSession
        // event. The weak reference lets an abandoned builder be collected;
        // the next session notification removes this handler.
        var session = Session;
        var weakBuilder = new WeakReference<WorldBuilderStudio>(this);
        Action? handler = null;
        handler = () =>
        {
            if (!weakBuilder.TryGetTarget(out var builder))
            {
                if (handler is not null)
                    session.Changed -= handler;
                return;
            }

            builder.QueueAssetLibraryBridge();
        };

        session.Changed += handler;
    }

    void QueueAssetLibraryBridge()
    {
        if (_assetLibraryBridgeBusy || _assetLibraryBridgeScheduled)
            return;

        _assetLibraryBridgeScheduled = true;
        _ = InvokeAsync(async () =>
        {
            _assetLibraryBridgeScheduled = false;
            await BridgeStagedLibraryTilesAsync();
        });
    }

    async Task BridgeStagedLibraryTilesAsync()
    {
        // Sprite Library has its own explicit preview/pin workflow. Only bridge
        // the general Library rail, whose old pallet is hidden in World Builder.
        if (_assetLibraryBridgeBusy || !Session.TileBrowserOpen || _libraryRailOpen)
            return;

        var stagedTiles = Session.StagedAssets
            .Where(x => x.Kind == "tile" && x.Key.StartsWith("tile:", StringComparison.Ordinal))
            .ToArray();

        if (stagedTiles.Length == 0)
            return;

        _assetLibraryBridgeBusy = true;
        var quickSlotsChanged = false;

        try
        {
            foreach (var staged in stagedTiles)
            {
                var assetId = staged.Key["tile:".Length..];
                var tile = FindAsset(assetId);
                if (tile is null)
                    continue;

                if (_quickTiles.All(x => !string.Equals(x.Id, tile.Id, StringComparison.Ordinal)))
                {
                    if (_quickTiles.Count >= QuickSlotCount)
                        _quickTiles.RemoveAt(0);

                    _quickTiles.Add(tile);
                    quickSlotsChanged = true;
                }

                // The World Builder does not display the legacy pallet. Remove
                // the bridged entry so a later tap on the same Library asset is
                // a fresh, visible action instead of an invisible no-op.
                Session.RemoveStaged(staged.Key);
            }

            if (quickSlotsChanged)
                await PersistQuickSlotsAsync();

            await InvokeAsync(StateHasChanged);
        }
        finally
        {
            _assetLibraryBridgeBusy = false;
        }
    }
}
