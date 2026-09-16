from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WWW = ROOT / "wwwroot"
JS = (WWW / "worldbuilder-ticker-data-keyboard-v2.js").read_text(encoding="utf-8")
INDEX = (WWW / "index.html").read_text(encoding="utf-8")


def test_ticker_data_v2_is_loaded_before_keyboard_decoration_and_retired_v1_is_not_loaded():
    data = INDEX.index("worldbuilder-ticker-data-keyboard-v2.js")
    keyboard = INDEX.index("worldbuilder-keyboard-authority-v2.js")
    assert data < keyboard
    assert "worldbuilder-ticker-data-keyboard.js" not in INDEX
    assert "worldbuilder-shaelvien-keyboard-skin.js" not in INDEX


def test_floating_viewer_widgets_are_suppressed_without_deletion():
    body = JS[JS.index("function keepWidgetLayerStable"):JS.index("function makeKey")]
    assert ".wb-viewer-widgets" in body
    assert "display','none','important" in body
    assert "aria-hidden" in body
    assert "node.remove()" not in body


def test_widget_slot_is_presented_as_data_keyboard():
    assert 'data-mode="widgets"' in JS
    assert "tab.textContent='DATA'" in JS
    assert "title.textContent='Data keyboard'" in JS
    for label in ("Time", "Date", "Weather", "Viewer", "Stars", "Sky", "Calendar", "UGC", "Reset"):
        assert f"makeKey('{label}'" in JS


def test_edit_labels_move_out_of_ticker_without_destroying_ticker_nodes():
    assert r"SKY\s*:\s*EDIT" in JS
    assert r"CALENDAR\s*:\s*EDIT" in JS
    assert r"UGC\s*:\s*EDIT" in JS
    assert "tickerDataHidden" in JS
    assert "node.hidden=true" in JS


def test_weather_only_appears_when_connected_and_enabled():
    assert "if(settings.weather&&weatherText())wanted.push('weather')" in JS


def test_data_edits_require_authoritative_writer():
    assert "rist:worldbuilder-data-edit-request" in JS
    assert "requiresAuthoritativeWriter:true" in JS


def test_sync_does_not_write_settings_or_self_emit():
    sync_body = JS.split("function sync(){", 1)[1].split("function start(){", 1)[0]
    assert "writeSettings" not in sync_body
    assert "dispatchEvent" not in sync_body
