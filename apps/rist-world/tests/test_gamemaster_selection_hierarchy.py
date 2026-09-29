from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_shaelvien_deeds_expand_only_across_flat_sides():
    land = (ROOT / "WorldSession.MmoLand.cs").read_text(encoding="utf-8")
    gate = (ROOT / "Components/ShaelvienDeedGate.razor").read_text(encoding="utf-8")

    assert "flatSides" in land
    assert "(0, -1)" in land
    assert "(1, 0)" in land
    assert "(0, 1)" in land
    assert "(-1, 0)" in land
    assert "Corner-only contact is not claimable." in gate


def test_gamemaster_root_matches_worldbuilder_context_contract():
    component = (ROOT / "Components/ExperimentsWorkspace.razor").read_text(encoding="utf-8")

    assert 'GameMasterPaths=["WORLD BUILDER","CONTEXT"]' in component
    assert 'Scopes=["WORLD","REGION","LOCAL","INSTANCE","CAMPAIGN"]' in component
    assert 'ContextPath=["HISTORY","LORE","TRUTH"]' in component
    assert 'WorldBuilderPath=["WORLD","REGION","LOCAL","INSTANCE","CAMPAIGN"]' in component


def test_region_local_instance_are_selection_first():
    component = (ROOT / "Components/ExperimentsWorkspace.razor").read_text(encoding="utf-8")
    regions = (ROOT / "WorldSession.Regions.cs").read_text(encoding="utf-8")

    assert "SpatialSelect" in component
    assert "Select a Region before editing its Tier or Layer." in component
    assert "Select a Local inside the active Region before editing its Tier or Layer." in component
    assert "Select an Instance inside the active Local before editing its Tier or Layer." in component
    assert "VIEW DEPTH != EDIT DEPTH" in component
    assert "if(requested>=2&&Session.ActiveSpatialRegion is null)current=1;" in component
    assert "else if(requested>=3&&Session.ActiveLocal is null)current=2;" in component
    assert "_requestedBuilderChainIndex>_builderChainIndex" in component
    assert "BeginBuilderScope(_builderChainIndex+1,true);" in component
    assert "CreateSpatialNodeAsync" in regions
    assert 'kind is not ("REGION" or "LOCAL" or "INSTANCE")' in regions
    assert "List<WorldSpatialNode>? SpatialNodes = null" in regions


def test_selected_spatial_identity_is_persisted_with_assets():
    component = (ROOT / "Components/ExperimentsWorkspace.razor").read_text(encoding="utf-8")
    bridge = (ROOT / "wwwroot/worldbuilder-source-host.js").read_text(encoding="utf-8")
    prototype = (ROOT / "wwwroot/prototype/prototype.js").read_text(encoding="utf-8")

    assert "spatialNodeId=CurrentSpatialNodeId" in component
    assert "spatialPath=CurrentSpatialPath" in component
    assert 'setDepth(frame,tier,layer,scope,spatialNodeId="",spatialPath="")' in bridge
    assert "spatialNodeId:String(item.spatialNodeId||'')" in prototype
    assert "spatialPath:String(item.spatialPath||'')" in prototype
    assert "lineage.includes(nodeId)" in prototype


def test_owner_inspect_and_account_world_list_are_separate_from_claiming():
    component = (ROOT / "Components/ExperimentsWorkspace.razor").read_text(encoding="utf-8")
    gate = (ROOT / "Components/ShaelvienDeedGate.razor").read_text(encoding="utf-8")

    assert '"__inspect__"' in component
    assert '"__claim__"' in component
    assert "Auth.IsOwnerDiscordAccount" in component
    assert 'InspectOnly="true"' in component
    assert "[Parameter] public bool InspectOnly" in gate
    assert "Owner inspection is read-only." in gate
    assert "var x=column-WorldSession.EndemarOriginColumn;" in gate
    assert "var y=WorldSession.EndemarOriginRow-row;" in gate
