from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_public_launcher_uses_page_scroll_instead_of_fixed_nested_scroller():
    shell_css = text("Components/PublicAlphaShell.razor.css")
    auth = text("Components/AuthenticatedWorld.razor")

    assert "position:relative;inset:auto;width:100%;height:auto;min-height:100dvh" in shell_css
    assert "overflow-y:visible" in shell_css
    assert "touch-action:pan-y" in shell_css

    assert ".rist-authenticated-body:has(.launcher-hub)" in auth
    assert "overflow-y:auto!important" in auth
    assert "-webkit-overflow-scrolling:touch!important" in auth
    assert "height:auto!important" in auth
    assert "min-height:100%!important" in auth
    assert "overflow:visible!important" in auth
