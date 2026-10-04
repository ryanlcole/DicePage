from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_spatial_title_handoff_is_loaded_after_canonical_viewer():
    index = (ROOT / "wwwroot/prototype/index.html").read_text(encoding="utf-8")

    prototype_pos = index.index("prototype.js?v=20261004-continuous-space-2")
    session_pos = index.index("spatial-selection-session.js?v=20261004-frozen-selection-2")
    handoff_pos = index.index("spatial-title-handoff.js?v=20261004-spatial-title-1")
    depth_pos = index.index("spatial-depth-authority.js?v=20261004-gm-depth-1")
    lock_pos = index.index("spatial-selector-lock.js?v=20261004-map-selector-lock-1")
    assert session_pos > prototype_pos
    assert handoff_pos > session_pos
    assert depth_pos > handoff_pos
    assert lock_pos > depth_pos


def test_hex_selection_is_anchored_to_visible_world_map_layers_not_viewer_stage():
    script = (ROOT / "wwwroot/prototype/spatial-title-handoff.js").read_text(encoding="utf-8")

    assert "function visibleMapLayers(snapshot)" in script
    assert "world.querySelectorAll('[data-tier][data-layer]')" in script
    assert "function anchorSelectorToMap()" in script
    assert "world.appendChild(overlay)" in script
    assert "overlay.dataset.coordinateSpace='world-map'" in script
    assert "mapSelectionAnchor=freezeSelectionSnapshot(initial)" in script
    assert "getSpatialSelection:anchoredSnapshot" in script


def test_select_area_freezes_exact_preselection_viewport_before_selector_starts():
    session = (ROOT / "wwwroot/prototype/spatial-selection-session.js").read_text(encoding="utf-8")

    pre = session.index("const preSelection=baseApi?.getSpatialSelection?.();")
    start = session.index("const started=baseApi?.beginSpatialSelection?.(raw);")
    assert pre < start
    assert "const preCamera=captureCameraVisual();" in session
    assert "const preWindow=freezeWindow(preSelection,raw);" in session
    assert "frozenWindow=preWindow;" in session
    assert "cameraVisual=preCamera;" in session
    assert "startCameraVisualLock();" in session
    assert "requestAnimationFrame(restoreCameraVisual);" in session
    assert "viewMinX:frozenWindow.viewMinX" in session
    assert "viewMaxY:frozenWindow.viewMaxY" in session


def test_spatial_editing_hides_map_chrome_without_hiding_semantic_controller():
    session = (ROOT / "wwwroot/prototype/spatial-selection-session.js").read_text(encoding="utf-8")

    assert ".universal-shell.spatial-map-selecting .depth-pip" in session
    assert ".universal-shell.spatial-map-selecting .viewer-compass" in session
    assert ".universal-shell.spatial-map-selecting .viewer-legend" in session
    assert ".universal-shell.spatial-map-selecting .asset-context-pip" in session
    assert ".universal-shell.spatial-map-selecting .viewer-reticle" in session
    assert ".viewer-menu-bar" not in session
    assert "shell?.classList.toggle('spatial-map-selecting',!!active);" in session


def test_gm_gets_tier_layer_controls_but_requester_does_not_allocate_depth():
    session = (ROOT / "wwwroot/prototype/spatial-selection-session.js").read_text(encoding="utf-8")
    depth = (ROOT / "wwwroot/prototype/spatial-depth-authority.js").read_text(encoding="utf-8")

    assert "const canAllocateDepth=String(query.get('access')||'view').toLowerCase()==='edit';" in session
    assert "GM DEED DEPTH" in session
    assert "DIRECT GM EDIT" in session
    assert "baseApi?.setExternalDepth?." in session
    assert "A requester selects X/Y and submits" in session
    assert "if(String(query.get('access')||'view').toLowerCase()!=='edit')return;" in depth
    assert "visibleTierIndices:[depth.tier]" in depth
    assert "visibleLayerOffsets:[depth.layer]" in depth


def test_gm_spatial_flow_saves_directly_without_self_approval_request():
    component = (ROOT / "Components/UniversalInterface.razor").read_text(encoding="utf-8")
    flow = component[component.index("async Task BeginOrSaveVisibleSpatialSelectionAsync()") : component.index("void SelectArtMethod()")]

    assert "CreateRegionAsync(" in flow
    assert "CreateSpatialNodeAsync(" in flow
    assert "SubmitClaimRequestAsync" not in flow
    assert "DecideClaimRequestAsync" not in flow


def test_camera_is_only_a_lens_during_active_hex_selection():
    handoff = (ROOT / "wwwroot/prototype/spatial-title-handoff.js").read_text(encoding="utf-8")
    lock = (ROOT / "wwwroot/prototype/spatial-selector-lock.js").read_text(encoding="utf-8")
    session = (ROOT / "wwwroot/prototype/spatial-selection-session.js").read_text(encoding="utf-8")

    assert "lockSelectorControls()" in handoff
    assert "blockCameraMutationWhileSelecting" in handoff
    assert ".spatial-selection-grid.active[data-coordinate-space=\"world-map\"]" in lock
    assert "new MutationObserver" in session
    assert "restoreCameraVisual()" in session


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


def test_viewer_only_seeds_new_placements_not_region_or_existing_object_selection():
    prototype = (ROOT / "wwwroot/prototype/prototype.js").read_text(encoding="utf-8")
    handoff = (ROOT / "wwwroot/prototype/spatial-title-handoff.js").read_text(encoding="utf-8")

    image_start = prototype[prototype.index("function openImageUpload()"):prototype.index("function fileDataUrl")]
    tile_start = prototype[prototype.index("function placeLibraryTile(asset)"):prototype.index("function libraryTileKey")]
    assert "viewerCenterPosition()" in image_start
    assert "viewerCenterPosition()" in tile_start

    existing = prototype[prototype.index("function beginImageDrag(event,item)"):prototype.index("function moveImageDrag")]
    assert "selectUserImage(item)" in existing
    assert "viewerCenterPosition()" not in existing

    assert "world.appendChild(overlay)" in handoff
    assert "overlay.dataset.coordinateSpace='world-map'" in handoff
    assert "viewerCenterPosition" not in handoff
