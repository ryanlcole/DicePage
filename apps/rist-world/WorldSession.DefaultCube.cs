namespace RistWorld;

public sealed partial class WorldSession
{
    // Canonical public-alpha world dimensions. One logical cell is one square mile.
    // Ocean 071 is the implicit terrain layer; authored terrain remains sparse.
    // A 30 x 30 world therefore exposes 900 addressable one-mile cells without
    // materializing 900 DOM nodes or save records for the ocean itself.
    public const int DefaultCubeWidthMiles = 30;
    public const int DefaultCubeHeightMiles = 30;
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

    public static int MileCellX(double normalizedX) =>
        Math.Clamp((int)Math.Floor(normalizedX * DefaultCubeWidthMiles), 0, DefaultCubeWidthMiles - 1);

    public static int MileCellY(double normalizedY) =>
        Math.Clamp((int)Math.Floor(normalizedY * DefaultCubeHeightMiles), 0, DefaultCubeHeightMiles - 1);

    public static (int X, int Y) MileCell(double normalizedX, double normalizedY) =>
        (MileCellX(normalizedX), MileCellY(normalizedY));
}
