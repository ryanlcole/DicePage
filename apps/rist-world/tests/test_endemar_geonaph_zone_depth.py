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


def test_shaelvien_zone_depth_exposes_ten_tiers_of_ten_layers():
    prototype = text("wwwroot/prototype/prototype.js")
    regions = text("WorldSession.Regions.cs")
    backend = (ROOT.parents[1] / "infra/aws/rist-platform-authority/app.py").read_text(encoding="utf-8")

    assert "const LAYERS_PER_TIER=10;" in prototype
    assert "const TIER_COUNT=Math.max(1,Math.ceil(MAX_HEIGHT/LAYERS_PER_TIER));" in prototype
    assert "Array.from({length:TIER_COUNT}" in prototype
    assert "WorldSession.MmoParcelMaxHeight:WorldSession.LayersPerTier" in text("Components/UniversalInterface.razor")
    assert "(MmoParcelMaxHeight - 1) / LayersPerTier" in regions
    assert "LAYERS_PER_TIER = 10" in backend
    assert "MMO_PARCEL_TIER_COUNT" in backend
    assert "max_tier = max(0, (max_height - 1) // LAYERS_PER_TIER)" in backend
