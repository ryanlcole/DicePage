using Microsoft.JSInterop;

namespace RistWorld.Components;

public partial class WorldBuilderStudio
{
    bool _autoSave = true;
    const double CanonicalKilometersPerCell = 1.0;

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

    [JSInvokable] public Task<double> SetDistancePerSquareKmAtZ0FromJs(double km) => Task.FromResult(CanonicalKilometersPerCell);
    [JSInvokable] public Task<double> GetDistancePerSquareKmAtZ0FromJs() => Task.FromResult(CanonicalKilometersPerCell);
    [JSInvokable] public Task<double> SetTileSizeKmAtOriginFromJs(double km) => Task.FromResult(CanonicalKilometersPerCell);
    [JSInvokable] public Task<double> GetTileSizeKmAtOriginFromJs() => Task.FromResult(CanonicalKilometersPerCell);

    [JSInvokable]
    public Task SetActiveCardLanguageFromJs(string mode, string displayLanguage, string inGameLanguage, string textDirection)
    {
        Session.SetActiveMapCardLanguage(mode, displayLanguage, inGameLanguage, textDirection);
        return Task.CompletedTask;
    }

    async Task CaptureActiveCardLanguageAsync()
    {
        try
        {
            var language = await JS.InvokeAsync<PhysicalCardLanguageProfile>("ristCardTiff.languageProfile");
            if (language is not null)
                Session.SetActiveMapCardLanguage(language.Mode, language.LanguageTag, language.InGameLanguage, language.TextDirection);
        }
        catch { }
    }

    // Save creates/updates the private account-owned map card. Browser storage remains
    // a recovery cache; logged-in users also receive the AWS card record immediately.
    [JSInvokable]
    public async Task SaveWorldFromJs()
    {
        await CaptureActiveCardLanguageAsync();
        await Session.SaveAsync();
        await Session.SaveActiveMapCardAsync(_quickTiles.Select(x => x.Id));
    }

    // Load prefers the account-owned card, then falls back to the older world snapshot.
    [JSInvokable]
    public async Task LoadWorldFromJs()
    {
        var loaded = await Session.LoadActiveMapCardAsync();
        if (!loaded)
        {
            if (Session.IsLoggedIn) await Session.LoadPrivateCheckpointAsync();
            else await Session.LoadAsync();
        }
        RestoreQuickTilesFromActiveCard();
    }

    [JSInvokable]
    public Task<bool> SetAutoSaveFromJs(bool enabled)
    {
        _autoSave = enabled;
        return Task.FromResult(_autoSave);
    }

    [JSInvokable]
    public Task<bool> GetAutoSaveFromJs() => Task.FromResult(_autoSave);

    // Publish promotes the current map card into account inventory and writes the
    // published representation. Unpublish changes availability without deleting
    // the inventory identity.
    [JSInvokable]
    public async Task<bool> SetPublishModeFromJs(bool published)
    {
        await CaptureActiveCardLanguageAsync();
        _publishMode = published;
        if (published)
            await Session.PublishActiveMapCardAsync(_quickTiles.Select(x => x.Id));
        else
            await Session.SaveActiveMapCardAsync(_quickTiles.Select(x => x.Id), false);
        return _publishMode;
    }

    void RestoreQuickTilesFromActiveCard()
    {
        _quickTiles.Clear();
        foreach (var id in Session.ActiveMapCardQuickSlotTileIds)
        {
            var tile = Session.AtlasTiles.FirstOrDefault(x => string.Equals(x.Id, id, StringComparison.Ordinal));
            if (tile is not null && _quickTiles.All(x => !string.Equals(x.Id, tile.Id, StringComparison.Ordinal)))
                _quickTiles.Add(tile);
        }
    }
}

public sealed record WorldBuilderDepthState(int SceneZ, int TierIndex, int LayerOffset, bool ViewerLocked);
public sealed record PhysicalCardLanguageProfile(string Mode, string LanguageTag, string InGameLanguage, string TextDirection);
