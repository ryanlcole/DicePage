from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "Components" / "TileEditingOverlay.razor.css").read_text()
JS = (ROOT / "wwwroot" / "tile-editing.js").read_text()


def test_tile_edit_controls_are_screen_space_and_fixed_size():
    assert "position: fixed;" in CSS
    assert "--tile-edit-control-size: 18px;" in CSS
    assert "--tile-edit-control-size: 20px;" in CSS
    assert "width: 34px" not in CSS
    assert "height: 34px" not in CSS
    assert "getBoundingClientRect()" in JS
    assert "--tile-width" in JS
    assert "--tile-height" in JS


def test_eight_nudge_controls_surround_selected_tile():
    directions = (
        "north-west", "north", "north-east", "east",
        "south-east", "south", "south-west", "west",
    )
    for direction in directions:
        assert f".tile-edit-arrow.{direction}" in CSS

    assert "--tile-edit-control-outset: -23px;" in CSS
    assert "--tile-edit-control-outset: -25px;" in CSS
    for edge in ("left", "right", "top", "bottom"):
        assert re.search(rf"{edge}: var\(--tile-edit-control-outset\)", CSS)


def test_lock_is_small_and_does_not_displace_northeast_arrow():
    assert "--tile-edit-lock-size: 18px;" in CSS
    assert "--tile-edit-lock-size: 20px;" in CSS
    northeast = re.search(r"\.tile-edit-arrow\.north-east\s*\{([^}]*)\}", CSS)
    assert northeast is not None
    assert "right: var(--tile-edit-control-outset)" in northeast.group(1)
    assert "right: 42px" not in CSS
