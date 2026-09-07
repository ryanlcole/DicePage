namespace RistWorld;

public sealed partial class WorldSession
{
    public void ResetMapForBlankRecursiveViewer()
    {
        PlacedTiles.Clear();
        Pieces.Clear();
        Rolls.Clear();
        Gems.Clear();
        StagedAssets.Clear();
        GridStyle = "none";
        MapLocked = false;
        ViewZoom = 1;
        SelectedTile = string.Empty;
        HeaderPinDragging = false;
        CloseHeaderMenus();
        Notify();
    }
}
