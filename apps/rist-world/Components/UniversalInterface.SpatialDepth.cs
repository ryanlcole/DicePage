using Microsoft.JSInterop;

namespace RistWorld.Components;

public partial class UniversalInterface
{
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

    async Task<bool> AdjustSpatialDepthSemanticAsync(int direction)
    {
        if (!IsSpatialDepthSemanticStage || !CanDirectEditSpatialDepth)
            return false;

        direction = Math.Sign(direction);
        if (direction == 0)
            return true;

        if (_stage == Stage.WorldBuilderTier)
        {
            _tier = Math.Clamp(_tier + direction, 0, SpatialMaxTierIndex);
            _layer = Math.Clamp(_layer, 0, SpatialMaxLayerForTier(_tier));
            _message = $"Tier {_tier}. Deed Layer {_layer} remains within this tier.";
        }
        else
        {
            _layer = Math.Clamp(_layer + direction, 0, SpatialMaxLayerForTier(_tier));
            _message = $"Layer {_layer} on Tier {_tier}.";
        }

        await SyncWorldBuilderDepthAsync();
        await InvokeAsync(StateHasChanged);
        return true;
    }

    async Task<bool> AdvanceSpatialDepthSemanticAsync()
    {
        if (!IsSpatialDepthSemanticStage || !CanDirectEditSpatialDepth)
            return false;

        if (_stage == Stage.WorldBuilderTier)
        {
            _stage = Stage.WorldBuilderLayer;
            _message = $"Tier {_tier} selected. Choose Layer on the same left display.";
        }
        else
        {
            _stage = Stage.WorldHome;
            _message = $"Deed depth set to Tier {_tier}, Layer {_layer}. Select the X/Y hexes, then use Save Area on the left display.";
        }

        await SyncWorldBuilderDepthAsync();
        await InvokeAsync(StateHasChanged);
        return true;
    }

    [JSInvokable]
    public async Task<bool> BeginWorldBuilderSpatialDepthControlAsync()
    {
        if (!CanDirectEditSpatialDepth)
            return false;

        ClampSpatialDepth(ref _tier, ref _layer);
        _spatialDefinitionActive = true;
        _stage = Stage.WorldBuilderTier;
        _message = $"Deed depth · Tier {_tier}. The parent semantic left display is authoritative; X/Y selection remains frozen to the visible map.";

        // Render the authoritative Tier state first, then push that exact value
        // into the embedded representation. This prevents Select Area from
        // briefly retaining the previously visible top parallax tier while the
        // left semantic display has already moved to Tier 0.
        await InvokeAsync(StateHasChanged);
        await SyncWorldBuilderDepthAsync();
        return true;
    }

    [JSInvokable]
    public async Task EndWorldBuilderSpatialDepthControlAsync()
    {
        if (_stage is Stage.WorldBuilderTier or Stage.WorldBuilderLayer)
            _stage = Stage.WorldHome;

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
            layer
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
