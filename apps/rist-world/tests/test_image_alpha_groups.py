from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_transparent_images_rebuild_derived_representation_after_reload():
    player = read("wwwroot/prototype/prototype.js")

    assert "async function preparedImageSource(" in player
    assert "transparent:!!raw.transparent" in player
    assert "alphaCrop:raw.alphaCrop" in player
    assert "alphaComponentSeed:raw.alphaComponentSeed" in player
    assert "item.transparentSrc=await preparedImageSource(fresh" in player
    assert "item.transparentSrc=fresh;" in player  # sprite branch remains direct
    assert "else{\n          item.transparentSrc=await preparedImageSource" in player


def test_alpha_split_creates_persistent_linked_selection_groups():
    player = read("wwwroot/prototype/prototype.js")

    assert "async function alphaComponentAnalysis(source)" in player
    assert "async function splitImageByAlpha(item=selectedImage)" in player
    assert "linkGroupId:groupId" in player
    assert "linkGroupIndex:index" in player
    assert "linkGroupCount:analysis.pieces.length" in player
    assert "alphaCrop:normalizeAlphaCrop(item.alphaCrop)" in player
    assert "alphaComponentSeed:normalizeAlphaSeed(item.alphaComponentSeed)" in player
    assert "linkGroupId:String(item.linkGroupId||'')" in player
    assert "linkGroupId:String(raw.linkGroupId||'')" in player


def test_linked_alpha_pieces_move_together_until_unlinked():
    player = read("wwwroot/prototype/prototype.js")

    assert "function linkedSelectionMembers(item=selectedImage)" in player
    assert "function unlinkSelectedGroup()" in player
    assert "move pieces separately" in player
    assert "moves as one selection" in player
    assert "imageDrag={id:event.pointerId,item,startX:event.clientX,startY:event.clientY" in player
    assert "members:linked.map(member=>" in player
    assert "for(const entry of next){entry.item.x=entry.x;entry.item.y=entry.y;refreshUserImage(entry.item)}" in player


def test_split_preserves_lead_object_identity_for_existing_local_anchors():
    player = read("wwwroot/prototype/prototype.js")

    assert "Preserve the original object identity on the lead piece" in player
    assert "id:index===0?String(item.id" in player
    assert "authorityResourceId:index===0?String(item.authorityResourceId||'')" in player


def test_linked_selection_has_visible_group_outline():
    css = read("wwwroot/prototype/prototype.css")

    assert ".user-image-placement.linked-selected" in css


def test_image_engine_allows_remote_pixel_reads_and_uses_connected_border_background():
    engine = read("wwwroot/prototype/image-engine.js")

    assert "img.crossOrigin='anonymous'" in engine
    assert "authoredAlpha/Math.max(count,1)>.01" in engine
    assert "dominant.count/Math.max(samples.length,1)<.12" in engine
    assert "remove only pixels connected to the image boundary" in engine
    assert "seen=new Uint8Array(count),queue=new Int32Array(count)" in engine


def test_pixels_keyboard_owns_transparency_and_cut_tools():
    player = read("wwwroot/prototype/prototype.js")
    index = read("wwwroot/prototype/index.html")

    assert "function renderPixelsKeyboard()" in player
    assert "if(keyboardMode==='Pixels'){renderPixelsKeyboard();return}" in player
    assert "MAKE TRANSPARENT" in player
    assert "CUT ALPHA" in player
    assert "remove connected border background" in player
    assert "toolKey('PIXELS',selectedImage.transparent?'alpha enabled':'transparency / cut'" in player
    assert "image-engine-v2" in index
    assert "asset-controls-v12" in index
