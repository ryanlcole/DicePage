namespace RistWorld;

/// <summary>
/// Compatibility bridge between the new recursive WORLD authoring contract and
/// the legacy TileItem topology. New Worldbuilder placements enter here. Legacy
/// placements are never silently promoted: they remain on the old address model
/// until a deliberate migration or an explicitly canonical creation path.
/// </summary>
public sealed partial class WorldSession
{
    const string WorldEditorScopeKind = "WORLD";

    public bool HasRecursiveWorldPlacement(TileItem tile) =>
        !string.IsNullOrWhiteSpace(tile.PlacementId) &&
        FindRecursiveScopePlacement(WorldEditorScopeKind, WorldId, tile.PlacementId) is not null;

    public RecursiveScopePlacement? RecursiveWorldPlacement(TileItem tile) =>
        string.IsNullOrWhiteSpace(tile.PlacementId)
            ? null
            : FindRecursiveScopePlacement(WorldEditorScopeKind, WorldId, tile.PlacementId);

    public RecursiveScopePlacement? RegisterNewWorldTilePlacement(int tileIndex, bool forceFront = false)
    {
        if (!HasActiveWorld || tileIndex < 0 || tileIndex >= PlacedTiles.Count)
            return null;

        var originalTile = PlacedTiles[tileIndex];
        var tile = NormalizePlacedTileIdentity(originalTile);
        if (tile != originalTile)
            PlacedTiles[tileIndex] = tile;

        var existing = RecursiveWorldPlacement(tile);
        if (existing is not null)
            return existing;

        var tier = NormalizeScopeTier(tile.TierIndex + 1);
        var scopePlacements = RecursivePlacementsForScope(WorldEditorScopeKind, WorldId);
        var overlapping = scopePlacements
            .Where(item => item.Visible && item.Tier == tier)
            .Select(item => new
            {
                Placement = item,
                Tile = PlacedTiles.FirstOrDefault(candidate =>
                    string.Equals(candidate.PlacementId, item.AssetId, StringComparison.Ordinal))
            })
            .Where(pair => pair.Tile is not null && TilesOverlap(tile, pair.Tile))
            .Select(pair => pair.Placement)
            .ToList();

        var layer = overlapping.Count > 0
            ? overlapping.Max(item => item.Layer) + 1
            : forceFront
                ? NextVisualLayer(scopePlacements, tier)
                : 1;

        var placement = NewRecursiveScopePlacement(
            tile.PlacementId,
            WorldEditorScopeKind,
            WorldId) with
        {
            X = tile.X,
            Y = tile.Y,
            Tier = tier,
            Layer = NormalizeScopeLayer(layer),
            Locked = false,
            Visible = true,
            Opacity = 1,
            LinkedGroupId = tile.GroupId ?? "",
            PermissionResourceId = RecursivePermissionResourceId(tile.PlacementId)
        };

        UpsertRecursiveScopePlacement(placement);
        return placement.Normalize();
    }

    public RecursiveScopePlacement? SyncRecursiveWorldTile(string placementId, bool bringForward = false)
    {
        if (!HasActiveWorld || string.IsNullOrWhiteSpace(placementId))
            return null;

        var index = PlacedTiles.FindIndex(tile =>
            string.Equals(tile.PlacementId, placementId, StringComparison.Ordinal));
        if (index < 0) return null;

        var tile = PlacedTiles[index];
        var current = RecursiveWorldPlacement(tile);
        if (current is null)
            return null; // Never silently migrate legacy content.

        var tier = NormalizeScopeTier(tile.TierIndex + 1);
        var layer = current.Layer;
        if (bringForward)
        {
            var peers = RecursivePlacementsForScope(WorldEditorScopeKind, WorldId)
                .Where(item => !string.Equals(item.AssetId, placementId, StringComparison.Ordinal));
            layer = NextVisualLayer(peers, tier);
        }

        var next = current with
        {
            X = tile.X,
            Y = tile.Y,
            Tier = tier,
            Layer = layer,
            LinkedGroupId = tile.GroupId ?? current.LinkedGroupId
        };
        UpsertRecursiveScopePlacement(next);
        return next.Normalize();
    }

