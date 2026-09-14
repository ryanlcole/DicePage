from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WWWROOT = ROOT / "wwwroot"


def test_view_button_controls_only_the_authoritative_stage_grid():
    script = (WWWROOT / "worldbuilder-view-controls.js").read_text()
    assert "commandButton('View')" in script
    assert "viewer-grid-disabled" in script
    assert ".world-stage>.grid" in script
    assert "studio-viewer-grid" in script
    assert "aria-pressed" in script


def test_lock_state_is_read_from_viewer_authority_not_button_copy():
    script = (WWWROOT / "worldbuilder-view-controls.js").read_text()
    assert "rist.world.viewerLocked" in script
    assert "strong==='Z-Lock'||strong==='Lock'||strong==='Unlock'" in script
    assert "Pinch zoom remains available" in script
    assert "viewer-unlocked" in script


def test_view_control_bridge_loads_after_navigation_authority():
    index = (WWWROOT / "index.html").read_text()
    navigation = 'worldbuilder-navigation-authority.js?v=20260914-unified-gesture-1'
    controls = 'worldbuilder-view-controls.js?v=20260914-unified-gesture-1'
    assert navigation in index
    assert controls in index
    assert index.index(controls) > index.index(navigation)
