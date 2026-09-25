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



def test_local_identity_is_region_object_anchored_and_restarts_recursive_coordinates():
    model = read("WorldSession.Locals.cs")
    local = read("Components/LocalDefinerWorkspace.razor")

    assert "AnchorObjectId" in model
    assert "AnchorAssetId" in model
    assert 'ParentNodeId: $"region:{region.RegionId}"' in model
    assert '"local-root-recursive-v1"' in model
    assert "RecursiveScopeFormat: RecursiveScopeFormat" in model
    assert "ViewDegrees: 30" in model
    assert "ParentScopeId: region.RegionId" in model
    assert "ParentAssetId: anchorObjectId" in model
    assert 'coordinateSpace="local-root-recursive-v1"' in local
    assert 'scopeKind="LOCAL"' in local
    assert "x=0" in local
    assert "y=0" in local
    assert "tier=1" in local
    assert "layer=1" in local
    assert "Select a placed regional object for the Local." in model


def test_local_camera_frames_region_asset_but_recursive_local_xy_is_authoritative():
    player = read("wwwroot/prototype/prototype.js")

    assert "function localAnchorBounds(local=activeLocal)" in player
    assert "function constrainLocalPoint(x,y)" in player
    assert "function fitLocalAnchor(local=activeLocal)" in player
    assert "function localRecursivePoint(worldX,worldY,local=activeLocal)" in player
    assert "function localRecursiveWorldPoint(localX,localY,local=activeLocal)" in player
    assert "(Number(worldX)-bounds.cx)/Math.max(bounds.width,.0001)" in player
    assert "(Number(worldY)-bounds.cy)/Math.max(bounds.height,.0001)" in player
    assert "sourceIsRecursiveLocal" in player
    assert "localRecursiveWorldPoint(recursive.x,recursive.y,local)" in player
    # The older 0..1 anchor-normalized format remains read-only migration input.
    assert "function localPointToWorld(x,y,local=activeLocal)" in player
    assert "sourceWasLocalNormalized" in player


def test_local_parent_region_depth_is_reference_only_and_children_use_local_recursive_depth():
    player = read("wwwroot/prototype/prototype.js")

    assert "function applyLocalAddress(item,tier=localTierIndex,layer=localLayerIndex)" in player
    assert "function syncLocalRecursiveEnvelope" in player
    assert "item.regionTier=Math.max(1" in player
    assert "const recursiveTier=existing?localOverlayTier(item):Math.max(1" in player
    assert "nextLocalVisualLayer(item,recursiveTier)" in player
    assert "syncLocalRecursiveEnvelope(item,recursiveTier,recursiveLayer)" in player
    assert "toolKey('LOCAL T −'" in player
    assert "toolKey('LOCAL T +'" in player
    assert "toolKey('LOCAL L −'" in player
    assert "toolKey('LOCAL L +'" in player


def test_local_children_persist_recursive_xy_tier_layer_with_legacy_projection_beside_it():
    player = read("wwwroot/prototype/prototype.js")
    local = read("Components/LocalDefinerWorkspace.razor")

    serialization = player.split("function serializableUserLayer", 1)[1].split(
        "async function saveWorldBuilder", 1
    )[0]
    assert "LOCAL_DEFINER&&item.localOverlay?syncLocalRecursiveEnvelope(item)" in serialization
    assert 'format="RIST_LOCAL_MAP_V3"' in local
    assert 'recursiveScopeFormat=WorldSession.RecursiveScopeFormat' in local
    assert 'coordinateSpace="local-root-recursive-v1"' in local
    assert "recursiveScope=new" in local
    assert "legacyHierarchy=new" in local

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



def test_local_visual_order_uses_layer_only_and_tier_is_parallax_only():
    player = read("wwwroot/prototype/prototype.js")

    stack = player.split("function assetSemanticStackTuple", 1)[1].split(
        "function compareStackTuple", 1
    )[0]
    local_branch = stack.split("if(LOCAL_DEFINER&&item?.localOverlay)", 1)[1].split(
        "if(REGION_DEFINER&&item?.regionOverlay)", 1
    )[0]
    assert "return[pin,localOverlayLayer(item),index]" in local_branch
    assert "localOverlayTier(item)" not in local_branch

    parallax = player.split("function applyParallax()", 1)[1].split(
        "function updateReadouts", 1
    )[0]
    assert "Math.max(0,localOverlayTier(item)-1)" in parallax

def test_local_catalog_deduplicates_by_region_anchor_and_supports_guarded_delete():
    model = read("WorldSession.Locals.cs")
    gate = read("Components/LocalGate.razor")
    shell = read("Components/PublicAlphaShell.razor")

    assert "static List<WorldLocal> CanonicalLocals" in model
    assert '"ANCHOR\\u001f{regionId}\\u001f{anchorId}"' in model
    assert "CanonicalLocals(catalog.Locals ?? [])" in model
    assert "var canonical = CanonicalLocals(_locals);" in model
    assert "public async Task<int> DeleteLocalAsync(WorldLocal local)" in model
    assert "Region edit authority is required to delete this Local." in model
    assert "localStorage.removeItem" in model

    assert "OnDelete" in gate
    assert "DELETE?" in gate
    assert "Tap DELETE? again" in gate
    assert "DeleteAsync(WorldLocal local)" in gate
    assert 'OnDelete="DeleteSavedLocal"' in shell
    assert "await Session.DeleteLocalAsync(local);" in shell
