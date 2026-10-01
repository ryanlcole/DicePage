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
    assert "MmoCellSurfaceUrl(cell)" in interface
    assert 'class="mmo-deed-cell-surface"' in interface
    assert 'class="mmo-inline-map-base"' not in interface
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
    interface = text("apps/rist-world/Components/UniversalInterface.razor")
    mmo = text("apps/rist-world/Components/UniversalInterface.MmoMap.cs")
    input_js = text("apps/rist-world/wwwroot/universal-interface-input.js")

    assert '"ENTER COORDINATES"' in mmo
    assert '"ENTER USER ID"' in mmo
    assert '"CLAIM"' in mmo
    assert '"PURCHASE TOKEN AND CLAIM"' in mmo
    assert '"EDIT"' in mmo
    assert '"VIEW"' in mmo
    assert '"ROLEPLAY"' in mmo
    assert '"INSPECT"' in mmo
    assert '"PRIVATE"' in mmo
    assert '"BID (CURRENT BID' in mmo
    assert '"MANAGE"' in mmo
    assert "MmoRightChoices" in mmo
    assert "MmoSelectedHasExplicitEditPermission" in mmo
    assert "MmoSelectedIsOwned || MmoSelectedHasExplicitEditPermission" in mmo
    assert "Session.TrustedPlatformDeveloper" in mmo
    assert '"private" => "TOUCH · ENTER CODE FROM GM"' in mmo
    assert "Stage.MmoMap=>MmoRightOptionCount" in interface
    assert "if(_stage==Stage.MmoMap)CycleMmoRightOption(direction);" in interface
    assert "MoveMmoSelection(direction,0)" in interface
    assert 'return $"BID (CURRENT BID {bid.ToString(' in mmo
    assert '"left-slider"' in input_js
    assert '"right-slider"' in input_js


def test_endemar_inherits_canonical_geanaph_owner_authority():
    interface = text("apps/rist-world/Components/UniversalInterface.razor")
    mmo = text("apps/rist-world/Components/UniversalInterface.MmoMap.cs")
    session = text("apps/rist-world/WorldSession.MmoLand.cs")
    source = text("apps/rist-world/WorldSession.WorldBuilderSource.cs")

    # Canonical Geonaph ownership is the persisted account bridge for Endemar.
    assert "public bool OwnsCanonicalGeonaphZone" in session
    assert "IsMmoParcelOwnedByCurrentUser(GeonaphCanonicalCell)" in session

    # The deed map, owned-zone rail, and world selector must all honor that bridge.
    assert "|| Session.OwnsCanonicalGeanaphZone" in mmo
    assert "var endemarOwner=platformOwner||Session.OwnsCanonicalGeanaphZone;" in interface
    assert "if(endemarOwner)" in interface

    # Opening Endemar through the controller must pass edit mode to the embedded
    # World Builder, and the authoritative save path must accept the same proof.
    assert 'string.Equals(_selectedDeedKind,"SHAELVIEN_ORIGIN",StringComparison.OrdinalIgnoreCase)' in interface
    assert "&&Session.OwnsCanonicalGeanaphZone" in interface
    assert "&&(IsGeonaphWorld && OwnsCanonicalGeanaphZone)" not in source
    assert "&& !(IsGeonaphWorld && OwnsCanonicalGeanaphZone)" in source


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


def test_inline_inspect_manage_can_open_selection_first_worldbuilder():
    interface = text("apps/rist-world/Components/UniversalInterface.razor")
    mmo = text("apps/rist-world/Components/UniversalInterface.MmoMap.cs")

    assert '@onclick="OpenMmoInspectEditorAsync"' in interface
    assert "OPEN WORLD BUILDER" in interface
    assert "@if(!MmoSelectedIsEndemar)" in interface
    assert "async Task OpenMmoInspectEditorAsync()" in mmo
    assert "if (!_mmoInspectMode || !Session.TrustedPlatformDeveloper)" in mmo
    assert "if (MmoSelectedIsEndemar)" in mmo
    assert 'new ControllerWorldOption(' in mmo
    assert '"__endemar__"' in mmo
    assert "_inspectionEditMode = true;" in mmo
    assert "_inspectionEditReason = reason.Length > 500 ? reason[..500] : reason;" in mmo
    assert "_stage = Stage.PathSelect;" in mmo
    assert "Every committed edit requires an audit reason." in mmo
    assert "await EnterMmoMapAsync(inspect:true);" in interface


def test_gamemaster_deed_map_isolates_stale_geanaph_viewer_state():
    interface = text("apps/rist-world/Components/UniversalInterface.razor")
    mmo = text("apps/rist-world/Components/UniversalInterface.MmoMap.cs")

    assert 'if(_stage is Stage.Environment or Stage.Role or Stage.DeedSelect or Stage.MmoMap or Stage.HistoryCampaign or Stage.ContextSelect)' in interface
    assert 'return "about:blank";' in interface
    assert "public async Task RequestHomeFromPrototypeAsync()" in interface
    assert "Stage.HistoryCampaign or Stage.PathSelect or Stage.ContextSelect" in interface
    assert "background child must never eject the player" in interface
    assert 'Session.SetActiveRegion("");' in mmo
    assert "previously opened zone" in mmo


def test_worldbuilder_home_messages_are_scoped_to_current_deed_document():
    interface = text("apps/rist-world/Components/UniversalInterface.razor")
    prototype = text("apps/rist-world/wwwroot/prototype/prototype.js")
    host = text("apps/rist-world/wwwroot/worldbuilder-source-host.js")

    assert "deedId:DEED_ID" in prototype
    assert "deedRegionId:DEED_REGION_ID" in prototype
    assert "deedZoneId:DEED_ZONE_ID" in prototype
    assert "seed:WORLD_SEED" in prototype
    assert "function messageMatchesCurrentFrame(frame,data)" in host
    assert 'if(!messageMatchesCurrentFrame(frame,data))return;' in host
    assert "20261001-deed-home-scope-1" in interface
