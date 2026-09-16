from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_admin_keyboard_preserves_authority_separation():
    js = (ROOT / 'wwwroot' / 'worldbuilder-admin-keyboard.js').read_text(encoding='utf-8')
    contract = (ROOT / 'WORLDBUILDER_ADMIN_KEYBOARD_CONTRACT.md').read_text(encoding='utf-8')
    assert "rist:worldbuilder-admin-permission-request" in js
    assert "requiresSharedRecursiveAuthority:true" in js
    assert "permission never requires a visible color" in contract.lower()
    assert "color or border never grants permission" in contract.lower()


def test_admin_keyboard_supports_region_cartography_and_shared_borders():
    js = (ROOT / 'wwwroot' / 'worldbuilder-admin-keyboard.js').read_text(encoding='utf-8')
    assert "shared-edge-perimeter" in js
    assert "Fill color" in js
    assert "Border type" in js
    assert "Anchor" in js
    assert "Rectangle" in js


def test_admin_keyboard_reuses_persistent_dpad():
    js = (ROOT / 'wwwroot' / 'worldbuilder-admin-keyboard.js').read_text(encoding='utf-8')
    assert "RistWorldBuilderGridCursor" in js
    assert "Admin selection anchor set" in js
