from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_filtered_quick_slot_uses_persistent_index():
    component = (ROOT / "Components/WorldBuilderStudio.razor").read_text()
    script = (ROOT / "wwwroot/worldbuilder-z-axis-core.js").read_text()
    assert 'data-quick-index="@_quickTiles.IndexOf(tile)"' in component
    expression = script.split("const quickIndexFor=", 1)[1].split("\n const placeQuick=", 1)[0].rstrip(";")
    subprocess.run(["node", "-e", f"""
const indexFor = {expression};
const assert = require('node:assert/strict');
// A visible first item can be the fifth item in the underlying quick rail.
assert.equal(indexFor({{dataset: {{quickIndex: '4'}}}}), 4);
for (const value of ['', '-1', 'NaN', '1.5']) {{
 assert.equal(indexFor({{dataset: {{quickIndex: value}}}}), -1);
}}
assert.equal(indexFor(null), -1);
"""], check=True)


def test_native_drag_matches_selected_footprint_and_undo():
    component = (ROOT / "Components/WorldBuilderStudio.razor").read_text()
    drop = component.split("async Task DropQuickAsset", 1)[1].split("async Task SaveAsync", 1)[0]
    assert "tile.DefaultFootprint" not in drop
    assert "Session.CanEditTiles" in drop
    assert "PushWorldBuilderUndo()" in drop
    assert "AddViewerTile(" in drop


def test_history_rejects_other_world_or_external_changes():
    source = (ROOT / "Components/WorldBuilderStudio.Interactions.cs").read_text()
    assert "Session.WorldId" in source
    assert "Session.TierIndex" in source
    assert "Session.LayerOffset" in source
    assert "_historyExpected.SequenceEqual(Session.PlacedTiles)" in source
    assert "!Session.PlacedTiles[index].Locked" in source
    assert "_worldBuilderUndo.Take(30).Reverse()" in source


def test_action_failure_keeps_dialog_open():
    script = (ROOT / "wwwroot/worldbuilder-z-axis.js").read_text()
    perform = script.split("const perform=", 1)[1].split("const openSave=", 1)[0]
    assert "await action();close()" in perform
    assert "setAttribute('role','alert')" in perform
    assert "catch{}close()" not in script


def test_mmo_roleplay_uses_visual_front_while_sandbox_keeps_light_viewer():
    workspace = (ROOT / "Components/WorkspaceSurface.razor").read_text()
    host = (ROOT / "Components/WorldBuilderGeonaphHost.razor").read_text()
    front = (ROOT / "Components/ShaelvienMmoFront.razor").read_text()
    router = (ROOT / "Components/TaskWorkspaceRouter.razor").read_text()
    shell = (ROOT / "Components/PublicAlphaShell.razor").read_text()
    prototype = (ROOT / "wwwroot/prototype/index.html").read_text()
    workflow = (ROOT.parents[1] / ".github/workflows/deploy-rist-frontend-aws.yml").read_text()

    # Sandbox/light roleplay keeps the existing canonical viewer path.
    assert '<WorldBuilderGeonaphHost EmbeddedRoleplay="true" OnHome="OnHome" OnStartMenu="OnStartMenu" />' in workspace
    assert '<WorkspaceSurface Mode="@Mode" OnHome="OnHome" OnStartMenu="OnStartMenu" />' in router

    # Shaelvien MMO enters a distinct visual/social front instead of turning the
    # Worldbuilder into the roleplay shell.
    assert 'Mode == "roleplay" && Session.IsGeonaphWorld' in router
    assert '<ShaelvienMmoFront />' in router
    assert "geonaph_full_static_canonical_surface_v001.png" in front
    assert "Hire GameMaster" in front
    assert "Recruit Players" in front
    assert ">Campaigns<" in front
    assert ">Modules<" in front
    assert "JOIN PARTY" in front
    assert 'aria-label="Zone chat"' in front
    assert "MESSAGE GM" in front
    assert "WORLD MAP → ZONE → PARTY → CHAT" in shell

    assert '[Parameter] public EventCallback OnHome' in workspace
    assert ".ws-table-host{box-sizing:border-box;position:relative;" in workspace
    assert "[Parameter] public bool EmbeddedRoleplay" in host
    assert "!EmbeddedRoleplay && Session.IsGeonaphWorld" in host
    assert "20260920-desktop-input-1" in host
    assert "20260920-desktop-input-1" in prototype
    assert "--cache-control 'public,max-age=0,must-revalidate'" in workflow


