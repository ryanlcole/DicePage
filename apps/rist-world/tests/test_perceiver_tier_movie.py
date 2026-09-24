from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_perceiver_is_live_on_shaelvien_landing_hub_without_replacing_immersion_builder():
    shell = read("Components/PublicAlphaShell.razor")
    router = read("Components/TaskWorkspaceRouter.razor")

    assert '<strong>PERCEIVER</strong>' in shell
    assert '@onclick="OpenPerceiver"' in shell
    assert 'void OpenPerceiver(){if(!WorldReady||!Session.IsGeonaphWorld)return;' in shell
    assert '"perceiver"' in shell
    assert '<PerceiverWorkspace OnStartMenu="OnStartMenu" OnHome="OnHome" />' in router

    # Perceiver is playback. ImmersionBuilder remains its separate authoring surface.
    assert '<strong>IMMERSIONBUILDER</strong>' in shell
    assert '<ImmersionBuilderWorkspace />' in router


def test_perceiver_reads_three_canonical_tiers_from_world_database_before_fallback():
    workspace = read("Components/PerceiverWorkspace.razor")

    assert "Session.LoadWorldBuilderSourceAsync()" in workspace
    assert 'state.TryGetProperty("tierImages"' in workspace
    assert ".Take(3)" in workspace
    assert "if(found.Length == 3)" in workspace
    assert '_sourceBadge = "DATABASE SOURCE · TRANSPARENT REPRESENTATION"' in workspace
    assert "CanonicalTransparentTierImages" in workspace
    assert "IsCanonicalEndemarTierSet(found)" in workspace
    assert "fallbackTierImages = _sourceTierImages" in workspace

    # Failure to hydrate the database must not strand the landing experience.
    assert "CanonicalFallbackTierImages" in workspace
    assert "DATABASE UNAVAILABLE · TRANSPARENT FALLBACK" in workspace


def test_perceiver_proof_sequence_and_reactive_depth_contract():
    player = read("wwwroot/perceiver-player.js")

    expected = [
        "{ label: 'Tier 1', tiers: [0] }",
        "{ label: 'Tier 2', tiers: [1] }",
        "{ label: 'Tier 3', tiers: [2] }",
        "{ label: 'Tier 1 + Tier 2', tiers: [0, 1] }",
        "{ label: 'Tier 1 + Tier 3', tiers: [0, 2] }",
        "{ label: 'Tier 2 + Tier 3', tiers: [1, 2] }",
        "{ label: 'Tier 1 + Tier 2 + Tier 3', tiers: [0, 1, 2] }",
    ]
    positions = [player.index(item) for item in expected]
    assert positions == sorted(positions)

    assert "const ENDEMAR_DEPTH_FACTORS = Object.freeze([0.28, 0.60, 1.0]);" in player
    assert "deviceorientation" in player
    assert "screenAdjusted" in player
    assert "applyPointerTarget" in player
    assert "lastMotionAt" in player
    assert "motionIsLive" in player
    assert "requestAnimationFrame" in player

    # A visual movie step changes visibility only; it never flattens tiers together.
    assert "state.layers.forEach" in player
    assert "image.style.opacity = visible ? '1' : '0';" in player
    assert "translate3d" in player


def test_perceiver_has_playback_and_accessibility_controls():
    workspace = read("Components/PerceiverWorkspace.razor")
    player = read("wwwroot/perceiver-player.js")

    for label in ["PLAY", "PAUSE", "↺", "Previous layer view", "Next layer view", "TILT", "FIT", "FULL SCREEN"]:
        assert label in workspace

    assert "prefers-reduced-motion: reduce" in player
    assert "prefers-reduced-motion:reduce" in workspace
    assert "tabindex=\"0\"" in workspace
    assert 'aria-label="Perceiver tiered movie player"' in workspace


def test_perceiver_transparency_is_a_derived_representation_not_a_canonical_asset_mutation():
    prepare = read("prepare_public_data.py")
    workspace = read("Components/PerceiverWorkspace.razor")
    player = read("wwwroot/perceiver-player.js")

    assert "build_geonaph_perceiver_representations" in prepare
    assert "assets' / 'perceiver" in prepare
    assert "source-alpha-preserved" in prepare
    assert "adaptive-delta-alpha" in prepare
    assert "edge-alpha-restored" in prepare
    assert "histogram_percentile" in prepare
    assert "ImageChops.difference" in prepare
    assert "ImageChops.multiply" in prepare
    assert "transparentRatio" in prepare
    assert "'canonical': False" in prepare

    assert "endemar_tier_1_perceiver_v001.png" in workspace
    assert "endemar_tier_2_perceiver_v001.png" in workspace
    assert "endemar_tier_3_perceiver_v001.png" in workspace

    assert "fallbackTierImages" in player
    assert "fallbackActive" in player


