using Microsoft.JSInterop;

namespace RistWorld.Components;

public partial class WorldBuilderStudio
{
    bool _autoSave = true;
    double _distancePerSquareKmAtZ0 = 1.0;

    [JSInvokable]
    public Task<WorldBuilderDepthState> GetWorldBuilderDepthState() =>
        Task.FromResult(new WorldBuilderDepthState(Session.SceneZ, Session.TierIndex, Session.LayerOffset, _zLocked));

    [JSInvokable]
    public Task<bool> ToggleViewerLockFromJs()
    {
        _zLocked = !_zLocked;
        return Task.FromResult(_zLocked);
    }

    [JSInvokable]
    public Task<bool> SetViewerLockFromJs(bool locked)
    {
        _zLocked = locked;
        return Task.FromResult(_zLocked);
    }

    [JSInvokable]
    public Task<WorldBuilderDepthState> SetViewerSceneZFromJs(int sceneZ)
    {
        sceneZ = Math.Clamp(sceneZ, -500, 500);
        var guard = 0;
        while (Session.SceneZ < sceneZ && guard++ < 1100) Session.MoveLayer(1);
        guard = 0;
        while (Session.SceneZ > sceneZ && guard++ < 1100) Session.MoveLayer(-1);
        return GetWorldBuilderDepthState();
    }

    [JSInvokable]
    public Task<WorldBuilderDepthState> AddTierAtSceneZFromJs(int sceneZ)
    {
        var targetTier = Math.Max(0, (int)Math.Floor(sceneZ / 10.0));
        var guard = 0;
        while (Session.TierIndex < targetTier && guard++ < 100) Session.MoveTier(1);
        guard = 0;
        while (Session.TierIndex > targetTier && guard++ < 100) Session.MoveTier(-1);
        return GetWorldBuilderDepthState();
    }

    [JSInvokable]
    public Task<WorldBuilderDepthState> AddLayerAtSceneZFromJs(int sceneZ) => SetViewerSceneZFromJs(sceneZ);

    [JSInvokable]
    public Task<double> SetDistancePerSquareKmAtZ0FromJs(double km)
    {
        if (double.IsFinite(km) && km > 0 && km <= 1_000_000)
            _distancePerSquareKmAtZ0 = km;
        return Task.FromResult(_distancePerSquareKmAtZ0);
    }

    [JSInvokable]
    public Task<double> GetDistancePerSquareKmAtZ0FromJs() => Task.FromResult(_distancePerSquareKmAtZ0);

    // Compatibility aliases for older cached clients. These now mean distance per viewer square at Z=0.
    [JSInvokable]
    public Task<double> SetTileSizeKmAtOriginFromJs(double km) => SetDistancePerSquareKmAtZ0FromJs(km);

    [JSInvokable]
    public Task<double> GetTileSizeKmAtOriginFromJs() => GetDistancePerSquareKmAtZ0FromJs();

    [JSInvokable]
    public async Task SaveWorldFromJs() => await SaveAsync();

    [JSInvokable]
    public async Task LoadWorldFromJs()
    {
        if (Session.IsLoggedIn) await Session.LoadPrivateCheckpointAsync();
        else await Session.LoadAsync();
    }

    [JSInvokable]
    public Task<bool> SetAutoSaveFromJs(bool enabled)
    {
        _autoSave = enabled;
        return Task.FromResult(_autoSave);
    }

    [JSInvokable]
    public Task<bool> GetAutoSaveFromJs() => Task.FromResult(_autoSave);

    [JSInvokable]
    public Task<bool> SetPublishModeFromJs(bool published)
    {
        _publishMode = published;
        return Task.FromResult(_publishMode);
    }
}

public sealed record WorldBuilderDepthState(int SceneZ, int TierIndex, int LayerOffset, bool ViewerLocked);
