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


def test_regiondefiner_consumes_database_worldbuilder_snapshot_not_static_fallbacks():
    workspace = text("Components/RegionDefinerWorkspace.razor")
    prototype = text("wwwroot/prototype/prototype.js")

    assert 'source="database"' in workspace
    assert 'state=databaseSource?.State' in workspace
    assert 'fallbackTierImages' not in workspace
    assert 'fallbackSurfaceImage' not in workspace

    assert "const snapshot=envelope.state" in prototype
    assert "Array.isArray(snapshot.tierImages)" in prototype
    assert "Array.isArray(snapshot.userLayers)" in prototype
    assert "attachRestoredLayer(raw,{sourceLocked:true})" in prototype
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
