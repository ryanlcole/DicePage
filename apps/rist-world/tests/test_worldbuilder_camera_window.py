from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WWWROOT = ROOT / "wwwroot"


def test_worldbuilder_grid_matches_local_30_cell_placement_authority():
    css = (WWWROOT / "css" / "worldbuilder-grid-authority.css").read_text()
    assert "--world-grid-columns:30" in css
    assert "--world-grid-rows:30" in css
    assert "--world-grid-columns:300" not in css
    assert ".world-stage>.grid.square" in css
    assert "background-size:var(--world-grid-cell-x) var(--world-grid-cell-y)" in css


def test_viewer_authority_owns_responsive_camera_bounds():
    authority = (WWWROOT / "worldbuilder-navigation-authority.js").read_text()
    assert "const GRID_CELLS=30" in authority
    assert "const MIN_VISIBLE_CELLS=10" in authority
    assert "const MAX_VISIBLE_CELLS=16" in authority
    assert "const TARGET_CELL_PX=30" in authority
    assert "const MIN_ZOOM=GRID_CELLS/MAX_VISIBLE_CELLS" in authority
    assert "const MAX_ZOOM=GRID_CELLS/MIN_VISIBLE_CELLS" in authority
    assert "cameraWindowV3" in authority
    assert "orientationchange" in authority
    assert "resize" in authority
    assert "window.ristViewerAuthority" in authority


def test_camera_window_delegates_zoom_to_viewer_authority():
    camera = (WWWROOT / "worldbuilder-camera-window.js").read_text()
    assert "const LOCAL_GRID_CELLS=30" in camera
    assert "const MIN_VISIBLE_CELLS=10" in camera
    assert "const MAX_VISIBLE_CELLS=16" in camera
    assert "const TARGET_CELL_PX=30" in camera
    assert "cameraWindowV3" in camera
    assert "authority()?.resetAutoZoom" in camera
    assert "authority()?.setZoom" in camera
    assert "localStorage.setItem" not in camera


def test_optics_share_camera_window_zoom_bounds():
    optics = (WWWROOT / "worldbuilder-optics.js").read_text()
    assert "const LOCAL_GRID_CELLS=30" in optics
    assert "const MIN_VISIBLE_CELLS=10" in optics
    assert "const MAX_VISIBLE_CELLS=16" in optics
    assert "const MIN_ZOOM=LOCAL_GRID_CELLS/MAX_VISIBLE_CELLS" in optics
    assert "const MAX_ZOOM=LOCAL_GRID_CELLS/MIN_VISIBLE_CELLS" in optics
    assert "const MIN_ZOOM=.35" not in optics
    assert "const MAX_ZOOM=8" not in optics


def test_lock_and_z_depth_cannot_change_stage_grid_scale():
    optics = (WWWROOT / "worldbuilder-optics.js").read_text()
    view_fix = (WWWROOT / "worldbuilder-view-fix.js").read_text()
    assert "scale(var(--wb-view-zoom,1))!important" in optics
    assert "scale(var(--wb-z-scale" not in optics
    assert "wb-z-unlocked .studio-viewer-canvas .world-stage" not in view_fix
    assert "scale(var(--wb-z-scale" not in view_fix


def test_viewer_authority_clamps_pan_to_visible_local_grid_edges():
    authority = (WWWROOT / "worldbuilder-navigation-authority.js").read_text()
    assert "function maxPanOffset()" in authority
    assert "GRID_CELLS-visibleCells()" in authority
    assert "function clampAxis(value)" in authority
    assert "setPosition" in authority


def test_viewer_authority_loads_before_gestures_and_helpers():
    index = (WWWROOT / "index.html").read_text()
    navigation = 'worldbuilder-navigation-authority.js?v=20260915-viewer-authority-1'
    gestures = 'worldbuilder-gesture-authority.js?v=20260915-viewer-authority-1'
    optics = 'worldbuilder-optics.js?v=20260915-completion-1'
    camera = 'worldbuilder-camera-window.js?v=20260915-viewer-authority-1'
    controls = 'worldbuilder-view-controls.js?v=20260915-viewer-authority-1'
    grid = 'css/worldbuilder-grid-authority.css?v=20260914-unified-gesture-1'
    for asset in (navigation, gestures, optics, camera, controls, grid):
        assert asset in index
    assert index.index(navigation) < index.index(gestures) < index.index(optics) < index.index(camera) < index.index(controls)
