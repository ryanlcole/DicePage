using Microsoft.JSInterop;

namespace RistWorld.Components;

public partial class RegionDefinerWorkspace
{
    [JSInvokable]
    public object GetSpatialPathForPrototype()
    {
        return SpatialPathPayload();
    }

    [JSInvokable]
    public async Task<object> EnterSpatialNodeFromPrototypeAsync(string nodeId)
    {
        var success = Session.EnterSpatialNode(nodeId);
        if (success) await SyncSpatialPathToViewerAsync();
        return new { success, state = SpatialPathPayload() };
    }

    [JSInvokable]
    public async Task<object> ExitSpatialNodeFromPrototypeAsync()
    {
        var success = Session.ExitSpatialNode();
        await SyncSpatialPathToViewerAsync();
        return new { success, state = SpatialPathPayload() };
    }

    public async Task<bool> EnterSpatialNodeAsync(string nodeId)
    {
        var success = Session.EnterSpatialNode(nodeId);
        if (success) await SyncSpatialPathToViewerAsync();
        return success;
    }

    public async Task<bool> ExitSpatialNodeAsync()
    {
        var success = Session.ExitSpatialNode();
        await SyncSpatialPathToViewerAsync();
        return success;
    }

    async Task SyncSpatialPathToViewerAsync()
    {
        if (_module is null) return;
        var node = Session.ActiveSpatialPath.LastOrDefault();
        var scope = Session.ActiveSpatialScope;
        var tier = node?.TierIndex ?? Session.TierIndex;
        var layer = node?.VisibleLayerOffsets?.FirstOrDefault() ?? Session.LayerOffset;
        try
        {
            await _module.InvokeAsync<bool>(
                "setDepth",
                _frame,
                tier,
                layer,
                scope,
                node?.NodeId ?? "",
                Session.ActiveSpatialPathKey);
        }
        catch (JSException)
        {
            // Viewer synchronization is representation only. The canonical active
            // path remains valid even when a cached viewer has not loaded the bridge.
        }
    }

    object SpatialPathPayload()
    {
        var path = Session.ActiveSpatialPath;
        return new
        {
            worldId = Session.WorldId,
            authorityRegionId = Session.ActiveRegion?.RegionId ?? "",
            scope = Session.ActiveSpatialScope,
            activeNodeId = Session.ActiveSpatialNodeId,
            pathKey = Session.ActiveSpatialPathKey,
            path = path.Select(node => new
            {
                id = node.NodeId,
                kind = WorldSession.NormalizeRecursionTier(node.Kind),
                name = node.Name,
                parentId = node.ParentNodeId,
                tierIndex = node.TierIndex,
                visibleTierIndices = node.VisibleTierIndices ?? [],
                visibleLayerOffsets = node.VisibleLayerOffsets ?? [],
                viewAngle = node.ViewAngle,
                viewZoomRatio = node.ViewZoomRatio,
                sceneBoundary = node.SceneBoundary
            }).ToList(),
            children = Session.SpatialChildren().Select(node => new
            {
                id = node.NodeId,
                kind = WorldSession.NormalizeRecursionTier(node.Kind),
                name = node.Name,
                parentId = node.ParentNodeId,
                tierIndex = node.TierIndex,
                sceneBoundary = node.SceneBoundary
            }).ToList()
        };
    }
}
