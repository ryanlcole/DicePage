from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def text(path):
    return (REPO / path).read_text(encoding="utf-8")


def test_geanaph_is_canonical_east_of_endemar_and_platform_owned():
    seed = text("infra/aws/rist-platform-geanaph-seed/app.py")
    ast.parse(seed)

    assert 'ZONE_NAME = "Geanaph"' in seed
    assert "CANONICAL_COLUMN = ENDEMAR_COLUMN + 1" in seed
    assert "CANONICAL_ROW = ENDEMAR_ROW" in seed
    assert '"ownerUserId": owner_user_id' in seed
    assert '"platformOwned": True' in seed
    assert '"status": "Canonical"' in seed
    assert '"visibility": "Public"' in seed
    assert '"bindingHash": ""' in seed
    assert '"canonicalEastOfEndemar": True' in seed
    assert '"ownerBoundToPlatformAccount": True' in seed
    assert "refusing to overwrite existing world truth" in seed


def test_geanaph_surface_is_representation_and_truth_manifest_is_separate():
    seed = text("infra/aws/rist-platform-geanaph-seed/app.py")
    assert 'SURFACE_FILE = "fantasy_archipelago_terrain_atlas.png"' in seed
    assert '"mmoSurface": True' in seed
    assert '"representationOnly": True' in seed
    assert '"provenance": "OUTSIDER_AI"' in seed
    assert 'f"{base}/truth/geanaph_truth_manifest.json"' in seed
    assert '"representationPolicy": "Representation != Semantic Truth"' in seed


def test_geanaph_seed_uses_same_configured_owner_as_endemar_and_runs_after_sunken_tundra():
    template = text("infra/aws/rist-platform.yml")
    assert "GeanaphSeedFunction:" in template
    assert "CodeUri: rist-platform-geanaph-seed/" in template
    assert "OWNER_USER_ID: !Ref OwnerUserId" in template
    assert "ASSET_BASE_URL: !Sub '${AssetOrigin}/zones/geanaph/v1'" in template
    assert "- SunkenTundraSeed" in template
    assert "Revision: geanaph-east-v1" in template
    assert "GeanaphCanonicalEastOfEndemar:" in template
    assert "GeanaphOwnerBoundToPlatformAccount:" in template


def test_mmo_deed_map_prefers_explicit_surface_without_rewriting_z_order():
    mmo = text("apps/rist-world/Components/UniversalInterface.MmoMap.cs")
    assert "bool MmoSurface" in mmo
    assert 'JsonBool(item, "mmoSurface", false)' in mmo
    assert "(layer.MmoSurface && !current.MmoSurface)" in mmo
    assert "(layer.MmoSurface == current.MmoSurface && layer.Layer > current.Layer)" in mmo


def test_mobile_display_can_wrap_long_coordinate_label():
    css = text("apps/rist-world/wwwroot/css/universal-interface.css")
    block = css[css.index(".single-analog-deck button.control-display-button>strong.display-text-sm{"):]
    block = block[:block.index("}", 1) + 1]
    assert "white-space:normal!important" in block
    assert "overflow:visible!important" in block
