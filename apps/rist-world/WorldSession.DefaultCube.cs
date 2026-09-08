namespace RistWorld;

public sealed partial class WorldSession
{
    // Canonical public-alpha WORLD surface.
    //
    // The world is 30 x 30 logical terrain tiles. One logical tile is exactly
    // 1 km x 1 km. The viewer may draw ten 100 m subdivisions inside a tile,
    // but placement, snapping, persistence, regions, and terrain all resolve
    // against the 30 x 30 one-kilometre tile authority.
    //
    // Ocean 071 is the implicit terrain layer; authored terrain remains sparse.
    public const int DefaultCubeWidthKilometers = 30;
    public const int DefaultCubeHeightKilometers = 30;
    public const int DefaultCubeCellCount = DefaultCubeWidthKilometers * DefaultCubeHeightKilometers;
    public const int DefaultCellWidthKilometers = 1;
    public const int DefaultCellHeightKilometers = 1;
    public const int SubcellsPerTile = 10;

    // Compatibility aliases retained so older callers do not break while the
    // codebase finishes moving from the former mile-named authority.
    public const int DefaultCubeWidthMiles = DefaultCubeWidthKilometers;
    public const int DefaultCubeHeightMiles = DefaultCubeHeightKilometers;
    public const int DefaultCellWidthMiles = DefaultCellWidthKilometers;
    public const int DefaultCellHeightMiles = DefaultCellHeightKilometers;

    public const string DefaultTerrainTilesetName = "Ocean 071";
    public const string DefaultTerrainTilesetSlug = "ocean-071";

    public int CubeWidthKilometers => DefaultCubeWidthKilometers;
    public int CubeHeightKilometers => DefaultCubeHeightKilometers;
    public int CubeCellCount => DefaultCubeCellCount;
    public int CellWidthKilometers => DefaultCellWidthKilometers;
    public int CellHeightKilometers => DefaultCellHeightKilometers;
    public string DefaultTerrainTileset => DefaultTerrainTilesetName;

    // Compatibility properties for saved/client code that still references the
    // previous names. Values now represent the canonical kilometre tile count.
    public int CubeWidthMiles => DefaultCubeWidthKilometers;
    public int CubeHeightMiles => DefaultCubeHeightKilometers;
    public int CellWidthMiles => DefaultCellWidthKilometers;
    public int CellHeightMiles => DefaultCellHeightKilometers;

    public static int KilometerCellX(double normalizedX) =>
        Math.Clamp((int)Math.Floor(normalizedX * DefaultCubeWidthKilometers), 0, DefaultCubeWidthKilometers - 1);

    public static int KilometerCellY(double normalizedY) =>
        Math.Clamp((int)Math.Floor(normalizedY * DefaultCubeHeightKilometers), 0, DefaultCubeHeightKilometers - 1);

    public static (int X, int Y) KilometerCell(double normalizedX, double normalizedY) =>
        (KilometerCellX(normalizedX), KilometerCellY(normalizedY));

    public static int MileCellX(double normalizedX) => KilometerCellX(normalizedX);
    public static int MileCellY(double normalizedY) => KilometerCellY(normalizedY);
    public static (int X, int Y) MileCell(double normalizedX, double normalizedY) => KilometerCell(normalizedX, normalizedY);
}