    public IReadOnlyList<TileItem> GetRecursiveWorldRenderTiles()
    {
        if (!HasActiveWorld) return PlacedTiles;

        var placements = RecursivePlacementsForScope(WorldEditorScopeKind, WorldId)
            .ToDictionary(item => item.AssetId, item => item, StringComparer.Ordinal);

        return PlacedTiles
            .Select((tile, index) => new
            {
                Tile = tile,
                Index = index,
                Placement = !string.IsNullOrWhiteSpace(tile.PlacementId) &&
                            placements.TryGetValue(tile.PlacementId, out var placement)
                    ? placement
                    : null
            })
            .Where(item => item.Placement?.Visible != false)
            // Visual Layer is the sole compositing authority. Tier is deliberately
            // absent from this ordering so depth cannot silently change draw order.
            .OrderBy(item => item.Placement?.Layer ?? 1)
            .ThenBy(item => item.Index)
            .Select(item => item.Tile)
            .ToList();
    }

    public double RecursiveWorldTileOpacity(TileItem tile) =>
        RecursiveWorldPlacement(tile)?.Opacity ?? 1;

    public bool RecursiveWorldTileLocked(TileItem tile) =>
        RecursiveWorldPlacement(tile)?.Locked ?? false;

    public bool SetRecursiveWorldTileLayer(string placementId, int layer) =>
        SetRecursivePlacementLayer(WorldEditorScopeKind, WorldId, placementId, layer);

    public bool SetRecursiveWorldTileOpacity(string placementId, double opacity) =>
        SetRecursivePlacementOpacity(WorldEditorScopeKind, WorldId, placementId, opacity);

    public bool SetRecursiveWorldTileVisible(string placementId, bool visible) =>
        SetRecursivePlacementVisible(WorldEditorScopeKind, WorldId, placementId, visible);

    public bool SetRecursiveWorldTileLocked(string placementId, bool locked) =>
        SetRecursivePlacementLocked(WorldEditorScopeKind, WorldId, placementId, locked);

    public bool SetRecursiveWorldTileLinkedGroup(string placementId, string linkedGroupId) =>
        SetRecursivePlacementLinkedGroup(WorldEditorScopeKind, WorldId, placementId, linkedGroupId);

    public bool SetRecursiveWorldTilePermissionResource(string placementId, string permissionResourceId) =>
        SetRecursivePlacementPermissionResource(WorldEditorScopeKind, WorldId, placementId, permissionResourceId);

    public bool SetRecursiveWorldTileTier(string placementId, int tier)
    {
        if (!HasActiveWorld || string.IsNullOrWhiteSpace(placementId))
            return false;

        var current = FindRecursiveScopePlacement(WorldEditorScopeKind, WorldId, placementId);
        if (current is null) return false;

        var canonicalTier = NormalizeScopeTier(tier);
        if (!IsLoggedIn)
            canonicalTier = Math.Clamp(canonicalTier, 1, GuestTierCount);

        var index = PlacedTiles.FindIndex(tile =>
            string.Equals(tile.PlacementId, placementId, StringComparison.Ordinal));
        if (index < 0) return false;

        var tile = PlacedTiles[index];
        var nextTile = tile with
        {
            // Compatibility projection only. New recursive Layer never enters
            // legacy LayerOffset; LayerOffset stays zero for canonical content.
            TierIndex = canonicalTier - 1,
            LayerOffset = 0
        };

        if (tile != nextTile)
        {
            // Relocate by stable placement identity directly in the legacy
            // storage adapter. This is independent of CompositeZView so a
            // canonical Tier edit cannot be flattened back onto the current
            // legacy page by StoreCurrentSpatialPage().
            StoreCurrentSpatialPage();
            foreach (var address in _terrainByAddress.Keys.ToList())
            {
                var page = _terrainByAddress[address];
                page.RemoveAll(candidate =>
                    string.Equals(candidate.PlacementId, placementId, StringComparison.Ordinal));
                if (page.Count == 0)
                    _terrainByAddress.Remove(address);
            }

            var target = new SpatialAddress(
                nextTile.CubeX,
                nextTile.CubeY,
                nextTile.CubeZ,
                nextTile.PlaneIndex,
                nextTile.TierIndex,
                0);
            if (!_terrainByAddress.TryGetValue(target, out var targetPage))
            {
                targetPage = [];
                _terrainByAddress[target] = targetPage;
            }
            targetPage.Add(nextTile);
            LoadCurrentSpatialPage();
        }

        return SetRecursivePlacementTier(WorldEditorScopeKind, WorldId, placementId, canonicalTier);
    }

    public bool RemoveRecursiveWorldPlacement(TileItem tile)
    {
        if (string.IsNullOrWhiteSpace(tile.PlacementId))
            return false;
        return RemoveRecursiveScopePlacement(WorldEditorScopeKind, WorldId, tile.PlacementId);
    }
}
