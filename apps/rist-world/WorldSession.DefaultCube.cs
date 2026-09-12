namespace RistWorld;

public sealed partial class WorldSession
{
    // Canonical geometry is unitless. A world cube is a 30 x 30 addressable cell
    // surface; measurement systems describe those cells but never redefine them.
    public const int DefaultCubeWidthCells = 30;
    public const int DefaultCubeHeightCells = 30;
    public const int DefaultCubeCellCount = DefaultCubeWidthCells * DefaultCubeHeightCells;
    public const int DefaultCellWidthCells = 1;
    public const int DefaultCellHeightCells = 1;

    // Ordinary authored worlds are limited to 300 x 300 addressable world cells
    // (10 x 10 viewer cubes). Geonaph is the explicit exception and is unbounded;
    // that capability is owned by WorldSession.WorldIdentity rather than the renderer.
    public const int DefaultWorldWidthCells = 300;
    public const int DefaultWorldHeightCells = 300;
    public const int DefaultWorldCubesAcross = DefaultWorldWidthCells / DefaultCubeWidthCells;
    public const int DefaultWorldCubesDown = DefaultWorldHeightCells / DefaultCubeHeightCells;
    public const long DefaultWorldTileCapacity = (long)DefaultWorldWidthCells * DefaultWorldHeightCells;

    // Compatibility aliases for older callers. These names are representation-era
    // artifacts only; new geometry code must use the Cell-named authority above.
    public const int DefaultCubeWidthKm = DefaultCubeWidthCells;
    public const int DefaultCubeHeightKm = DefaultCubeHeightCells;
    public const int DefaultCellWidthKm = DefaultCellWidthCells;
    public const int DefaultCellHeightKm = DefaultCellHeightCells;
    public const int DefaultWorldWidthKm = DefaultWorldWidthCells;
    public const int DefaultWorldHeightKm = DefaultWorldHeightCells;
    public const int DefaultCubeWidthMiles = DefaultCubeWidthCells;
    public const int DefaultCubeHeightMiles = DefaultCubeHeightCells;
    public const int DefaultCellWidthMiles = DefaultCellWidthCells;
    public const int DefaultCellHeightMiles = DefaultCellHeightCells;

    public const string DefaultTerrainTilesetName = "Ocean 071";
    public const string DefaultTerrainTilesetSlug = "ocean-071";

    public int CubeWidthCells => DefaultCubeWidthCells;
    public int CubeHeightCells => DefaultCubeHeightCells;
    public int CubeCellCount => DefaultCubeCellCount;
    public int CellWidthCells => DefaultCellWidthCells;
    public int CellHeightCells => DefaultCellHeightCells;
    public string DefaultTerrainTileset => DefaultTerrainTilesetName;

    // Compatibility accessors for legacy UI until all callers are renamed.
    public int CubeWidthKm => CubeWidthCells;
    public int CubeHeightKm => CubeHeightCells;
    public int CellWidthKm => CellWidthCells;
    public int CellHeightKm => CellHeightCells;
    public int CubeWidthMiles => CubeWidthCells;
    public int CubeHeightMiles => CubeHeightCells;
    public int CellWidthMiles => CellWidthCells;
    public int CellHeightMiles => CellHeightCells;

    public static int CellX(double normalizedX) =>
        Math.Clamp((int)Math.Floor(normalizedX * DefaultCubeWidthCells), 0, DefaultCubeWidthCells - 1);

    public static int CellY(double normalizedY) =>
        Math.Clamp((int)Math.Floor(normalizedY * DefaultCubeHeightCells), 0, DefaultCubeHeightCells - 1);

    public static (int X, int Y) Cell(double normalizedX, double normalizedY) =>
        (CellX(normalizedX), CellY(normalizedY));

    public static int KmCellX(double normalizedX) => CellX(normalizedX);
    public static int KmCellY(double normalizedY) => CellY(normalizedY);
    public static (int X, int Y) KmCell(double normalizedX, double normalizedY) => Cell(normalizedX, normalizedY);
    public static int MileCellX(double normalizedX) => CellX(normalizedX);
    public static int MileCellY(double normalizedY) => CellY(normalizedY);
    public static (int X, int Y) MileCell(double normalizedX, double normalizedY) => Cell(normalizedX, normalizedY);
}
