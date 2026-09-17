from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_cloudfront_rewrites_directory_routes_before_spa_fallback():
    template = (ROOT / "infra/aws/rist-frontend.yml").read_text(encoding="utf-8")
    assert "DirectoryIndexRewrite:" in template
    assert "if (uri.endsWith('/'))" in template
    assert "request.uri = uri + 'index.html';" in template
    assert "EventType: viewer-request" in template
    assert "FunctionARN: !GetAtt DirectoryIndexRewrite.FunctionARN" in template


def test_store_has_real_empty_catalog_not_invented_products():
    catalog = json.loads((ROOT / "site/relic-home/store/catalog.json").read_text(encoding="utf-8"))
    assert catalog["storeStatus"] == "invite-preview"
    assert catalog["invitationsIssued"] is False
    assert catalog["products"] == []
    store = (ROOT / "site/relic-home/store/index.html").read_text(encoding="utf-8")
    assert "ReLiC Creator Store" in store
    assert "No creator packs are published yet." in store


def test_entry_identifies_discord_and_has_return_path():
    entry = (ROOT / "site/relic-home/Play/index.html").read_text(encoding="utf-8")
    assert "SIGN IN WITH DISCORD" in entry
    assert "CREATE ACCOUNT WITH DISCORD" in entry
    assert 'href="/">RETURN TO RELICGAMEMASTER.COM</a>' in entry
    assert "Friends &amp; Family Alpha" in entry
    assert "Wider public testing in preparation" in entry


def test_canonical_game_route_remains_game_index():
    home = (ROOT / "site/relic-home/index.html").read_text(encoding="utf-8")
    assert 'href="/Game/index.html">Game Now</a>' in home
    assert 'href="/Game/index.html">Enter Shaelvien</a>' in home
