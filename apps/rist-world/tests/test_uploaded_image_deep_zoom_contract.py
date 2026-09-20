from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_deep_zoom_is_relative_to_the_fitted_world_view():
    source = read("wwwroot/prototype/prototype.js")
    assert "const MAX_VIEW_ZOOM_RATIO=256;" in source
    assert "function recomputeMaxViewScale()" in source
    assert "maxScale=Math.max(minScale*MAX_VIEW_ZOOM_RATIO,8);" in source
    fit = source[source.index("function fitMap()"):source.index("function zoomAt(")]
    assert "recomputeMaxViewScale();" in fit
    upscale = source[source.index("async function applyUpscalePreference()"):source.index("function canvasBlob(")]
    assert "recomputeMaxViewScale();" in upscale


def test_uploaded_images_do_not_disappear_when_they_fill_the_viewport():
    source = read("wwwroot/prototype/prototype.js")
    block = source[source.index("function prepareZoomCollision"):source.index("function userCollision")]
    assert "passUserImage" not in block
    assert "Filling the viewport is not a semantic boundary" in block


def test_prototype_script_cache_key_moves_with_the_zoom_fix():
    html = read("wwwroot/prototype/index.html")
    assert "prototype.js?v=20260920-deep-image-zoom-1" in html
