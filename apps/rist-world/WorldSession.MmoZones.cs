namespace RistWorld;

public sealed partial class WorldSession
{
    public string OperatingMode { get; private set; } = "mmo";
    public bool IsMmoMode => string.Equals(OperatingMode, "mmo", StringComparison.Ordinal);

    public async Task SetOperatingModeAsync(string value)
    {
        if(!IsLoggedIn)return;
        RestoreOperatingMode(value);
        Notify();
        await SaveAsync();
        await AutoSavePrivateAsync();
    }

    public Task SetSandboxModeAsync() => SetOperatingModeAsync("sandbox");
    public Task SetMmoModeAsync() => SetOperatingModeAsync("mmo");

    public async Task BeginPersonalZone()
    {
        if(!IsLoggedIn)return;
        RestoreOperatingMode("sandbox");
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
        await SaveAsync();
        await AutoSavePrivateAsync();
    }

    // MMO expansion is coordinate-first. The browser expansion rail chooses the
    // nearest unclaimed coordinate; the newly claimed cube starts as sparse
    // Ocean 071 and receives a user-editable alias rather than a campaign name.
    public async Task ClaimShaelvienZone()
    {
        if(!IsLoggedIn)return;
        RestoreOperatingMode("mmo");
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
        await SaveAsync();
        await AutoSavePrivateAsync();
    }

    internal void RestoreOperatingMode(string? value)
        => OperatingMode = string.Equals(value, "sandbox", StringComparison.OrdinalIgnoreCase) ? "sandbox" : "mmo";
}
