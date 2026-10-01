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
    assert "function worldBuilderSourceLayersForCurrentDeed(layers)" in prototype
    assert "if(DEED_REGION_ID)return list.filter" in prototype
    assert "if(IS_ENDEMAR_SEED)return list.filter" in prototype
    assert "return [];" in prototype


def test_deed_saves_preserve_other_deeds_and_endemar_scope():
    source = text("WorldSession.WorldBuilderSource.cs")
    controller = text("Components/UniversalInterface.razor")
    root_host = text("Components/WorldBuilderGeonaphHost.razor")
    prototype = text("wwwroot/prototype/prototype.js")

    assert "MergeWorldBuilderRepresentationState" in source
    assert 'string.Equals(property.Key, "userLayers"' in source
    assert "if (!InScope(layer))" in source
    assert "if (InScope(layer))" in source
    assert "SelectedDeedRegionId" in controller
    assert "MergeWorldBuilderRepresentationState(state,current?.State)" in root_host
    assert "worldBuilderSourceLayersForCurrentDeed(layers).map(serializableUserLayer)" in prototype


def test_whole_map_assets_keep_one_deed_frame_across_tiers():
    prototype = text("wwwroot/prototype/prototype.js")
    controller = text("Components/UniversalInterface.razor")

    assert "function looksLikeWholeMapAsset(raw)" in prototype
    assert "raw?.fullFrame===true||looksLikeWholeMapAsset(raw)" in prototype
    assert "const fullDeedFrame=geonaphSeaLevelMap||raw.fullFrame===true||looksLikeWholeMapAsset" in prototype
    assert "placementRole:fullDeedFrame?'deed-frame':'layer'" in prototype
    assert "size:clamp(Number(raw.scale)||1,.01,20)" in prototype
    assert "rotation:geonaphSeaLevelMap?0:" in prototype
    assert "frameLock:geonaphSeaLevelMap" in prototype
    assert "scale(${size})" in prototype
    assert 'bool SelectedAssetUsesFullDeedFrame=>CurrentBuilderScope=="WORLD";' in controller
    assert "fullFrame=SelectedAssetUsesFullDeedFrame" in controller


def test_returning_to_endemar_home_restores_fitted_parallax_overview():
    controller = text("Components/UniversalInterface.razor")

    assert 'renderer=20261001-world-home-fill-1' in controller
    assert controller.count("_=ShowAllWorldLayersAsync();") >= 3


def test_world_home_precedes_tier_and_save_returns_to_overview():
    controller = text("Components/UniversalInterface.razor")
    css = text("wwwroot/css/universal-interface.css")

    assert "WorldHome," in controller
    assert 'HandleViewerMenuCommandAsync("world-home")' in controller
    assert ">WORLD HOME</button>" in controller
    assert 'Stage.WorldHome=>"CHOOSE TIER"' in controller
    assert 'Stage.WorldHome=>$"{CurrentBuilderSuite} · WORLD HOME"' in controller
    assert 'if(command=="world-home"){await OpenWorldHomeAsync();return;}' in controller
    assert 'if(savedScope=="WORLD")' in controller
    assert 'Returned to World Home with all layers and parallax visible.' in controller
    assert "grid-template-columns:repeat(8,minmax(0,1fr))!important;" in css


def test_zone_fill_resize_reaches_one_percent_and_repeats_on_hold():
    controller = text("Components/UniversalInterface.razor")
    prototype = text("wwwroot/prototype/prototype.js")
    universal_input = text("wwwroot/universal-interface-input.js")

    assert "const double MinAssetScale=.01;" in controller
    assert 'Math.Abs(_assetScale-1)<.0005?"FILL ZONE"' in controller
    assert "Hold Y to keep resizing." in controller
    assert "selectedImage.size=clamp(Math.round(next*10000)/10000,.01,20);" in prototype
    assert 'shell?.dataset?.semanticContext === "shaep.scale"' in universal_input
    assert "SCALE_REPEAT_DELAY_MS" in universal_input
    assert "SCALE_REPEAT_INTERVAL_MS" in universal_input
