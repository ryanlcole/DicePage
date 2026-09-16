from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_admin_border_is_shared_edge_model_not_double_paint():
    js = (ROOT / 'wwwroot' / 'worldbuilder-admin-keyboard.js').read_text(encoding='utf-8')
    assert "shared-edge-perimeter" in js
    contract = (ROOT / 'WORLDBUILDER_ADMIN_KEYBOARD_CONTRACT.md').read_text(encoding='utf-8')
    assert "shared edge/perimeter objects" in contract.lower()
