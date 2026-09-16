from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_admin_controls_have_semantic_translation_hooks():
    js = (ROOT / 'wwwroot' / 'worldbuilder-admin-keyboard.js').read_text(encoding='utf-8')
    assert "dataset.accessTranslation='available'" in js
    assert "aria-label" in js
    assert "announce(" in js


def test_admin_color_is_not_only_region_identifier():
    js = (ROOT / 'wwwroot' / 'worldbuilder-admin-keyboard.js').read_text(encoding='utf-8')
    assert "Region name" in js
    assert "Border type" in js
    assert "selectionSummary" in js
