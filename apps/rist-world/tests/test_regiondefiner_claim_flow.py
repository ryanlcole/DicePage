from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def text(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def authority_text():
    return (REPO / "infra" / "aws" / "rist-platform-authority" / "app.py").read_text(encoding="utf-8")


def projector_text():
    return (REPO / "infra" / "aws" / "rist-platform-authority" / "region_projection.py").read_text(encoding="utf-8")


def test_region_gate_exposes_new_or_claim_from_trusted_database_authority():
    gate = text("Components/RegionGate.razor")
    assert "Session.HasTrustedWorldBuilderAuthority" in gate
    assert "Session.CanRequestWorldClaim" in gate
    assert "CLAIM REGION" in gate
    assert "LoadPendingWorldClaimRequestsAsync" in gate
    assert "LoadMyWorldClaimRequestsAsync" in gate
    assert "DecideWorldClaimRequestAsync" in gate


def test_regiondefiner_reuses_worldbuilder_source_and_exact_saved_deed_coordinates():
    workspace = text("Components/RegionDefinerWorkspace.razor")
    session = text("WorldSession.RegionSource.cs")
    assert 'source="database"' in workspace
    assert "GetRegionSourceForPrototypeAsync" in workspace
    assert "Session.LoadRegionSourceAsync(regionId)" in workspace
    assert "Session.CanEditRegion(activeRegion)" in workspace
    assert "RegionSourceProjector.Project(" in session
    assert "parentState" in session
    assert "region.SelectedCells" in session
    assert "region.TierIndex" in session


def test_new_region_selects_actual_world_cells_before_claiming():
    prototype = text("wwwroot/prototype/prototype.js")
    regions = text("WorldSession.Regions.cs")
    contract = text("REGION_DEFINER_CONTRACT.md")

    assert "ensureRegionTierPreview" in prototype
    assert "const regionSelectedCells=new Set();" in prototype
    assert "let regionGridShape='hex'" in prototype
    assert "overlay.className='region-definition-grid hex'" in prototype
    assert "regionCellFromPoint" in prototype
    assert "!regionSelectedCells.size" in prototype
    assert "Name the region before claiming the deed." in prototype
    assert "CLAIM DEED" in prototype
    assert 'if (cells.Count == 0) throw new InvalidOperationException("Select at least one world tile for the region.");' in regions
    assert "WorldBuilder source cells" in contract


def test_completed_deed_removes_claim_grid_and_uses_filtered_source_as_table():
    prototype = text("wwwroot/prototype/prototype.js")
    styles = text("wwwroot/prototype/prototype.css")
    handoff = prototype[
        prototype.index("function applyClaimedRegionCrop("):
        prototype.index("function ensureRegionTierPreview(")
    ]

    assert "retireRegionSelectionOverlay();" in handoff
    assert "clearRegionMask(false);" in handoff
    assert "stage.dataset.cropMode='selected-source-cells';" in handoff
    assert "applyRegionMask(region,'visibility-mask',true)" not in handoff
    assert ".stage.region-cropped .region-definition-grid{display:none!important;" in styles
    assert "regionSelectionOverlay.remove();" in prototype


def test_region_depth_is_world_integer_z_plus_region_hundredths_only():
    prototype = text("wwwroot/prototype/prototype.js")
    projector = projector_text()

    assert "function regionZ100(worldLayer,regionLayer)" in prototype
    assert "*100+clamp(Math.trunc(Number(regionLayer)||1),1,9)" in prototype
    assert "let regionProjectionLoaded=false,regionRasterIndexMissing=false,regionLayerIndex=1;" in prototype
    assert "function createRegionWorkingTier()" not in prototype
    assert "regionRelativeTiers" not in prototype
    assert "regionRelativeTierIndex" not in prototype
    assert "REGION L +" in prototype
    assert "WORLD Z +" in prototype

    assert "def region_z100(world_layer, region_layer):" in projector
    assert "return world_layer * 100 + region_layer" in projector
    assert 'item["parallaxMode"] = "anchored"' not in projector  # update() form is canonical
    assert '"parallaxMode": "anchored"' in projector
    assert '"regionLayer": region_layer' in projector
    assert '"z100": exact' in projector
    assert "relativeTiers" not in projector


def test_region_overlay_remains_on_selected_world_tier_and_has_no_independent_parallax():
    prototype = text("wwwroot/prototype/prototype.js")
    projector = projector_text()

    assert "item.tier=parentTier;" in prototype
    assert "item.parallaxMode='anchored';" in prototype
    assert "if(REGION_DEFINER)return'anchored';" in prototype
    assert "Regional overlay must remain on the claimed WorldBuilder tier" in projector
    assert '"anchorTier": parent_tier' in projector


def test_region_save_patches_worldbuilder_source_instead_of_creating_region_map_truth():
    app = authority_text()
    session = text("WorldSession.RegionSource.cs")
    route = app[
        app.index('if method == "POST" and path == "/world/source/region":'):
        app.index('if method == "GET" and path == "/world/regions":')
    ]

    assert "merge_region_layers(state, region_state, region_id, incoming)" in route
    assert "world.update_item(" in route
    assert "Key=key" in route
    assert "region_map_key(" not in route
    assert '"region.overlay.save"' in route
    assert "SaveWorldBuilderSourceAsync(merged)" in session
    assert "region-maps/" not in session


def test_filtered_region_projection_returns_only_selected_worldbuilder_scope():
    projector = projector_text()
    viewer = text("wwwroot/prototype/prototype.js")

    assert '"projection": "region-world-z-v2"' in projector
    assert '"sourceUserLayers": source_user_layers' in projector
    assert '"userLayers": region_layers' in projector
    assert '"tierImages"' not in projector[projector.index('return {'):]
    assert "state.projection!=='region-world-z-v2'" in viewer
    assert "state.sourceUserLayers" in viewer
    assert "sourceLocked:true" in viewer
    assert "stage.dataset.sourceScope='selected-parent-cells'" in viewer
    assert "stage.dataset.renderer='region-world-z-v2'" in viewer


def test_hex_claim_geometry_uses_same_column_staggered_addressing_everywhere():
    prototype = text("wwwroot/prototype/prototype.js")
    regions = text("WorldSession.Regions.cs")

    assert "function regionGridExtents(" in prototype
    assert "REGION_GRID_COLUMNS*.75+.25" in prototype
    assert "REGION_GRID_ROWS+.5" in prototype
    assert "regionCellCenter(cell,'hex')" in prototype
    assert "var spanX = hex ? GridColumns * .75 + .25 : GridColumns;" in regions
    assert "var spanY = hex ? GridRows + .5 : GridRows;" in regions
    assert "var hx = hex ? col * .75 : col;" in regions
    assert "var hy = hex ? row + (col % 2) * .5 : row;" in regions


def test_requested_region_reset_is_scoped_to_geonaph_regions_not_worldbuilder_terrain():
    app = authority_text()

    assert 'REGION_Z_RESET_MARKER = "MIGRATION#20260924_REGION_Z100_RESET_V1"' in app
    reset = app[
        app.index("def ensure_region_z100_reset():"):
        app.index("def handler(event, context):")
    ]
    assert 'for prefix in ("REGION#", "REGIONMAP#")' in reset
    assert 'str(item.get("regionId") or "")' in reset
    assert "state["userLayers"] = kept" in reset
    assert "WORLDSOURCE" not in reset or "world_source_key" in reset
    assert "batch.delete_item" in reset
    assert "delete_item(Key=source_key)" not in reset


def test_regiondefiner_api_exposes_both_filtered_read_and_overlay_save():
    app = authority_text()
    template = (REPO / "infra" / "aws" / "rist-platform.yml").read_text(encoding="utf-8")
    client = text("AwsAuthorityClient.cs")

    assert 'method == "GET" and path == "/world/source/region"' in app
    assert 'method == "POST" and path == "/world/source/region"' in app
    assert "Path: /world/source/region, Method: GET" in template
    assert "Path: /world/source/region, Method: POST" in template
    assert "GetRegionSourceAsync" in client
    assert "SaveWorldRegionMapAsync" in client
