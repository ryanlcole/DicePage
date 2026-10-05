from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_spatial_selection_enhancement_is_loaded_after_selector_lock():
    html = (ROOT / "wwwroot/prototype/index.html").read_text(encoding="utf-8")

    lock = html.index("spatial-selector-lock.js")
    enhancements = html.index("spatial-selection-enhancements.js")
    assert enhancements > lock


def test_select_area_forces_real_tier_zero_before_freeze():
    source = (ROOT / "wwwroot/prototype/spatial-selection-enhancements.js").read_text(encoding="utf-8")

    assert "setExternalDepth?.({...raw,tier:0,layer:0})" in source
    assert source.index("setExternalDepth?.({...raw,tier:0,layer:0})") < source.index("beginSpatialSelection?.(raw)")


def test_selection_outline_is_composited_and_autofill_closes_holes():
    source = (ROOT / "wwwroot/prototype/spatial-selection-enhancements.js").read_text(encoding="utf-8")

    assert "function filledSelection(snapshot)" in source
    assert "if(!selected.has(cell)&&!outside.has(cell))filled.add(cell);" in source
    assert "feMorphology" in source
    assert 'operator="out"' in source
    assert "data-selection-enhanced" in source


def test_right_display_controls_autofill_and_border_palette():
    source = (ROOT / "wwwroot/prototype/spatial-selection-enhancements.js").read_text(encoding="utf-8")

    assert "SELECTION OPTIONS" in source
    assert "AUTOFILL ·" in source
    assert "BORDER ·" in source
    assert "SWIPE ↔ BORDER · TOUCH TOGGLE" in source
    assert "SWIPE ↔ AUTOFILL · TOUCH COLOR" in source
    for label in ("GOLD", "SILVER", "CYAN", "MAGENTA", "WHITE", "BLACK"):
        assert f"label:'{label}'" in source
