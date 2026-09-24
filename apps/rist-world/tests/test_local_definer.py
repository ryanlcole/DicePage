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
    assert '"region-normalized-v1"' in model
    assert "Select a placed regional object for the Local." in model
    assert "SaveLocalsAsync" in model
