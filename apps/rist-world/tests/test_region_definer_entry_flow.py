from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_regiondefiner_opens_through_region_gate():
    shell = (ROOT / "Components" / "PublicAlphaShell.razor").read_text(encoding="utf-8")
    gate = (ROOT / "Components" / "RegionGate.razor").read_text(encoding="utf-8")

    assert '<RegionGate Open="@_regionGateOpen"' in shell
    assert "async Task OpenRegionDefiner()" in shell
    assert "void OpenNewRegion()" in shell
    assert "void OpenSavedRegion(WorldRegion region)" in shell
    assert "CHOOSE A REGION" in gate
    assert "NEW REGION" in gate
    assert "Session.SetActiveRegion(region.RegionId)" in gate


def test_new_region_uses_database_world_source_and_swipe_tier_preview():
    host = (ROOT / "Components" / "RegionDefinerWorkspace.razor").read_text(encoding="utf-8")
    prototype = (ROOT / "wwwroot" / "prototype" / "prototype.js").read_text(encoding="utf-8")

    assert 'source="database"' in host
    assert 'var seed=Session.IsGeonaphWorld?"geonaph":"empty";' in host
    assert "await Session.LoadWorldBuilderSourceAsync()" in host
    assert "state=databaseSource?.State" in host
    assert "fallbackTierImages" not in host
    assert "&regionFlow={regionFlow}&regionId={regionId}" in host
    assert "firstSizedTile=tiles.find" in prototype
    assert "stage.dataset.worldSource='database'" in prototype
    assert "saveRegionMapToDatabase" in prototype

    assert "REGION_FLOW" in prototype
    assert "REQUESTED_REGION_ID" in prototype
    assert "function showRegionTierPreview()" in prototype
    assert "function stepRegionTierPreview(delta)" in prototype
    assert "Swipe through the world tiers" in prototype
    assert "if(regionClaimPhase==='tier-preview'||regionClaimPhase==='select'||regionClaimPhase==='crop'||regionClaimPhase==='requested')return['Select'];" in prototype


def test_workspace_home_returns_to_authenticated_landing_without_game_reload():
    shell = (ROOT / "Components" / "PublicAlphaShell.razor").read_text(encoding="utf-8")
    router = (ROOT / "Components" / "TaskWorkspaceRouter.razor").read_text(encoding="utf-8")
    world_host = (ROOT / "Components" / "WorldBuilderGeonaphHost.razor").read_text(encoding="utf-8")
    region_host = (ROOT / "Components" / "RegionDefinerWorkspace.razor").read_text(encoding="utf-8")
    world_bridge = (ROOT / "wwwroot" / "worldbuilder-source-host.js").read_text(encoding="utf-8")
    region_bridge = (ROOT / "wwwroot" / "region-definer-host.js").read_text(encoding="utf-8")
    prototype = (ROOT / "wwwroot" / "prototype" / "prototype.js").read_text(encoding="utf-8")
    prototype_index = (ROOT / "wwwroot" / "prototype" / "index.html").read_text(encoding="utf-8")

    assert '⌂ HOME' in shell
    assert 'aria-label="Home — return to the Shaelvien landing page"' in shell
    assert 'OnHome="ReturnToHub"' in shell
    assert 'OnHome="OnHome"' in router
    assert 'RequestHomeFromPrototypeAsync' in world_host
    assert 'RequestHomeFromPrototypeAsync' in region_host
    assert 'data.type==="home"' in world_bridge
    assert 'data.type==="home"' in region_bridge
    assert "postRegionMessage('home')" in prototype
    assert "postWorldBuilderHostMessage('home')" in prototype
    assert 'id="home"' in prototype_index
    assert 'aria-label="Home — return to the Shaelvien landing page"' in prototype_index
    assert "$('home').addEventListener('click',goHome);" in prototype
    home_block = prototype[prototype.index("function goHome()"):prototype.index("function openStartMenu()")]
    assert "/Game/index.html" not in home_block
    assert "location.href" not in home_block
    assert "location.replace" not in home_block


def test_save_region_crops_then_unlocks_remaining_ui():
    prototype = (ROOT / "wwwroot" / "prototype" / "prototype.js").read_text(encoding="utf-8")
    regions = (ROOT / "WorldSession.Regions.cs").read_text(encoding="utf-8")

    assert "SAVE REGION" in prototype
    assert "applyClaimedRegionCrop(claimed)" in prototype
    assert "stage.classList.remove('region-build-mode','region-tier-previewing','region-selection-only')" in prototype
    assert "persistentSave?.addEventListener('click',()=>{" in prototype
    assert "createRegionDefinition();return" in prototype
    assert "requestedActiveRegionId" in regions
