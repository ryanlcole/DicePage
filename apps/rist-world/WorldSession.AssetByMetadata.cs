namespace RistWorld;

/// <summary>
/// Asset-by-metadata (ABM) world truth. This layer is intentionally independent
/// of graphics and AI. Humans, assistive interfaces, scripted importers, or AI
/// may all produce the same semantic record; artwork is an optional representation.
/// </summary>
public sealed record AssetByMetadata(
    string AssetType,
    double ElevationMeters = 0,
    string Terrain = "",
    string Biome = "",
    string Moisture = "",
    string Temperature = "",
    string Material = "",
    string Description = "",
    string Provenance = "HUMAN",
    Dictionary<string,string>? Attributes = null);

public sealed record AbmMapEntry(
    string PlacementId,
    string TypeId,
    string GroupId,
    double X,
    double Y,
    int TierIndex,
    int LayerOffset,
    string Description,
    AssetByMetadata? Metadata);

public sealed partial class WorldSession
{
    const string TransparentPixel = "data:image/gif;base64,R0lGODlhAQABAAAAACw=";

    public bool DescriptionOnlyMode { get; private set; }

    public void SetDescriptionOnlyMode(bool enabled)
    {
        if (DescriptionOnlyMode == enabled) return;
        DescriptionOnlyMode = enabled;
        Notify();
    }

    public void ToggleDescriptionOnlyMode() => SetDescriptionOnlyMode(!DescriptionOnlyMode);

    public static double FeetToMeters(double feet) => feet * 0.3048;
    public static double MetersToFeet(double meters) => meters / 0.3048;

    static string AbmSlug(string? value)
    {
        if (string.IsNullOrWhiteSpace(value)) return "unknown";
        var chars = value.Trim().ToLowerInvariant()
            .Select(ch => char.IsLetterOrDigit(ch) ? ch : '.')
            .ToArray();
        return string.Join('.', new string(chars).Split('.', StringSplitOptions.RemoveEmptyEntries));
    }

    static string ElevationTerrain(double elevationMeters)
    {
        var feet = MetersToFeet(elevationMeters);
        return feet switch
        {
            < 0 => "below-sea-level",
            < 500 => "lowland",
            < 2000 => "upland",
            < 5000 => "highland",
            _ => "mountain"
        };
    }

    /// <summary>
    /// Deterministic semantic inference used when no AI is enabled. Explicit
    /// terrain always wins; otherwise physical elevation supplies the terrain
    /// family and AssetType supplies the feature. Example: cave at 8,000 ft ->
    /// mountain.cave.
    /// </summary>
    public static string InferAbmTypeId(AssetByMetadata metadata)
    {
        if (metadata is null) return "unknown";
        var feature = AbmSlug(metadata.AssetType);
        var terrain = string.IsNullOrWhiteSpace(metadata.Terrain)
            ? ElevationTerrain(metadata.ElevationMeters)
            : AbmSlug(metadata.Terrain);
        return $"{terrain}.{feature}";
    }

    public static string DescribeAbm(AssetByMetadata metadata)
    {
        if (metadata is null) return "Unknown world feature.";

        var feature = string.IsNullOrWhiteSpace(metadata.AssetType) ? "feature" : metadata.AssetType.Trim();
        var terrain = string.IsNullOrWhiteSpace(metadata.Terrain)
            ? ElevationTerrain(metadata.ElevationMeters).Replace('-', ' ')
            : metadata.Terrain.Trim();
        var feet = Math.Round(MetersToFeet(metadata.ElevationMeters));
        var parts = new List<string> { $"{feature} in {terrain} terrain at approximately {feet:N0} ft above sea level" };

        if (!string.IsNullOrWhiteSpace(metadata.Biome)) parts.Add($"biome {metadata.Biome.Trim()}");
        if (!string.IsNullOrWhiteSpace(metadata.Moisture)) parts.Add($"moisture {metadata.Moisture.Trim()}");
        if (!string.IsNullOrWhiteSpace(metadata.Temperature)) parts.Add($"temperature {metadata.Temperature.Trim()}");
        if (!string.IsNullOrWhiteSpace(metadata.Material)) parts.Add($"material {metadata.Material.Trim()}");
        if (!string.IsNullOrWhiteSpace(metadata.Description)) parts.Add(metadata.Description.Trim());

        return string.Join("; ", parts) + ".";
    }

