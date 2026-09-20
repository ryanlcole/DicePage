from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_region_gate_exposes_new_or_claim_from_trusted_database_authority():
    gate = text("Components/RegionGate.razor")
    assert "Session.HasTrustedWorldBuilderAuthority" in gate
    assert "Session.CanRequestWorldClaim" in gate
    assert "CLAIM REGION" in gate
    assert "LoadPendingWorldClaimRequestsAsync" in gate
    assert "LoadMyWorldClaimRequestsAsync" in gate
    assert "DecideWorldClaimRequestAsync" in gate


def test_region_definer_uses_selected_world_source_and_scoped_region_authority():
    workspace = text("Components/RegionDefinerWorkspace.razor")
    assert 'source="database"' in workspace
    assert 'var seed=Session.IsGeonaphWorld?"geonaph":"empty";' in workspace
    assert "await Session.LoadWorldBuilderSourceAsync()" in workspace
    assert "state=databaseSource?.State" in workspace
    assert "Session.CanEditRegion(activeRegion)" in workspace
    assert "requestedName:name" in workspace
    assert "regionFlow" in workspace
    assert "regionId" in workspace
    assert "SaveRegionMapLayersFromPrototypeAsync" in workspace


def test_new_and_claim_region_share_tier_swipe_and_select_only_flow():
    prototype = text("wwwroot/prototype/prototype.js")
    assert "ensureRegionTierPreview" in prototype
    assert "Swipe left or right across the map to preview tiers." in prototype
    assert "if(regionClaimPhase==='tier-preview'||regionClaimPhase==='select'||regionClaimPhase==='crop'||regionClaimPhase==='requested')return['Select']" in prototype
    assert "if(!name){announce('Name the region before saving or requesting it.');return}" in prototype
    assert prototype.count("regionNameInput(),") >= 2
    assert "toolKey('−','zoom'" in prototype
    assert "toolKey('+','zoom'" in prototype
    assert "const renderedTierImages=regionTierPreviewSources().slice(0,TIERS.length);" in prototype
    assert "updateRegionWorldSourceVisibility();" in prototype
    assert "fitMap();" in prototype
    assert "applyParallax();" in prototype


def test_shared_region_catalog_is_database_first_and_claim_owner_is_scoped():
    regions = text("WorldSession.Regions.cs")
    assert "await authority.GetRegionsAsync(WorldId)" in regions
    assert "await authority.SaveRegionAsync(WorldId, region)" in regions
    assert "CanEditRegion(WorldRegion? region)" in regions
    assert "if (!CanEditRegion(region)) return false;" in regions
    assert "_regions.Where(CanEditRegion)" in regions
