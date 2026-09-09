namespace RistWorld;

public sealed partial class WorldSession
{
    public int ViewerGridColumns { get; private set; } = 30;
    public int ViewerGridRows { get; private set; } = 30;
    public int ViewerZStep { get; private set; } = 3;

    static readonly double[] ViewerScaleMeters = [1d, 10d, 100d, 1000d, 10000d, 100000d, 1000000d];

    public double ViewerZDistanceMeters => ViewerScaleMeters[Math.Clamp(ViewerZStep, 0, ViewerScaleMeters.Length - 1)];
    public double ViewerAspectRatio => ViewerGridRows <= 0 ? 1d : ViewerGridColumns / (double)ViewerGridRows;
    public string ViewerZDistanceLabel => FormatViewerDistance(ViewerZDistanceMeters);
    public string ViewerGridSizeLabel => $"{ViewerGridColumns}×{ViewerGridRows}";
    public string ViewerPhysicalSizeLabel => $"{FormatViewerDistance(ViewerGridColumns * ViewerZDistanceMeters)} × {FormatViewerDistance(ViewerGridRows * ViewerZDistanceMeters)}";

    public void SetViewerGridColumns(int value)
    {
        ViewerGridColumns = Math.Clamp(value, 1, 100);
        Notify();
    }

    public void SetViewerGridRows(int value)
    {
        ViewerGridRows = Math.Clamp(value, 1, 100);
        Notify();
    }

    public void SetViewerZStep(int value)
    {
        ViewerZStep = Math.Clamp(value, 0, ViewerScaleMeters.Length - 1);
        var meters = ViewerZDistanceMeters;
        if (meters >= 1000)
        {
            SetDistanceUnit("km");
            GridDistance = meters / 1000d;
        }
        else
        {
            SetDistanceUnit("m");
            GridDistance = meters;
        }
        GridCalibrationZoom = Math.Max(ViewZoom, .01);
        Notify();
    }

    static string FormatViewerDistance(double meters)
    {
        if (meters >= 1_000_000) return $"{meters / 1_000_000:0.##} Mm";
        if (meters >= 1000) return $"{meters / 1000:0.##} km";
        return $"{meters:0.##} m";
    }
}
