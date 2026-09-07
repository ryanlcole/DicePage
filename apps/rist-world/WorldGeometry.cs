namespace RistWorld;

/// <summary>
/// Canonical geometry for the recursive Shaelvien world viewer.
/// The world is larger than the viewer. The viewer is a 10x10 window into
/// a 300x300 logical collision field, with the 30x30 origin ocean centered.
/// </summary>
public static class WorldGeometry
{
    public const int WorldColumns = 300;
    public const int WorldRows = 300;
    public const int ViewerColumns = 10;
    public const int ViewerRows = 10;
    public const int OriginOceanColumns = 30;
    public const int OriginOceanRows = 30;

    public const int OriginOceanX = (WorldColumns - OriginOceanColumns) / 2; // 135
    public const int OriginOceanY = (WorldRows - OriginOceanRows) / 2;       // 135

    public const double ViewerWorldScaleX = WorldColumns / (double)ViewerColumns; // 30
    public const double ViewerWorldScaleY = WorldRows / (double)ViewerRows;       // 30

    // At the canonical centered camera, the 10x10 viewer spans cells 145..154.
    public const int CenterViewX = (WorldColumns - ViewerColumns) / 2; // 145
    public const int CenterViewY = (WorldRows - ViewerRows) / 2;       // 145
}
