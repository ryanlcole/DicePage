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
    assert 'worldbuilder-source-host.js?v=20260918-db-source-1' in host

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
    assert "CANONICAL_PLANE_KEYS" in prototype
    assert "Array.isArray(snapshot.userLayers)" in prototype
    assert "belongsToActiveRegion" in prototype
    assert "canonicalSource:true" in prototype
    assert "if(!item?.canonicalSource)continue;" in prototype
    assert "canonicalHydrationRevision" in prototype
    assert "hydrateCanonicalRegionLayers(sourceLayers,activeRegionId,hydrationRevision)" in prototype
    assert "Promise.allSettled(tasks)" in prototype
    assert "stage.dataset.canonicalLayerCount=String(sourceLayers.length)" in prototype
    assert "stage.dataset.hydratedCanonicalLayerCount=String(count)" in prototype
    assert "saveRegionMapToDatabase(serializedLayers)" in prototype
    assert "RIST_REGIONDEFINER_OVERLAYS" not in prototype
    assert "stage.dataset.worldSource='database'" in prototype


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
    assert "./prototype.js?v=20260918-region-layers-2" in index
    assert "renderer=20260918-region-layers-2" in workspace
    assert "./region-definer-host.js?v=20260918-region-layers-2" in workspace
