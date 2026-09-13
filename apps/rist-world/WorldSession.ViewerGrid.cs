namespace RistWorld;

public sealed partial class WorldSession
{
    public int ViewerGridColumns { get; private set; } = DefaultWorldWidthCells;
    public int ViewerGridRows { get; private set; } = DefaultWorldHeightCells;
    public int ViewerZStep { get; private set; } = 3;

    // These are representation-scale multipliers, not world truth. Canonical geometry
    // remains cells; physical or fictional measurement profiles describe those cells.
    static readonly double[] ViewerScaleMultipliers = [1d, 10d, 100d, 1000d, 10000d, 100000d, 1000000d];

    public double ViewerScaleMultiplier => ViewerScaleMultipliers[Math.Clamp(ViewerZStep, 0, ViewerScaleMultipliers.Length - 1)];
    public double ViewerZDistanceMeters => ViewerScaleMultiplier; // compatibility readout for physical profiles
    public double ViewerAspectRatio => ViewerGridRows <= 0 ? 1d : ViewerGridColumns / (double)ViewerGridRows;
    public string ViewerZDistanceLabel => IsMeasurefict
        ? FormatMeasurefictDistance(GridDistance)
        : FormatViewerDistance(ViewerZDistanceMeters);
    public string ViewerGridSizeLabel => $"{ViewerGridColumns}×{ViewerGridRows}";
    public string ViewerPhysicalSizeLabel => IsMeasurefict
        ? $"{FormatMeasurefictDistance(ViewerGridColumns * GridDistance)} × {FormatMeasurefictDistance(ViewerGridRows * GridDistance)}"
        : $"{FormatViewerDistance(ViewerGridColumns * ViewerZDistanceMeters)} × {FormatViewerDistance(ViewerGridRows * ViewerZDistanceMeters)}";

    public void SetViewerGridColumns(int value)
    {
        ViewerGridColumns = Math.Clamp(value, 1, DefaultWorldWidthCells);
        Notify();
    }

    public void SetViewerGridRows(int value)
    {
        ViewerGridRows = Math.Clamp(value, 1, DefaultWorldHeightCells);
        Notify();
    }

    public void SetViewerZStep(int value)
    {
        var oldScale = ViewerScaleMultiplier;
        var nextStep = Math.Clamp(value, 0, ViewerScaleMultipliers.Length - 1);
        if (nextStep == ViewerZStep) return;
        ViewerZStep = nextStep;
        var nextScale = ViewerScaleMultiplier;

        if (IsMeasurefict)
        {
            var ratio = oldScale <= 0d ? 1d : nextScale / oldScale;
            GridDistance = Math.Clamp(GridDistance * ratio, MinMeasurementPerCell, MaxMeasurementPerCell);
        }
        else if (nextScale >= 1000d)
        {
            SetDistanceUnit("km");
            GridDistance = nextScale / 1000d;
        }
        else
        {
            SetDistanceUnit("m");
            GridDistance = nextScale;
        }

        GridCalibrationZoom = Math.Max(ViewZoom, .01);
        Notify();
    }

    string FormatMeasurefictDistance(double amount) =>
        $"{FormatMeasurementNumber(amount)} {MeasurementUnitName(amount)}";

    static string FormatViewerDistance(double meters)
    {
        if (meters >= 1_000_000) return $"{meters / 1_000_000:0.##} Mm";
        if (meters >= 1000) return $"{meters / 1000:0.##} km";
        return $"{meters:0.##} m";
    }
}
