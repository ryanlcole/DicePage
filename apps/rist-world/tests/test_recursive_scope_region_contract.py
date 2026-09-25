from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def prototype() -> str:
    return read("wwwroot/prototype/prototype.js")


def test_region_scope_starts_at_15_degrees_and_one_based_depth():
    source = prototype()
    assert "const RECURSIVE_SCOPE_FORMAT='RIST_RECURSIVE_SCOPE_V1';" in source
    assert "LOCAL_DEFINER?30:REGION_DEFINER?15:0" in source
    assert "regionTierIndex=1,regionLayerIndex=1" in source
    assert "regionTierIndex=1;" in source
    assert "regionLayerIndex=1;" in source


def test_region_recursive_envelope_owns_local_coordinates_tier_and_layer():
    source = prototype()
    sync = source.split("function syncRegionRecursiveEnvelope", 1)[1].split(
        "function nestedVerticalAddress", 1
    )[0]
    assert "scopeKind:'REGION'" in sync
    assert "scopeId:regionId" in sync
    assert "parentScopeId:WORLD_ID" in sync
    assert "x:point.x,y:point.y" in sync
    assert "tier:Math.max(1" in sync
    assert "layer:Math.max(1" in sync
    assert "viewDegrees:15" in sync
    assert "permissionResourceId:authority" in sync


def test_claimed_region_is_the_recursive_coordinate_frame():
    source = prototype()
    frame = source.split("function regionScopeFrame", 1)[1].split(
        "function syncRegionRecursiveEnvelope", 1
    )[0]
    assert "selectedCells" in frame
    assert "left" in frame and "right" in frame
    assert "top" in frame and "bottom" in frame
    assert "regionLocalPoint" in frame
    assert "regionWorldPoint" in frame


def test_region_tier_changes_parallax_not_composition():
    source = prototype()
    move = source.split("function moveSelectedRegionTier", 1)[1].split(
        "function moveSelectedLayer", 1
    )[0]
    assert "Math.max(1,regionOverlayTier" in move
    assert "syncRegionRecursiveEnvelope(member,next,regionOverlayLayer(member))" in move
    assert "member.worldLayer=" not in move
    assert "member.regionLayer=" not in move

    parallax = source.split("function applyParallax()", 1)[1].split(
        "function updateReadouts", 1
    )[0]
    assert "regionOverlayTier(item)-1" in parallax
    assert "recursiveRegion?1.5" in parallax


def test_region_layer_changes_composition_not_tier():
    source = prototype()
    move = source.split("function moveSelectedLayer", 1)[1].split(
        "function isWorldMapItem", 1
    )[0]
    region_branch = move.split("if(REGION_DEFINER&&!LOCAL_DEFINER)", 1)[1].split(
        "const maxSceneZ", 1
    )[0]
    assert "Math.max(1,regionOverlayLayer" in region_branch
    assert "syncRegionRecursiveEnvelope(member,regionOverlayTier(member),next)" in region_branch
    assert "regionTierIndex=" not in region_branch
    assert "Math.min" not in region_branch
    assert "clamp(regionOverlayLayer" not in region_branch


def test_region_visual_stack_ignores_recursive_tier():
    source = prototype()
    stack = source.split("function assetSemanticStackTuple", 1)[1].split(
        "function compareStackTuple", 1
    )[0]
    region_branch = stack.split("if(REGION_DEFINER&&item?.regionOverlay)", 1)[1]
    assert "return[pin,regionOverlayLayer(item),index]" in region_branch
    assert "regionOverlayTier(item)" not in region_branch


