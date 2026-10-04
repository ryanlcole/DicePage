from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_new_recursive_region_opens_hex_map_selector_before_authoritative_create():
    component = (ROOT / "Components/UniversalInterface.razor").read_text(encoding="utf-8")
    assert 'if(CurrentBuilderScope=="REGION"&&_spatialDefinitionActive)' in component
    assert 'await BeginSpatialRegionDefinitionAsync(name,inspectionReason);' in component
    assert '"beginSpatialSelection"' in component
    assert 'gridShape="hex"' in component
    assert 'columns=30' in component
    assert 'rows=30' in component
    assert 'selection.SelectedCells' in component
    assert 'CommitPendingSpatialRegionAsync' in component


def test_world_spatial_region_geometry_is_persisted_with_the_recursive_node():
    regions = (ROOT / "WorldSession.Regions.cs").read_text(encoding="utf-8")
    assert "IEnumerable<int>? selectedCells = null" in regions
    assert 'gridShape = string.Equals(gridShape, "square"' in regions
    assert 'if (kind == "REGION" && selectedCells is not null && spatialCells.Count == 0)' in regions
    assert 'GridShape: kind == "REGION" ? gridShape : ""' in regions
    assert 'SelectedCells: kind == "REGION" ? spatialCells : null' in regions


def test_embedded_worldbuilder_exposes_touch_keyboard_and_analog_region_selection():
    prototype = (ROOT / "wwwroot/prototype/prototype.js").read_text(encoding="utf-8")
    host = (ROOT / "wwwroot/worldbuilder-source-host.js").read_text(encoding="utf-8")
    semantic = (ROOT / "Components/UniversalInterface.SemanticControls.cs").read_text(encoding="utf-8")
    assert "function beginSpatialSelection(raw={})" in prototype
    assert "spatialSelectionGridShape='hex'" in prototype
    assert "pointerdown" in prototype
    assert "pointermove" in prototype
    assert "event.key==='ArrowUp'" in prototype
    assert "toggleSpatialSelectionCursor" in prototype
    assert "spatial-selection-change" in prototype
    assert "ReceiveWorldBuilderSpatialSelectionStateAsync" in host
    assert "moveSpatialSelectionCursor" in host
    assert "_stage == Stage.SpatialSelect && _spatialDefinitionActive" in semantic


def test_saved_region_footprint_returns_to_viewer_when_region_is_selected():
    component = (ROOT / "Components/UniversalInterface.razor").read_text(encoding="utf-8")
    prototype = (ROOT / "wwwroot/prototype/prototype.js").read_text(encoding="utf-8")
    host = (ROOT / "wwwroot/worldbuilder-source-host.js").read_text(encoding="utf-8")
    assert "spatialDefinition=new" in component
    assert "selectedCells=region.SelectedCells??[]" in component
    assert "export function setSpatialDefinition" in host
    assert '"setSpatialDefinition"' in component
    assert "function setSpatialDefinition(raw=null)" in prototype
    assert "showSpatialRegionDefinition(raw)" in prototype
