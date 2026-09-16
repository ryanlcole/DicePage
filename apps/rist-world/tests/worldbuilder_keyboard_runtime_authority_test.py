from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "wwwroot"


def test_runtime_geometry_uses_real_shaelvien_assets_and_six_by_two_keys():
    css = (ROOT / "css" / "worldbuilder-keyboard-runtime-authority.css").read_text(encoding="utf-8")
    assert "runtime/worldbuilder/keyboards/v1/common/blank.png" in css
    assert "runtime/worldbuilder/keyboards/v1/common/active.png" in css
    assert "grid-template-columns:repeat(6,minmax(0,1fr))" in css
    assert "calc(var(--wb-device-keyboard-h) - 70px)" not in css
    assert "pointer-events:auto!important" in css


def test_runtime_authority_provides_ios_touch_activation_and_resume_recovery():
    js = (ROOT / "worldbuilder-keyboard-runtime-authority.js").read_text(encoding="utf-8")
    assert "touchstart" in js
    assert "touchend" in js
    assert "state.button.click()" in js
    assert "pageshow" in js
    assert "visibilitychange" in js
    assert "repaintWorld" in js
    assert "RistWorldBuilderShaelvienKeyboardSkin?.refresh" in js
    assert "RistWorldBuilderGridCursor?.refresh" in js


def test_mode_relocation_bootstraps_runtime_authority():
    js = (ROOT / "worldbuilder-mode-keyboard-relocation.js").read_text(encoding="utf-8")
    assert "worldbuilder-keyboard-runtime-authority.js?v=20260916-touch-art-resume-1" in js
    assert "ensureRuntime" in js
