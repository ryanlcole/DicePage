from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_controller_uses_main_world_viewer_for_visible_space_selection():
    component = (ROOT / "Components/UniversalInterface.razor").read_text(encoding="utf-8")
    bridge = (ROOT / "wwwroot/worldbuilder-source-host.js").read_text(encoding="utf-8")

    flow = component[component.index("async Task BeginOrSaveVisibleSpatialSelectionAsync()"):component.index("void SelectArtMethod()")]
    assert '"beginSpatialSelection"' in flow
    assert '"getSpatialSelection"' in flow
    assert '"finishSpatialSelection"' in flow
    assert "CreateSpatialNodeAsync(" in flow
    assert "CreateRegionAsync(" in flow
    assert "_regionDefinerOpen=true" not in flow
    assert "beginSpatialSelection" in bridge
    assert "moveSpatialSelectionCursor" in bridge
    assert "toggleSpatialSelectionCursor" in bridge


def test_selection_is_viewer_relative_and_preserves_canonical_world_bounds():
    prototype = (ROOT / "wwwroot/prototype/prototype.js").read_text(encoding="utf-8")
    regions = (ROOT / "WorldSession.Regions.cs").read_text(encoding="utf-8")

    assert "function spatialViewerWindow()" in prototype
    assert "function spatialSelectionLocalBounds()" in prototype
    assert "canonicalCells" in prototype
    assert "canonicalMinX" in prototype
    assert "viewMinX" in prototype
    assert "stage.appendChild(overlay)" in prototype
    assert "BoundaryCells" in regions
    assert "ViewZoomRatio" in regions
    assert "ResolutionScope" in regions


def test_view_angle_is_independent_from_zoom_resolution():
    prototype = (ROOT / "wwwroot/prototype/prototype.js").read_text(encoding="utf-8")
    html = (ROOT / "wwwroot/prototype/index.html").read_text(encoding="utf-8")
    component = (ROOT / "Components/UniversalInterface.razor").read_text(encoding="utf-8")

    assert "function currentSpatialViewAngle(){return viewAngle}" in prototype
    assert "function setViewAngle(" in prototype
    assert "SCOPE_VIEW_ANGLE" not in prototype
    assert 'id="viewAngleSelect"' in html
    receive = component[component.index("ReceiveWorldBuilderSpatialScopeAsync"):component.index("ReceiveWorldBuilderSelectionContextAsync")]
    assert "_viewerSpatialViewAngle=Math.Clamp(angle,0,89);" in receive
    assert '"REGION"=>15' not in receive
    assert '"LOCAL"=>30' not in receive


def test_regions_can_nest_and_instance_is_a_scene_boundary_not_local_requirement():
    regions = (ROOT / "WorldSession.Regions.cs").read_text(encoding="utf-8")

    create = regions[regions.index("public async Task<WorldSpatialNode> CreateSpatialNodeAsync"):regions.index("void ClearSpatialSelection()")]
    assert "ActiveSpatialRegion?.NodeId" in create
    assert "ActiveLocal?.NodeId" in create
    assert 'throw new InvalidOperationException("Select a Local before creating an Instance.")' not in create
    assert "SceneBoundary: kind == \"INSTANCE\"" in create
    assert "lineage, not containment proof" in create


def test_saving_selection_focuses_into_bounded_space_without_mutating_coordinates():
    prototype = (ROOT / "wwwroot/prototype/prototype.js").read_text(encoding="utf-8")

    assert "function focusSpatialSelection()" in prototype
    assert "finishSpatialSelection(focus=true)" in prototype
    assert "World coordinates and spatial identity are unchanged." in prototype
    assert "scale=clamp(nextScale" in prototype
