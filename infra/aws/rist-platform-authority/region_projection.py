"""RegionDefiner recursive scope projection.

The claimed deed is the REGION scope boundary. RIST_RECURSIVE_SCOPE_V1 owns
Region-local x/y, visual Layer, and parallax Tier at a fixed 15° representation.

Legacy worldLayer/regionLayer/z100 fields remain beside the recursive envelope
only as a compatibility projection for the current prototype during migration.
They are not the new Region spatial authority.
"""
from decimal import Decimal
from region_geometry import region_cell_for_point

COLUMNS = 30
ROWS = 30
WORLD_LAYER_MIN = 0
WORLD_LAYER_MAX = 9
LEGACY_REGION_LAYER_MIN = 1
LEGACY_REGION_LAYER_MAX = 9
RECURSIVE_SCOPE_FORMAT = "RIST_RECURSIVE_SCOPE_V1"


def canonical_cells(region, columns=COLUMNS, rows=ROWS):
    cells = region.get("selectedCells") or []
    result = sorted({
        int(i) for i in cells
        if isinstance(i, (int, Decimal)) and not isinstance(i, bool)
        and 0 <= int(i) < columns * rows
    })
    if not result:
        raise ValueError("Region deed has no valid source tile cells")
    return result


def region_frame(region):
    cells = canonical_cells(region)
    min_column = min(cell % COLUMNS for cell in cells)
    max_column = max(cell % COLUMNS for cell in cells)
    min_row = min(cell // COLUMNS for cell in cells)
    max_row = max(cell // COLUMNS for cell in cells)
    return {
        "left": min_column / COLUMNS,
        "top": min_row / ROWS,
        "right": (max_column + 1) / COLUMNS,
        "bottom": (max_row + 1) / ROWS,
    }


def local_point(world_x, world_y, frame):
    width = max(1 / COLUMNS, frame["right"] - frame["left"])
    height = max(1 / ROWS, frame["bottom"] - frame["top"])
    return (
        max(0.0, min(1.0, (world_x - frame["left"]) / width)),
        max(0.0, min(1.0, (world_y - frame["top"]) / height)),
    )


def world_point(local_x, local_y, frame):
    width = max(1 / COLUMNS, frame["right"] - frame["left"])
    height = max(1 / ROWS, frame["bottom"] - frame["top"])
    return (
        frame["left"] + max(0.0, min(1.0, local_x)) * width,
        frame["top"] + max(0.0, min(1.0, local_y)) * height,
    )


def recursive_permission_resource_id(asset_id):
    identity = str(asset_id or "").strip()
    if not identity:
        return ""
    return identity if identity.startswith("asset:") else "asset:" + identity


def region_z100(world_layer, region_layer):
    """Legacy compatibility address only."""
    world_layer = int(world_layer)
    region_layer = int(region_layer)
    if not WORLD_LAYER_MIN <= world_layer <= WORLD_LAYER_MAX:
        raise ValueError("World Z must be between 0 and 9")
    if not LEGACY_REGION_LAYER_MIN <= region_layer <= LEGACY_REGION_LAYER_MAX:
        raise ValueError("Legacy Region layer must be between 1 and 9")
    return world_layer * 100 + region_layer


def normalize_region_layer(region, raw, region_id, world_id="", parent_node_id=""):
    if not isinstance(raw, dict):
        raise ValueError("Region layer must be an object")

    item = dict(raw)
    recursive = item.get("recursive")
    has_recursive = (
        isinstance(recursive, dict)
        and str(recursive.get("format") or "") == RECURSIVE_SCOPE_FORMAT
        and str(recursive.get("scopeKind") or "").upper() == "REGION"
        and str(recursive.get("scopeId") or "") == region_id
    )

    frame = region_frame(region)
    try:
        if has_recursive:
            local_x = max(0.0, min(1.0, float(recursive.get("x", 0))))
            local_y = max(0.0, min(1.0, float(recursive.get("y", 0))))
            x, y = world_point(local_x, local_y, frame)
        else:
            x = float(item.get("x", -1))
            y = float(item.get("y", -1))
            local_x, local_y = local_point(x, y, frame)

        world_layer = int(item.get("worldLayer", item.get("layer", 0)))
        legacy_region_layer = int(item.get("regionLayer", 1))
    except (TypeError, ValueError):
        raise ValueError("Region layer address is invalid")

    if not (0 <= x <= 1 and 0 <= y <= 1):
        raise ValueError("Region layer is outside the world map")
    if item.get("fullWorld") or item.get("placementRole") == "world-map":
        raise PermissionError("Region overlays cannot replace the parent world map")

    selected = set(canonical_cells(region))
    shape = region.get("gridShape") if region.get("gridShape") in ("square", "hex") else "square"
    cell = region_cell_for_point(x, y, shape, COLUMNS, ROWS)
    if cell not in selected:
        raise PermissionError("Region overlay is outside the claimed coordinates")

    parent_tier = int(region.get("tierIndex") or 0)
    if "tier" in item and int(item.get("tier") or 0) != parent_tier:
        raise PermissionError("Region overlay must remain on the claimed WorldBuilder tier")

    if not WORLD_LAYER_MIN <= world_layer <= WORLD_LAYER_MAX:
        raise ValueError("World Z must be between 0 and 9")
    if not LEGACY_REGION_LAYER_MIN <= legacy_region_layer <= LEGACY_REGION_LAYER_MAX:
        raise ValueError("Legacy Region layer must be between 1 and 9")

    if has_recursive:
        try:
            recursive_tier = max(1, int(recursive.get("tier", 1)))
            recursive_layer = max(1, int(recursive.get("layer", legacy_region_layer)))
            opacity = max(0.0, min(1.0, float(recursive.get("opacity", 1))))
        except (TypeError, ValueError):
            raise ValueError("Recursive Region address is invalid")
    else:
        recursive_tier = 1
        recursive_layer = max(1, legacy_region_layer)
        opacity = 1.0

    compatibility_region_layer = max(
        LEGACY_REGION_LAYER_MIN,
        min(LEGACY_REGION_LAYER_MAX, recursive_layer),
    )
    exact = region_z100(world_layer, compatibility_region_layer)

    # Old saves can still prove their old z100 truth. Once a canonical recursive
    # envelope exists, recursive Tier/Layer no longer need to equal the legacy
    # compatibility address.
    if not has_recursive and item.get("z100") is not None:
        try:
            supplied = int(item.get("z100"))
        except (TypeError, ValueError):
            raise ValueError("Legacy Region Z is invalid")
        if supplied != region_z100(world_layer, legacy_region_layer):
            raise ValueError("Legacy Region Z does not match its world and region layers")

    asset_id = str(item.get("id") or "").strip()
    linked_group_id = (
        str(recursive.get("linkedGroupId") or "").strip()
        if has_recursive
        else str(item.get("groupId") or "").strip()
    )
    permission_resource_id = (
        str(recursive.get("permissionResourceId") or "").strip()
        if has_recursive
        else ""
    )
    if not permission_resource_id and asset_id:
        permission_resource_id = recursive_permission_resource_id(asset_id)

    item.update({
        "worldId": world_id or str(item.get("worldId") or ""),
        "regionId": region_id,
        "parentNodeId": parent_node_id or str(item.get("parentNodeId") or ""),
        "tier": parent_tier,
        "parentTierIndex": parent_tier,
        "x": x,
        "y": y,
        "worldLayer": world_layer,
        "layer": world_layer,
        "regionLayer": compatibility_region_layer,
        "z100": exact,
        "parallaxMode": "recursive-region",
        "anchorTier": parent_tier,
        "recursive": {
            "format": RECURSIVE_SCOPE_FORMAT,
            "assetId": asset_id,
            "scopeKind": "REGION",
            "scopeId": region_id,
            "parentScopeId": world_id or str(item.get("worldId") or ""),
            "parentAssetId": parent_node_id or str(item.get("parentNodeId") or ""),
            "x": local_x,
            "y": local_y,
            "tier": recursive_tier,
            "layer": recursive_layer,
            "viewDegrees": 15,
            "opacity": opacity,
            "visible": bool(recursive.get("visible", True)) if has_recursive else True,
            "locked": bool(recursive.get("locked", False)) if has_recursive else False,
            "linkedGroupId": linked_group_id,
            "permissionResourceId": recursive_permission_resource_id(permission_resource_id),
        },
    })
    return item


def merge_region_layers(world_state, region, region_id, incoming, world_id="", parent_node_id=""):
    state = dict(world_state) if isinstance(world_state, dict) else {}
    world_id = str(world_id or state.get("worldId") or region.get("worldId") or "")
    parent_node_id = str(
        parent_node_id
        or region.get("parentNodeId")
        or (("world:" + world_id) if world_id else "")
    )
    preserved = [
        dict(item) for item in (state.get("userLayers") or [])
        if isinstance(item, dict) and str(item.get("regionId") or "") != region_id
    ]
    normalized = [
        normalize_region_layer(region, item, region_id, world_id, parent_node_id)
        for item in incoming
    ]
    state["userLayers"] = preserved + normalized
    return state, normalized


def project(world_id, region_id, region, world_state, region_map_state=None):
    state = world_state if isinstance(world_state, dict) else {}
    child_state = region_map_state if isinstance(region_map_state, dict) else None
    tier = int(region.get("tierIndex") or 0)
    shape = region.get("gridShape") if region.get("gridShape") in ("square", "hex") else "square"
    chosen = canonical_cells(region)
    chosen_set = set(chosen)
    frame = region_frame(region)
    parent_node_id = str(region.get("parentNodeId") or ("world:" + world_id))
    source_layers = set(int(x) for x in (region.get("sourceLayerOffsets") or range(10)))
    source_layers = {x for x in source_layers if WORLD_LAYER_MIN <= x <= WORLD_LAYER_MAX}
    if not source_layers:
        source_layers = set(range(10))

    source_cells = [{
        "id": f"{world_id}:{parent_node_id}:tier:{tier}:cell:{cell}",
        "cellIndex": cell,
        "column": cell % COLUMNS,
        "row": cell // COLUMNS,
        "tierIndex": tier,
    } for cell in chosen]

    indexed = [
        dict(tile) for tile in (state.get("sourceTileIndex") or [])
        if isinstance(tile, dict)
        and int(tile.get("tierIndex") or 0) == tier
        and int(tile.get("layerOffset") if tile.get("layerOffset") is not None else 0) in source_layers
        and int(tile.get("cellIndex") if tile.get("cellIndex") is not None else -1) in chosen_set
    ]

    tiles = [
        dict(tile) for tile in (state.get("tiles") or [])
        if isinstance(tile, dict)
        and int(tile.get("tierIndex") or 0) == tier
        and int(tile.get("layerOffset") or 0) in source_layers
        and region_cell_for_point(tile.get("x", 0), tile.get("y", 0), shape, COLUMNS, ROWS) in chosen_set
    ]

    source_user_layers = [
        dict(item) for item in (state.get("userLayers") or [])
        if isinstance(item, dict)
        and not str(item.get("regionId") or "")
        and int(item.get("tier") or 0) == tier
        and int(item.get("layer") or 0) in source_layers
        and region_cell_for_point(item.get("x", 0), item.get("y", 0), shape, COLUMNS, ROWS) in chosen_set
    ]

    legacy_region_layers = [
        dict(item) for item in (state.get("userLayers") or [])
        if isinstance(item, dict)
        and str(item.get("regionId") or "") == region_id
    ]
    child_region_layers = (
        [dict(item) for item in (child_state.get("userLayers") or []) if isinstance(item, dict)]
        if child_state is not None
        else []
    )
    legacy_import_complete = bool(
        child_state is not None and child_state.get("legacyImportComplete") is True
    )

    if child_state is None:
        region_layer_source = legacy_region_layers
        legacy_region_import_pending = False
    elif legacy_import_complete:
        region_layer_source = child_region_layers
        legacy_region_import_pending = False
    else:
        child_ids = {
            str(item.get("id") or "").strip()
            for item in child_region_layers
            if str(item.get("id") or "").strip()
        }
        merged_legacy = [
            item for item in legacy_region_layers
            if not str(item.get("id") or "").strip()
            or str(item.get("id") or "").strip() not in child_ids
        ]
        region_layer_source = child_region_layers + merged_legacy
        legacy_region_import_pending = bool(merged_legacy)

    region_layers = []
    seen_ids = set()
    for item in region_layer_source:
        if not isinstance(item, dict):
            continue
        try:
            normalized = normalize_region_layer(
                region, item, region_id, world_id, parent_node_id
            )
        except (ValueError, PermissionError):
            continue
        item_id = str(normalized.get("id") or "").strip()
        if item_id and item_id in seen_ids:
            continue
        if item_id:
            seen_ids.add(item_id)
        region_layers.append(normalized)

    tier_images = state.get("tierImages") or []
    has_full_bitmap = bool(tier_images[tier]) if isinstance(tier_images, list) and len(tier_images) > tier else False
    official_files = (
        "geonaph_full_static_canonical_surface_v001",
        "geonaph_full_static_highlands_rivers_v001",
        "geonaph_full_static_mountain_volcanic_archipelago_v001",
    )
    full_source = str(tier_images[tier] or "") if has_full_bitmap else ""
    official = (
        world_id == "shaelvien-geonaph-alpha-001"
        and 0 <= tier < len(official_files)
        and (not has_full_bitmap or official_files[tier] in full_source)
    )
    tile_pattern = (
        f"/Game/prototype/region-cells/geonaph/{{shape}}/{tier}/{{cell}}.webp"
        if official else None
    )

    return {
        "projection": "region-recursive-scope-v1",
        "legacyProjection": "region-world-z-v2",
        "recursiveScopeFormat": RECURSIVE_SCOPE_FORMAT,
        "recursiveScope": {
            "kind": "REGION",
            "scopeId": region_id,
            "parentScopeId": world_id,
            "parentAssetId": parent_node_id,
            "viewDegrees": 15,
            "origin": "claimed-region",
            "coordinateFrame": frame,
        },
        "worldId": world_id,
        "regionId": region_id,
        "parentNodeId": parent_node_id,
        "parentTierIndex": tier,
        "sourcePixelWidth": int(state.get("sourcePixelWidth") or 2508),
        "sourcePixelHeight": int(state.get("sourcePixelHeight") or 2508),
        "sourceLayerOffsets": sorted(source_layers),
        "gridShape": shape,
        "selectedCells": chosen,
        "sourceCells": source_cells,
        "tiles": tiles,
        "sourceTileIndex": indexed,
        "sourceUserLayers": source_user_layers,
        "userLayers": region_layers,
        "legacyRegionImportPending": legacy_region_import_pending,
        "gridColumns": COLUMNS,
        "gridRows": ROWS,
        "zModel": {
            "status": "legacy-compatibility-only",
            "worldIntegerMin": 0,
            "worldIntegerMax": 9,
            "regionHundredthMin": 1,
            "regionHundredthMax": 9,
            "storage": "z100",
        },
        "requiresRasterIndex": has_full_bitmap and len({
            int(x.get("cellIndex", -1)) for x in indexed
        }) < len(chosen) and not official,
        "publicTilePattern": tile_pattern,
        "sourceBitmapWasOmitted": has_full_bitmap,
    }
