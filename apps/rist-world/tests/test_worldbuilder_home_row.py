from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAV = ROOT / "Components" / "WorldCoordinateNavigator.razor"


def mobile_css(source: str) -> str:
    marker = "@@media(max-width:760px)"
    assert marker in source
    return source.split(marker, 1)[1]


def test_mobile_home_row_is_one_non_scrolling_coordinate_grid():
    source = NAV.read_text()
    mobile = mobile_css(source)
    assert "display:grid" in mobile
    assert "grid-template-columns:minmax(52px,1.1fr) repeat(3,minmax(0,.9fr)) minmax(54px,1.1fr)" in mobile
    assert "overflow:hidden" in mobile
    assert "touch-action:manipulation" in mobile
    assert "justify-content:flex-start" not in mobile
    assert ".axis-control{min-width:106px}" not in mobile


def test_mobile_axis_buttons_use_compact_screen_space_cells():
    source = NAV.read_text()
    mobile = mobile_css(source)
    assert ".axis-control{box-sizing:border-box;min-width:0;width:auto;display:grid" in mobile
    assert "grid-template-columns:minmax(0,1fr) 12px minmax(0,1fr)" in mobile
    assert ".axis-control button{width:100%;min-width:0" in mobile
    assert "width:44px;min-width:44px" not in mobile
    assert "min-height:44px" in mobile


def test_home_row_keeps_coordinate_and_height_context_visible():
    source = NAV.read_text()
    assert '<small>COORD</small><strong>@Session.CubeX,@Session.CubeY,@Session.CubeZ</strong>' in source
    assert '<small>HEIGHT</small><strong>@HeightLabel</strong>' in source
    assert 'aria-label="X coordinate navigation"' in source
    assert 'aria-label="Y coordinate navigation"' in source
    assert 'aria-label="Z coordinate navigation"' in source


def test_ultra_narrow_home_row_remains_bounded():
    source = NAV.read_text()
    assert "@@media(max-width:340px)" in source
    narrow = source.split("@@media(max-width:340px)", 1)[1]
    assert "grid-template-columns:minmax(46px,1fr) repeat(3,minmax(0,.85fr)) minmax(48px,1fr)" in narrow
    assert ".coordinate-readout small,.height-readout small{display:none}" in narrow
