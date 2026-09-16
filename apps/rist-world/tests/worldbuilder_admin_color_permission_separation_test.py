from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_color_and_permission_emit_distinct_operations():
    js = (ROOT / 'wwwroot' / 'worldbuilder-admin-keyboard.js').read_text(encoding='utf-8')
    assert "rist:worldbuilder-admin-region-write" in js
    assert "rist:worldbuilder-admin-permission-request" in js
    assert "Permissions are not inferred from map color or borders" in js