    public static IReadOnlyList<string> GetAbmClarifyingQuestions(AssetByMetadata metadata)
    {
        var questions = new List<string>();
        if (metadata is null) return questions;

        var feature = metadata.AssetType.Trim().ToLowerInvariant();
        if (string.IsNullOrWhiteSpace(metadata.Biome))
            questions.Add("What biome surrounds it: forest, grassland, desert, snow/ice, wetland, or something else?");
        if (string.IsNullOrWhiteSpace(metadata.Material))
            questions.Add(feature.Contains("cave", StringComparison.Ordinal)
                ? "What is the cave formed from: limestone, volcanic rock, ice, sandstone, or another material?"
                : "What is the dominant ground or structural material?");
        if (string.IsNullOrWhiteSpace(metadata.Moisture))
            questions.Add(feature.Contains("cave", StringComparison.Ordinal)
                ? "Is the cave dry, damp, flowing with water, or flooded?"
                : "How wet or dry is this location?");
        if (feature.Contains("cave", StringComparison.Ordinal) && !(metadata.Attributes?.ContainsKey("entrance") ?? false))
            questions.Add("What is the cave entrance like: hidden, narrow, walk-in, large, vertical, or multiple entrances?");
        return questions;
    }

    /// <summary>
    /// Creates a world tile with semantic truth only. The transparent placeholder
    /// prevents an image request while preserving compatibility with the current
    /// renderer. A later theme pack can replace only its GroupId representation.
    /// </summary>
    public TileItem CreateAbmTile(AssetByMetadata metadata, double x, double y, double placementZoom = 1.0)
    {
        var typeId = InferAbmTypeId(metadata);
        return new TileItem(
            Id: $"abm:{typeId}",
            Name: DescribeAbm(metadata),
            Image: TransparentPixel,
            X: Math.Clamp(x, 0, 1),
            Y: Math.Clamp(y, 0, 1),
            PlacementZoom: placementZoom,
            CubeX: CubeX,
            CubeY: CubeY,
            CubeZ: CubeZ,
            PlaneIndex: PlaneIndex,
            TierIndex: TierIndex,
            LayerOffset: LayerOffset,
            AssetKind: "metadata",
            TypeId: typeId,
            GroupId: "abm:description",
            Metadata: metadata);
    }

    public TileItem CreateAbmTileFromFeet(string assetType, double elevationFeet, double x, double y, string terrain = "", string description = "", string provenance = "HUMAN") =>
        CreateAbmTile(new AssetByMetadata(
            AssetType: assetType,
            ElevationMeters: FeetToMeters(elevationFeet),
            Terrain: terrain,
            Description: description,
            Provenance: provenance), x, y);

    public void PlaceAbmTile(AssetByMetadata metadata, double x, double y, double placementZoom = 1.0) =>
        AddPlacedTileAtGridDepth(CreateAbmTile(metadata, x, y, placementZoom));

    public IReadOnlyList<AbmMapEntry> GetDescriptionOnlyMap() =>
        PlacedTiles
            .Select(tile => new AbmMapEntry(
                string.IsNullOrWhiteSpace(tile.PlacementId) ? tile.Id : tile.PlacementId,
                GetTileTypeId(tile),
                GetTileGroupId(tile),
                tile.X,
                tile.Y,
                tile.TierIndex,
                tile.LayerOffset,
                tile.Metadata is null ? tile.Name : DescribeAbm(tile.Metadata),
                tile.Metadata))
            .OrderBy(entry => entry.TierIndex)
            .ThenBy(entry => entry.LayerOffset)
            .ThenBy(entry => entry.Y)
            .ThenBy(entry => entry.X)
            .ToList();
}
