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

        // Register the current production chunk before seeding. This keeps the
        // authored PNG stack authoritative while the general Pangea catalog
        // continues to expose the reusable source sprites.
        RegisterGeonaphChunkCatalogV004();

        PlacedTiles.Clear();
        Pieces.Clear();
        Rolls.Clear();
        Gems.Clear();
        StagedAssets.Clear();
        SeedRegisteredGeonaphChunk();

        _originMapApplied = true;
        MapLocked = true;
        Notify();
    }

    void RegisterGeonaphChunkCatalogV004()
    {
        const string root = "https://d2d6rnm6fnsp89.cloudfront.net/assets/sprites/pangea/registered/GEO_X00_Y00/";

        AtlasTile[] layers =
        [
            new(
                "pangea-sprite-geo-x00-y00-ocean-floor-v004",
                "GEO X00 Y00 · Ocean Floor",
                root + "geonaph_geo_x00_y00_t00_l00_ocean_floor_v004.png",
                "WORLD", "Pangea", "01 Ocean Floor", "Shaelvien",
                SourceWidth: 1200, SourceHeight: 1200,
                AssetKind: "sprite", AuthoredDepth: true,
                DefaultTierIndex: 0, DefaultLayerOffset: 0, DefaultFootprint: 30),
            new(
                "pangea-sprite-geo-x00-y00-ocean-surface-v004",
                "GEO X00 Y00 · Ocean Surface",
                root + "geonaph_geo_x00_y00_t00_l09_ocean_surface_v004.png",
                "WORLD", "Pangea", "02 Ocean Surface", "Shaelvien",
                SourceWidth: 1200, SourceHeight: 1200,
                AssetKind: "sprite", AuthoredDepth: true,
                DefaultTierIndex: 0, DefaultLayerOffset: 9, DefaultFootprint: 30),
            new(
                "pangea-sprite-geo-x00-y00-plains-v004",
                "GEO X00 Y00 · Plains",
                root + "geonaph_geo_x00_y00_t01_l01_plains_v004.png",
                "WORLD", "Pangea", "04 Low Plains", "Shaelvien",
                SourceWidth: 1200, SourceHeight: 1200,
                AssetKind: "sprite", AuthoredDepth: true,
                DefaultTierIndex: 1, DefaultLayerOffset: 1, DefaultFootprint: 30),
            new(
                "pangea-sprite-geo-x00-y00-coast-shallows-v004",
                "GEO X00 Y00 · Coast & Shallows",
                root + "geonaph_geo_x00_y00_t01_l00_coast_shallows_v004.png",
                "WORLD", "Pangea", "03 Coast and Shallows", "Shaelvien",
                SourceWidth: 1200, SourceHeight: 1200,
                AssetKind: "sprite", AuthoredDepth: true,
                DefaultTierIndex: 1, DefaultLayerOffset: 0, DefaultFootprint: 30),
            new(
                "pangea-sprite-geo-x00-y00-valleys-v004",
                "GEO X00 Y00 · Valleys",
                root + "geonaph_geo_x00_y00_t01_l02_valleys_v004.png",
                "WORLD", "Pangea", "05 Valleys and Depressions", "Shaelvien",
                SourceWidth: 1200, SourceHeight: 1200,
                AssetKind: "sprite", AuthoredDepth: true,
                DefaultTierIndex: 1, DefaultLayerOffset: 2, DefaultFootprint: 30),
            new(
                "pangea-sprite-geo-x00-y00-forests-v004",
                "GEO X00 Y00 · Forests",
                root + "geonaph_geo_x00_y00_t01_l03_forests_v004.png",
                "WORLD", "Pangea", "06 Forests and Wetlands", "Shaelvien",
                SourceWidth: 1200, SourceHeight: 1200,
                AssetKind: "sprite", AuthoredDepth: true,
                DefaultTierIndex: 1, DefaultLayerOffset: 3, DefaultFootprint: 30),
            new(
                "pangea-sprite-geo-x00-y00-waterways-v004",
                "GEO X00 Y00 · Waterways",
                root + "geonaph_geo_x00_y00_t01_l01_waterways_v004.png",
                "WORLD", "Pangea", "09 Waterways", "Shaelvien",
                SourceWidth: 1200, SourceHeight: 1200,
                AssetKind: "sprite", AuthoredDepth: true,
                DefaultTierIndex: 1, DefaultLayerOffset: 1, DefaultFootprint: 30),
            new(
                "pangea-sprite-geo-x00-y00-hills-v004",
                "GEO X00 Y00 · Hills",
                root + "geonaph_geo_x00_y00_t01_l06_hills_v004.png",
                "WORLD", "Pangea", "07 Hills and Uplands", "Shaelvien",
                SourceWidth: 1200, SourceHeight: 1200,
                AssetKind: "sprite", AuthoredDepth: true,
                DefaultTierIndex: 1, DefaultLayerOffset: 6, DefaultFootprint: 30),
            new(
                "pangea-sprite-geo-x00-y00-mountains-v004",
                "GEO X00 Y00 · Mountains",
                root + "geonaph_geo_x00_y00_t02_l00_mountains_v004.png",
                "WORLD", "Pangea", "08 Mountains and Peaks", "Shaelvien",
                SourceWidth: 1200, SourceHeight: 1200,
                AssetKind: "sprite", AuthoredDepth: true,
                DefaultTierIndex: 2, DefaultLayerOffset: 0, DefaultFootprint: 30)
        ];

        foreach (var layer in layers)
        {
            if (AtlasTiles.All(existing => !string.Equals(existing.Id, layer.Id, StringComparison.Ordinal)))
                AtlasTiles.Add(layer);
        }
    }

    void SeedRegisteredGeonaphChunk()
    {
        const string chunkPrefix = "pangea-sprite-geo-x00-y00-";

        var registeredLayers = AtlasTiles
            .Where(tile => tile.AuthoredDepth
                && tile.AssetKind.Equals("sprite", StringComparison.OrdinalIgnoreCase)
                && tile.Id.StartsWith(chunkPrefix, StringComparison.Ordinal)
                && tile.DefaultFootprint >= GridColumns)
            .GroupBy(tile => GeonaphChunkSemanticKey(tile.Id), StringComparer.Ordinal)
            .Select(group => group
                .OrderByDescending(tile => GeonaphChunkVersion(tile.Id))
                .ThenByDescending(tile => tile.Id, StringComparer.Ordinal)
                .First())
            // Draw order is intentionally separate from authored Z. For example,
            // the coastline is Tier 1 / Layer 0 but must visually sit over the
            // low-plains image when the composite world view is shown.
            .OrderBy(tile => GeonaphChunkRenderOrder(tile.Id))
            .ThenBy(tile => tile.DefaultTierIndex)
            .ThenBy(tile => tile.DefaultLayerOffset)
            .ThenBy(tile => tile.Id, StringComparer.Ordinal)
            .ToList();

        foreach (var tile in registeredLayers)
        {
            var footprint = Math.Max(1, tile.DefaultFootprint);
            PlacedTiles.Add(new TileItem(
                tile.Id,
                tile.Name,
                tile.Image,
                0,
                0,
                SourceWidth: tile.SourceWidth,
                SourceHeight: tile.SourceHeight,
                CropX: tile.CropX,
                CropY: tile.CropY,
                CropWidth: tile.CropWidth,
                CropHeight: tile.CropHeight,
                PlacementZoom: 1.0 / footprint,
                Locked: true,
                CubeX: CubeX,
                CubeY: CubeY,
                CubeZ: CubeZ,
                PlaneIndex: PlaneIndex,
                TierIndex: tile.DefaultTierIndex,
                LayerOffset: tile.DefaultLayerOffset,
                RotationQuarterTurns: 0,
                PlacementTreatment: "normal",
                AssetKind: tile.AssetKind,
                AuthoredDepth: true,
                FrameCount: Math.Max(1, tile.FrameCount),
                FramesPerSecond: Math.Max(0, tile.FramesPerSecond)));
        }
    }

    static int GeonaphChunkRenderOrder(string id)
    {
        if (id.Contains("ocean-floor", StringComparison.Ordinal)) return 0;
        if (id.Contains("ocean-surface", StringComparison.Ordinal)) return 10;
        if (id.Contains("-plains-", StringComparison.Ordinal)) return 20;
        if (id.Contains("coast-shallows", StringComparison.Ordinal)) return 30;
        if (id.Contains("-valleys-", StringComparison.Ordinal)) return 40;
        if (id.Contains("-forests-", StringComparison.Ordinal)) return 50;
        if (id.Contains("-waterways-", StringComparison.Ordinal)) return 60;
        if (id.Contains("-hills-", StringComparison.Ordinal)) return 70;
        if (id.Contains("-mountains-", StringComparison.Ordinal)) return 80;
        return 1000;
    }

    static string GeonaphChunkSemanticKey(string id)
    {
        var marker = id.LastIndexOf("-v", StringComparison.Ordinal);
        return marker > 0 ? id[..marker] : id;
    }

    static int GeonaphChunkVersion(string id)
    {
        var marker = id.LastIndexOf("-v", StringComparison.Ordinal);
        if (marker < 0 || marker + 2 >= id.Length) return 0;
        return int.TryParse(id[(marker + 2)..], System.Globalization.NumberStyles.None, System.Globalization.CultureInfo.InvariantCulture, out var version)
            ? version
            : 0;
    }
}
