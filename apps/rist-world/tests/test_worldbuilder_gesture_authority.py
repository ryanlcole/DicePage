from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WWWROOT = ROOT / "wwwroot"


def test_two_fingers_are_camera_zoom_not_z_movement():
    gestures = (WWWROOT / "worldbuilder-gesture-authority.js").read_text()
    core = (WWWROOT / "worldbuilder-z-axis-core.js").read_text()
    assert "ownsViewerGestures:true" in gestures
    assert "beginPinch" in gestures
    assert "publishZoom(pinch.zoom*ratio)" in gestures
    assert "pointercancel" in gestures
    assert "stopImmediatePropagation" in gestures
    assert "authority()?.setZoom" in gestures
    assert "cameraWindowV1" not in gestures
    assert "addZTravel((1-ratio)*2.8)" not in core
    assert "wheelAccumulator" not in core


def test_navigation_is_single_viewer_state_authority_not_a_pointer_interpreter():
    navigation = (WWWROOT / "worldbuilder-navigation-authority.js").read_text()
    assert "window.ristViewerAuthority" in navigation
    assert "window.ristViewerNavigation" in navigation
    assert "setPosition" in navigation
    assert "nudge(axis,steps)" in navigation
    assert "setZoom" in navigation
    assert "setLocked" in navigation
    assert "setGrid" in navigation
    assert "pointerdown" not in navigation
    assert "fallbackPinch" not in navigation
    assert "sendZWheel" not in navigation


def test_worldbuilder_writes_resolve_from_actual_transformed_stage():
    gestures = (WWWROOT / "worldbuilder-gesture-authority.js").read_text()
    assert "const rect=world.getBoundingClientRect()" in gestures
    assert "api.worldPoint=" in gestures
    assert "api.dropPoint=" in gestures
    assert "api.tileDropPoint=" in gestures
    assert "Math.floor(clamp(p[0],0,.999999)*cols)" in gestures


def test_asset_editor_does_not_block_empty_viewer_when_locked():
    zaxis = (WWWROOT / "worldbuilder-z-axis.js").read_text()
    assert "const tile=tileAt(e.clientX,e.clientY);if(!tile)return;" in zaxis
    assert "Map + Viewer Locked" not in zaxis
    assert "Viewer Locked" in zaxis
    assert "worldbuilder-z-axis-core.js?v=20260915-completion-1" in zaxis


def test_z_axis_core_no_longer_owns_grid_or_camera_transform():
    core = (WWWROOT / "worldbuilder-z-axis-core.js").read_text()
    assert "world-stage::before" not in core
    assert "--wb-z-scale" not in core
    assert "[class*=\"grid\"]" not in core


def test_camera_mode_key_has_one_authoritative_writer():
    navigation = (WWWROOT / "worldbuilder-navigation-authority.js").read_text()
    camera = (WWWROOT / "worldbuilder-camera-window.js").read_text()
    gestures = (WWWROOT / "worldbuilder-gesture-authority.js").read_text()
    assert "cameraWindowV3" in navigation
    assert "cameraWindowV3" in camera
    assert "cameraWindowV1" not in gestures
    assert "cameraWindowV2" not in gestures
    assert "localStorage.setItem" not in camera
