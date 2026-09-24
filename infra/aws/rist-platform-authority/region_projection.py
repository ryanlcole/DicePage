"""RegionDefiner = WorldBuilder filtered by deed coordinates.

The parent WorldBuilder tier is immutable. World layers remain integer Z 0..9.
Regional overlays use exact hundredths above a world layer:
  z100 = worldLayer * 100 + regionLayer, regionLayer in 1..9.
No independent regional tier graph exists.
"""
from decimal import Decimal
from region_geometry import region_cell_for_point

COLUMNS = 30
ROWS = 30
WORLD_LAYER_MIN = 0
WORLD_LAYER_MAX = 9
REGION_LAYER_MIN = 1
REGION_LAYER_MAX = 9


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


def region_z100(world_layer, region_layer):
    world_layer = int(world_layer)
    region_layer = int(region_layer)
    if not WORLD_LAYER_MIN <= world_layer <= WORLD_LAYER_MAX:
        raise ValueError("World Z must be between 0 and 9")
    if not REGION_LAYER_MIN <= region_layer <= REGION_LAYER_MAX:
        raise ValueError("Region layer must be between 1 and 9")
    return world_layer * 100 + region_layer


def normalize_region_layer(region, raw, region_id):
    if not isinstance(raw, dict):
        raise ValueError("Region layer must be an object")
    item = dict(raw)
    try:
        x = float(item.get("x", 0))
        y = float(item.get("y", 0))
        world_layer = int(item.get("worldLayer", item.get("layer", 0)))
        region_layer = int(item.get("regionLayer", 1))
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
    exact = region_z100(world_layer, region_layer)
    if item.get("z100") is not None and int(item.get("z100")) != exact:
        raise ValueError("Region Z does not match its world and region layers")
    item.update({
        "regionId": region_id,
        "tier": parent_tier,
        "parentTierIndex": parent_tier,
        "worldLayer": world_layer,
        "layer": world_layer,
        "regionLayer": region_layer,
        "z100": exact,
        "parallaxMode": "anchored",
        "anchorTier": parent_tier,
    })
    return item


def merge_region_layers(world_state, region, region_id, incoming):
    state = dict(world_state) if isinstance(world_state, dict) else {}
    preserved = [
        dict(item) for item in (state.get("userLayers") or [])
        if isinstance(item, dict) and str(item.get("regionId") or "") != region_id
    ]
    normalized = [normalize_region_layer(region, item, region_id) for item in incoming]
    state["userLayers"] = preserved + normalized
    return state, normalized


def project(world_id, region_id, region, world_state, region_map_state=None):
    state = world_state if isinstance(world_state, dict) else {}
    child_state = region_map_state if isinstance(region_map_state, dict) else None
    tier = int(region.get("tierIndex") or 0)
    shape = region.get("gridShape") if region.get("gridShape") in ("square", "hex") else "square"
    chosen = canonical_cells(region)
    chosen_set = set(chosen)
    parent_node_id = str(region.get("parentNodeId") or ("world:" + world_id))
    source_layers = set(int(x) for x in (region.get("sourceLayerOffsets") or range(10)))
    source_layers = {x for x in source_layers if WORLD_LAYER_MIN <= x <= WORLD_LAYER_MAX}
    if not source_layers:
        source_layers = set(range(10))

    source_cells = [{
        "id": f"{world_id}:{parent_node_id}:tier:{tier}:cell:{cell}",
        "cellIndex": cell, "column": cell % COLUMNS, "row": cell // COLUMNS,
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

    # REGIONMAP is the canonical child persistence boundary. Legacy worlds may
    # still have regional overlays embedded in WORLDSOURCE, so fall back only
    # when no REGIONMAP record exists. An existing empty REGIONMAP deliberately
    # means the region has no overlays.
    region_layer_source = (
        child_state.get("userLayers") or []
        if child_state is not None
        else state.get("userLayers") or []
    )
    region_layers = []
    for item in region_layer_source:
        if not isinstance(item, dict):
            continue
        if child_state is None and str(item.get("regionId") or "") != region_id:
            continue
        try:
            region_layers.append(normalize_region_layer(region, item, region_id))
        except (ValueError, PermissionError):
            continue

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
        "projection": "region-world-z-v2",
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
        "gridColumns": COLUMNS,
        "gridRows": ROWS,
        "zModel": {
            "worldIntegerMin": 0,
            "worldIntegerMax": 9,
            "regionHundredthMin": 1,
            "regionHundredthMax": 9,
            "storage": "z100",
        },
        "requiresRasterIndex": has_full_bitmap and len({int(x.get("cellIndex", -1)) for x in indexed}) < len(chosen) and not official,
        "publicTilePattern": tile_pattern,
        "sourceBitmapWasOmitted": has_full_bitmap,
    }
