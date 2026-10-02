namespace RistWorld;

public sealed partial class WorldSession
{
    // Canonical geometry is unitless. One viewer window is a 30 x 30 addressable-cell
    // surface; measurement systems describe those cells but never redefine them.
    public const int DefaultCubeWidthCells = 30;
    public const int DefaultCubeHeightCells = 30;
    public const int DefaultCubeCellCount = DefaultCubeWidthCells * DefaultCubeHeightCells;
    public const int DefaultCellWidthCells = 1;
    public const int DefaultCellHeightCells = 1;

    // An authored world is 300 x 300 addressable world cells. A 30 x 30 viewer therefore
    // moves across a 10 x 10 set of viewer-sized windows without changing world truth.
    public const int DefaultWorldWidthCells = 300;
    public const int DefaultWorldHeightCells = 300;
    public const int DefaultWorldCubesAcross = DefaultWorldWidthCells / DefaultCubeWidthCells;
    public const int DefaultWorldCubesDown = DefaultWorldHeightCells / DefaultCubeHeightCells;
    public const long DefaultWorldTileCapacity = (long)DefaultWorldWidthCells * DefaultWorldHeightCells;

    // Every recursive authoring scope uses the full 300 x 300 coordinate field.
    // The 30 x 30 cube is the viewer window; the MMO deed grid is a separate
    // ownership/navigation surface. A scope transition therefore occurs every
    // 10 viewer-window widths: 300 / 30 = 10.
    public const int SpatialScopeGridColumns = DefaultWorldWidthCells;
    public const int SpatialScopeGridRows = DefaultWorldHeightCells;
    public const int SpatialScopeTransitionLayers = LayersPerTier;
    public const int SpatialScopeZoomFactor = DefaultWorldWidthCells / DefaultCubeWidthCells;
    public const int WorldViewAngleDegrees = 0;
    public const int RegionViewAngleDegrees = 15;
    public const int LocalViewAngleDegrees = 30;
    public const int InstanceViewAngleDegrees = 45;
    public const string SpatialWorldCoordinateSpace = "world-grid-300-v2";

    // Starting authoring raster for every user's surface world. This is a presentation
    // boundary only; recursive world identity/coordinates remain independent of pixels.
    public const int DefaultSurfaceWorldWidthPixels = 2048;
    public const int DefaultSurfaceWorldHeightPixels = 2048;

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

    // Worlds have no implicit terrain/background. Every visible terrain asset is authored.
    public const string DefaultTerrainTilesetName = "";
    public const string DefaultTerrainTilesetSlug = "";

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
