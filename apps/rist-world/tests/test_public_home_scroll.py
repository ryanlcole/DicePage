from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_public_home_links_to_standalone_creator_info_page():
    shell = text("Components/PublicAlphaShell.razor")
    info = text("wwwroot/info.html")

    assert 'NavigateTo("info.html",forceLoad:true)' in shell
    assert "ABOUT / CREATOR" in shell
    assert 'id="creator-profile"' not in shell
    assert '<section class="profile-card">' in info
    assert "Ryan Leigh Cole" in info
    assert "Creator of ReLiCGameMaster, Shaelvien, and RIST." in info


def test_public_home_uses_original_mobile_scroll_container():
    shell_css = text("Components/PublicAlphaShell.razor.css")
    auth = text("Components/AuthenticatedWorld.razor")

    assert "position:fixed;inset:0;width:100%;height:100dvh" in shell_css
    assert "overflow-y:auto" in shell_css
    assert "-webkit-overflow-scrolling:touch" in shell_css
    assert ".rist-authenticated-body .launcher-hub{position:absolute!important" in auth
