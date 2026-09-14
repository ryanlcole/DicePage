from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WWWROOT = ROOT / "wwwroot"


def test_view_button_controls_the_authoritative_stage_grid():
    script = (WWWROOT / "worldbuilder-view-controls.js").read_text()
    assert "commandButton('View')" in script
    assert "viewer-grid-disabled" in script
    assert ".world-stage>.grid" in script
    assert "aria-pressed" in script


def test_z_lock_button_controls_viewer_navigation_lock_state():
    script = (WWWROOT / "worldbuilder-view-controls.js").read_text()
    assert "commandButton('Z-Lock')" in script
    assert "rist.world.viewerLocked" in script
    assert "ristViewerNavigation?.resync?.()" in script
    assert "viewer-unlocked" in script


def test_view_control_bridge_loads_after_navigation_authority():
    index = (WWWROOT / "index.html").read_text()
    navigation = 'worldbuilder-navigation-authority.js?v=20260911-rulers-zoom-1'
    controls = 'worldbuilder-view-controls.js?v=20260914-view-controls-1'
    assert navigation in index
    assert controls in index
    assert index.index(controls) > index.index(navigation)
