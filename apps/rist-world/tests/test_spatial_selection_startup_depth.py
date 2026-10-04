from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_selection_uses_large_ten_by_ten_hexes():
    depth = (ROOT / "wwwroot/prototype/spatial-depth-authority.js").read_text(encoding="utf-8")
    session = (ROOT / "wwwroot/prototype/spatial-selection-session.js").read_text(encoding="utf-8")

    assert "gridShape:'hex'" in depth
    assert "columns:10" in depth
    assert "rows:10" in depth
    assert "gridShape:'hex'" in session
    assert "columns:10" in session
    assert "rows:10" in session
    assert "baseApi?.beginSpatialSelection?.(options)" in session


def test_initial_parent_depth_is_reapplied_after_selector_startup_frames():
    depth = (ROOT / "wwwroot/prototype/spatial-depth-authority.js").read_text(encoding="utf-8")

    assert "function settleDepth(payload)" in depth
    assert "requestAnimationFrame" in depth
    assert "setTimeout" in depth
    assert "120" in depth
    assert "if(active)settleDepth(payload);" in depth
    assert "cancelDepthSettlement();" in depth
