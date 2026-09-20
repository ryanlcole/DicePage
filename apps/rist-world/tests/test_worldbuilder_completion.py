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


def test_roleplay_uses_canonical_prototype_viewer_and_alpha_assets_revalidate():
    workspace = (ROOT / "Components/WorkspaceSurface.razor").read_text()
    host = (ROOT / "Components/WorldBuilderGeonaphHost.razor").read_text()
    prototype = (ROOT / "wwwroot/prototype/index.html").read_text()
    workflow = (ROOT.parents[1] / ".github/workflows/deploy-rist-frontend-aws.yml").read_text()
    assert '<WorldBuilderGeonaphHost EmbeddedRoleplay="true" />' in workspace
    assert ".ws-table-host{box-sizing:border-box;position:relative;" in workspace
    assert "[Parameter] public bool EmbeddedRoleplay" in host
    assert "!EmbeddedRoleplay && Session.IsGeonaphWorld" in host
    assert "20260920-desktop-input-1" in host
    assert "20260920-desktop-input-1" in prototype
    assert "--cache-control 'public,max-age=0,must-revalidate'" in workflow
