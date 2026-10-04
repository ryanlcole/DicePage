from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_controller_reuses_established_regiondefiner_in_same_viewer_surface():
    component = (ROOT / "Components/UniversalInterface.razor").read_text(encoding="utf-8")
    region = (ROOT / "Components/RegionDefinerWorkspace.razor").read_text(encoding="utf-8")

    assert '<RegionDefinerWorkspace @ref="_regionDefinerWorkspace"' in component
    assert 'EmbeddedController="true"' in component
    assert 'NewRegionFlow="@_regionDefinerNewFlow"' in component
    assert 'Session.SetActiveRegion("");' in component
    flow = component[component.index("async Task ActivateSpatialSelectionAsync()"):component.index("void LoadGameAssets()")]
    assert '"beginSpatialSelection"' not in flow
    assert "CreateSpatialNodeAsync(" not in flow
    assert "mode=regiondefiner" in region
    assert "embedded-controller=1" in region


def test_controller_is_only_an_adapter_over_old_regiondefiner_selection():
    prototype = (ROOT / "wwwroot/prototype/prototype.js").read_text(encoding="utf-8")
    host = (ROOT / "wwwroot/region-definer-host.js").read_text(encoding="utf-8")
    semantic = (ROOT / "Components/UniversalInterface.SemanticControls.cs").read_text(encoding="utf-8")

    assert "function enterRegionController()" in prototype
    assert "regionSelectedCells.size" in prototype
    assert "previewRegionCrop()" in prototype
    assert "createRegionDefinition()" in prototype
    assert "toggleRegionCell(regionCellFromPoint(point.x,point.y,regionGridShape))" in prototype
    assert "REGION_DEFINER&&EMBEDDED_CONTROLLER?'hex':'square'" in prototype
    assert "if(REGION_DEFINER&&!EMBEDDED_CONTROLLER)return'REGION';" in prototype
    assert "enterControllerRegionSelection" in host
    assert "controllerPrimary" in host
    assert "controllerSelect" in host
    assert "_stage == Stage.SpatialSelect && _regionDefinerOpen" in semantic


def test_region_creation_uses_worldregion_then_continues_local_in_same_viewer():
    component = (ROOT / "Components/UniversalInterface.razor").read_text(encoding="utf-8")
    region = (ROOT / "Components/RegionDefinerWorkspace.razor").read_text(encoding="utf-8")

    assert "Session.CreateRegionAsync" in region
    assert "Session.ActiveRegion" in component
    assert '_builderChainIndex=2;' in component
    assert '_assetScope="LOCAL";' in component
    assert '"LOCAL",savedRegion.RegionId' in component
    assert "Continuing into Local inside the same recursive viewer." in component
    assert "_regionDefinerWorkspace.SetDepthAsync" in component
    assert "_regionDefinerWorkspace.PlaceAssetAsync(payload)" in component
    assert "_regionDefinerWorkspace.EditCommandAsync(command)" in component


def test_old_regiondefiner_grid_remains_selection_geometry():
    prototype = (ROOT / "wwwroot/prototype/prototype.js").read_text(encoding="utf-8")

    assert "const REGION_GRID_COLUMNS=SCOPE_GRID_COLUMNS" in prototype
    assert "const REGION_GRID_ROWS=SCOPE_GRID_ROWS" in prototype
    assert "function regionSelectionSvg()" in prototype
    assert "function regionOverlayFigure(" in prototype
    assert "const offset=shape==='hex'&&(row%2)?0.5:0;" in prototype
    assert "regionSelectedCells" in prototype


def test_saved_region_is_hard_cropped_and_world_source_is_flat_until_region_tiers_exist():
    prototype = (ROOT / "wwwroot/prototype/prototype.js").read_text(encoding="utf-8")

    assert "stage.dataset.cropMode='hard-region-crop'" in prototype
    assert "zooming out restores the surrounding" not in prototype
    assert "function claimedRegionSourceTier()" in prototype
    assert "function claimedRegionSourceLayerSet()" in prototype
    assert "viewerTier=tierByIndex(0).key" in prototype
    assert "entry.tier===regionSourceTier" in prototype
    assert "const depth=presentationDepthForTier(item.tier);" in prototype
    assert "const renderedDepth=REGION_DEFINER&&regionClaimedRegion&&item.canonicalSource?0:depth;" in prototype
    assert "flattened as Region base Tier 1" in prototype


def test_region_hex_mask_uses_same_old_seam_closing_geometry_as_selection():
    prototype = (ROOT / "wwwroot/prototype/prototype.js").read_text(encoding="utf-8")

    assert "const REGION_HEX_HEIGHT_RATIO=4/3;" in prototype
    assert "const REGION_HEX_SEAM_OVERLAP=1.004;" in prototype
    assert "function regionHexPolygonPoints" in prototype
    assert "regionHexPolygonPoints(x,y,sx,sy)" in prototype
    assert "regionHexPolygonPoints(x,y)" in prototype
