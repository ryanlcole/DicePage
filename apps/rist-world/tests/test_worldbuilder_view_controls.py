from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WWWROOT = ROOT / "wwwroot"


def test_view_button_commands_authoritative_grid_state():
    script = (WWWROOT / "worldbuilder-view-controls.js").read_text()
    assert "commandButton('View')" in script
    assert "toggleGrid" in script
    assert "source:'view-button'" in script
    assert "stopImmediatePropagation" in script
    assert "aria-pressed" in script
    assert "rist:viewer-state" in script


def test_grid_visibility_is_applied_by_viewer_authority_not_button_copy():
    authority = (WWWROOT / "worldbuilder-navigation-authority.js").read_text()
    controls = (WWWROOT / "worldbuilder-view-controls.js").read_text()
    assert "const GRID_KEY='rist.world.viewerGrid'" in authority
    assert "viewer-grid-disabled" in authority
    assert ".world-stage>.grid" in authority
    assert ".studio-viewer-grid" in authority
    assert "setGrid" in authority
    assert "state.grid" in controls


def test_lock_state_is_read_from_viewer_authority_not_button_copy():
    script = (WWWROOT / "worldbuilder-view-controls.js").read_text()
    assert "const authority=()=>window.ristViewerAuthority" in script
    assert "strong==='Z-Lock'||strong==='Lock'||strong==='Unlock'" in script
    assert "Pinch zoom remains available" in script
    assert "state.locked" in script


def test_view_control_bridge_loads_after_navigation_authority():
    index = (WWWROOT / "index.html").read_text()
    navigation = 'worldbuilder-navigation-authority.js?v=20260915-viewer-authority-1'
    controls = 'worldbuilder-view-controls.js?v=20260915-viewer-authority-1'
    assert navigation in index
    assert controls in index
    assert index.index(controls) > index.index(navigation)
