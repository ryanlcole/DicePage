from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_recursive_scope_format_and_scope_angles_are_canonical():
    source = read("WorldSession.RecursiveScopeEditor.cs")
    assert 'RecursiveScopeFormat = "RIST_RECURSIVE_SCOPE_V1"' in source
    assert '["WORLD"] = new("WORLD", 0, null)' in source
    assert '["REGION"] = new("REGION", 15, "WORLD")' in source
    assert '["LOCAL"] = new("LOCAL", 30, "REGION")' in source
    assert '["INSTANCE"] = new("INSTANCE", 45, "LOCAL")' in source


def test_layer_tier_and_coordinates_have_independent_mutators():
    source = read("WorldSession.RecursiveScopeEditor.cs")
    assert "SetRecursivePlacementPosition" in source
    assert "item with { X = x, Y = y }" in source
    assert "SetRecursivePlacementTier" in source
    assert "item with { Tier = NormalizeScopeTier(tier) }" in source
    assert "SetRecursivePlacementLayer" in source
    assert "item with { Layer = NormalizeScopeLayer(layer) }" in source
    assert "SetRecursivePlacementOpacity" in source
    assert "SetRecursivePlacementVisible" in source
    assert "SetRecursivePlacementLocked" in source
    assert "SetRecursivePlacementPermissionResource" in source


def test_world_render_order_uses_visual_layer_not_tier():
    source = read("WorldSession.RecursiveWorldBuilder.cs")
    method = source.split("GetRecursiveWorldRenderTiles()", 1)[1].split(
        "public double RecursiveWorldTileOpacity", 1
    )[0]
    assert ".OrderBy(item => item.Placement?.Layer ?? 1)" in method
    assert ".ThenBy(item => item.Index)" in method
    assert "Placement?.Tier" not in method
    assert "Tier is deliberately" in method


def test_new_worldbuilder_placement_never_encodes_visual_layer_as_legacy_z():
    source = read("Components/WorldBuilderStudio.Interactions.cs")
    creator = source.split("TileItem CreateViewerTile", 1)[1].split(
        "void AddViewerTile", 1
    )[0]
    placement = source.split("void AddViewerTile", 1)[1].split(
        "async Task<(int Column,int Row)?> ViewerCell", 1
    )[0]
    assert "LayerOffset = 0" in creator
    assert "PlacementId = $" in creator
    assert "if (upperTier)" in placement
    assert "forceFront: upperLayer" in placement
    assert "SceneZ + 1" not in placement


def test_asset_keyboard_uses_recursive_visual_layer_semantics():
    source = read("Components/WorldBuilderStudio.AssetKeyboard.cs")
    assert "forceFront: choice.UpperLayer" in source
    assert "LayerOffset = 0" in source
    assert "SceneAddress(Session.SceneZ + 1)" not in source


def test_worldbuilder_asset_list_exposes_gimp_and_shaelvien_concepts():
    source = read("Components/WorldBuilderStudio.razor")
    assert 'WORLD · 0°' in source
    assert "Layer = appearance · Tier = depth" in source
    assert "ToggleWorldVisibilityAsync" in source
    assert "ToggleWorldLockAsync" in source
    assert "SetWorldOpacityAsync" in source
    assert "scope-layer" in source
    assert "scope-tier" in source
    assert "Permission resource:" in source
    assert "legacy asset" in source
    assert "will not infer Layer or Tier from appearance" in source


def test_worldbuilder_map_uses_recursive_composition_only_when_requested():
    razor = read("Components/WorldMap.razor")
    code = read("Components/WorldMap.razor.cs")
    studio = read("Components/WorldBuilderStudio.razor")
    assert '<WorldMap UseRecursiveWorldComposition="true" />' in studio
    assert "@foreach(var t in RenderTiles)" in razor
    assert 'data-wb-index="@TileSessionIndex(t)"' in razor
    assert "GetRecursiveWorldRenderTiles()" in code
    assert "RecursiveWorldTileOpacity" in code
    assert "RecursiveWorldTileLocked" in code


def test_worldbuilder_js_uses_stable_session_identity_after_layer_sorting():
    core = read("wwwroot/worldbuilder-z-axis-core.js")
    zaxis = read("wwwroot/worldbuilder-z-axis.js")
    assert "dataset?.wbIndex" in core
    assert "dataset?.wbIndex" in zaxis
    assert "set.has(tileIndex(tile,index))" in core
    assert "set.has(tileIndex(t,i))" in zaxis
    hidden_layers = "for(const n of ['Layers','Tiers'])"
    assert hidden_layers not in zaxis


