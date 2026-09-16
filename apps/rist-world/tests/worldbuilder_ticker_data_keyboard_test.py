from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WWW = ROOT / "wwwroot"
JS = (WWW / "worldbuilder-ticker-data-keyboard.js").read_text(encoding="utf-8")
CSS = (WWW / "css" / "worldbuilder-ticker-data-keyboard.css").read_text(encoding="utf-8")
INDEX = (WWW / "index.html").read_text(encoding="utf-8")


def test_ticker_data_authority_is_loaded_after_keyboard_skin():
    skin = INDEX.index("worldbuilder-shaelvien-keyboard-skin.js")
    data = INDEX.index("worldbuilder-ticker-data-keyboard.js")
    assert skin < data
    assert "worldbuilder-ticker-data-keyboard.css" in INDEX


def test_floating_viewer_widgets_are_suppressed():
    assert ".wb-viewer-widgets" in CSS
    assert "display:none!important" in CSS
    assert "suppressViewerWidgets" in JS


def test_widget_slot_is_presented_as_data_keyboard():
    assert 'data-mode="widgets"' in JS
    assert "button.textContent='DATA'" in JS
    assert "modeName.textContent='Data keyboard'" in JS
    for label in ("Time", "Date", "Weather", "Viewer", "Sky", "Calendar", "UGC", "Reset"):
        assert f"makeDataKey('{label}'" in JS


def test_edit_labels_move_out_of_ticker():
    assert r"SKY\s*:\s*EDIT" in JS
    assert r"CALENDAR\s*:\s*EDIT" in JS
    assert r"UGC\s*:\s*EDIT" in JS
    assert "data-ticker-data-hidden" in CSS


def test_weather_only_appears_when_connected_and_enabled():
    assert "if(settings.weather&&weatherText())wanted.push('weather')" in JS


def test_data_edits_require_authoritative_writer():
    assert "rist:worldbuilder-data-edit-request" in JS
    assert "requiresAuthoritativeWriter:true" in JS


def test_sync_does_not_write_settings_or_self_emit():
    sync_body = JS.split("function sync(){", 1)[1].split("function start(){", 1)[0]
    assert "saveSettings" not in sync_body
    assert "dispatchEvent" not in sync_body