def test_image_and_tile_can_be_full_world_or_adjustable_layers():
    prototype = (ROOT / "wwwroot/prototype/index.html").read_text()
    script = (ROOT / "wwwroot/prototype/prototype.js").read_text()
    style = (ROOT / "wwwroot/prototype/prototype.css").read_text()
    assert 'id="imagePlacementRole"' in prototype
    assert 'value="world-map"' in prototype
    assert 'World Map / Sea Level · 100% × 100%' in prototype
    assert "function isWorldMapItem(item)" in script
    assert "placementRole:isWorldMapItem(item)?'world-map':'layer'" in script
    assert "placementRole,fullWorld:placementRole==='world-map'" in script
    assert "appendPlacementRoleControls()" in script
    assert "full-world-placement" in script
    assert "World Map always fills 100% by 100% of the world." in script
    assert ".user-image-placement.full-world-placement" in style
    assert "width:100%!important;height:100%!important" in style


def test_empty_world_starts_with_sea_level_reference():
    prototype = (ROOT / "wwwroot/prototype/index.html").read_text()
    script = (ROOT / "wwwroot/prototype/prototype.js").read_text()
    assert "20260920-sea-level-reference-1" in prototype
    assert "DEFAULT_SEA_LEVEL_REFERENCE" in script
    assert "tilesets/world/terrain/ocean/ocean-067/tile-03-03.jpg" in script
    assert "stage.dataset.seaLevelReference='ocean'" in script
    assert "surface.dataset.referenceOnly='true'" in script
    assert "surface.src=DEFAULT_SEA_LEVEL_REFERENCE" in script
    assert "Sea Level ocean reference ready." in script
    assert "intentionally not serialized as authored world content" in script


def test_sandbox_owner_can_edit_while_authority_refresh_is_transient():
    relationships = (ROOT / "WorldSession.WorldRelationships.cs").read_text()
    source = (ROOT / "WorldSession.WorldBuilderSource.cs").read_text()
    host = (ROOT / "Components/WorldBuilderGeonaphHost.razor").read_text()
    assert "HasLoadedSandboxOwnerAuthority" in relationships
    assert "HasWorldBuilderEditAuthority" in relationships
    assert '_activeWorldRelationship = "owner"' in relationships
    assert "privateOwnerAtEntry" in source
    assert "HasOwnedPrivateWorldDescriptorAsync" in source
    assert 'var access=Session.HasWorldBuilderEditAuthority?"edit":"view";' in host


def test_empty_world_and_claimed_region_are_visually_actionable():
    prototype = (ROOT / "wwwroot/prototype/index.html").read_text()
    script = (ROOT / "wwwroot/prototype/prototype.js").read_text()
    style = (ROOT / "wwwroot/prototype/prototype.css").read_text()
    assert "20260920-don-blockers-1" in prototype
    assert "world.style.transformOrigin='0 0'" in script
    assert "function syncClaimedRegionOutline(region)" in script
    assert "REGION_FLOW==='existing'&&ACCESS_MODE==='edit'" in script
    assert "if(editableExisting)keyboardMode='Tiles'" in script
    assert "if(keyboard.hidden)openKeyboard()" in script
    assert "point=REGION_DEFINER?snapRegionPoint" in script
    assert ".region-claim-outline" in style
    assert "radial-gradient(circle at 50% 42%" in style
