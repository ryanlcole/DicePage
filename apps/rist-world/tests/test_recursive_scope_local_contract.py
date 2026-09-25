from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def prototype() -> str:
    return read("wwwroot/prototype/prototype.js")


def test_local_scope_is_30_degrees_and_starts_one_based():
    source = prototype()
    assert "const REPRESENTATION_ANGLE_DEGREES=LOCAL_DEFINER?30:REGION_DEFINER?15:0;" in source
    assert "localTierIndex=1,localLayerIndex=1" in source
    assert "viewDegrees:30" in source


def test_selected_region_asset_is_local_root_reference():
    contract = read("LOCAL_RECURSIVE_SCOPE_CONTRACT.md")
    local = read("Components/LocalDefinerWorkspace.razor")
    assert "x = 0" in contract
    assert "y = 0" in contract
    assert "tier = 1" in contract
    assert "layer = 1" in contract
    assert 'scopeKind="LOCAL"' in local
    assert "x=0" in local
    assert "y=0" in local
    assert "tier=1" in local
    assert "layer=1" in local
    assert "viewDegrees=30" in local
    assert "locked=true" in local


def test_local_coordinates_restart_at_anchor_center():
    source = prototype()
    local_point = source.split("function localRecursivePoint", 1)[1].split(
        "function localRecursiveWorldPoint", 1
    )[0]
    assert "(Number(worldX)-bounds.cx)/Math.max(bounds.width,.0001)" in local_point
    assert "(Number(worldY)-bounds.cy)/Math.max(bounds.height,.0001)" in local_point


def test_local_recursive_envelope_owns_xy_tier_layer():
    source = prototype()
    sync = source.split("function syncLocalRecursiveEnvelope", 1)[1].split(
        "function constrainLocalPoint", 1
    )[0]
    assert "scopeKind:'LOCAL'" in sync
    assert "scopeId:activeLocalMapId()" in sync
    assert "parentScopeId:String(activeLocal?.regionId" in sync
    assert "parentAssetId:String(activeLocal?.anchorObjectId" in sync
    assert "x:point.x,y:point.y" in sync
    assert "tier:Math.max(1" in sync
    assert "layer:Math.max(1" in sync
    assert "viewDegrees:30" in sync
    assert "permissionResourceId:assetAuthorityResourceId(item)" in sync


def test_local_first_overlap_stacks_above_root_without_changing_tier():
    source = prototype()
    overlap = source.split("function nextLocalVisualLayer", 1)[1].split(
        "function syncLocalRecursiveEnvelope", 1
    )[0]
    assert "let highest=tier===1?1:0" in overlap
    assert "localOverlayTier(other)!==tier" in overlap
    assert "regionBoundsOverlap(bounds,localPlacementBounds(other))" in overlap


def test_local_visual_stack_ignores_local_tier():
    source = prototype()
    stack = source.split("function assetSemanticStackTuple", 1)[1].split(
        "function compareStackTuple", 1
    )[0]
    local_branch = stack.split("if(LOCAL_DEFINER&&item?.localOverlay)", 1)[1].split(
        "if(REGION_DEFINER&&item?.regionOverlay)", 1
    )[0]
    assert "return[pin,localOverlayLayer(item),index]" in local_branch
    assert "localOverlayTier(item)" not in local_branch


def test_local_tier_drives_parallax_without_layer_contribution():
    source = prototype()
    parallax = source.split("function applyParallax()", 1)[1].split(
        "function updateReadouts", 1
    )[0]
    assert "Math.max(0,localOverlayTier(item)-1)" in parallax
    local_depth = parallax.split("LOCAL_DEFINER&&item.localOverlay", 1)[1]
    assert "localOverlayLayer(item)/10" not in local_depth


def test_local_tier_and_layer_mutators_are_independent_and_unbounded_layer():
    source = prototype()
    tier = source.split("function moveSelectedTier", 1)[1].split(
        "function moveSelectedRegionTier", 1
    )[0]
    layer = source.split("function moveSelectedLayer", 1)[1].split(
        "function isWorldMapItem", 1
    )[0]
    assert "Math.max(1,localOverlayTier(selectedImage)+Math.sign(delta))" in tier
    assert "syncLocalRecursiveEnvelope(member,next,localOverlayLayer(member))" in tier
    assert "Math.max(1,localOverlayLayer(selectedImage)+Math.sign(delta))" in layer
    assert "syncLocalRecursiveEnvelope(member,localOverlayTier(member),next)" in layer
    assert "clamp(Math.trunc(Number(selectedImage.localLayer)" not in layer


def test_local_serialization_writes_recursive_truth_and_v3_scope_envelope():
    source = prototype()
    serialization = source.split("function serializableUserLayer", 1)[1].split(
        "async function saveWorldBuilder", 1
    )[0]
    local = read("Components/LocalDefinerWorkspace.razor")
    assert "LOCAL_DEFINER&&item.localOverlay?syncLocalRecursiveEnvelope(item)" in serialization
    assert 'format="RIST_LOCAL_MAP_V3"' in local
    assert 'recursiveScopeFormat=WorldSession.RecursiveScopeFormat' in local
    assert 'coordinateSpace="local-root-recursive-v1"' in local
    assert 'kind="LOCAL"' in local
    assert 'parentAssetId=local.AnchorObjectId' in local


def test_local_restore_prefers_recursive_coordinates_and_keeps_legacy_adapter():
    source = prototype()
    restore = source.split("async function enterLocalBuild", 1)[1].split(
        "function fitClaimedRegion", 1
    )[0]
    assert "sourceIsRecursiveLocal" in restore
    assert "localRecursiveWorldPoint(recursive.x,recursive.y,local)" in restore
    assert "sourceWasLocalNormalized" in restore
    assert "localPointToWorld(raw?.x,raw?.y,local)" in restore


def test_new_local_catalog_records_recursive_scope_contract():
    model = read("WorldSession.Locals.cs")
    assert 'CoordinateSpace: "local-root-recursive-v1"' in model
    assert "LocalTier: 1" in model
    assert "LocalLayer: 1" in model
    assert "RecursiveScopeFormat: RecursiveScopeFormat" in model
    assert "ViewDegrees: 30" in model
    assert "ParentScopeId: region.RegionId" in model
    assert "ParentAssetId: anchorObjectId" in model


def test_local_asset_list_reuses_gimp_editor_and_server_acl():
    source = prototype()
    local = read("Components/LocalDefinerWorkspace.razor")
    bridge = read("wwwroot/region-definer-host.js")
    assert "function localEditableAssetRows()" in source
    assert "const scope=LOCAL_DEFINER?'LOCAL':'REGION';" in source
    assert "const degrees=LOCAL_DEFINER?30:15;" in source
    assert "PERMISSION FOR" in source
    assert "request-resource-permissions" in source
    assert "set-resource-permission" in source
    assert "GetPermissionDirectoryForPrototypeAsync" in local
    assert "GetResourcePermissionsForPrototypeAsync" in local
    assert "SetResourcePermissionFromPrototypeAsync" in local
    assert 'mode==="localdefiner"' in bridge
    assert 'type:"permission-directory"' in bridge


if __name__ == "__main__":
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
    print(f"recursive Local scope contract: {len(tests)} checks passed")
