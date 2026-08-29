namespace RistWorld;

public sealed partial class WorldSession
{
    public string AssetFamily { get; private set; } = "";
    public string UserMode { get; private set; } = "Player";
    public string GameMode { get; private set; } = "Build";
    public string PresentationMode { get; private set; } = "World";
    public string MapDirection { get; private set; } = "North";
    public string AreaName { get; set; } = "";
    public string GmNote { get; set; } = "";
    public string GmName => string.IsNullOrWhiteSpace(DiscordDisplayName) ? "GameMaster" : DiscordDisplayName;

    public void OpenAssetFamily(string family)
    {
        AssetFamily = family ?? "";
        TileBrowserOpen = true;
        CardBrowserOpen = false;
        Notify();
    }

    private void ApplyUserMode(string mode)
    {
        UserMode = mode switch
        {
            "GameMaster" when IsLoggedIn => "GameMaster",
            "Moderator" when IsLoggedIn => "Moderator",
            "Spectator" => "Spectator",
            _ => "Player"
        };
        Role = UserMode is "GameMaster" or "Moderator" ? "GM" : "PC";
    }

    public void SetUserMode(string mode)
    {
        ApplyUserMode(mode);
        Notify();
    }

    public void SetRole(string role)
    {
        ApplyUserMode(role == "GM" ? "GameMaster" : "Player");
        Notify();
    }

    public void CycleUserMode()
    {
        var next = UserMode switch
        {
            "Player" => IsLoggedIn ? "GameMaster" : "Spectator",
            "GameMaster" => "Spectator",
            "Spectator" => IsLoggedIn ? "Moderator" : "Player",
            _ => "Player"
        };
        SetUserMode(next);
    }

    public void CycleGameMode()
    {
        GameMode = GameMode switch { "Build" => "Test", "Test" => "Live", _ => "Build" };
        SetTableMode(GameMode switch { "Build" => "worldbuilder", "Test" => "test", _ => "play" });
    }

    public void CyclePresentationMode()
    {
        PresentationMode = PresentationMode switch { "World" => "Encounter", "Encounter" => "Game", "Game" => "Media", _ => "World" };
        Notify();
    }

    public void CycleMapDirection()
    {
        MapDirection = MapDirection switch { "North" => "East", "East" => "South", "South" => "West", _ => "North" };
        Notify();
    }
}
