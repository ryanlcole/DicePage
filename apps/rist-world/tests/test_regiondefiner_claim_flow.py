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
    assert "if(!name){announce('Name the region before claiming the deed.');return}" in prototype
    assert prototype.count("regionNameInput(),") == 1
    assert "toolKey('−','zoom'" in prototype
    assert "toolKey('+','zoom'" in prototype
    assert "const renderedTierImages=regionTierPreviewSources().slice(0,TIERS.length);" in prototype
    assert "updateRegionWorldSourceVisibility();" in prototype
    assert "fitMap();" in prototype
    assert "applyParallax();" in prototype


def test_deed_confirmation_is_minimal_and_editable_deed_reuses_worldbuilder_controls():
    prototype = text("wwwroot/prototype/prototype.js")
    crop = prototype[prototype.index("if(regionClaimPhase==='crop'){"):prototype.index("if(regionClaimPhase==='requested'){")]

    assert "regionNameInput()" in crop
    assert "toolKey('BACK'" in crop
    assert "'CLAIM DEED'" in crop
    assert "readoutKey(" not in crop
    assert "SAVE REGION" not in crop
    assert "BUILD REGION" not in prototype
    assert "const editableRegion=ACCESS_MODE==='edit';" in prototype
    assert "if(editableRegion)keyboardMode='Viewer';" in prototype
    assert "if(REGION_DEFINER&&regionClaimPhase!=='build'){renderRegionSelectKeyboard();return}" in prototype


def test_new_region_starts_deselected_on_hex_grid_and_requires_a_tile():
    prototype = text("wwwroot/prototype/prototype.js")
    styles = text("wwwroot/prototype/prototype.css")
    regions = text("WorldSession.Regions.cs")
    contract = text("REGION_DEFINER_CONTRACT.md")

    assert "const regionSelectedCells=new Set();" in prototype
    assert "let regionGridShape='hex'" in prototype
    assert "overlay.className='region-definition-grid hex'" in prototype
    assert "select at least 1" in prototype
    assert "!regionSelectedCells.size" in prototype
    assert ".region-definition-grid.hex .region-definition-cell" in styles
    assert 'if (cells.Count == 0) throw new InvalidOperationException("Select at least one world tile for the region.");' in regions
    assert "Hex is the default for every new region" in contract


def test_shared_region_catalog_is_database_first_and_claim_owner_is_scoped():
    regions = text("WorldSession.Regions.cs")
    assert "await authority.GetRegionsAsync(requestedWorldId)" in regions
    assert "await authority.SaveRegionAsync(WorldId, region)" in regions
    assert "CanEditRegion(WorldRegion? region)" in regions
    assert "if (!CanEditRegion(region)) return false;" in regions
    assert "_regions.Where(CanEditRegion)" in regions
