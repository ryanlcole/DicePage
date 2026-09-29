from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_shaelvien_gamemaster_deed_selection_is_separate_from_edit_home():
    component = (ROOT / "Components/ExperimentsWorkspace.razor").read_text(encoding="utf-8")
    assert "DeedSelect" in component
    assert "ContextSelect" in component
    assert 'Stage.DeedSelect=>"SHAELVIEN"' in component
    assert 'Stage.PathSelect=>IsShaelvienDeedHome?"WORLD BUILDER"' in component
    assert 'Stage.PathSelect=>IsShaelvienDeedHome?"CONTEXT"' in component
    assert "World Builder is on the left; Context is on the right." in component


def test_shaelvien_context_is_history_lore_truth_without_changing_edit_depth():
    component = (ROOT / "Components/ExperimentsWorkspace.razor").read_text(encoding="utf-8")
    assert 'ContextPath=["HISTORY","LORE","TRUTH"]' in component
    assert "Stage.ContextSelect=>ContextPath.Length" in component
    assert "Context does not change the selected spatial edit object." in component
    assert "IsDeedContextNode" in component


def test_deed_home_preserves_selection_first_spatial_hierarchy():
    component = (ROOT / "Components/ExperimentsWorkspace.razor").read_text(encoding="utf-8")
    assert 'Scopes=["WORLD","REGION","LOCAL","INSTANCE","CAMPAIGN"]' in component
    assert "Select a Region before editing its Tier or Layer." in component
    assert "Select a Local inside the active Region before editing its Tier or Layer." in component
    assert "Select an Instance inside the active Local before editing its Tier or Layer." in component
    assert "spatialNodeId=CurrentSpatialNodeId" in component
    assert "spatialPath=CurrentSpatialPath" in component


def test_deed_coordinates_are_endemar_relative_and_north_positive():
    gate = (ROOT / "Components/ShaelvienDeedGate.razor").read_text(encoding="utf-8")
    assert "var x=column-WorldSession.EndemarOriginColumn;" in gate
    assert "var y=WorldSession.EndemarOriginRow-row;" in gate
    assert 'return $"({x},{y})";' in gate
    assert "coordinate (0,0)" in gate