def test_perceiver_camera_matches_worldbuilder_interaction_model():
    workspace = read("Components/PerceiverWorkspace.razor")
    player = read("wwwroot/perceiver-player.js")
    prototype = read("wwwroot/prototype/prototype.js")

    assert "stage.addEventListener('wheel'" in prototype
    assert "pointers.size===2&&pinchStart" in prototype
    assert "zoomAt(e.clientX,e.clientY" in prototype

    assert "MIN_CAMERA_SCALE = 1" in player
    assert "MAX_CAMERA_SCALE = 256" in player
    assert "canvas.addEventListener('wheel'" in player
    assert "state.pointers.size === 2 && state.pinchStart" in player
    assert "zoomAt(state, event.clientX, event.clientY" in player
    assert "state.cameraX = state.panStart.x + (event.clientX - state.panStart.pointerX)" in player
    assert "export function zoomIn" in player
    assert "export function zoomOut" in player
    assert "export function fit" in player
    assert "data-perceiver-zoom" in workspace
    assert '@onclick="ZoomInAsync"' in workspace
    assert '@onclick="ZoomOutAsync"' in workspace
    assert '@onclick="FitAsync"' in workspace

    # Camera movement and tilt/parallax remain separate transforms.
    assert "state.camera.style.transform" in player
    assert "image.style.transform" in player


def test_perceiver_phone_video_spectral_converter_is_local_and_reactive():
    workspace = read("Components/PerceiverWorkspace.razor")
    player = read("wwwroot/perceiver-player.js")

    assert 'accept="video/*"' in workspace
    assert "data-perceiver-upload-button" in workspace
    assert "data-perceiver-video-input" in workspace
    assert "data-perceiver-endemar-button" in workspace
    assert "VIOLET · FASTEST · SHORTEST" in workspace
    assert "RED · SLOWEST · LONGEST" in workspace

    assert "URL.createObjectURL(file)" in player
    assert "URL.revokeObjectURL" in player
    assert "SPECTRAL_MAX_PIXELS = 512 * 288" in player
    assert "spectralTierForPixel" in player
    assert "rgbHue" in player
    assert "getImageData" in player
    assert "putImageData" in player
    assert "state.mode = 'spectral'" in player
    assert "state.currentStep = SPECTRAL_STEP_SEQUENCE.length - 1" in player
    assert "state.layers = state.spectralLayers" in player
    assert "renderSpectralFrame" in player
    assert "CAPTURING PARALLAX SPRITES" in player
    assert "LOCAL" in player

    # Existing parallax transform is reused for seven live spectral canvases.
    assert "state.layers.forEach" in player
    assert "SPECTRAL_DEPTH_FACTORS" in player
    assert "SPECTRAL_OVERSCAN" in player
    assert "deviceorientation" in player


def test_perceiver_centers_spectral_video_and_supports_fullscreen_with_ios_fallback():
    workspace = read("Components/PerceiverWorkspace.razor")
    player = read("wwwroot/perceiver-player.js")

    assert "data-perceiver-fullscreen-button" in workspace
    assert "perceiver-pseudo-fullscreen" in workspace
    assert "100dvh" in workspace

    assert "objectFit: 'contain'" in player
    assert "objectPosition: '50% 50%'" in player
    assert "width: '100%'" in player
    assert "height: '100%'" in player

    assert "requestFullscreen" in player
    assert "webkitRequestFullscreen" in player
    assert "perceiver-pseudo-fullscreen" in player
    assert "EXIT FULL SCREEN" in player
    assert "fullscreenchange" in player
    assert "webkitfullscreenchange" in player


