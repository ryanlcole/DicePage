from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / "wwwroot" / "worldbuilder-mode-keyboard-relocation.js").read_text(encoding="utf-8")
INDEX = (ROOT / "wwwroot" / "index.html").read_text(encoding="utf-8")
KEYBOARD = (ROOT / "wwwroot" / "worldbuilder-keyboard-authority-v2.js").read_text(encoding="utf-8")


def test_relocation_is_loaded_after_consolidated_keyboard_authority():
    keyboard = INDEX.index("worldbuilder-keyboard-authority-v2.js")
    relocation = INDEX.index("worldbuilder-mode-keyboard-relocation.js")
    assert relocation > keyboard
    assert "worldbuilder-shaelvien-keyboard-skin.js" not in INDEX


def test_viewer_surface_controls_are_hidden_as_bridges_not_deleted():
    assert ".worldbuilder-studio .studio-edit-mode" in JS
    assert ".worldbuilder-studio .description-mode-toggle" in JS
    assert "clip-path:inset(50%)" in JS
    assert "editBridge()?.querySelector('button')" in JS
    assert "button.click()" in JS


def test_viewer_keyboard_receives_world_status_and_build_action():
    assert "currentMode()!=='viewer'" in JS
    assert "makeKey('World View'" in JS
    assert "makeKey('Build Mode'" in JS
    assert "Viewing world" in JS
    assert "Sign in required" in JS


def test_description_remains_in_access_keyboard_and_uses_current_art_mapping():
    assert "currentMode()!=='access'" in JS
    assert "==='Description'" in JS
    assert "'Description':'screen_read'" in KEYBOARD


def test_relocated_keys_stay_in_consolidated_keyboard_pipeline():
    assert "button.className='wb-device-key'" in JS
    assert "RistWorldBuilderKeyboardAuthority?.refresh?.()" in JS
