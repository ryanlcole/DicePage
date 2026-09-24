from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_local_staging_is_live_and_reuses_region_projection():
    shell = read("Components/PublicAlphaShell.razor")
    router = read("Components/TaskWorkspaceRouter.razor")
    local = read("Components/LocalDefinerWorkspace.razor")

    assert '<strong>LOCAL STAGING</strong>' in shell
    assert '@onclick="OpenLocalStaging"' in shell
    assert 'case "local"' in shell
    assert 'OpenWorkspace("local","LOCAL DEFINER"' in shell
    assert 'Mode == "local"' in router
    assert "<LocalDefinerWorkspace" in router

    assert "Session.LoadRegionSourceAsync(region.RegionId)" in local
    assert "mode=localdefiner" in local
    assert "regionFlow=existing" in local


def test_local_selects_one_existing_regional_object_not_region_cells():
    player = read("wwwroot/prototype/prototype.js")
    local = read("Components/LocalDefinerWorkspace.razor")

    assert "const LOCAL_DEFINER=WORKSPACE_MODE===\'localdefiner\';" in player
    assert "select one placed regional object" in player
    assert "Select regional object for Local" in player
    assert "createSelectedLocal" in player
    assert "localAnchorPayload" in player
    assert "data.type===\'local-created\'" in player

    assert "CreateLocalFromPrototypeAsync" in local
    assert "Session.CreateLocalAsync" in local
    assert "SubmitRegionClaimRequestFromPrototypeAsync" not in local


def test_representation_ladder_is_world_0_region_15_local_30():
    player = read("wwwroot/prototype/prototype.js")
    shell = read("Components/PublicAlphaShell.razor")

    assert "const REPRESENTATION_ANGLE_DEGREES=LOCAL_DEFINER?30:REGION_DEFINER?15:0;" in player
    assert "rotateX(${REPRESENTATION_ANGLE_DEGREES}deg)" in player
    assert "REGION 15° → OBJECT → LOCAL 30° → INSTANCE 45°" in shell
    assert "WORLD 0° → REGION 15°" in shell


def test_local_exposes_region_z_depth_instead_of_flat_region_editing():
    player = read("wwwroot/prototype/prototype.js")

    assert "REGION_DEFINER&&!LOCAL_DEFINER&&regionDeedIsComplete()" in player
    assert "regionWorldLayer(item)*.10" in player
    assert "regionOverlayLayer(item)*.01" in player
    assert "const representationDepth=LOCAL_DEFINER?2:1;" in player


def test_local_identity_is_object_anchored_and_persistent():
    model = read("WorldSession.Locals.cs")

    assert "AnchorObjectId" in model
    assert "AnchorAssetId" in model
    assert 'ParentNodeId: $"region:{region.RegionId}"' in model
    assert '"local-anchor-normalized-v2"' in model
    assert "Select a placed regional object for the Local." in model
    assert "SaveLocalsAsync" in model


def test_local_claim_rebases_selected_region_asset_to_full_local_canvas():
    player = read("wwwroot/prototype/prototype.js")
    local = read("Components/LocalDefinerWorkspace.razor")
    model = read("WorldSession.Locals.cs")

    assert "function localAnchorBounds(local=activeLocal)" in player
    assert "function worldPointToLocal(x,y,local=activeLocal)" in player
    assert "function localPointToWorld(x,y,local=activeLocal)" in player
    assert "local-anchor-normalized-v2" in player
    assert "item.node.style.width='100%'" in player
    assert "item.node.style.height='100%'" in player
    assert "The Region asset is the locked 100% Local base" in player
    assert 'coordinateSpace="local-anchor-normalized-v2"' in local
    assert '"local-anchor-normalized-v2"' in model
    assert "X: Math.Clamp(x, 0, 1)" in model
    assert "Y: Math.Clamp(y, 0, 1)" in model


def test_local_parent_region_depth_is_inherited_and_children_use_local_depth():
    player = read("wwwroot/prototype/prototype.js")

    assert "function applyLocalAddress(item,tier=localTierIndex,layer=localLayerIndex)" in player
    assert "item.regionTier=Math.max(0,Math.trunc(Number(activeLocal.regionTier)||0));" in player
    assert "item.regionLayer=clamp(Math.trunc(Number(activeLocal.regionLayer)||1),1,9);" in player
    assert "item.localTier=Math.max(0,Math.trunc(Number(item.localTier??tier)||0));" in player
    assert "item.localLayer=clamp(Math.trunc(Number(item.localLayer??layer)||0),0,9);" in player
    assert "toolKey('LOCAL T −'" in player
    assert "toolKey('LOCAL L +'" in player


def test_local_children_persist_local_xy_and_derived_world_projection():
    player = read("wwwroot/prototype/prototype.js")
    local = read("Components/LocalDefinerWorkspace.razor")

    assert "localCoordinateSpace:item.localOverlay?'local-anchor-normalized-v2':undefined" in player
    assert "projectedWorldX:item.localOverlay?localPointToWorld(item.x,item.y).x:undefined" in player
    assert "projectedWorldY:item.localOverlay?localPointToWorld(item.x,item.y).y:undefined" in player
    assert 'format="RIST_LOCAL_MAP_V2"' in local
    assert "hierarchy=new" in local
    for field in (
        "worldTier=local.WorldTier",
        "worldLayer=local.WorldLayer",
        "regionTier=local.RegionTier",
        "regionLayer=local.RegionLayer",
        "localTier=local.LocalTier",
        "localLayer=local.LocalLayer",
        "instanceTier=local.InstanceTier",
        "instanceLayer=local.InstanceLayer",
    ):
        assert field in local


def test_local_map_is_persisted_separately_from_region_map():
    local = read("Components/LocalDefinerWorkspace.razor")
    model = read("WorldSession.Locals.cs")
    bridge = read("wwwroot/region-definer-host.js")
    player = read("wwwroot/prototype/prototype.js")

    assert "GetLocalSourceForPrototypeAsync" in local
    assert "SaveLocalMapLayersFromPrototypeAsync" in local
    assert "LoadLocalMapAsync" in model
    assert "SaveLocalMapAsync" in model
    assert 'data.type==="save-map-local"' in bridge
    assert "function saveLocalMapToDatabase(userLayers)" in player
    assert "map-local-saved" in player


def test_local_opens_full_asset_toolset_after_region_anchor_selection():
    player = read("wwwroot/prototype/prototype.js")

    assert "if(LOCAL_DEFINER)return localIsOpen()?BASE_KEYBOARD_MODES:['Viewer','Tiers','Select'];" in player
    assert "OPEN LOCAL" in player
    assert "CREATE LOCAL" in player
    assert "await enterLocalBuild(local,data.localSource||null)" in player
    assert "item.localOverlay=true" in player
    assert "ensureLocalEditLayer" in player
