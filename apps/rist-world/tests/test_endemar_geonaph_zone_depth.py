from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_endemar_and_geonaph_are_distinct_canonical_zones():
    identity = text("WorldSession.WorldIdentity.cs")
    land = text("WorldSession.MmoLand.cs")
    host = text("Components/RegionDefinerWorkspace.razor")
    controller = text("Components/UniversalInterface.razor")

    assert 'public const string EndemarStartingPointDisplayName = "Endemar";' in identity
    assert 'public const string GeonaphZoneDisplayName = "Geonaph";' in identity
    assert 'public const string EndemarTruthMode = "FANTASY_FICTION";' in identity
    assert 'public const string GeonaphTruthMode = "TRUTH_HYBRID";' in identity
    assert "public const int GeonaphCanonicalCell" in land
    assert 'var seed=isEndemar?"endemar":isGeonaph?"geonaph":"empty";' in host
    assert 'selectedIsEndemar?"endemar":selectedIsGeonaph?"geonaph":"empty"' in controller


def test_endemar_has_three_tiers_while_mmo_parcels_keep_full_depth():
    prototype = text("wwwroot/prototype/prototype.js")
    identity = text("WorldSession.WorldIdentity.cs")
    host = text("Components/WorldBuilderGeonaphHost.razor")
    regions = text("WorldSession.Regions.cs")
    backend = (ROOT.parents[1] / "infra/aws/rist-platform-authority/app.py").read_text(encoding="utf-8")

    assert "const LAYERS_PER_TIER=10;" in prototype
    assert "const TIER_COUNT=Math.max(1,Math.ceil(MAX_HEIGHT/LAYERS_PER_TIER));" in prototype
    assert "Array.from({length:TIER_COUNT}" in prototype
    assert "public const int EndemarTierCount = 3;" in identity
    assert "public const int EndemarMaxHeight = EndemarTierCount * LayersPerTier;" in identity
    assert "WorldSession.EndemarMaxHeight" in host
    assert "(MmoParcelMaxHeight - 1) / LayersPerTier" in regions
    assert "LAYERS_PER_TIER = 10" in backend
    assert "MMO_PARCEL_TIER_COUNT" in backend
    assert "max_tier = max(0, (max_height - 1) // LAYERS_PER_TIER)" in backend


def test_endemar_never_bootstraps_geonaph_base_art():
    prototype = text("wwwroot/prototype/prototype.js")

    assert "const BASE_WORLD_ASSETS=Object.freeze(IS_GEONAPH_SEED?[" in prototype
    assert "const BASE_WORLD_ASSETS=Object.freeze(IS_ENDEMAR_SEED?[" not in prototype
    assert "geonaph_full_static_canonical_surface_v001.png" in prototype
    assert "geonaph_full_static_highlands_rivers_v001.png" in prototype
    assert "geonaph_full_static_mountain_volcanic_archipelago_v001.png" in prototype
    assert "Object.freeze({key:'surface',tier:0,layer:1" in prototype
    assert "Object.freeze({key:'highlands',tier:1,layer:1" in prototype
    assert "Object.freeze({key:'mountains',tier:2,layer:1" in prototype
