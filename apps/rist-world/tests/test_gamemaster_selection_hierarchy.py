from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def test_shaelvien_deeds_expand_only_across_flat_sides():
    land = (ROOT / "WorldSession.MmoLand.cs").read_text(encoding="utf-8")
    gate = (ROOT / "Components/ShaelvienDeedGate.razor").read_text(encoding="utf-8")

    assert "flatSides" in land
    assert "(0, -1)" in land
    assert "(1, 0)" in land
    assert "(0, 1)" in land
    assert "(-1, 0)" in land
    assert "not yet connected to the claim frontier" in gate


def test_gamemaster_worldbuilder_enters_one_continuous_space():
    component = (ROOT / "Components/UniversalInterface.razor").read_text(encoding="utf-8")

    assert 'GameMasterPaths=["WORLD BUILDER","CONTEXT"]' in component
    begin = component[component.index("void BeginGameMasterPath()"):component.index("void SelectArtMethod()")]
    assert "_stage=Stage.WorldHome;" in begin
    assert "World Builder is one continuous space." in begin
    assert "Stage.GameMasterScope" not in begin


def test_zoom_scope_is_resolution_not_a_separate_editor():
    component = (ROOT / "Components/UniversalInterface.razor").read_text(encoding="utf-8")

    begin = component[component.index("void BeginBuilderScope"):component.index("void SelectActiveSpatialOption")]
    assert "resolution label, not a separate editor" in begin
    assert "_regionDefinerOpen=true" not in begin
    assert "_stage=Stage.SpatialSelect" not in begin
    assert "_stage=Stage.WorldHome" in begin


def test_selected_spatial_identity_is_persisted_with_assets():
    component = (ROOT / "Components/UniversalInterface.razor").read_text(encoding="utf-8")
    bridge = (ROOT / "wwwroot/worldbuilder-source-host.js").read_text(encoding="utf-8")
    prototype = (ROOT / "wwwroot/prototype/prototype.js").read_text(encoding="utf-8")

    assert "spatialNodeId=CurrentSpatialNodeId" in component
    assert "Session.ActiveSpatialRegion?.NodeId" in component
    assert 'setDepth(frame,tier,layer,scope,spatialNodeId="",spatialPath="")' in bridge
    assert "spatialNodeId:String(item.spatialNodeId||'')" in prototype
    assert "spatialPath:String(item.spatialPath||'')" in prototype
    assert "lineage.includes(nodeId)" in prototype


def test_owner_inspect_and_account_world_list_are_separate_from_claiming():
    component = (ROOT / "Components/UniversalInterface.razor").read_text(encoding="utf-8")
    mmo = (ROOT / "Components/UniversalInterface.MmoMap.cs").read_text(encoding="utf-8")
    authority = (ROOT / "WorldSession.WorldAuthority.cs").read_text(encoding="utf-8")
    workflow = (REPO / ".github/workflows/deploy-rist-platform.yml").read_text(encoding="utf-8")
    discord = (REPO / "infra/aws/rist-discord-storage.yml").read_text(encoding="utf-8")

    assert "Session.TrustedPlatformOwner" in component
    assert "Session.TrustedPlatformDeveloper" in component
    assert '"__endemar__"' in component
    assert '"__inspect__"' in component
    assert '"__explore__"' in component
    assert "Auth.IsOwnerDiscordAccount" not in component
    assert "profile?.PlatformOwner == true" in authority
    assert '"access.developer"' in authority

    formula = 'uuid.uuid5(uuid.NAMESPACE_URL, "rist:discord:" + discord_id)'
    assert formula in workflow
    assert formula in discord
    assert 'OWNER_USER_ID="$DERIVED_OWNER_USER_ID"' in workflow

    assert "OpenMmoInspectEditorAsync" in mmo
    assert "_inspectionEditMode = true;" in mmo
    assert "_stage = Stage.PathSelect;" in mmo
    assert "Developer Inspect authority is required." in mmo
