from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def text(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_worldbuilder_publishes_shared_source_to_database_bridge():
    host = text("Components/WorldBuilderGeonaphHost.razor")
    prototype = text("wwwroot/prototype/prototype.js")
    bridge = text("wwwroot/worldbuilder-source-host.js")

    assert 'GetWorldBuilderSourceForPrototypeAsync' in host
    assert 'SaveWorldBuilderSourceFromPrototypeAsync' in host
    assert 'Session.LoadWorldBuilderSourceAsync()' in host
    assert 'Session.SaveWorldBuilderSourceAsync(state)' in host
    assert 'worldbuilder-source-host.js?v=20260920-canonical-roleplay-1' in host

    assert "worldBuilderSourceState" in prototype
    assert "tierImages:worldBuilderTierImages()" in prototype
    assert "saveWorldSourceToDatabase(state)" in prototype
    assert "World Builder loaded from the shared database." in prototype
    assert "world-source-missing" in prototype

    assert 'GetWorldBuilderSourceForPrototypeAsync' in bridge
    assert 'SaveWorldBuilderSourceFromPrototypeAsync' in bridge
    assert 'type:"world-source"' in bridge
    assert 'type:"save-source"' in bridge or 'data.type==="save-source"' in bridge


def test_regiondefiner_is_permissioned_view_of_same_canonical_database_map():
    workspace = text("Components/RegionDefinerWorkspace.razor")
    prototype = text("wwwroot/prototype/prototype.js")

    assert 'source="database"' in workspace
    assert 'state=databaseSource?.State' in workspace
    assert 'fallbackTierImages' not in workspace
    assert 'fallbackSurfaceImage' not in workspace

    assert "const snapshot=envelope.state" in prototype
    assert "Array.isArray(snapshot.tierImages)" in prototype
    assert "applyDatabaseTierImages(tierImages)" in prototype
    assert "applyCanonicalWorldBuilderSnapshot(state,{region:false})" in prototype
    assert "applyCanonicalWorldBuilderSnapshot(snapshot,{" in prototype
    assert "stage.dataset.renderer='worldbuilder-replica'" in prototype
    assert "CANONICAL_PLANE_KEYS" in prototype
    assert "if(BASE_WORLD_ASSETS.length)" in prototype
    assert "stage.dataset.canonicalPlaneSource='worldbuilder-shared'" in prototype
    assert "const probe=new Image()" in prototype
    assert "Array.isArray(snapshot.userLayers)" in prototype
    assert "belongsToActiveRegion" in prototype
    assert "canonicalSource:true" in prototype
    assert "if(!item?.canonicalSource)continue;" in prototype
    assert "canonicalHydrationRevision" in prototype
    assert "hydrateCanonicalRegionLayers(sourceLayers,activeRegionId,hydrationRevision)" in prototype
    assert "Promise.allSettled(tasks)" in prototype
    assert "stage.dataset.canonicalLayerCount=String(sourceLayers.length)" in prototype
    assert "stage.dataset.hydratedCanonicalLayerCount=String(count)" in prototype
    assert "if(REGION_DEFINER)return{surface:1,highlands:index>=1?1:0,mountains:index>=2?1:0}" in prototype
    assert "entry.tier<=currentRegionTierIndex()" in prototype
    assert "item.canonicalSource?item.tier<=regionTier:item.tier===regionTier" in prototype
    assert "if(!REGION_DEFINER)void restoreSavedWorldBuilder()" in prototype
    assert "viewerTier='sea';viewerLayer=0;" not in prototype[prototype.index("async function restoreSavedWorldBuilder"):prototype.index("function ensureRegionEnhanceCanvas")]
    assert "saveRegionMapToDatabase(serializedLayers)" in prototype
    assert "readSavedWorldBuilder(WORLD_SOURCE_SAVE_KEY)" in prototype
    assert "worldbuilder-recovery-cache" in prototype
    assert "promote-world-source" in prototype
    assert "PromoteWorldSourceFromPrototypeAsync" in workspace
    assert "RIST_REGIONDEFINER_OVERLAYS" not in prototype
    assert "stage.dataset.worldSource='database'" in prototype


def test_claimed_region_never_reveals_world_outside_deed_at_any_zoom():
    prototype = text("wwwroot/prototype/prototype.js")
    block = prototype[prototype.index("function syncClaimedRegionContextMask()"):prototype.index("function applyRegionMask(")]

    assert "world.style.maskImage=regionClaimMaskUrl" in block
    assert "stage.dataset.regionContext='region'" in block
    assert "stage.dataset.regionContext='world'" not in block
    assert "world-context" not in block


def test_platform_authority_exposes_world_source_database_routes():
    app = (REPO / "infra" / "aws" / "rist-platform-authority" / "app.py").read_text(encoding="utf-8")
    template = (REPO / "infra" / "aws" / "rist-platform.yml").read_text(encoding="utf-8")
    client = text("AwsAuthorityClient.cs")

    assert 'path == "/world/source"' in app
    assert '"sk": "WORLDSOURCE"' in app
    assert '"world.source.save"' in app
    assert 'Path: /world/source, Method: GET' in template
    assert 'Path: /world/source, Method: POST' in template
    assert 'GetWorldSourceAsync' in client
    assert 'SaveWorldSourceAsync' in client
    assert 'SaveWorldRegionMapAsync' in client
    assert 'path == "/world/source/region"' in app
    assert 'Path: /world/source/region, Method: POST' in template


def test_region_records_define_permissions_not_a_second_map():
    regions = text("WorldSession.Regions.cs")
    assert "A region is authority/view metadata over the canonical world map." in regions
    assert "SourceTiles: []" in regions
    assert "var sourceTiles = PlacedTiles" not in regions


def test_regiondefiner_viewer_never_presents_the_map_as_a_second_locked_source():
    workspace = text("Components/RegionDefinerWorkspace.razor")
    prototype = text("wwwroot/prototype/prototype.js")
    bridge = text("wwwroot/region-definer-host.js")
    index = text("wwwroot/prototype/index.html")

    assert "REGION DEFINER · CANONICAL MAP · 15° VIEW" in prototype
    assert "WORLD SOURCE LOCKED" not in prototype
    assert "Save authorized changes to the canonical map" in prototype
    assert "sourceWorldLocked" not in prototype
    assert "mapAuthorityScoped" in prototype

    # The map bridge attaches before slower claim/region metadata refreshes.
    assert workspace.index('InvokeVoidAsync("attach"') < workspace.index("RefreshMmoLandAsync()")
    assert 'InvokeVoidAsync("refresh"' in workspace
    assert "async function sendState" in bridge
    assert 'type:"map-load-error"' in bridge
    assert "./prototype.js?v=20260923-region-hex-geometry-4" in index
    assert "renderer=20260923-region-hex-geometry-4" in workspace
    assert "./region-definer-host.js?v=20260920-region-entry-2" in workspace


def test_regiondefiner_claim_flow_is_linear_and_crop_is_real():
    prototype = text("wwwroot/prototype/prototype.js")
    css = text("wwwroot/prototype/prototype.css")

    assert "const DISPLAY_WORLD_NAME=WORLD_NAME||'Shaelvien';" in prototype
    assert "IS_GEONAPH_SEED?'Endemar'" not in prototype
    assert "toolKey('CROP','preview selected region as the full regional map',previewRegionCrop,!regionSelectedCells.size)" in prototype
    assert "if(regionClaimPhase!=='crop'){announce('Preview the crop before saving the region.');return}" in prototype
    assert "applyRegionMask(preview,'selection-preview',false)" in prototype
    assert "applyRegionMask(region,'visibility-mask',true)" in prototype
    assert 'viewBox="0 0 ${REGION_GRID_COLUMNS} ${REGION_GRID_ROWS}"' in prototype
    assert "regionClaimedRegion&&regionClaimBounds(regionClaimedRegion)" in prototype
    assert ".stage.region-selection-only .persistent-save{display:none!important}" in css