def test_perceiver_video_import_uses_seven_frequency_layers_with_lower_tier_overscan():
    workspace = read("Components/PerceiverWorkspace.razor")
    player = read("wwwroot/perceiver-player.js")

    assert "const SPECTRAL_STEP_SEQUENCE" in player
    for tier in range(1, 8):
        assert f"data-perceiver-layer=\"{tier}\"" in workspace

    assert "data-perceiver-layer=\"all\"" in workspace
    assert "state.spectralLayers = [0, 1, 2, 3, 4, 5, 6].map" in player
    assert "SPECTRAL_DEPTH_FACTORS = Object.freeze([1.00, 0.88, 0.76, 0.64, 0.52, 0.40, 0.30])" in player
    assert "SPECTRAL_OVERSCAN = Object.freeze([1.24, 1.20, 1.16, 1.13, 1.10, 1.07, 1.04])" in player

    # Lowest/fastest spectral tiers move more and are deliberately enlarged more.
    assert "SPECTRAL_OVERSCAN[index]" in player
    assert "Violet · fastest" in player
    assert "Red · slowest" in player

    # Neutral/no-hue pixels remain a structural reference in the middle layer.
    assert "if (spectral.saturation < 0.10) return 3;" in player


def test_perceiver_uses_standard_sprite_sheets_for_movies():
    workspace = read("Components/PerceiverWorkspace.razor")
    player = read("wwwroot/perceiver-player.js")

    assert "VIDEO → SPRITES" in workspace
    assert "OPEN SPRITES" in workspace
    assert "SAVE SPRITES" in workspace
    assert "data-perceiver-sprite-button" in workspace
    assert "data-perceiver-save-sprites-button" in workspace
    assert "data-perceiver-sprite-input" in workspace
    assert 'accept="image/png,image/webp,image/jpeg"' in workspace
    assert "multiple data-perceiver-sprite-input" in workspace
    assert "OPEN MOVIE FILE" not in workspace
    assert "data-perceiver-movie-input" not in workspace

    # Existing normal sprite sheets are inferred directly, including the
    # generated 4x2 / 8-frame dragon and effect sheets.
    assert "parseSpriteFilename" in player
    assert "inferSpriteMeta" in player
    assert "frameCount: 8" in player
    assert "columns: 4" in player
    assert "rows: 2" in player
    assert "loadSpriteFiles" in player
    assert "renderSpriteFrame" in player
    assert "state.mode = 'sprite'" in player
    assert "knownSpriteLayout" in player
    assert "dragon_water" in player
    assert "dragon_celestial" in player
    assert "dragon_night" in player
    assert "foreground" in player
    assert "background" in player
    assert "effects" in player

    # Uploaded video is captured on presented video frames, split into the
    # seven parallax tiers, and exported as ordinary WebP sprite sheets.
    assert "requestVideoFrameCallback" in player
    assert "captureParallaxFrame" in player
    assert "finishVideoSpriteCapture" in player
    assert "canvas.toBlob(blob => resolve(blob), 'image/webp'" in player
    assert "__tier" in player
    assert "__fps" in player
    assert "__fw" in player
    assert "__fh" in player
    assert "__fc" in player
    assert "__page" in player
    assert "captureFps" in player
    assert "median(capture && capture.frameDeltas" in player
    assert "SPRITES READY" in player


def test_perceiver_keeps_legacy_ristmovie_reader_off_the_active_ui():
    workspace = read("Components/PerceiverWorkspace.razor")
    player = read("wwwroot/perceiver-player.js")

    # Backward compatibility may remain in code, but the user-facing path is
    # ordinary image sprite sheets so mobile file pickers need no custom type.
    assert "loadRistMovie" in player
    assert "data-perceiver-movie-button" not in workspace
    assert "data-perceiver-movie-input" not in workspace

def test_perceiver_mobile_controls_use_one_swipeable_slider():
    workspace = read("Components/PerceiverWorkspace.razor")

    assert 'class="perceiver-control-slider"' in workspace
    assert "overflow-x:auto" in workspace
    assert "-webkit-overflow-scrolling:touch" in workspace
    assert "scroll-snap-type:x proximity" in workspace
    assert "touch-action:pan-x" in workspace
    assert ".perceiver-control-slider::-webkit-scrollbar{display:none}" in workspace
    assert "min-width:max-content" in workspace
    assert "flex:0 0 auto" in workspace
    assert "padding:4px 4px max(8px,env(safe-area-inset-bottom))" in workspace
    assert ".perceiver-stage{min-height:260px}" in workspace
