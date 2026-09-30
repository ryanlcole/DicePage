from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def text(path):
    return (REPO / path).read_text(encoding="utf-8")


def test_geanaph_seed_is_canonical_east_of_endemar_and_platform_owned():
    seed = text("infra/aws/rist-platform-geanaph-seed/app.py")
    ast.parse(seed)

    assert 'ZONE_NAME = "Geanaph"' in seed
    assert "CANONICAL_COLUMN = ENDEMAR_COLUMN + 1" in seed
    assert "CANONICAL_ROW = ENDEMAR_ROW" in seed
    assert '"ownerUserId": owner_user_id' in seed
    assert '"canonicalOwner": "platformOwner"' in seed
    assert '"tokenSpent": False' in seed
    assert '"eastOfEndemar": True' in seed
    assert '"ownerMatchesPlatformOwner": True' in seed


def test_geanaph_seed_uses_verified_truth_package_without_synthetic_links():
    seed = text("infra/aws/rist-platform-geanaph-seed/app.py")

    assert "len(TRUTH_LAYERS)" in seed
    assert 'T_truth_groundwater_boundaries.png' in seed
    assert 'T_truth_active_faults.png' in seed
    assert 'T_truth_plate_boundaries.png' in seed
    assert 'T_truth_submerged.png' in seed
    assert 'T_truth_subterranean.png' in seed
    assert 'T_truth_current_coastline.png' in seed
    assert 'T_truth_current_rivers.png' in seed
    assert 'T_truth_early_engineering.png' in seed
    assert 'T_truth_archaeology_surface.png' in seed
    assert 'T_truth_chronology_stars.png' in seed
    assert '"truthManifestUrl": manifest_url' in seed
    assert '"relationshipLinesSynthetic": 0' in seed
    assert '"mmoSurface": mmo_surface' in seed
    assert '"current-coastline", "Current Coastline", "T_truth_current_coastline.png", 0, True' in seed


def test_geanaph_cloudformation_seed_runs_after_sunken_tundra_seed():
    template = text("infra/aws/rist-platform.yml")

    assert "AssetCdnOrigin:" in template
    assert "GeanaphSeedFunction:" in template
    assert "CodeUri: rist-platform-geanaph-seed/" in template
    assert "GeanaphSeedInvokePermission:" in template
    assert "GeanaphSeed:" in template
    assert "- SunkenTundraSeed" in template
    assert "Revision: geanaph-east-v1" in template
    assert "RelativeX: 1" in template
    assert "RelativeY: 0" in template
    assert "GeanaphOwnerMatchesPlatformOwner:" in template
    assert "GeanaphTruthManifestUrl:" in template


def test_mmo_map_prefers_explicit_surface_marker_over_highest_truth_layer():
    mmo = text("apps/rist-world/Components/UniversalInterface.MmoMap.cs")

    assert "bool MmoSurface" in mmo
    assert 'JsonBool(item, "mmoSurface", false)' in mmo
    assert "(layer.MmoSurface && !current.MmoSurface)" in mmo
    assert "(layer.MmoSurface == current.MmoSurface && layer.Layer > current.Layer)" in mmo
