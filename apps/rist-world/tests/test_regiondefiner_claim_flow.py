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


def test_completed_deed_removes_selection_overlay_without_losing_claim_mask():
    prototype = text("wwwroot/prototype/prototype.js")
    styles = text("wwwroot/prototype/prototype.css")
    contract = text("REGION_DEFINER_CONTRACT.md")
    handoff = prototype[prototype.index("function applyClaimedRegionCrop("):prototype.index("function ensureRegionTierPreview(")]
    ensure = prototype[prototype.index("function ensureRegionSelectionOverlay("):prototype.index("function regionNameInput()")]

    assert "retireRegionSelectionOverlay();" in handoff
    assert "regionClaimPhase=editableRegion?'build':'saved';" in handoff
    assert "retireRegionSelectionOverlay();" in ensure
    assert "if(regionDeedIsComplete()" in ensure
    assert "regionSelectionOverlay.remove();" in prototype
    assert ".stage.region-cropped .region-definition-grid{display:none!important;" in styles
    assert "applyRegionMask(region,'visibility-mask',true)" in handoff
    assert "remove the selection-grid DOM" in contract


def test_region_is_independently_editable_above_locked_selected_world_tier():
    prototype = text("wwwroot/prototype/prototype.js")
    css = text("wwwroot/prototype/prototype.css")
    assert "function ensureRegionEditLayer()" in prototype
    assert "function mountUserPlacement(item)" in prototype
    assert "layer.style.zIndex=String(tierStackBase(tier)+80);" in prototype
    assert "item.node.hidden=!active" in prototype
    assert "item.regionOverlay" in prototype
    assert "item.tier===Number(regionClaimedRegion?.tierIndex)" in prototype
    assert "if(REGION_DEFINER&&item.regionOverlay){" in prototype
    assert ".region-edit-layer .user-image-placement{pointer-events:auto" in css
    assert ".region-edit-layer[hidden]{display:none!important}" in css


def test_new_hex_region_metadata_uses_displayed_column_staggered_extent():
    regions = text("WorldSession.Regions.cs")
    assert "var spanX = hex ? GridColumns * .75 + .25 : GridColumns;" in regions
    assert "var spanY = hex ? GridRows + .5 : GridRows;" in regions
    assert "var hx = hex ? col * .75 : col;" in regions
    assert "var hy = hex ? row + (col % 2) * .5 : row;" in regions
    assert "CanonicalMinX: Math.Clamp(positions.Min(p => p.MinX), 0, 1)" in regions


def test_seed_can_read_customer_key_encrypted_world_state():
    template = (ROOT.parents[1] / "infra" / "aws" / "rist-platform.yml").read_text(encoding="utf-8")
    seed = template[template.index("  SunkenTundraSeedFunction:"):template.index("  SunkenTundraSeedInvokePermission:")]
    assert "DynamoDBCrudPolicy" in seed
    assert "Action: [kms:Decrypt, kms:GenerateDataKey]" in seed
    assert "Resource: !GetAtt UserDataKey.Arn" in seed


def test_region_city_default_map_attached_with_parallax_only_on_explicit_tier_change():
    prototype = text("wwwroot/prototype/prototype.js")
    assert "function itemParallaxMode(" in prototype
    assert "if(!item.parallaxMode)item.parallaxMode='anchored';" in prototype
    assert "selectedImage.parallaxMode=selectedImage.tier===itemAnchorTier(selectedImage)?'anchored':'tier';" in prototype
    assert "regionReferenceFrozen=REGION_DEFINER&&regionDeedIsComplete();" in prototype
    assert "itemParallaxMode(item)==='anchored'" in prototype
    assert "parallaxMode:itemParallaxMode(item)" in prototype
    assert "parallaxMode:restoredParallaxMode(raw,regionOverlay)" in prototype


def test_complete_parent_source_layer_and_canonical_lake_reference_remain_visible():
    prototype = text("wwwroot/prototype/prototype.js")
    assert "function revealCompleteRegionWorldReference()" in prototype
    assert "for(let layer=0;layer<10;layer++)layers.add(layer);" in prototype
    assert "function syncRegionReferenceImage(tier,src)" in prototype
    assert "syncRegionReferenceImage(tier,resolved);" in prototype
    assert "const attached=regionReferenceFrozen||itemParallaxMode(item)==='anchored';" in prototype
    assert "item.parallaxX=selectionFrozen?0:attached?reference.x:" in prototype
