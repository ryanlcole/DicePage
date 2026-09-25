from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_relic_image_engine_boundary_loads_before_editor_and_has_local_fallback():
    index = read("wwwroot/prototype/index.html")
    engine = read("wwwroot/prototype/image-engine.js")
    player = read("wwwroot/prototype/prototype.js")

    assert "image-engine.js?v=20260925-image-engine-v1" in index
    assert index.index("image-engine.js") < index.index("prototype.js")
    assert "window.ReLiCImageEngine" in engine
    assert "registerGeglWasmAdapter" in engine
    assert "browser-fallback" in engine
    assert "localProcessing:true" in engine
    assert "const IMAGE_ENGINE=window.ReLiCImageEngine||null;" in player
    assert "IMAGE_ENGINE?.makeTransparent" in player
    assert "IMAGE_ENGINE?.crop" in player
    assert "IMAGE_ENGINE?.components" in player


def test_shared_asset_controls_apply_to_images_tiles_sprites_and_labels():
    player = read("wwwroot/prototype/prototype.js")

    assert "assetInteractionMode='select'" in player
    assert "function appendAssetInteractionControls" in player
    assert "function setAssetInteractionMode" in player
    assert "function toggleSelectedPositionLock" in player
    assert "function setSelectedStackPin" in player
    assert "function nudgeSelectedByPixels" in player

    for label in ("SELECT ✓", "MOVE ✓", "UNLOCK", "LOCK", "FRONT ✓", "BACK ✓"):
        assert label in player

    # Tiles and sprites share this path.
    assert "appendAssetInteractionControls(item);" in player
    # Labels and ordinary images call the shared controls directly.
    assert "appendAssetInteractionControls(selected);" in player
    assert "appendAssetInteractionControls(selectedImage);" in player


def test_asset_selection_is_separate_from_movement_and_supports_keyboard():
    player = read("wwwroot/prototype/prototype.js")

    assert "if(!alreadySelected)" in player
    assert "if(assetInteractionMode!=='move')" in player
    assert "if(item.positionLocked)" in player
    assert "function ensureAssetNodeAccessibility" in player
    assert "node.tabIndex=selectable?0:-1" in player
    assert "node.setAttribute('aria-pressed',String(selectedImage===item))" in player
    assert "event.key==='Enter'||event.key===' '" in player
    assert "['ArrowLeft','ArrowRight','ArrowUp','ArrowDown']" in player
    assert "event.shiftKey?1:8" in player


def test_visual_stack_is_integer_and_front_back_are_persistent():
    player = read("wwwroot/prototype/prototype.js")

    assert "CSS z-index accepts integers only" in player
    assert "Math.trunc(z)" in player
    assert "index/1000" not in player
    assert "index/100)" not in player
    assert "['front','back'].includes(item.stackPin)?item.stackPin:''" in player
    assert "['front','back'].includes(raw.stackPin)?raw.stackPin:''" in player
    assert "item.stackPin==='back'?-1:item?.stackPin==='front'?1:0" in player


def test_local_creation_uses_inline_mobile_accessible_name_field_not_prompt():
    player = read("wwwroot/prototype/prototype.js")

    assert "function localNameInput" in player
    assert "className='region-name-input local-name-input'" in player
    assert "input.setAttribute('aria-label','Local zone name')" in player
    assert "input.setAttribute('data-focus-key','local-name')" in player
    assert "if(event.key==='Enter')" in player
    assert "prompt('Name this Local'" not in player
    assert "Enter a Local name before creating the zone." in player


def test_mobile_asset_controls_keep_large_touch_targets():
    css = read("wwwroot/prototype/prototype.css")

    assert "Shared asset interaction: touch-first" in css
    assert '.stage[data-asset-interaction="select"]' in css
    assert '.stage[data-asset-interaction="move"]' in css
    assert ".user-image-placement[data-position-locked="true"]" in css
    assert ".keyboard-keys .local-name-input" in css
    assert "min-height:48px" in css
