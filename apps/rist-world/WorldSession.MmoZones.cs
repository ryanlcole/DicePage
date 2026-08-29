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
        MapName = "Personal Zone";
        MapLocked = false;
        ApplyUserMode("GameMaster");
        Notify();
    }

    public void ClaimShaelvienZone()
    {
        if(!IsLoggedIn)return;
        MapName = "Shaelvien GM Zone";
        MapLocked = false;
        ApplyUserMode("GameMaster");
        Notify();
    }
}
