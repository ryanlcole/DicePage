from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def text(path):
    return (REPO / path).read_text(encoding="utf-8")


def test_universal_mmo_map_flattens_tier_zero_and_keeps_frontier_selectable():
    interface = text("apps/rist-world/Components/UniversalInterface.razor")
    mmo = text("apps/rist-world/Components/UniversalInterface.MmoMap.cs")
    session = text("apps/rist-world/WorldSession.MmoLand.cs")

    assert "Stage.MmoMap" in interface
    assert "mmo-inline-map" in interface
    assert "MmoCanonicalSurfaceUrl" in mmo
    assert 'JsonInt(item, "tier", 0)' in mmo
    assert "if (tier != 0) continue;" in mmo
    assert "layer.Layer > current.Layer" in mmo
    assert "Session.IsMmoParcelOpen(cell)" in mmo
    assert "MoveMmoSelection(direction,0)" in interface
    assert "MoveMmoSelection(0,-direction)" in interface
    assert "ReadOnlySpan<(int Dx, int Dy)> flatSides" in session
    assert "(0, -1)" in session
    assert "(1, 0)" in session
    assert "(0, 1)" in session
    assert "(-1, 0)" in session


def test_universal_mmo_map_has_requested_deed_actions_and_left_rail():
    mmo = text("apps/rist-world/Components/UniversalInterface.MmoMap.cs")
    input_js = text("apps/rist-world/wwwroot/universal-interface-input.js")

    assert '"ENTER COORDINATES"' in mmo
    assert '"ENTER USER ID"' in mmo
    assert '"CLAIM DEED"' in mmo
    assert '"PURCHASE TOKEN AND CLAIM DEED"' in mmo
    assert '"ROLEPLAY"' in mmo
    assert '"REQUEST DEED FROM GM"' in mmo
    assert '"BID (CURRENT BID' in mmo
    assert '"MANAGE"' in mmo
    assert 'return $"USE 1/{count} TOKEN' in mmo
    assert 'return $"CURRENT BID {bid.ToString(' in mmo
    assert '"left-slider"' in input_js
    assert '"right-slider"' in input_js


def test_private_names_and_deed_requests_remain_server_authoritative():
    backend = text("infra/aws/rist-platform-authority/app.py")
    template = text("infra/aws/rist-platform.yml")
    client = text("apps/rist-world/AwsAuthorityClient.cs")
    session = text("apps/rist-world/WorldSession.MmoLand.cs")

    assert 'name_only = visibility == "Restricted"' in backend
    assert '"displayName": str(item.get("displayName") or "")' in backend
    assert '"ownerUserId": ""' in backend
    assert 'path == "/world/parcels/request-deed"' in backend
    assert '"entityType": "deedRequest"' in backend
    assert '"status": "Pending"' in backend
    assert '"parcelId": ""' in backend
    assert '"parcel.deed.request"' in backend
    assert "Path: /world/parcels/request-deed" in template
    assert "RequestMmoDeedAsync" in client
    assert "RequestMmoDeedAsync" in session


def test_mmo_map_exposes_refund_bid_metadata_without_fake_settlement():
    backend = text("infra/aws/rist-platform-authority/app.py")
    client = text("apps/rist-world/AwsAuthorityClient.cs")
    mmo = text("apps/rist-world/Components/UniversalInterface.MmoMap.cs")

    assert '"status": str(item.get("status") or "Claimed")' in backend
    assert '"currentBid": float(item.get("currentBid") or 0)' in backend
    assert '"currentBidUsername": str(item.get("currentBidUsername") or "")' in backend
    assert 'string Status = "Claimed"' in client
    assert "decimal CurrentBid = 0m" in client
    assert 'string CurrentBidUsername = ""' in client
    assert '"Refunded"' in mmo
    assert "bid submission is not enabled until server-side auction settlement is implemented" in mmo
    assert "paid Shaelvien Token checkout is not implemented yet" in mmo
