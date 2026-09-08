namespace RistWorld;

public sealed partial class WorldSession
{
    // Canonical public-alpha world dimensions. One logical cell is one square kilometre.
    // Ocean 071 is the implicit terrain layer; authored terrain remains sparse.
    // A 30 x 30 world therefore exposes 900 addressable one-kilometre cells without
    // materializing 900 DOM nodes or save records for the ocean itself.
    public const int DefaultCubeWidthKm = 30;
    public const int DefaultCubeHeightKm = 30;
    public const int DefaultCubeCellCount = DefaultCubeWidthKm * DefaultCubeHeightKm;
    public const int DefaultCellWidthKm = 1;
    public const int DefaultCellHeightKm = 1;

    // Compatibility aliases for older callers. Values are now metric; new code must use Km names.
    public const int DefaultCubeWidthMiles = DefaultCubeWidthKm;
    public const int DefaultCubeHeightMiles = DefaultCubeHeightKm;
    public const int DefaultCellWidthMiles = DefaultCellWidthKm;
    public const int DefaultCellHeightMiles = DefaultCellHeightKm;

    public const string DefaultTerrainTilesetName = "Ocean 071";
    public const string DefaultTerrainTilesetSlug = "ocean-071";

    public int CubeWidthKm => DefaultCubeWidthKm;
    public int CubeHeightKm => DefaultCubeHeightKm;
    public int CubeCellCount => DefaultCubeCellCount;
    public int CellWidthKm => DefaultCellWidthKm;
    public int CellHeightKm => DefaultCellHeightKm;
    public string DefaultTerrainTileset => DefaultTerrainTilesetName;

    // Compatibility accessors for legacy UI until all callers are renamed.
    public int CubeWidthMiles => CubeWidthKm;
    public int CubeHeightMiles => CubeHeightKm;
    public int CellWidthMiles => CellWidthKm;
    public int CellHeightMiles => CellHeightKm;

    public static int KmCellX(double normalizedX) =>
        Math.Clamp((int)Math.Floor(normalizedX * DefaultCubeWidthKm), 0, DefaultCubeWidthKm - 1);

    public static int KmCellY(double normalizedY) =>
        Math.Clamp((int)Math.Floor(normalizedY * DefaultCubeHeightKm), 0, DefaultCubeHeightKm - 1);

    public static (int X, int Y) KmCell(double normalizedX, double normalizedY) =>
        (KmCellX(normalizedX), KmCellY(normalizedY));

    // Legacy method names preserve binary/source compatibility while metric becomes canonical.
    public static int MileCellX(double normalizedX) => KmCellX(normalizedX);
    public static int MileCellY(double normalizedY) => KmCellY(normalizedY);
    public static (int X, int Y) MileCell(double normalizedX, double normalizedY) => KmCell(normalizedX, normalizedY);
}
