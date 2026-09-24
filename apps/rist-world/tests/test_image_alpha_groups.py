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