def test_overlapping_assets_auto_stack_within_same_region_tier():
    source = prototype()
    overlap = source.split("function nextRegionVisualLayer", 1)[1].split(
        "function syncRegionRecursiveEnvelope", 1
    )[0]
    assert "regionOverlayTier(other)!==tier" in overlap
    assert "recursive?.visible===false" in overlap
    assert "regionBoundsOverlap" in overlap
    assert "highest=Math.max(highest,regionOverlayLayer(other))" in overlap
    apply = source.split("function applyRegionAddress", 1)[1].split(
        "function localIsOpen", 1
    )[0]
    assert "nextRegionVisualLayer(item,recursiveTier)" in apply


def test_region_save_and_restore_carries_recursive_envelope():
    source = prototype()
    assert "recursive:REGION_DEFINER&&!LOCAL_DEFINER&&item.regionOverlay?syncRegionRecursiveEnvelope(item)" in source
    assert "recursive:raw?.recursive&&typeof raw.recursive==='object'?{...raw.recursive}:undefined" in source
    assert "state.projection!=='region-recursive-scope-v1'&&state.projection!=='region-world-z-v2'" in source
    assert "snapshot.projection==='region-recursive-scope-v1'||snapshot.projection==='region-world-z-v2'" in source


def test_region_ui_no_longer_exposes_world_z_as_region_authoring_control():
    source = prototype()
    assert "WORLD Z −" not in source
    assert "WORLD Z +" not in source
    assert "WORLD L −" not in source
    assert "WORLD L +" not in source
    assert "Region Tier controls parallax depth; visual Layer controls appearance order." in source
    assert "Position is stored in Region-local X/Y." in source


def test_region_source_projector_writes_recursive_truth_beside_legacy_adapter():
    source = read("RegionSourceProjector.cs")
    assert 'projection = "region-recursive-scope-v1"' in source
    assert 'legacyProjection = "region-world-z-v2"' in source
    assert 'recursiveScopeFormat = WorldSession.RecursiveScopeFormat' in source
    assert 'kind = "REGION"' in source
    assert "viewDegrees = 15" in source
    assert "x = localX" in source
    assert "y = localY" in source
    assert "tier = recursiveTier" in source
    assert "layer = recursiveLayer" in source
    assert "status = \"legacy-compatibility-only\"" in source



def test_region_has_shared_gimp_style_asset_list():
    source = prototype()
    style = read("wwwroot/prototype/prototype.css")
    assert "const REGION_KEYBOARD_MODES=['Viewer','Tiers','Layers'" in source
    assert "function renderRecursiveAssetList()" in source
    assert "REGION · 15°" in source
    assert "Layer = appearance · Tier = depth · X/Y local to deed" in source
    assert "recursive-icon" in source
    assert "recursive-opacity" in source
    assert "recursive-layer" in source
    assert "recursive-tier" in source
    assert "recursive-link" in source
    assert "recursive-permission" in source
    assert ".recursive-asset-list{" in style
    assert "@media(max-width:760px)" in style


def test_region_list_visibility_lock_and_opacity_are_recursive_appearance_state():
    source = prototype()
    editor = source.split("function updateRegionAssetFromList", 1)[1].split(
        "function renderRecursiveAssetList", 1
    )[0]
    assert "item.recursive={...current,visible:" in editor
    assert "item.positionLocked=!item.positionLocked" in editor
    assert "item.opacity=clamp(Number(value),0,1)" in editor
    assert "syncRegionRecursiveEnvelope(item)" in editor
    parallax = source.split("function applyParallax()", 1)[1].split(
        "function updateReadouts", 1
    )[0]
    assert "recursiveRegionEnvelope(item)?.visible!==false" in parallax
    assert "opacity:clamp(Number(item.opacity??1),0,1)" in source


def test_region_list_permission_is_identity_projection_not_geometry():
    source = prototype()
    panel = source.split("function renderRecursiveAssetList()", 1)[1].split(
        "function syncRegionEditLayer", 1
    )[0]
    assert "permissionResourceId" in panel
    assert "Authority remains server controlled." in panel
    assert "Permission identity" in panel

if __name__ == "__main__":
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
    print(f"recursive Region scope contract: {len(tests)} checks passed")
