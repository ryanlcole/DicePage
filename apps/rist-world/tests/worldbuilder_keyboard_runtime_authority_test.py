from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "wwwroot"
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
KEYBOARD = (ROOT / "worldbuilder-keyboard-authority-v2.js").read_text(encoding="utf-8")
LIFECYCLE = (ROOT / "worldbuilder-lifecycle-authority-v2.js").read_text(encoding="utf-8")
RELOCATION = (ROOT / "worldbuilder-mode-keyboard-relocation.js").read_text(encoding="utf-8")


def test_consolidated_keyboard_uses_shaelvien_assets_without_reloading_retired_runtime():
    assert "runtime/worldbuilder/keyboards/v1" in KEYBOARD
    assert "/common/blank.png" in KEYBOARD
    assert "/common/active.png" in KEYBOARD
    assert "worldbuilder-keyboard-authority-v2.js" in INDEX
    assert "worldbuilder-keyboard-runtime-authority.js" not in INDEX
    assert "worldbuilder-shaelvien-keyboard-skin.js" not in INDEX


def test_consolidated_keyboard_uses_pointer_authority_not_synthetic_touch_clicks():
    assert "addEventListener('pointerdown'" in KEYBOARD
    assert "addEventListener('touchend'" not in KEYBOARD
    assert "state.button.click()" not in KEYBOARD
    assert "pointer-events:auto!important" in LIFECYCLE
    assert "touch-action:manipulation!important" in LIFECYCLE


def test_lifecycle_owns_resume_recovery_for_keyboard_and_viewer_authorities():
    assert "pageshow" in LIFECYCLE
    assert "visibilitychange" in LIFECYCLE
    assert "guardedReload" in LIFECYCLE
    assert "RistWorldBuilderKeyboardAuthority?.refresh" in LIFECYCLE
    assert "RistWorldBuilderGridCursor?.refresh" in LIFECYCLE


def test_mode_relocation_refreshes_consolidated_keyboard_without_bootstrapping_retired_runtime():
    assert "RistWorldBuilderKeyboardAuthority?.refresh?.()" in RELOCATION
    assert "worldbuilder-keyboard-runtime-authority.js" not in RELOCATION
    assert "ensureRuntime" not in RELOCATION
