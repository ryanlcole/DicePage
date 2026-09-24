from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_local_staging_chooses_local_zone_grouped_by_region():
    shell = read("Components/PublicAlphaShell.razor")
    router = read("Components/TaskWorkspaceRouter.razor")
    local = read("Components/LocalDefinerWorkspace.razor")
    gate = read("Components/LocalGate.razor")

    assert '<strong>LOCAL STAGING</strong>' in shell
    assert '@onclick="OpenLocalStaging"' in shell
    assert '<LocalGate Open="@_localGateOpen"' in shell
    assert '<h1>CHOOSE A LOCAL ZONE</h1>' in gate
    assert "NEW LOCAL" in gate
    assert "LocalGroups" in gate
    assert "new LocalGroup(" in gate
    assert "OpenSavedLocal(WorldLocal local)" in shell
    assert "Session.SetActiveLocal(local.LocalId);" in shell
    assert 'case "local"' in shell
    assert '"world","local","accessibility"' in shell
    assert 'Session.SetActiveRegion("");' in shell
    assert 'Session.SetActiveLocal("");' in shell
    assert 'OpenWorkspace("local","LOCAL DEFINER","REGION → ASSET → LOCAL · 30°")' in shell
    assert '_localRegionGateOpen' not in shell
    assert 'SelectionOnly="true"' not in shell
    assert 'Mode == "local"' in router
    assert "<LocalDefinerWorkspace" in router
    assert "Session.LoadRegionSourceAsync(region.RegionId)" in local
    assert "mode=localdefiner" in local
    assert "regionFlow=existing&regionId=" in local


def test_local_selects_region_then_asset_instead_of_parent_region_gate():
    player = read("wwwroot/prototype/prototype.js")
    local = read("Components/LocalDefinerWorkspace.razor")
    bridge = read("wwwroot/region-definer-host.js")

    assert "const LOCAL_DEFINER=WORKSPACE_MODE==='localdefiner';" in player
    assert "function ensureLocalRegionPreview()" in player
    assert "Choose the Region, then select the asset that becomes the Local zone." in player
    assert "postRegionMessage('open-local-region'" in player
    assert "data.type==='local-region-opened'" in player
    assert "Select Region asset for Local zone" in player
    assert "select one asset to become the Local zone" in player
    assert "createSelectedLocal" in player
    assert "localAnchorPayload" in player
    assert 'data.type==="open-local-region"' in bridge
    assert "OpenLocalRegionForPrototypeAsync" in local
    assert "LocalRegions.Select(DescribeRegion).ToList()" in local
    assert "CreateLocalFromPrototypeAsync" in local
    assert "Session.CreateLocalAsync" in local
    assert "SubmitRegionClaimRequestFromPrototypeAsync" not in local


def test_local_parent_region_assets_are_locked_but_selectable_as_local_anchors():
    player = read("wwwroot/prototype/prototype.js")

    assert "sourceLocked:LOCAL_DEFINER||READ_ONLY" in player
    assert "sourceLocked:READ_ONLY||!localRegionEditable" in player
    assert "persistentSave.hidden=READ_ONLY||!localRegionEditable" in player
    assert "function isLocalAnchorCandidate(item)" in player
    assert "item.sourceLocked&&!isLocalAnchorCandidate(item)?'none'" in player
    assert "const localAnchorCandidate=isLocalAnchorCandidate(item);" in player
    assert "if(LOCAL_DEFINER&&!localIsOpen()){event.preventDefault();event.stopPropagation();selectUserImage(item);return;}" in player


def test_saved_local_rehydrates_parent_region_before_opening_anchor():
    shell = read("Components/PublicAlphaShell.razor")
    local = read("Components/LocalDefinerWorkspace.razor")
    player = read("wwwroot/prototype/prototype.js")

    assert "Session.SetActiveRegion(local.RegionId);" in shell
    assert "Session.SetActiveLocal(local.LocalId);" in shell
    assert "_initialLocalId=local.LocalId;" in local
    assert "_initialRegionId=local.RegionId;" in local
    assert "localId={localId}" in local
    assert "const REQUESTED_LOCAL_ID=String(QUERY.get('localId')||'');" in player
    assert "function maybeOpenRequestedLocal()" in player
    assert "localRegionSourceReady" in player
    assert "if(LOCAL_DEFINER)localRegionSourceReady=true;" in player
    assert "postRegionMessage('open-local',{localId:REQUESTED_LOCAL_ID})" in player


