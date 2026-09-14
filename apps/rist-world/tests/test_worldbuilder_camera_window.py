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


def test_camera_window_is_responsive_and_never_squeezes_entire_surface_onto_phone():
    camera = (WWWROOT / "worldbuilder-camera-window.js").read_text()
    assert "const LOCAL_GRID_CELLS=30" in camera
    assert "const MIN_VISIBLE_CELLS=10" in camera
    assert "const MAX_VISIBLE_CELLS=16" in camera
    assert "const TARGET_CELL_PX=30" in camera
    assert "orientationchange" in camera
    assert "resize" in camera
    assert "cameraWindowV1" in camera


def test_camera_clamps_navigation_to_visible_world_edges():
    camera = (WWWROOT / "worldbuilder-camera-window.js").read_text()
    assert "const maxOffset=Math.max(0,Math.floor((LOCAL_GRID_CELLS-visible)/2))" in camera
    assert "navigation.setPosition(x,y,true)" in camera
    assert "requestAnimationFrame(clampPan)" in camera


def test_camera_authority_is_loaded_after_legacy_optics_and_cache_busted():
    index = (WWWROOT / "index.html").read_text()
    optics = 'worldbuilder-optics.js?v=20260912-optics-pinchzoom-1'
    camera = 'worldbuilder-camera-window.js?v=20260914-camera-window-1'
    grid = 'css/worldbuilder-grid-authority.css?v=20260914-camera-window-1'
    assert optics in index
    assert camera in index
    assert grid in index
    assert index.index(camera) > index.index(optics)
