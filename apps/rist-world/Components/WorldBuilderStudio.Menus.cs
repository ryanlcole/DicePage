using Microsoft.JSInterop;

namespace RistWorld.Components;

public partial class WorldBuilderStudio
{
    bool _autoSave = true;
    const double CanonicalKilometersPerCell = 1.0;

    static readonly WorldBuilderTierShortcut[] TierShortcuts =
    [
        new("ocean-floor", "Ocean Floor", 0),
        new("surface", "Surface", 1),
        new("higher-ground", "Higher Ground", 2),
        new("clouds", "Clouds", 3)
    ];

    [JSInvokable]
    public Task<WorldBuilderDepthState> GetWorldBuilderDepthState() =>
        // Compatibility DTO for the existing JS bridge. Recursive Worldbuilder
        // view depth is Tier-only; visual Layer is edited per asset and is never
        // projected into this viewer address.
        Task.FromResult(new WorldBuilderDepthState(
            WorldSession.SceneZOf(Session.TierIndex, 0),
            Session.TierIndex,
            0,
            _zLocked));

    [JSInvokable]
    public Task<IReadOnlyList<WorldBuilderTierShortcut>> GetWorldBuilderTierShortcuts() =>
        Task.FromResult<IReadOnlyList<WorldBuilderTierShortcut>>(TierShortcuts);

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
    public async Task<WorldBuilderDepthState> SetViewerSceneZFromJs(int sceneZ)
    {
        if (_zLocked) return await GetWorldBuilderDepthState();

        var (tier, _) = WorldSession.SplitSceneZ(Math.Clamp(sceneZ, -500, 500));
        Session.SetSceneZ(WorldSession.SceneZOf(tier, 0));
        await InvokeAsync(StateHasChanged);
        return await GetWorldBuilderDepthState();
    }

    [JSInvokable]
    public async Task<WorldBuilderDepthState> MoveViewerSceneZFromJs(int delta)
    {
        if (_zLocked || delta == 0) return await GetWorldBuilderDepthState();

        Session.SetSceneZ(WorldSession.SceneZOf(Session.TierIndex + Math.Sign(delta), 0));
        await InvokeAsync(StateHasChanged);
        return await GetWorldBuilderDepthState();
    }

    [JSInvokable]
    public async Task<WorldBuilderDepthState> SetViewerTierFromJs(int tierIndex)
    {
        if (_zLocked) return await GetWorldBuilderDepthState();

        var shortcut = TierShortcuts.FirstOrDefault(x => x.TierIndex == tierIndex);
        if (shortcut is null) return await GetWorldBuilderDepthState();

        Session.SetSceneZ(WorldSession.SceneZOf(shortcut.TierIndex, 0));
        await InvokeAsync(StateHasChanged);
        return await GetWorldBuilderDepthState();
    }

    // Compatibility entry points for older JS callers. Tier may move the
    // viewer's spatial depth. "Add Layer" is intentionally a no-op because
    // visual Layer belongs to a placed asset, not to global Z.
    [JSInvokable]
    public Task<WorldBuilderDepthState> AddTierAtSceneZFromJs(int sceneZ) => SetViewerSceneZFromJs(sceneZ);

    [JSInvokable]
    public Task<WorldBuilderDepthState> AddLayerAtSceneZFromJs(int sceneZ) => GetWorldBuilderDepthState();

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
        ResetWorldBuilderHistory();
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
        if (published)
            await Session.PublishActiveMapCardAsync(_quickTiles.Select(x => x.Id));
        else
            await Session.SaveActiveMapCardAsync(_quickTiles.Select(x => x.Id), false);
        _publishMode = published;
        return _publishMode;
    }

    void RestoreQuickTilesFromActiveCard()
    {
        _quickTiles.Clear();
        foreach (var id in Session.ActiveMapCardQuickSlotTileIds)
        {
            var tile = FindAsset(id);
            if (tile is not null && _quickTiles.All(x => !string.Equals(x.Id, tile.Id, StringComparison.Ordinal)))
                _quickTiles.Add(tile);
        }
    }
}

public sealed record WorldBuilderDepthState(int SceneZ, int TierIndex, int LayerOffset, bool ViewerLocked);
public sealed record WorldBuilderTierShortcut(string Key, string Label, int TierIndex);
public sealed record PhysicalCardLanguageProfile(string Mode, string LanguageTag, string InGameLanguage, string TextDirection);