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
    assert "fallbackTierImages=Session.IsGeonaphWorld" in host
    assert "&regionFlow={regionFlow}&regionId={regionId}" in host

    assert "REGION_FLOW" in prototype
    assert "REQUESTED_REGION_ID" in prototype
    assert "function showRegionTierPreview()" in prototype
    assert "function stepRegionTierPreview(delta)" in prototype
    assert "Swipe through the world tiers" in prototype
    assert "if(regionClaimPhase==='tier-preview'||regionClaimPhase==='select'||regionClaimPhase==='crop'||regionClaimPhase==='requested')return['Select'];" in prototype


def test_save_region_crops_then_unlocks_remaining_ui():
    prototype = (ROOT / "wwwroot" / "prototype" / "prototype.js").read_text(encoding="utf-8")
    regions = (ROOT / "WorldSession.Regions.cs").read_text(encoding="utf-8")

    assert "SAVE REGION" in prototype
    assert "applyClaimedRegionCrop(claimed)" in prototype
    assert "stage.classList.remove('region-build-mode','region-tier-previewing','region-selection-only')" in prototype
    assert "persistentSave?.addEventListener('click',()=>{" in prototype
    assert "createRegionDefinition();return" in prototype
    assert "requestedActiveRegionId" in regions
