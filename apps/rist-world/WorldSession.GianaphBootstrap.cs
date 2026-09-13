using System.Net.Http.Json;

namespace RistWorld;

public sealed partial class WorldSession
{
    public const string OriginMapId = "MapU000X000Y000Z";
    public const string OriginMapAlias = GeonaphDisplayName;
    bool _originMapApplied;
    GeonaphRuntimeCatalog? _geonaphRuntimeCatalog;

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

    async Task LoadGeonaphRuntimeCatalogAsync()
    {
        try
        {
            var catalog = await http.GetFromJsonAsync<GeonaphRuntimeCatalog>(
                "assets/worlds/geonaph/v1/runtime_catalog.json?v=20260914-geonaph-v1");
            if (catalog is not null &&
                string.Equals(catalog.WorldId, "geonaph-world-v1", StringComparison.Ordinal) &&
                catalog.GridWidth == GridColumns && catalog.GridHeight == GridRows)
                _geonaphRuntimeCatalog = catalog;
        }
        catch
        {
            // Geonaph remains accessible as an empty authored world if its optional
            // package catalog has not been installed yet.
        }
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

        RegisterGeonaphPackageCatalog();
        SeedGeonaphPackage();

        _originMapApplied = true;
        MapLocked = true;
        Notify();
    }

    void RegisterGeonaphPackageCatalog()
    {
        // Remove only the obsolete prototype records. Their useful artwork remains
        // available through reclassified normal-Library entries.
        AtlasTiles.RemoveAll(tile =>
            tile.Id.StartsWith("pangea-sprite-geo-x00-y00-", StringComparison.OrdinalIgnoreCase));

        if (_geonaphRuntimeCatalog is null) return;
        foreach (var placement in _geonaphRuntimeCatalog.Placements)
        {
            var index = AtlasTiles.FindIndex(tile =>
                string.Equals(tile.Id, placement.Asset.Id, StringComparison.Ordinal));
            if (index >= 0) AtlasTiles[index] = placement.Asset;
            else AtlasTiles.Add(placement.Asset);
        }
    }

    void SeedGeonaphPackage()
    {
        PlacedTiles.RemoveAll(tile =>
            tile.Id.StartsWith("pangea-sprite-geo-x00-y00-", StringComparison.OrdinalIgnoreCase));
        if (_geonaphRuntimeCatalog is null) return;

        foreach (var placement in _geonaphRuntimeCatalog.Placements)
        {
            if (PlacedTiles.Any(tile => string.Equals(tile.Id, placement.PlacementId, StringComparison.Ordinal)))
                continue;

            var asset = placement.Asset;
            var footprint = Math.Clamp(placement.Footprint, 1, GridColumns);
            PlacedTiles.Add(new TileItem(
                placement.PlacementId,
                asset.Name,
                asset.Image,
                Math.Clamp(placement.X / GridColumns, 0, 1),
                Math.Clamp(placement.Y / GridRows, 0, 1),
                SourceWidth: asset.SourceWidth,
                SourceHeight: asset.SourceHeight,
                PlacementZoom: 1.0 / footprint,
                Locked: true,
                CubeX: CubeX,
                CubeY: CubeY,
                CubeZ: CubeZ,
                PlaneIndex: PlaneIndex,
                TierIndex: asset.DefaultTierIndex,
                LayerOffset: Math.Clamp(asset.DefaultLayerOffset, 0, LayersPerTier - 1),
                PlacementTreatment: "normal",
                AssetKind: asset.AssetKind,
                AuthoredDepth: true,
                FrameCount: Math.Max(1, asset.FrameCount),
                FramesPerSecond: Math.Max(0, asset.FramesPerSecond)));
        }
    }
}

public sealed record GeonaphRuntimeCatalog(
    string WorldId,
    string Name,
    int GridWidth,
    int GridHeight,
    List<GeonaphRuntimePlacement> Placements);

public sealed record GeonaphRuntimePlacement(
    string PlacementId,
    AtlasTile Asset,
    double X,
    double Y,
    int Footprint);
