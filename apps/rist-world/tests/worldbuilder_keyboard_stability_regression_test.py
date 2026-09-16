from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TICKER = ROOT / "wwwroot" / "worldbuilder-ticker-data-keyboard-v2.js"
KEYBOARD = ROOT / "wwwroot" / "worldbuilder-keyboard-authority-v2.js"


def test_ticker_hides_widget_layer_without_removing_shell_contract():
    source = TICKER.read_text(encoding="utf-8")
    body = source[source.index("function keepWidgetLayerStable"):source.index("function makeKey")]
    assert ".wb-viewer-widgets" in body
    assert "node.remove()" not in body
    assert "node.hidden=true" in body
    assert "aria-hidden" in body
    assert "display','none','important" in body


def test_keyboard_hides_duplicate_visual_text_but_keeps_accessibility():
    source = KEYBOARD.read_text(encoding="utf-8")
    assert "wb-keyboard-v2-exact>strong" in source
    assert "wb-keyboard-v2-exact>small" in source
    assert "wb-keyboard-v2-dpad-art" in source
    assert "aria-label" in source
    assert "clip-path:inset(50%)" in source
