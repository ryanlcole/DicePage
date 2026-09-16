from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_admin_keyboard_is_loaded_after_device_shell_and_dpad():
    html = (ROOT / 'wwwroot' / 'index.html').read_text(encoding='utf-8')
    device = html.index('worldbuilder-device-shell.js')
    dpad = html.index('worldbuilder-grid-cursor-dpad.js')
    admin = html.index('worldbuilder-admin-keyboard.js')
    assert device < dpad < admin