def test_representation_ladder_is_world_0_region_15_local_30():
    player = read("wwwroot/prototype/prototype.js")
    shell = read("Components/PublicAlphaShell.razor")

    assert "const REPRESENTATION_ANGLE_DEGREES=LOCAL_DEFINER?30:REGION_DEFINER?15:0;" in player
    assert "rotateX(${REPRESENTATION_ANGLE_DEGREES}deg)" in player
    assert "REGION 15° → OBJECT → LOCAL 30° → INSTANCE 45°" in shell
    assert "WORLD 0° → REGION 15°" in shell


def test_local_identity_is_region_object_anchored_and_uses_constant_canonical_xy():
    model = read("WorldSession.Locals.cs")
    local = read("Components/LocalDefinerWorkspace.razor")

    assert "AnchorObjectId" in model
    assert "AnchorAssetId" in model
    assert 'ParentNodeId: $"region:{region.RegionId}"' in model
    assert '"canonical-world-xy+hierarchical-depth-v1"' in model
    assert 'coordinateSpace="canonical-world-xy+hierarchical-depth-v1"' in local
    assert 'coordinateSpace="canonical-world-xy+region-depth-v1"' in local
    assert "X: Math.Clamp(x, 0, 1)" in model
    assert "Y: Math.Clamp(y, 0, 1)" in model
    assert "Select a placed regional object for the Local." in model


def test_local_camera_frames_region_asset_without_creating_a_new_xy_plane():
    player = read("wwwroot/prototype/prototype.js")

    assert "function localAnchorBounds(local=activeLocal)" in player
    assert "function constrainLocalPoint(x,y)" in player
    assert "function fitLocalAnchor(local=activeLocal)" in player
    assert "const cropX=bounds.minX*naturalWidth" in player
    assert "const cropY=bounds.minY*naturalHeight" in player
    assert "const cropW=Math.max(1,bounds.width*naturalWidth)" in player
    assert "canonical X within Local anchor" in player
    # Local does not create a second active X/Y authority. The one remaining
    # localPointToWorld helper exists only to migrate a short-lived experimental
    # local-normalized save format back into canonical World X/Y.
    assert "worldPointToLocal" not in player
    assert "function localPointToWorld(x,y,local=activeLocal)" in player
    assert "sourceWasLocalNormalized" in player
    assert "setLocalCanvasFromAnchor" not in player


def test_local_parent_region_depth_is_inherited_and_children_use_local_depth():
    player = read("wwwroot/prototype/prototype.js")

    assert "function applyLocalAddress(item,tier=localTierIndex,layer=localLayerIndex)" in player
    assert "item.regionTier=Math.max(0,Math.trunc(Number(activeLocal.regionTier)||0));" in player
    assert "item.regionLayer=clamp(Math.trunc(Number(activeLocal.regionLayer)||1),1,9);" in player
    assert "item.localTier=Math.max(0,Math.trunc(Number(item.localTier??tier)||0));" in player
    assert "item.localLayer=clamp(Math.trunc(Number(item.localLayer??layer)||1),1,9);" in player
    assert "toolKey('LOCAL T −'" in player
    assert "toolKey('LOCAL T +'" in player
    assert "toolKey('LOCAL L −'" in player
    assert "toolKey('LOCAL L +'" in player


def test_local_children_persist_canonical_xy_plus_full_hierarchical_depth():
    player = read("wwwroot/prototype/prototype.js")
    local = read("Components/LocalDefinerWorkspace.razor")

    assert "x:clamp(Number(item.x)||0,0,1)" in player
    assert "y:clamp(Number(item.y)||0,0,1)" in player
    assert 'format="RIST_LOCAL_MAP_V2"' in local
    assert 'coordinateSpace="canonical-world-xy+hierarchical-depth-v1"' in local
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


def test_local_opens_full_regiondefiner_asset_toolset_after_anchor_selection():
    player = read("wwwroot/prototype/prototype.js")

    assert "if(LOCAL_DEFINER)return localIsOpen()?((localRegionEditable&&!READ_ONLY)?BASE_KEYBOARD_MODES:['Viewer','Tiers','Select']):(activeRegionMapId()?['Viewer','Tiers','Select']:['Select']);" in player
    assert "OPEN LOCAL" in player
    assert "CREATE LOCAL" in player
    assert "toolKey('REGIONS','change Region'" in player
    assert "await enterLocalBuild(local,data.localSource||null)" in player
    assert "item.localOverlay=true" in player
    assert "ensureLocalEditLayer" in player


def test_local_and_future_instance_depth_participate_in_renderer_order():
    player = read("wwwroot/prototype/prototype.js")

    assert "Math.max(0,Math.trunc(Number(item.localTier)||0))*1000" in player
    assert "clamp(Math.trunc(Number(item.localLayer)||1),1,9)*100" in player
    assert "Math.max(0,Math.trunc(Number(item.instanceTier)||0))*10" in player
    assert "clamp(Math.trunc(Number(item.instanceLayer)||0),0,9)" in player
