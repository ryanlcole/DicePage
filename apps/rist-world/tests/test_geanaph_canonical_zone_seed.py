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


def test_geanaph_has_nine_locked_full_frame_visual_layers_and_separate_truth():
    seed = text("infra/aws/rist-platform-geanaph-seed/app.py")

    expected_files = [
        "luminous_underground_cavern_network.png",
        "enchanted_subterranean_realm_map.png",
        "luminous_underground_aquifer_world_map.png",
        "glowing_volcanic_world_map_layer.png",
        "fantasy_archipelago_terrain_atlas.png",
        "luminous_fantasy_archipelago_map_overlay.png",
        "glowing_fantasy_waterway_map.png",
        "fantastical_ruined_archipelago_layer.png",
        "celestial_nebula_archipelago_map.png",
    ]
    for filename in expected_files:
        assert filename in seed

    assert "FRAME_WIDTH = 1672" in seed
    assert "FRAME_HEIGHT = 941" in seed
    assert '"placementRole": "deed-frame"' in seed
    assert '"fullDeedFrame": True' in seed
    assert '"frameLock": True' in seed
    assert '"mmoSurface": mmo_surface' in seed
    assert '"representationOnly": True' in seed
    assert '"provenance": "OUTSIDER_AI"' in seed
    assert 'f"{base}/truth/geanaph_truth_manifest.json"' in seed
    assert '"representationPolicy": "Representation != Semantic Truth"' in seed
    assert "len(verify_layers) != len(VISUAL_LAYERS)" in seed


def test_geanaph_seed_uses_same_configured_owner_as_endemar_and_revision_runs():
    template = text("infra/aws/rist-platform.yml")
    assert "GeanaphSeedFunction:" in template
    assert "CodeUri: rist-platform-geanaph-seed/" in template
    assert "OWNER_USER_ID: !Ref OwnerUserId" in template
    assert "ASSET_BASE_URL: !Sub '${AssetOrigin}/zones/geanaph/v1'" in template
    assert "- SunkenTundraSeed" in template
    assert "Revision: geanaph-east-v2" in template
    assert "GeanaphCanonicalEastOfEndemar:" in template
    assert "GeanaphOwnerBoundToPlatformAccount:" in template


def test_endemar_edit_authority_follows_same_canonical_geanaph_owner_account():
    land = text("apps/rist-world/WorldSession.MmoLand.cs")
    relationships = text("apps/rist-world/WorldSession.WorldRelationships.cs")
    source = text("apps/rist-world/WorldSession.WorldBuilderSource.cs")
    mmo = text("apps/rist-world/Components/UniversalInterface.MmoMap.cs")

    assert "public const int GeanaphCanonicalColumn = EndemarOriginColumn + 1;" in land
    assert "public bool OwnsCanonicalGeanaphZone" in land
    assert 'string.Equals(parcel.DisplayName, "Geanaph"' in land
    assert 'string.Equals(parcel.Status, "Canonical"' in land
    assert "|| (IsGeonaphWorld && OwnsCanonicalGeanaphZone);" in relationships
    assert "&& !(IsGeonaphWorld && OwnsCanonicalGeanaphZone)" in source
    assert "Session.IsServerVerifiedPlatformOwner || Session.HasWorldBuilderEditAuthority" in mmo


def test_mmo_deed_map_prefers_explicit_surface_without_rewriting_z_order():
    mmo = text("apps/rist-world/Components/UniversalInterface.MmoMap.cs")
    assert "bool MmoSurface" in mmo
    assert 'JsonBool(item, "mmoSurface", false)' in mmo
    assert "(layer.MmoSurface && !current.MmoSurface)" in mmo
    assert "(layer.MmoSurface == current.MmoSurface && layer.Layer > current.Layer)" in mmo


def test_edit_entry_starts_all_layers_in_parallax_and_deed_frame_fills_viewer():
    interface = text("apps/rist-world/Components/UniversalInterface.razor")
    host = text("apps/rist-world/wwwroot/worldbuilder-source-host.js")
    prototype = text("apps/rist-world/wwwroot/prototype/prototype.js")
    css = text("apps/rist-world/wwwroot/prototype/prototype.css")

    assert 'entryView={entryView}' in interface
    assert 'entryView=access=="edit"' in interface
    assert '_=ShowAllWorldLayersAsync();' in interface
    assert 'InvokeVoidAsync("showAllParallax"' in interface
    assert "export async function showAllParallax(frame)" in host
    assert "const ENTRY_VIEW=String(QUERY.get('entryView')||'saved').toLowerCase();" in prototype
    assert "function showAllParallax()" in prototype
    assert "viewerTier='all';" in prototype
    assert "viewerLayer=9;" in prototype
    assert "const sceneDepth=(item.tier*10)+item.layer;" in prototype
    assert "function isFullDeedFrameItem(item)" in prototype
    assert "fullDeedFrame:isFullDeedFrameItem(item)" in prototype
    assert "fullDeedFrame:storedPlacementRole(raw)==='deed-frame'" in prototype
    assert "mmoSurface:!!item.mmoSurface" in prototype
    assert "truthManifestUrl:String(item.truthManifestUrl||'')" in prototype
    assert ".user-image-placement.full-deed-frame-placement" in css


def test_mobile_display_can_wrap_long_coordinate_label():
    css = text("apps/rist-world/wwwroot/css/universal-interface.css")
    block = css[css.index(".single-analog-deck button.control-display-button>strong.display-text-sm{"):]
    block = block[:block.index("}", 1) + 1]
    assert "white-space:normal!important" in block
    assert "overflow:visible!important" in block
