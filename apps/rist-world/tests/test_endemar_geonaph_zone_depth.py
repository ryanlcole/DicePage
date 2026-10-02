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
    assert "const TIER_TOP_LAYER=LAYERS_PER_TIER-1;" in prototype
    assert "Object.freeze({key:'surface',tier:0,layer:TIER_TOP_LAYER" in prototype
    assert "Object.freeze({key:'highlands',tier:1,layer:TIER_TOP_LAYER" in prototype
    assert "Object.freeze({key:'mountains',tier:2,layer:TIER_TOP_LAYER" in prototype
    assert "function worldBuilderSourceLayersForCurrentDeed(layers,strictIdentity=false)" in prototype
    assert "if(DEED_REGION_ID)return list.filter" in prototype
    assert "identity===WORLD_SEED||identity===DEED_ZONE_ID" in prototype
    assert "if(IS_ENDEMAR_SEED)return list.filter" in prototype
    assert "identity==='endemar'||(!strictIdentity&&!identity)" in prototype
    assert "worldBuilderSourceLayersForCurrentDeed(allSourceLayers,true)" in prototype
    assert "zoneIdentity:String(item.zoneIdentity||WORLD_SEED||'')" in prototype
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
    prototype_css = text("wwwroot/prototype/prototype.css")
    controller = text("Components/UniversalInterface.razor")

    assert "function looksLikeWholeMapAsset(raw)" in prototype
    assert "raw?.fullFrame===true||looksLikeWholeMapAsset(raw)" not in prototype
    assert "if(raw?.mmoSurface===true&&raw?.frameLock===true)return'deed-frame';" in prototype
    assert "const fullDeedFrame=geonaphSeaLevelMap;" in prototype
    assert "placementRole:fullDeedFrame?'deed-frame':'layer'" in prototype
    assert "size:clamp(Number(raw.scale)||1,.01,20)" in prototype
    assert "rotation:geonaphSeaLevelMap?0:" in prototype
    assert "frameLock:geonaphSeaLevelMap" in prototype
    assert "scale(${size})" in prototype
    assert "item.node.style.objectFit='fill';" in prototype
    assert ".user-image-placement.full-deed-frame-placement" in prototype_css
    assert "object-fit:fill!important" in prototype_css
    assert 'bool AssetScaleUsesZoneBasis=>CurrentBuilderScope=="WORLD";' in controller
    assert 'bool SelectedAssetUsesFullDeedFrame=>CurrentBuilderScope=="WORLD";' in controller
    assert "fullFrame=SelectedAssetUsesFullDeedFrame" in controller


def test_all_zones_keep_pre_controller_compact_placement_geometry():
    prototype = text("wwwroot/prototype/prototype.js")
    projection = text("wwwroot/worldbuilder-projection.js")

    assert "const COMPACT_TIER_PRESENTATION_STEP=.4;" in prototype
    assert "function presentationDepthForTier(tier)" in prototype
    assert "const depth=presentationDepthForTier(entry.tier);" in prototype
    assert "const depth=presentationDepthForTier(item.tier);" in prototype
    assert "world.style.transform=REGION_DEFINER" in prototype
    assert "TIER_REST_X_PER_LAYER" not in prototype
    assert "TIER_REST_Y_PER_LAYER" not in prototype
    assert "allParallaxRestOffset" not in prototype
    assert "tierRestOffset" not in prototype
    assert "const lift=hasPreviousTop?clamp(-tierStep*9*strength*spatialWeight,-42,0):0;" in projection
    assert "LAYER_VISUAL_GAP_PX" not in projection


def test_geonaph_tier_top_surfaces_keep_semantic_depth_but_use_compact_presentation():
    prototype = text("wwwroot/prototype/prototype.js")

    assert "Object.freeze({key:'surface',tier:0,layer:TIER_TOP_LAYER" in prototype
    assert "Object.freeze({key:'highlands',tier:1,layer:TIER_TOP_LAYER" in prototype
    assert "Object.freeze({key:'mountains',tier:2,layer:TIER_TOP_LAYER" in prototype
    assert "sceneZ:(asset.tier*LAYERS_PER_TIER)+asset.layer" in prototype
    assert "return{surface:1,highlands:index>=1?1:0,mountains:index>=2?1:0};" in prototype
    assert "const depth=presentationDepthForTier(entry.tier);" in prototype


