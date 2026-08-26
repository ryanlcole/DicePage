namespace RistWorld;

public sealed partial class WorldSession
{
    public void BeginPersonalZone()
    {
        PlacedTiles.Clear();
        Pieces.Clear();
        StagedAssets.Clear();
        Rolls.Clear();
        MapName = "Personal Zone";
        MapLocked = false;
        Role = "GM";
        Notify();
    }

    public void ClaimShaelvienZone()
    {
        MapName = "Shaelvien GM Zone";
        MapLocked = false;
        Role = "GM";
        Notify();
    }
}
