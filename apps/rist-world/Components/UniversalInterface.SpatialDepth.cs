using Microsoft.JSInterop;

namespace RistWorld.Components;

public partial class UniversalInterface
{
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

    bool IsSpatialDepthSemanticStage =>
        _spatialDefinitionActive && (_stage is Stage.WorldBuilderTier or Stage.WorldBuilderLayer);

    async Task<bool> SendSpatialSelectionMarkerAsync(object marker)
    {
        if (_worldBuilderSourceModule is null)
            return false;

        try
        {
            await _worldBuilderSourceModule.InvokeVoidAsync(
                "setSpatialDefinition",
                _worldBuilderFrame,
                marker);
            return true;
        }
        catch (JSException)
        {
            return false;
        }
    }

    async Task<bool> AdjustSpatialDepthSemanticAsync(int direction)
    {
        if (!IsSpatialDepthSemanticStage || !CanDirectEditSpatialDepth)
            return false;

        direction = Math.Sign(direction);
        if (direction == 0)
            return true;

        if (_spatialZSelectionActive)
        {
            if (_stage != Stage.WorldBuilderTier)
                return true;

            _tier = Math.Clamp(_tier + direction, 0, SpatialMaxTierIndex);
            _layer = Math.Clamp(_spatialReferenceLayer, 0, SpatialMaxLayerForTier(_tier));
            _message = _spatialZStartTier.HasValue
                ? $"Z Tier {_tier}. First boundary is Tier {_spatialZStartTier.Value}; choose the opposite boundary and touch the left display."
                : $"Z Tier {_tier}. Touch the left display to set the first vertical boundary.";
        }
        else if (_stage == Stage.WorldBuilderTier)
        {
            _tier = Math.Clamp(_tier + direction, 0, SpatialMaxTierIndex);
            _layer = Math.Clamp(_layer, 0, SpatialMaxLayerForTier(_tier));
            _message = $"Reference Tier {_tier}. Choose the tier whose visible layer you will trace.";
        }
        else
        {
            _layer = Math.Clamp(_layer + direction, 0, SpatialMaxLayerForTier(_tier));
            _message = $"Reference Layer {_layer} on Tier {_tier}.";
        }

        await SyncWorldBuilderDepthAsync();
        await InvokeAsync(StateHasChanged);
        return true;
    }

    async Task<bool> AdvanceSpatialDepthSemanticAsync()
    {
        if (!IsSpatialDepthSemanticStage || !CanDirectEditSpatialDepth)
            return false;

        if (_spatialZSelectionActive)
        {
            if (_stage != Stage.WorldBuilderTier)
                return true;

            if (!_spatialZStartTier.HasValue)
            {
                _spatialZStartTier = _tier;
                _message = $"First Z boundary set at Tier {_tier}. Move to the other vertical boundary; choose the same tier again for a single-tier region.";
                await InvokeAsync(StateHasChanged);
                return true;
            }

            _spatialZEndTier = _tier;
            var minTier = Math.Min(_spatialZStartTier.Value, _spatialZEndTier.Value);
            var maxTier = Math.Max(_spatialZStartTier.Value, _spatialZEndTier.Value);
            _stage = Stage.WorldHome;

            await SendSpatialSelectionMarkerAsync(new
            {
                spatialVolumeDepth = true,
                minTier,
                maxTier,
                referenceTier = _spatialReferenceTier,
                referenceLayer = _spatialReferenceLayer,
                layersPerTier = WorldSession.LayersPerTier
            });

            _message = minTier == maxTier
                ? $"Z volume limited to Tier {minTier}. Touch Save Area once more to name and save the 3D space."
                : $"Z volume spans Tiers {minTier}–{maxTier}. Touch Save Area once more to name and save the 3D space.";
            await InvokeAsync(StateHasChanged);
            return true;
        }

        if (_stage == Stage.WorldBuilderTier)
        {
            _stage = Stage.WorldBuilderLayer;
            _message = $"Reference Tier {_tier} selected. Choose the visible Layer you want to trace.";
            await InvokeAsync(StateHasChanged);
            return true;
        }

        _spatialReferenceTier = _tier;
        _spatialReferenceLayer = _layer;
        _spatialReferenceDepthChosen = true;
        _stage = Stage.WorldHome;
        await SyncWorldBuilderDepthAsync();

        var activated = await SendSpatialSelectionMarkerAsync(new
        {
            beginSpatialFootprint = true,
            tier = _spatialReferenceTier,
            layer = _spatialReferenceLayer
        });

        _message = activated
            ? $"Tier {_spatialReferenceTier}, Layer {_spatialReferenceLayer} is the reference slice. The 30×30 hex footprint is active now; select cells until the left display says Save Area."
            : "The depth reference is set, but the X/Y footprint selector could not be activated.";
        await InvokeAsync(StateHasChanged);
        return true;
    }

    [JSInvokable]
    public async Task<bool> BeginWorldBuilderSpatialDepthControlAsync()
    {
        if (!CanDirectEditSpatialDepth)
            return false;

        var volumePhase = _spatialReferenceDepthChosen && _spatialSelectionCount > 0;
        _spatialDefinitionActive = true;

        if (volumePhase)
        {
            _spatialZSelectionActive = true;
            _spatialZStartTier = null;
            _spatialZEndTier = null;
            _tier = Math.Clamp(_spatialReferenceTier, 0, SpatialMaxTierIndex);
            _layer = Math.Clamp(_spatialReferenceLayer, 0, SpatialMaxLayerForTier(_tier));
            _stage = Stage.WorldBuilderTier;
            _message = $"Vertical volume selection · 60° view. Start at Z Tier {_tier}; touch the left display to set the first boundary, then choose the other boundary.";
        }
        else
        {
            ClampSpatialDepth(ref _tier, ref _layer);
            _spatialReferenceDepthChosen = false;
            _spatialZSelectionActive = false;
            _spatialZStartTier = null;
            _spatialZEndTier = null;
            _stage = Stage.WorldBuilderTier;
            _message = $"Choose the reference Tier first. Hex selection is locked until Tier and Layer are both chosen.";
        }

        await InvokeAsync(StateHasChanged);
        await SyncWorldBuilderDepthAsync();
        return true;
    }

    [JSInvokable]
    public async Task EndWorldBuilderSpatialDepthControlAsync()
    {
        if (_stage is Stage.WorldBuilderTier or Stage.WorldBuilderLayer)
            _stage = Stage.WorldHome;

        _spatialReferenceDepthChosen = false;
        _spatialZSelectionActive = false;
        _spatialZStartTier = null;
        _spatialZEndTier = null;
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
            canEdit = CanDirectEditSpatialDepth,
            maxHeight = SelectedSpatialMaxHeight,
            maxTierIndex = SpatialMaxTierIndex,
            maxLayer = SpatialMaxLayerForTier(tier),
            tier,
            layer,
            referenceDepthChosen = _spatialReferenceDepthChosen,
            verticalVolume = _spatialZSelectionActive
        });
    }

    [JSInvokable]
    public async Task ReceiveWorldBuilderSpatialDepthAsync(int tier, int layer)
    {
        // Compatibility only. The embedded viewer is a representation and may
        // not write parent Tier/Layer state. Reassert the parent-owned depth so
        // an older cached viewer cannot become an independent editing authority.
        _ = tier;
        _ = layer;
        await SyncWorldBuilderDepthAsync();
    }
}
