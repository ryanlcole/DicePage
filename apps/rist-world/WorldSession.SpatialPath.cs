namespace RistWorld;

public sealed partial class WorldSession
{
    // The active path is navigation state over canonical spatial identity. It does
    // not crop, copy, transform, or otherwise rewrite World/Region map truth.
    public IReadOnlyList<WorldSpatialNode> ActiveSpatialPath
    {
        get
        {
            if (ActiveRegion is null) return [];
            var nodes = ActiveRegion.SpatialNodes ?? [];
            var result = new List<WorldSpatialNode>();
            var visited = new HashSet<string>(StringComparer.Ordinal);

            void Append(string? nodeId)
            {
                if (string.IsNullOrWhiteSpace(nodeId) || !visited.Add(nodeId)) return;
                var node = nodes.FirstOrDefault(item => string.Equals(item.NodeId, nodeId, StringComparison.Ordinal));
                if (node is null) return;
                if (!string.Equals(node.ParentNodeId, ActiveRegion.RegionId, StringComparison.Ordinal))
                    Append(node.ParentNodeId);
                result.Add(node);
            }

            Append(ActiveInstance?.NodeId ?? ActiveLocal?.NodeId ?? ActiveSpatialRegion?.NodeId);
            return result;
        }
    }

    public string ActiveSpatialScope => ActiveInstance is not null ? "INSTANCE"
        : ActiveLocal is not null ? "LOCAL"
        : ActiveSpatialRegion is not null ? "REGION"
        : "WORLD";

    public string ActiveSpatialNodeId => ActiveSpatialPath.LastOrDefault()?.NodeId ?? "";

    public string ActiveSpatialPathKey => ActiveRegion is null
        ? "WORLD"
        : string.Join("/", new[] { ActiveRegion.RegionId }.Concat(ActiveSpatialPath.Select(node => node.NodeId)));

    public IReadOnlyList<WorldSpatialNode> SpatialChildren(string? parentNodeId = null)
    {
        if (ActiveRegion is null) return [];
        var parent = string.IsNullOrWhiteSpace(parentNodeId)
            ? ActiveSpatialNodeId
            : parentNodeId.Trim();
        if (string.IsNullOrWhiteSpace(parent)) parent = ActiveRegion.RegionId;
        return (ActiveRegion.SpatialNodes ?? [])
            .Where(node => string.Equals(node.ParentNodeId, parent, StringComparison.Ordinal))
            .OrderBy(node => SpatialScopeRank(node.Kind))
            .ThenBy(node => node.Name, StringComparer.OrdinalIgnoreCase)
            .ToList();
    }

    public bool EnterSpatialNode(string nodeId)
    {
        if (ActiveRegion is null || string.IsNullOrWhiteSpace(nodeId)) return false;
        var nodes = ActiveRegion.SpatialNodes ?? [];
        var node = nodes.FirstOrDefault(item => string.Equals(item.NodeId, nodeId, StringComparison.Ordinal));
        if (node is null) return false;

        // Reconstruct lineage from the selected identity so going down or jumping
        // to a saved child restores its authored parent representation.
        var lineage = new List<WorldSpatialNode>();
        var cursor = node;
        var visited = new HashSet<string>(StringComparer.Ordinal);
        while (cursor is not null && visited.Add(cursor.NodeId))
        {
            lineage.Add(cursor);
            if (string.Equals(cursor.ParentNodeId, ActiveRegion.RegionId, StringComparison.Ordinal)) break;
            cursor = nodes.FirstOrDefault(item => string.Equals(item.NodeId, cursor.ParentNodeId, StringComparison.Ordinal));
        }
        lineage.Reverse();

        _activeSpatialRegionId = lineage.LastOrDefault(item => string.Equals(item.Kind, "REGION", StringComparison.OrdinalIgnoreCase))?.NodeId ?? "";
        _activeLocalId = lineage.LastOrDefault(item => string.Equals(item.Kind, "LOCAL", StringComparison.OrdinalIgnoreCase))?.NodeId ?? "";
        _activeInstanceId = lineage.LastOrDefault(item => string.Equals(item.Kind, "INSTANCE", StringComparison.OrdinalIgnoreCase))?.NodeId ?? "";
        SetViewportTier(NormalizeRecursionTier(node.Kind));
        Notify();
        return true;
    }

    public bool ExitSpatialNode()
    {
        if (ActiveRegion is null) return false;
        var path = ActiveSpatialPath;
        if (path.Count == 0)
        {
            SetViewportTier("WORLD");
            return false;
        }

        var parentId = path[^1].ParentNodeId;
        if (string.Equals(parentId, ActiveRegion.RegionId, StringComparison.Ordinal))
        {
            ClearSpatialSelection();
            SetViewportTier("WORLD");
            Notify();
            return true;
        }
        return EnterSpatialNode(parentId);
    }

    public void RestoreSpatialRepresentation()
    {
        var node = ActiveSpatialPath.LastOrDefault();
        if (node is null)
        {
            SetViewportTier("WORLD");
            return;
        }
        SetViewportTier(NormalizeRecursionTier(node.Kind));
        SetSceneTier(Math.Max(0, node.TierIndex));
        var layer = node.VisibleLayerOffsets?.FirstOrDefault() ?? 0;
        SetLayerOffset(Math.Clamp(layer, 0, LayersPerTier - 1));
    }

    static int SpatialScopeRank(string? kind) => NormalizeRecursionTier(kind) switch
    {
        "REGION" => 1,
        "LOCAL" => 2,
        "INSTANCE" => 3,
        _ => 0
    };
}
