namespace RistWorld;

public sealed partial class WorldSession
{
    public void BeginPersonalZone()
    {
        if(!IsLoggedIn)return;
        PlacedTiles.Clear();
        Pieces.Clear();
        StagedAssets.Clear();
        Rolls.Clear();
        MapName = "map1";
        MapLocked = false;
        ApplyUserMode("GameMaster");
        Notify();
    }

    // MMO expansion is coordinate-first. The browser expansion rail chooses the
    // nearest unclaimed coordinate; the newly claimed cube starts as sparse
    // Ocean 071 and receives a user-editable alias rather than a campaign name.
    public void ClaimShaelvienZone()
    {
        if(!IsLoggedIn)return;
        PlacedTiles.Clear();
        Pieces.Clear();
        StagedAssets.Clear();
        Rolls.Clear();
        MapName = "map1";
        GridDistance = 1;
        DistanceUnit = "mi";
        GridCalibrationZoom = 1;
        ViewZoom = 1;
        MapLocked = false;
        ApplyUserMode("GameMaster");
        Notify();
    }
}
