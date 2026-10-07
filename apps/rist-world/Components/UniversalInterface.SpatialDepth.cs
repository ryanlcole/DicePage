using Microsoft.JSInterop;

namespace RistWorld.Components;

public partial class UniversalInterface
{
    // Compatibility state retained so cached World Builder clients cannot fail
    // while the authority boundary moves to Region Definer.
    bool _spatialReferenceDepthChosen;
    bool _spatialZSelectionActive;
    int _spatialReferenceTier;
    int _spatialReferenceLayer;
    int? _spatialZStartTier;
    int? _spatialZEndTier;

    bool CanDirectEditSpatialDepth =>
        !_exploreReadOnlyMode
        && ((_inspectionEditMode && Session.TrustedPlatformDeveloper)
            || Session.HasWorldBuilderEditAuthority
            || (string.Equals(_selectedDeedKind, "SHAELVIEN_ORIGIN", StringComparison.OrdinalIgnoreCase)
                && Session.OwnsCanonicalGeonaphZone));

    int SelectedSpatialMaxHeight
    {
        get
        {
            if (string.Equals(_selectedDeedKind, "SHAELVIEN_ORIGIN", StringComparison.OrdinalIgnoreCase))
                return Math.Max(1, WorldSession.EndemarMaxHeight);

            var parcel = Session.MmoParcels.FirstOrDefault(item =>
                (!string.IsNullOrWhiteSpace(_selectedDeedId)
                    && string.Equals(item.ParcelId, _selectedDeedId, StringComparison.Ordinal))
                || (!string.IsNullOrWhiteSpace(_selectedDeedRegionId)
                    && string.Equals(item.RegionId, _selectedDeedRegionId, StringComparison.Ordinal)));

            if (parcel is { MaxHeight: > 0 })
                return Math.Max(1, parcel.MaxHeight);

            return Session.IsGeonaphWorld
                ? Math.Max(1, WorldSession.MmoParcelMaxHeight)
                : Math.Max(1, WorldSession.LayersPerTier);
        }
    }

    int SpatialMaxTierIndex => Math.Max(0, (SelectedSpatialMaxHeight - 1) / WorldSession.LayersPerTier);

    int SpatialMaxLayerForTier(int tier)
    {
        tier = Math.Clamp(tier, 0, SpatialMaxTierIndex);
        var remaining = SelectedSpatialMaxHeight - (tier * WorldSession.LayersPerTier);
        return Math.Clamp(remaining - 1, 0, WorldSession.LayersPerTier - 1);
    }

    void ClampSpatialDepth(ref int tier, ref int layer)
    {
        tier = Math.Clamp(tier, 0, SpatialMaxTierIndex);
        layer = Math.Clamp(layer, 0, SpatialMaxLayerForTier(tier));
    }

    // World Builder owns World terrain/Tier/Layer authoring. It no longer owns
    // the Region-bounding workflow, so semantic spatial-depth mode is dormant.
    bool IsSpatialDepthSemanticStage => false;

    void ResetLegacySpatialDefinitionState()
    {
        _spatialDefinitionActive = false;
        _spatialReferenceDepthChosen = false;
        _spatialZSelectionActive = false;
        _spatialZStartTier = null;
        _spatialZEndTier = null;
        _spatialReferenceTier = 0;
        _spatialReferenceLayer = 0;
        if (_stage is Stage.WorldBuilderTier or Stage.WorldBuilderLayer)
            _stage = Stage.WorldHome;
    }

    async Task<bool> AdjustSpatialDepthSemanticAsync(int direction)
    {
        _ = direction;
        if (_spatialDefinitionActive)
        {
            ResetLegacySpatialDefinitionState();
            _message = "Region X/Y/Z volume definition belongs to Region Definer. World Builder continues editing the continuous World.";
            await InvokeAsync(StateHasChanged);
        }
        return false;
    }

    async Task<bool> AdvanceSpatialDepthSemanticAsync()
    {
        if (_spatialDefinitionActive)
        {
            ResetLegacySpatialDefinitionState();
            _message = "Open Region Definer to set X min/max and Y min/max first, then Z min/max Tier. World Builder does not create Region footprints.";
            await InvokeAsync(StateHasChanged);
        }
        return false;
    }

    async Task<bool> BeginWorldBuilderSpatialDepthControlCoreAsync(string phase)
    {
        _ = phase;
        if (!CanDirectEditSpatialDepth)
            return false;

        ResetLegacySpatialDefinitionState();
        _message = "Region definition has moved to Region Definer: define X min/max and Y min/max on the square World coordinate grid, then define Z min/max Tier. World Builder remains the continuous underlying World.";
        await InvokeAsync(StateHasChanged);
        await SyncWorldBuilderDepthAsync();

        // Return true because the legacy request was deliberately handled. This
        // prevents cached hosts from falling back to the retired hex workflow.
        return true;
    }

    [JSInvokable]
    public Task<bool> BeginWorldBuilderSpatialDepthControlPhaseAsync(string phase) =>
        BeginWorldBuilderSpatialDepthControlCoreAsync(phase);

    [JSInvokable]
    public Task<bool> BeginWorldBuilderSpatialDepthControlAsync() =>
        BeginWorldBuilderSpatialDepthControlCoreAsync("delegated");

    [JSInvokable]
    public async Task EndWorldBuilderSpatialDepthControlAsync()
    {
        ResetLegacySpatialDefinitionState();
        await InvokeAsync(StateHasChanged);
    }

    [JSInvokable]
    public Task<object> GetWorldBuilderDepthAuthorityAsync()
    {
        var tier = _tier;
        var layer = _layer;
        ClampSpatialDepth(ref tier, ref layer);
        _tier = tier;
        _layer = layer;

        return Task.FromResult<object>(new
        {
            canEdit = false,
            delegatedTo = "REGION_DEFINER",
            worldBuilderRole = "CONTINUOUS_WORLD_AUTHORING",
            regionDefinitionOrder = new[] { "X_MIN_MAX", "Y_MIN_MAX", "Z_MIN_MAX_TIER" },
            maxHeight = SelectedSpatialMaxHeight,
            maxTierIndex = SpatialMaxTierIndex,
            maxLayer = SpatialMaxLayerForTier(tier),
            tier,
            layer,
            referenceDepthChosen = false,
            verticalVolume = false
        });
    }

    [JSInvokable]
    public async Task ReceiveWorldBuilderSpatialDepthAsync(int tier, int layer)
    {
        // The embedded viewer is representation only. It cannot revive retired
        // Region authority inside World Builder or write parent Tier/Layer state.
        _ = tier;
        _ = layer;
        ResetLegacySpatialDefinitionState();
        await SyncWorldBuilderDepthAsync();
    }
}