def test_returning_to_endemar_home_restores_fitted_parallax_overview():
    controller = text("Components/UniversalInterface.razor")

    assert 'renderer=20261001-zone-fill-endemar-2' in controller
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


def test_fill_zone_preview_uses_the_full_world_viewer():
    controller = text("Components/UniversalInterface.razor")
    css = text("wwwroot/css/universal-interface.css")
    prototype = text("wwwroot/prototype/prototype.js")

    assert 'AssetScaleUsesZoneBasis?"zone-fill-preview":""' in controller
    assert ".asset-preview.zone-fill-preview{" in css
    assert ".asset-preview.zone-fill-preview img{" in css
    assert "object-fit:fill;" in css
    assert "item.node.style.objectFit='fill';" in prototype
    assert "size:clamp(Number(raw.size)||1,.01,20)" in prototype


def test_endemar_root_requires_explicit_endemar_zone_identity():
    prototype = text("wwwroot/prototype/prototype.js")
    assert "function layerZoneIdentity(item)" in prototype
    assert "worldBuilderSourceLayersForCurrentDeed(allSourceLayers,true)" in prototype
    assert "identity==='endemar'||(!strictIdentity&&!identity)" in prototype


def test_mmo_deed_grid_is_separate_from_recursive_300_cell_scope_geometry():
    cube = text("WorldSession.DefaultCube.cs")
    land = text("WorldSession.MmoLand.cs")
    regions = text("WorldSession.Regions.cs")
    host = text("Components/RegionDefinerWorkspace.razor")
    prototype = text("wwwroot/prototype/prototype.js")

    assert "public const int MmoParcelGridColumns = 30;" in land
    assert "public const int MmoParcelGridRows = 30;" in land
    assert "public const int DefaultCubeWidthCells = 30;" in cube
    assert "public const int DefaultWorldWidthCells = 300;" in cube
    assert "public const int SpatialScopeGridColumns = DefaultWorldWidthCells;" in cube
    assert "public const int SpatialScopeGridRows = DefaultWorldHeightCells;" in cube
    assert "public const int SpatialScopeZoomFactor = DefaultWorldWidthCells / DefaultCubeWidthCells;" in cube
    assert 'public const string SpatialWorldCoordinateSpace = "world-grid-300-v2";' in cube
    assert "SpatialScopeGridColumns * SpatialScopeGridRows" in regions
    assert "CoordinateSpace: SpatialWorldCoordinateSpace" in regions
    assert "gridColumns=WorldSession.SpatialScopeGridColumns" in host
    assert "gridRows=WorldSession.SpatialScopeGridRows" in host
    assert "const SCOPE_GRID_COLUMNS=300;" in prototype
    assert "const SCOPE_GRID_ROWS=300;" in prototype
    assert "const VIEWER_WINDOW_GRID_COLUMNS=30;" in prototype
    assert "const VIEWER_WINDOW_GRID_ROWS=30;" in prototype


def test_zoom_crosses_recursive_scope_every_ten_viewer_windows():
    prototype = text("wwwroot/prototype/prototype.js")

    assert "const SCOPE_TRANSITION_Z_LAYERS=LAYERS_PER_TIER;" in prototype
    assert "const SCOPE_ZOOM_FACTOR=SCOPE_GRID_COLUMNS/VIEWER_WINDOW_GRID_COLUMNS;" in prototype
    assert "REGION:SCOPE_ZOOM_FACTOR" in prototype
    assert "LOCAL:SCOPE_ZOOM_FACTOR*SCOPE_ZOOM_FACTOR" in prototype
    assert "INSTANCE:SCOPE_ZOOM_FACTOR*SCOPE_ZOOM_FACTOR*SCOPE_ZOOM_FACTOR" in prototype
    assert "const SCOPE_VIEW_ANGLE=Object.freeze({WORLD:0,REGION:15,LOCAL:30,INSTANCE:45});" in prototype
    assert "const SCOPE_DEPTH_PREFIX=Object.freeze({WORLD:'Z',REGION:'R',LOCAL:'L',INSTANCE:'I'});" in prototype
    assert "function zoomScopeSteps()" in prototype
    assert "return SCOPE_ORDER[Math.min(SCOPE_ORDER.length-1,base+zoomScopeSteps())];" in prototype
    assert "rotateX(${angle}deg)" in prototype
    assert "rist:spatial-scope-change" in prototype
    assert "const MAX_VIEW_ZOOM_RATIO=2048;" in prototype
