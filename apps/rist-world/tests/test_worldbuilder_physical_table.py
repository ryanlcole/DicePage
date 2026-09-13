import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WWWROOT = ROOT / "wwwroot"
COMPONENTS = ROOT / "Components"


def test_sprite_catalog_contains_motion_not_static_depth_art():
    catalog = json.loads((WWWROOT / "assets" / "sprites" / "catalog.json").read_text())
    assert catalog
    assert all(item["assetKind"] == "sprite" for item in catalog)
    assert all(item["frameCount"] > 1 for item in catalog)
    assert all(item["framesPerSecond"] > 0 for item in catalog)
    assert all(item["directory"] == "Terrain" for item in catalog)
    assert all("/world/terrain/" in item["image"] for item in catalog)
    assert all("pangea" not in json.dumps(item).lower() for item in catalog)


def test_geonaph_package_is_manifest_driven_and_legacy_catalog_is_not_loaded():
    session = (ROOT / "WorldSession.cs").read_text()
    bootstrap = (ROOT / "WorldSession.GianaphBootstrap.cs").read_text()
    studio = (COMPONENTS / "WorldBuilderStudio.razor").read_text()
    assert 'assets/sprites/catalog.json?v=20260914-geonaph-v1' in session
    assert 'assets/sprites/pangea/catalog.json' not in session
    assert 'assets/sprites/pangea/catalog.json' not in studio
    assert 'assets/worlds/geonaph/v1/runtime_catalog.json' in bootstrap
    assert 'GeonaphRuntimeCatalog' in bootstrap
    assert 'placement.Asset.AssetKind' not in bootstrap
    assert 'FrameCount: Math.Max(1, asset.FrameCount)' in bootstrap
    assert 'FramesPerSecond: Math.Max(0, asset.FramesPerSecond)' in bootstrap
    assert not any(path.is_file() for path in (WWWROOT / "assets" / "sprites" / "pangea").rglob("*"))


def test_sprite_library_only_exposes_true_animated_assets():
    rail = (COMPONENTS / "WorldAssetFolderRail.razor").read_text()
    catalog_authority = (COMPONENTS / "WorldAnimatedAssetCatalog.razor").read_text()
    assert 'x.FrameCount>1' in rail
    assert 'x.FramesPerSecond>0' in rail
    assert 'asset.FrameCount > 1' in catalog_authority
    assert 'asset.FramesPerSecond > 0' in catalog_authority
    assert 'RemoveAll' in catalog_authority
    assert 'Pangea' not in rail


def test_explicit_tile_size_controls_next_worldbuilder_placement():
    interaction = (COMPONENTS / "WorldBuilderStudio.Interactions.cs").read_text()
    assert 'var footprint=Math.Clamp((double)_tileFootprint' in interaction
    assert 'Session.AddPlacedTileAtGridDepth(placed);' in interaction
    assert 'Session.AddPlacedTileStacked(placed' not in interaction
    assert 'tile.DefaultFootprint' not in interaction


def test_raised_grid_depth_is_exact_and_midair_is_legal():
    placement = (ROOT / "WorldSession.LayerPlacement.cs").read_text()
    assert 'public void AddPlacedTileAtGridDepth' in placement
    assert 'StorePlacedAtSceneZ(tile,SceneZOf(tile));' in placement
    exact_method = placement.split('public void AddPlacedTileAtGridDepth', 1)[1].split('public void AddPlacedTileAtLayerDelta', 1)[0]
    assert 'TilesOverlap' not in exact_method
    assert 'forceUpper' not in exact_method


def test_worldbuilder_table_and_construction_grid_are_separate_authorities():
    authority = (WWWROOT / "worldbuilder-table-authority.js").read_text()
    contract = (ROOT / "WORLDBUILDER_STUDIO_CONTRACT.md").read_text()
    assert 'aspect-ratio:1 / 1' in authority
    assert 'background-size:calc(100% / 30) calc(100% / 30)' in authority
    assert '.studio-viewer-grid.off' in authority
    assert 'table surface → independent GM square construction grid → placed static/animated asset stack → optional gameplay mat/grid' in contract
    assert 'The table itself owns **no grid**.' in contract
    assert 'Unsupported/mid-air placement is valid.' in contract


def test_legacy_faded_underlay_is_not_mounted_in_worldbuilder():
    router = (COMPONENTS / "TaskWorkspaceRouter.razor").read_text()
    assert '<WorldBuilderGestureFix' not in router
    assert '<WorldAnimatedAssetCatalog' in router
