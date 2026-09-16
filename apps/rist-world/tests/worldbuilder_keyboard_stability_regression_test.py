from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TICKER = ROOT / "wwwroot" / "worldbuilder-ticker-data-keyboard.js"
FINAL = ROOT / "wwwroot" / "worldbuilder-final-keyboard-authority.js"


def test_ticker_hides_widget_layer_without_removing_shell_contract():
    source = TICKER.read_text(encoding="utf-8")
    assert ".wb-viewer-widgets" in source
    assert "node.remove()" not in source[source.index("function suppressViewerWidgets"):source.index("function renameAccessWidgetShortcut")]
    assert "aria-hidden" in source[source.index("function suppressViewerWidgets"):source.index("function renameAccessWidgetShortcut")]


def test_final_keyboard_hides_duplicate_visual_text_but_keeps_accessibility():
    source = FINAL.read_text(encoding="utf-8")
    assert "wb-final-art-loaded>strong" in source
    assert "wb-final-art-loaded>small" in source
    assert "wb-final-dpad-art" in source
    assert "aria-label" in source
