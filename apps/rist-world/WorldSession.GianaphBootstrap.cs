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

        // Geonaph is authored from registered chunk layers. The atlas is loaded
        // before the world selector enters Geonaph, so seed the current registered
        // chunk truth instead of clearing the map to an empty grid.
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
            .OrderBy(tile => tile.DefaultTierIndex)
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
