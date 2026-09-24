from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def text(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_worldbuilder_remains_the_canonical_database_source():
    host = text("Components/WorldBuilderGeonaphHost.razor")
    prototype = text("wwwroot/prototype/prototype.js")
    bridge = text("wwwroot/worldbuilder-source-host.js")

    assert "GetWorldBuilderSourceForPrototypeAsync" in host
    assert "SaveWorldBuilderSourceFromPrototypeAsync" in host
    assert "Session.LoadWorldBuilderSourceAsync()" in host
    assert "Session.SaveWorldBuilderSourceAsync(state)" in host
    assert "worldBuilderSourceState" in prototype
    assert "tierImages:worldBuilderTierImages()" in prototype
    assert "saveWorldSourceToDatabase(state)" in prototype
    assert "GetWorldBuilderSourceForPrototypeAsync" in bridge
    assert "SaveWorldBuilderSourceFromPrototypeAsync" in bridge


def test_regiondefiner_existing_deed_requests_filtered_worldbuilder_projection():
    workspace = text("Components/RegionDefinerWorkspace.razor")
    session = text("WorldSession.RegionSource.cs")
    host = text("wwwroot/region-definer-host.js")

    assert "Session.LoadRegionSourceAsync(active.RegionId)" in workspace
    assert "GetRegionSourceForPrototypeAsync" in workspace
    assert "RegionSourceProjector.Project(" in session
    assert "region.SelectedCells" in session
    assert "region.TierIndex" in session
    assert 'GetRegionSourceForPrototypeAsync",regionId' in host
    assert 'type:"world-source"' in host


def test_claimed_region_renders_selected_source_cells_not_full_parent_bitmap():
    prototype = text("wwwroot/prototype/prototype.js")

    assert "async function renderRegionProjection(payload)" in prototype
    assert "state.projection!=='region-world-z-v2'" in prototype
    assert "stage.dataset.sourceScope='selected-parent-cells'" in prototype
    assert "plane.removeAttribute('src');" in prototype
    assert "sourceCells.flatMap" in prototype
    assert "state.sourceUserLayers" in prototype
    assert "sourceLocked:true" in prototype
    assert "stage.dataset.renderer='region-world-z-v2'" in prototype


def test_claimed_region_uses_loaded_cells_as_table_without_second_visibility_mask():
    prototype = text("wwwroot/prototype/prototype.js")
    handoff = prototype[
        prototype.index("function applyClaimedRegionCrop("):
        prototype.index("function ensureRegionTierPreview(")
    ]

    assert "clearRegionMask(false);" in handoff
    assert "stage.dataset.cropMode='selected-source-cells';" in handoff
    assert "applyRegionMask(region,'visibility-mask',true)" not in handoff
    assert "requestAnimationFrame(()=>fitClaimedRegion(region));" in handoff


def test_region_overlay_is_a_patch_to_worldbuilder_user_layers():
    app = (REPO / "infra" / "aws" / "rist-platform-authority" / "app.py").read_text(encoding="utf-8")
    projector = (REPO / "infra" / "aws" / "rist-platform-authority" / "region_projection.py").read_text(encoding="utf-8")
    session = text("WorldSession.RegionSource.cs")

    route = app[
        app.index('if method == "POST" and path == "/world/source/region":'):
        app.index('if method == "GET" and path == "/world/regions":')
    ]
    assert "merge_region_layers(state, region_state, region_id, incoming)" in route
    assert "world.update_item(" in route
    assert "region_map_key(" not in route
    assert '"region.overlay.save"' in route

    assert "preserved = [" in projector
    assert 'state["userLayers"] = preserved + normalized' in projector
    assert "SaveWorldBuilderSourceAsync(merged)" in session
    assert "region-maps/" not in session


def test_region_z_model_is_exact_integer_storage_not_floating_point_truth():
    prototype = text("wwwroot/prototype/prototype.js")
    projector = (REPO / "infra" / "aws" / "rist-platform-authority" / "region_projection.py").read_text(encoding="utf-8")

    assert "function regionZ100(worldLayer,regionLayer)" in prototype
    assert "function regionZLabel(" in prototype
    assert "z100:REGION_DEFINER?regionZ100(" in prototype
    assert "def region_z100(world_layer, region_layer):" in projector
    assert "return world_layer * 100 + region_layer" in projector
    assert '"storage": "z100"' in projector


def test_region_overlays_are_map_attached_and_do_not_create_parallax_tiers():
    prototype = text("wwwroot/prototype/prototype.js")

    assert "if(REGION_DEFINER)return'anchored';" in prototype
    assert "item.parallaxMode='anchored';" in prototype
    assert "regionRelativeTiers" not in prototype
    assert "createRegionWorkingTier" not in prototype
    assert "WORLD Z +" in prototype
    assert "REGION L +" in prototype


def test_platform_authority_exposes_filtered_region_read_and_overlay_write():
    app = (REPO / "infra" / "aws" / "rist-platform-authority" / "app.py").read_text(encoding="utf-8")
    template = (REPO / "infra" / "aws" / "rist-platform.yml").read_text(encoding="utf-8")
    client = text("AwsAuthorityClient.cs")

    assert 'method == "GET" and path == "/world/source/region"' in app
    assert 'method == "POST" and path == "/world/source/region"' in app
    assert "Path: /world/source/region, Method: GET" in template
    assert "Path: /world/source/region, Method: POST" in template
    assert "GetRegionSourceAsync" in client
    assert "SaveWorldRegionMapAsync" in client


def test_region_records_are_permission_and_coordinate_metadata_not_second_maps():
    regions = text("WorldSession.Regions.cs")
    assert "A region is authority/view metadata over the canonical world map." in regions
    assert "SourceTiles: []" in regions
    assert "var sourceTiles = PlacedTiles" not in regions


def test_region_host_suppresses_stale_load_errors():
    bridge = text("wwwroot/region-definer-host.js")
    prototype = text("wwwroot/prototype/prototype.js")

    assert "const stateRevisions=new WeakMap();" in bridge
    assert "const revision=beginStateRequest(frame);" in bridge
    assert bridge.count("if(!isCurrentStateRequest(frame,revision))return;") >= 4
    assert "stateRevisions.delete(frame);" in bridge
    assert "if(regionProjectionLoaded){" in prototype
    error_block = prototype[
        prototype.index("if(data.type==='map-load-error')"):
        prototype.index("if(data.type==='catalog-error')")
    ]
    assert "loading.hidden=true;" in error_block


def test_regiondefiner_mobile_assets_are_cache_busted_for_z100_build():
    index = text("wwwroot/prototype/index.html")
    workspace = text("Components/RegionDefinerWorkspace.razor")

    assert "./prototype.js?v=20260924-region-z100-1" in index
    assert "./prototype.css?v=20260924-region-z100-1" in index
    assert "renderer=20260924-region-z100-1" in workspace
    assert "./region-definer-host.js?v=20260924-region-z100-1" in workspace
