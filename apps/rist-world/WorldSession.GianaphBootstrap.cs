namespace RistWorld;

public sealed partial class WorldSession
{
    public const string OriginMapId = "MapU000X000Y000Z";
    public const string OriginMapAlias = GeonaphDisplayName;
    bool _originMapApplied;

    public string MapId { get; private set; } = OriginMapId;
    public string MapAlias => MapName;
    public string MapIdentityLabel => string.Equals(MapAlias, MapId, StringComparison.Ordinal)
        ? MapId
        : $"{MapId} · {MapAlias}";
    public int GianaphWorldWidthMiles => DefaultCubeWidthKm;
    public int GianaphWorldHeightMiles => DefaultCubeHeightKm;
    public long GianaphWorldTileCapacity => IsGeonaphWorld ? long.MaxValue : DefaultWorldTileCapacity;
    public string GianaphWorldExtentLabel => IsGeonaphWorld ? "Unbounded · 1 km/tile" : $"{DefaultWorldWidthKm}×{DefaultWorldHeightKm} km · 1 km/tile";

    public void SetMapAlias(string? value)
    {
        var alias = (value ?? string.Empty).Trim();
        MapName = alias.Length == 0 ? MapId : alias;
        Notify();
    }

    // Kept under the existing method name so legacy callers continue to initialize
    // the Geonaph origin without changing its stable map identity.
    public void EnsureGianaphWorld()
    {
        MapId = OriginMapId;
        MapName = GeonaphDisplayName;
        GridDistance = 1;
        DistanceUnit = "km";
        GridCalibrationZoom = 1;
        ViewZoom = 1;

        if (_originMapApplied) return;

        _originMapApplied = true;

        // New origin cubes are sparse. Ocean 071 is the implicit 1×1-km base,
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
