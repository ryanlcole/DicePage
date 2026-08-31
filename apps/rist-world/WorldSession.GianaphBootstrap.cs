namespace RistWorld;

public sealed partial class WorldSession
{
    public const string OriginMapId = "MapU000X000Y000Z";
    const string DefaultMapAlias = "map1";
    const string OwnerOriginAlias = "Geanaph";
    bool _originMapApplied;

    public string MapId { get; private set; } = OriginMapId;
    public string MapAlias => MapName;
    public string MapIdentityLabel => string.Equals(MapAlias, MapId, StringComparison.Ordinal)
        ? MapId
        : $"{MapId} · {MapAlias}";
    public int GianaphWorldWidthMiles => DefaultCubeWidthMiles;
    public int GianaphWorldHeightMiles => DefaultCubeHeightMiles;
    public long GianaphWorldTileCapacity => DefaultCubeCellCount;
    public string GianaphWorldExtentLabel => $"{DefaultCubeWidthMiles}×{DefaultCubeHeightMiles} mi · 1 mi/tile";

    public void SetMapAlias(string? value)
    {
        var alias = (value ?? string.Empty).Trim();
        MapName = alias.Length == 0 ? MapId : alias;
        Notify();
    }

    // Kept under the existing method name so the component partial does not need
    // a migration-only patch. This now initializes the neutral coordinate origin,
    // not a campaign-specific world.
    public void EnsureGianaphWorld()
    {
        MapId = OriginMapId;
        MapName = auth.IsOwnerDiscordAccount ? OwnerOriginAlias : DefaultMapAlias;
        GridDistance = 1;
        DistanceUnit = "mi";
        GridCalibrationZoom = 1;
        ViewZoom = 1;

        if (_originMapApplied) return;

        _originMapApplied = true;

        // New origin cubes are sparse. Ocean 071 is the implicit 1×1-mile base,
        // so old campaign/import tiles must never be materialized as the default.
        PlacedTiles.Clear();
        Pieces.Clear();
        Rolls.Clear();
        Gems.Clear();
        StagedAssets.Clear();
        MapLocked = true;
        Notify();
    }
}
