using Microsoft.JSInterop;

namespace RistWorld.Components;

public sealed partial class WorldMap
{
    private static WeakReference<WorldMap>? _activeViewer;

    public WorldMap()
    {
        _activeViewer = new WeakReference<WorldMap>(this);
    }

    private static bool TryGetActiveViewer(out WorldMap viewer)
    {
        viewer = null!;
        return _activeViewer is not null && _activeViewer.TryGetTarget(out viewer);
    }

    private object ViewerCameraSnapshot() => new
    {
        panX = G.PanX,
        panY = G.PanY,
        zoom = G.Zoom,
        minZoom = MapGestureState.MinZoom,
        maxZoom = MapGestureState.MaxZoom,
        defaultZoom = MapGestureState.DefaultZoom
    };

    [JSInvokable("WorldMapViewerGetState")]
    public static object? GetViewerStateFromJs()
        => TryGetActiveViewer(out var viewer) ? viewer.ViewerCameraSnapshot() : null;

    [JSInvokable("WorldMapViewerSetZoom")]
    public static async Task<object?> SetViewerZoomFromJs(double zoom)
    {
        if (!TryGetActiveViewer(out var viewer)) return null;

        await viewer.InvokeAsync(async () =>
        {
            await viewer.ZoomAt(null, null, zoom);
            viewer.StateHasChanged();
        });

        return viewer.ViewerCameraSnapshot();
    }

    [JSInvokable("WorldMapViewerSetPan")]
    public static async Task<object?> SetViewerPanFromJs(double panX, double panY)
    {
        if (!TryGetActiveViewer(out var viewer)) return null;

        await viewer.InvokeAsync(() =>
        {
            viewer.G.PanX = panX;
            viewer.G.PanY = panY;
            viewer.Session.Notify();
            viewer.StateHasChanged();
        });

        return viewer.ViewerCameraSnapshot();
    }

    [JSInvokable("WorldMapViewerReset")]
    public static async Task<object?> ResetViewerFromJs()
    {
        if (!TryGetActiveViewer(out var viewer)) return null;

        await viewer.InvokeAsync(() =>
        {
            viewer.G.PanX = 0;
            viewer.G.PanY = 0;
            viewer.G.Zoom = MapGestureState.DefaultZoom;
            viewer.Session.ViewZoom = viewer.G.Zoom;
            viewer.Session.Notify();
            viewer.StateHasChanged();
        });

        return viewer.ViewerCameraSnapshot();
    }
}
