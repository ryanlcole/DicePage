namespace RistWorld;

public sealed partial class WorldSession
{
    // Canonical new-world dimensions. One logical cell is one square mile.
    // Do not materialize 10,000 placed tiles: Ocean 071 is the implicit base
    // terrain and authored tiles are sparse overrides.
    public const int DefaultCubeWidthMiles = 100;
    public const int DefaultCubeHeightMiles = 100;
    public const int DefaultCubeCellCount = DefaultCubeWidthMiles * DefaultCubeHeightMiles;
    public const int DefaultCellWidthMiles = 1;
    public const int DefaultCellHeightMiles = 1;

    public const string DefaultTerrainTilesetName = "Ocean 071";
    public const string DefaultTerrainTilesetSlug = "ocean-071";

    public int CubeWidthMiles => DefaultCubeWidthMiles;
    public int CubeHeightMiles => DefaultCubeHeightMiles;
    public int CubeCellCount => DefaultCubeCellCount;
    public int CellWidthMiles => DefaultCellWidthMiles;
    public int CellHeightMiles => DefaultCellHeightMiles;
    public string DefaultTerrainTileset => DefaultTerrainTilesetName;

    // World-space conversion helpers. The existing normalized placement model
    // remains intact while recursive geography can address exact one-mile cells.
    public static int MileCellX(double normalizedX) =>
        Math.Clamp((int)Math.Floor(normalizedX * DefaultCubeWidthMiles), 0, DefaultCubeWidthMiles - 1);

    public static int MileCellY(double normalizedY) =>
        Math.Clamp((int)Math.Floor(normalizedY * DefaultCubeHeightMiles), 0, DefaultCubeHeightMiles - 1);

    public static (int X, int Y) MileCell(double normalizedX, double normalizedY) =>
        (MileCellX(normalizedX), MileCellY(normalizedY));
}
