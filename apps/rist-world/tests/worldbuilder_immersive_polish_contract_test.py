from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WWW = ROOT / "wwwroot"
LIFECYCLE = WWW / "worldbuilder-lifecycle-authority-v2.js"
INDEX = WWW / "index.html"


def test_consolidated_lifecycle_preserves_art_aspect_and_loads_after_keyboard_authorities():
    js = LIFECYCLE.read_text(encoding="utf-8")
    html = INDEX.read_text(encoding="utf-8")

    assert "object-fit:contain!important" in js
    assert "wb-keyboard-v2-art" in js
    assert "wb-keyboard-v2-dpad-art" in js

    keyboard = html.index("worldbuilder-keyboard-authority-v2.js")
    relocation = html.index("worldbuilder-mode-keyboard-relocation.js")
    lifecycle = html.index("worldbuilder-lifecycle-authority-v2.js")
    assert keyboard < relocation < lifecycle
    assert "worldbuilder-immersive-polish.js" not in html


def test_worldbuilder_lifecycle_hides_only_immersive_footer_notice():
    js = LIFECYCLE.read_text(encoding="utf-8")

    assert "wb-immersive-worldbuilder" in js
    assert ".site-copyright-notice" in js
    assert "classList.toggle('wb-immersive-worldbuilder',active)" in js
    assert "setFooterContext(active)" in js


def test_ios_resume_has_guarded_recovery_and_authority_refresh():
    js = LIFECYCLE.read_text(encoding="utf-8")

    assert "addEventListener('pageshow'" in js
    assert "addEventListener('pagehide',markBackground" in js
    assert "addEventListener('visibilitychange'" in js
    assert "guardedReload" in js
    assert "wasActiveWorldbuilder" in js
    assert "location.reload()" in js
    assert "RistWorldBuilderKeyboardAuthority?.refresh" in js
    assert "RistWorldBuilderGridCursor?.refresh" in js
