namespace RistWorld;

public sealed partial class WorldSession
{
    public event Action? MapViewResetRequested;

    public double ViewPanX { get; private set; }
    public double ViewPanY { get; private set; }

    public void RequestMapViewReset()
    {
        MapViewResetRequested?.Invoke();
    }

    public void PublishMapView(double panX, double panY, double zoom, bool notify = true)
    {
        ViewPanX = panX;
        ViewPanY = panY;
        ViewZoom = zoom;
        if (notify) Notify();
    }
}
