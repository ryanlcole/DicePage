from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_admin_selection_marks_presentation_density_as_noncanonical():
    js = (ROOT / 'wwwroot' / 'worldbuilder-admin-keyboard.js').read_text(encoding='utf-8')
    assert "presentationSelection:true" in js
    assert "selectionDensity" in js
    contract = (ROOT / 'WORLDBUILDER_ADMIN_KEYBOARD_CONTRACT.md').read_text(encoding='utf-8')
    assert "presentation density is not world truth" in contract.lower()
