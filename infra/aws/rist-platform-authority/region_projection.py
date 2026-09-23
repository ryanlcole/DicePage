"""Permission-bounded recursive RegionDefiner source projection.

This module reads no AWS services. A region is a view/child of selected tiles
on exactly one parent world tier; it never receives an entire parent bitmap.
"""
from decimal import Decimal
from region_geometry import region_cell_for_point


def canonical_cells(region, columns=30, rows=30):
    cells = region.get("selectedCells") or []
    result = sorted({int(i) for i in cells if isinstance(i, (int, Decimal)) and not isinstance(i, bool)
                     and 0 <= i < columns * rows})
    if not result:
        raise ValueError("Region deed has no valid source tile cells")
    return result


def project(world_id, region_id, region, world_state, child_state=None):
    state = world_state if isinstance(world_state, dict) else {}
    child = child_state if isinstance(child_state, dict) else {}
    tier = int(region.get("tierIndex") or 0)
    shape = region.get("gridShape") if region.get("gridShape") in ("square", "hex") else "square"
    columns, rows = 30, 30
    chosen = canonical_cells(region, columns, rows)
    chosen_set = set(chosen)
    parent_node_id = str(region.get("parentNodeId") or ("world:" + world_id))
    source_cells = [{
        "id": f"{world_id}:{parent_node_id}:tier:{tier}:cell:{cell}",
        "cellIndex": cell, "column": cell % columns, "row": cell // columns,
        "tierIndex": tier,
    } for cell in chosen]

    # Explicitly indexed source assets can be filtered without fetching a
    # single unclaimed full-world bitmap. Tile metadata is not the bitmap.
    indexed = [dict(tile) for tile in (state.get("sourceTileIndex") or [])
               if isinstance(tile, dict)
               and int(tile.get("tierIndex") or 0) == tier
               and int(tile.get("cellIndex") if tile.get("cellIndex") is not None else -1) in chosen_set]
    source_layers = set(int(x) for x in (region.get("sourceLayerOffsets") or list(range(10))))
    indexed = [tile for tile in indexed if int(tile.get("layerOffset") or 0) in source_layers]

    # WorldBuilder's individually authored terrain tiles are also part of the
    # source subset. Existing x/y are normalized parent-world coordinates.
    tiles = [dict(tile) for tile in (state.get("tiles") or [])
             if isinstance(tile, dict)
             and int(tile.get("tierIndex") or 0) == tier
             and int(tile.get("layerOffset") or 0) in source_layers
             and region_cell_for_point(tile.get("x", 0), tile.get("y", 0),
                                       shape, columns, rows) in chosen_set]

    # A legacy city saved into the parent map is region-owned already, not
    # parent terrain. No other world/user/region layers can leak into a child.
    legacy = [dict(item) for item in (state.get("userLayers") or [])
              if isinstance(item, dict) and str(item.get("regionId") or "") == region_id]
    for item in legacy:
        item["tier"] = int(item.get("relativeTier") or 0)
        item["relativeTier"] = item["tier"]
    child_layers = child.get("userLayers") if "userLayers" in child else legacy
    relative_tiers = child.get("relativeTiers") or [
        {"id": f"{region_id}:tier:0", "index": 0, "label": "Region Base", "sourceParentTier": tier}
    ]
    tier_images = state.get("tierImages") or []
    has_full_bitmap = bool(tier_images[tier]) if isinstance(tier_images, list) and len(tier_images) > tier else False
    return {
        "projection": "region-child-v1",
        "worldId": world_id,
        "regionId": region_id,
        "parentNodeId": parent_node_id,
        "parentTierIndex": tier,
        "gridShape": shape,
        "selectedCells": chosen,
        "sourceCells": source_cells,
        "tiles": tiles,
        "sourceTileIndex": indexed,
        "userLayers": child_layers,
        "relativeTiers": relative_tiers,
        "gridColumns": columns,
        "gridRows": rows,
        "requiresRasterIndex": has_full_bitmap and len(indexed) < len(chosen),
        "sourceBitmapWasOmitted": has_full_bitmap,
    }
