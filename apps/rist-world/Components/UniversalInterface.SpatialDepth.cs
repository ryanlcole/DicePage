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
        if (!CanDirectEditSpatialDepth)
            return;

        ClampSpatialDepth(ref tier, ref layer);
        _tier = tier;
        _layer = layer;
        _message = $"Deed depth: Tier {_tier}, Layer {_layer}. X/Y selection remains locked to the chosen map area.";
        await InvokeAsync(StateHasChanged);
    }
}
