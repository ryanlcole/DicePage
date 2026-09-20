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

    assert "const DEPTH_FACTORS = Object.freeze([0.28, 0.60, 1.0]);" in player
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

    for label in ["PLAY", "PAUSE", "RESTART", "NEXT ▶", "◀ PREV", "TILT / MOTION", "FIT"]:
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
    assert "delta-alpha" in prepare
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