def test_worldbuilder_view_depth_is_tier_only():
    source = read("Components/WorldBuilderStudio.Menus.cs")
    assert "WorldSession.SceneZOf(Session.TierIndex, 0)" in source
    assert "Session.TierIndex + Math.Sign(delta)" in source
    add_layer = source.split("AddLayerAtSceneZFromJs", 1)[1].split(
        "[JSInvokable] public Task<double>", 1
    )[0]
    assert "GetWorldBuilderDepthState()" in add_layer
    assert "SetViewerSceneZFromJs" not in add_layer


def test_recursive_records_persist_in_world_save_and_map_card():
    models = read("WorldSession.Models.cs")
    persistence = read("WorldSession.Persistence.cs")
    cards = read("WorldSession.MapCards.cs")
    assert "RecursiveScopeFormat" in models
    assert "RecursiveScopePlacements" in models
    assert "RecursiveScopePlacements=ExportRecursiveScopePlacements()" in persistence
    assert "ImportRecursiveScopePlacements(save.RecursiveScopePlacements,save.RecursiveScopeFormat)" in persistence
    assert "const int MapCardVersion = 5" in cards
    assert "RecursiveScopePlacements = ExportRecursiveScopePlacements()" in cards
    assert "ImportRecursiveScopePlacements(card.RecursiveScopePlacements, card.RecursiveScopeFormat)" in cards


def test_legacy_content_is_never_silently_promoted():
    bridge = read("WorldSession.RecursiveWorldBuilder.cs")
    persistence = read("WorldSession.Persistence.cs")
    assert "Never silently migrate legacy content." in bridge
    assert "visual similarity never creates child scopes" in persistence


def test_world_scope_origin_is_first_authored_asset_not_canvas_position():
    editor = read("WorldSession.RecursiveScopeEditor.cs")
    bridge = read("WorldSession.RecursiveWorldBuilder.cs")
    assert "RecursiveScopeRoot" in editor
    assert "the first successfully authored" in editor
    assert "var localX = rootTile is null ? 0 : tile.X - rootTile.X;" in bridge
    assert "var localY = rootTile is null ? 0 : tile.Y - rootTile.Y;" in bridge
    assert "SyncRecursiveWorldCoordinates()" in bridge
    assert "X = tile.X - rootTile.X" in bridge
    assert "Y = tile.Y - rootTile.Y" in bridge


def test_recursive_permission_identity_reuses_server_asset_acl_namespace():
    editor = read("WorldSession.RecursiveScopeEditor.cs")
    bridge = read("WorldSession.RecursiveWorldBuilder.cs")
    permissions = read("Components/WorldBuilderStudio.Permissions.cs")
    assert '"asset:" + identity' in editor
    assert "RecursivePermissionResourceId(tile.PlacementId)" in bridge
    assert "Authority.GetResourcePermissionsAsync" in permissions
    assert "Authority.SetResourcePermissionAsync" in permissions
    assert "_scopePermissionPrincipal = "EVERYONE"" in permissions


def test_map_card_recursive_version_default_matches_writer():
    cards = read("WorldSession.MapCards.cs")
    assert "const int MapCardVersion = 5" in cards
    assert "public int Version { get; set; } = 5;" in cards


def test_first_world_asset_forces_recursive_tier_one():
    bridge = read("WorldSession.RecursiveWorldBuilder.cs")
    assert "var isFirstAsset = root is null;" in bridge
    assert "var tier = isFirstAsset ? 1" in bridge
    assert "SetRecursiveWorldTileTier(tile.PlacementId, 1)" in bridge


def test_layer_list_never_uses_tier_as_secondary_visual_order():
    studio = read("Components/WorldBuilderStudio.razor")
    visual_order = studio.split("WorldScopePlacements=>", 1)[1].split(
        "int LegacyWorldTileCount", 1
    )[0]
    assert "OrderByDescending(item=>item.Layer)" in visual_order
    assert "ThenBy(item=>item.Tier)" not in visual_order
    assert 'aria-pressed="@placement.Visible"' in studio
    assert 'aria-pressed="@placement.Locked"' in studio
