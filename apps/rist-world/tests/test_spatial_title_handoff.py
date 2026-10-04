from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_spatial_title_handoff_is_loaded_after_canonical_viewer():
    index = (ROOT / "wwwroot/prototype/index.html").read_text(encoding="utf-8")

    prototype_pos = index.index("prototype.js?v=20261004-continuous-space-2")
    handoff_pos = index.index("spatial-title-handoff.js?v=20261004-spatial-title-1")
    lock_pos = index.index("spatial-selector-lock.js?v=20261004-map-selector-lock-1")
    assert handoff_pos > prototype_pos
    assert lock_pos > handoff_pos


def test_hex_selection_is_anchored_to_visible_world_map_layers_not_viewer_stage():
    script = (ROOT / "wwwroot/prototype/spatial-title-handoff.js").read_text(encoding="utf-8")

    assert "function visibleMapLayers(snapshot)" in script
    assert "world.querySelectorAll('[data-tier][data-layer]')" in script
    assert "function anchorSelectorToMap()" in script
    assert "world.appendChild(overlay)" in script
    assert "overlay.dataset.coordinateSpace='world-map'" in script
    assert "mapSelectionAnchor=freezeSelectionSnapshot(initial)" in script
    assert "getSpatialSelection:anchoredSnapshot" in script
    assert "visibleTierIndices:[...anchor.visibleTierIndices]" in script
    assert "visibleLayerOffsets:[...anchor.visibleLayerOffsets]" in script


def test_camera_is_only_a_lens_during_active_hex_selection():
    handoff = (ROOT / "wwwroot/prototype/spatial-title-handoff.js").read_text(encoding="utf-8")
    lock = (ROOT / "wwwroot/prototype/spatial-selector-lock.js").read_text(encoding="utf-8")

    assert "lockSelectorControls()" in handoff
    assert "const ids=['zoomIn','zoomOut','fit','settingsFit','tierToggle']" in handoff
    assert "blockCameraMutationWhileSelecting" in handoff
    assert "stage?.addEventListener('wheel'" in handoff
    assert "releaseSelectorFromMap()" in handoff
    assert ".spatial-selection-grid.active[data-coordinate-space=\"world-map\"]" in lock
    assert "if(event.pointerType==='touch')blockTouchCameraMove(event);" in lock
    assert "document.addEventListener('touchmove',blockTouchCameraMove" in lock
    assert "['+','=','-','_','f','t']" in lock


def test_spatial_name_uses_text_editor_and_requires_enter_instead_of_browser_prompt():
    script = (ROOT / "wwwroot/prototype/spatial-title-handoff.js").read_text(encoding="utf-8")

    assert "if(String(message||'')==='Name this space')return beginSpatialTitle(defaultValue);" in script
    assert "return nativePrompt('Name this space'" not in script
    assert "function createDraftTitle(snapshot)" in script
    assert "const center=selectionCenter(snapshot)" in script
    assert "openLabelsComposer()" in script
    assert "Name this area · Enter to save" in script
    assert "if(event.key==='Enter')" in script
    assert "if(!name)" in script
    assert "resolve(name)" in script


def test_saved_boundary_title_returns_to_existing_label_editor_for_font_and_position():
    script = (ROOT / "wwwroot/prototype/spatial-title-handoff.js").read_text(encoding="utf-8")

    assert "input.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter'" in script
    assert "editor.placeholder='Edit title text'" in script
    assert "Title selected; adjust font and position" in script
