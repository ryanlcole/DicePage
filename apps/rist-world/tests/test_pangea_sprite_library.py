import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPRITES = ROOT / "wwwroot" / "assets" / "sprites" / "pangea"


def test_registered_chunk_assets_use_the_canonical_canvas_and_cdn():
    catalog = json.loads((SPRITES / "catalog.json").read_text())
    registered = catalog[:2]
    assert all((item["sourceWidth"], item["sourceHeight"]) == (1200, 1200) for item in registered)
    assert all(item["image"].startswith("https://d2d6rnm6fnsp89.cloudfront.net/assets/sprites/pangea/registered/") for item in registered)


def test_catalog_covers_every_layer_folder_and_authored_depth():
    library = json.loads((SPRITES / "library.json").read_text())
    catalog = json.loads((SPRITES / "catalog.json").read_text())
    expected = {folder["name"] for folder in library["folders"]}
    assert expected == {item["folder"] for item in catalog}
    assert len(catalog) == library["assetCount"] >= 60
    assert all(item["assetKind"] == "sprite" for item in catalog)
    assert all(item["authoredDepth"] is True for item in catalog)
    assert {(item["defaultTierIndex"], item["defaultLayerOffset"]) for item in catalog} >= {(0, 0), (0, 9), (1, 0), (2, 5)}


def test_worldbuilder_runtime_has_three_requested_controls_and_shared_depth_event():
    mode = (ROOT / "wwwroot" / "parallax-mode.js").read_text()
    projection = (ROOT / "wwwroot" / "worldbuilder-projection.js").read_text()
    tilt = (ROOT / "wwwroot" / "worldbuilder-device-tilt.js").read_text()
    for control in ("parallax", "transport", "fps"):
        assert f"command('{control}'" in mode
    assert "wb-parallax-active .studio-workbench{pointer-events:none" not in mode
    assert "rist-depth-visuals" in projection
    assert "rist-depth-visuals" in tilt
    assert "addEventListener('rist-depth-visuals'" in tilt


def test_worldbuilder_model_preserves_sprite_metadata():
    models = (ROOT / "WorldSession.Models.cs").read_text()
    studio = (ROOT / "Components" / "WorldBuilderStudio.razor").read_text()
    interaction = (ROOT / "Components" / "WorldBuilderStudio.Interactions.cs").read_text()
    assert 'string AssetKind = "tile"' in models
    assert "bool AuthoredDepth = false" in models
    assert '"Sprites"=>category=="Sprites"' in studio
    assert "tile.AuthoredDepth ? tile.DefaultTierIndex" in interaction
    assert "tile.AuthoredDepth ? tile.DefaultLayerOffset" in interaction
