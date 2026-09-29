from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_local_request_selects_region_then_local_before_editor():
    component = (ROOT / "Components/UniversalInterface.razor").read_text(encoding="utf-8")
    assert "RequestedBuilderChainIndex" in component
    assert "_requestedBuilderChainIndex=requested" in component
    assert "BeginBuilderScope(_builderChainIndex+1,true);" in component
    assert "Editing remains locked until the requested" in component


def test_instance_request_selects_region_local_instance_in_order():
    component = (ROOT / "Components/UniversalInterface.razor").read_text(encoding="utf-8")
    assert 'BuilderChain=["WORLD","REGION","LOCAL","INSTANCE"]' in component
    assert "requested>=2&&Session.ActiveSpatialRegion is null" in component
    assert "requested>=3&&Session.ActiveLocal is null" in component
    assert "Session.SetActiveSpatialRegion(node.NodeId)" in component
    assert "Session.SetActiveLocal(node.NodeId)" in component
    assert "Session.SetActiveInstance(node.NodeId)" in component


def test_same_parent_reselection_preserves_deeper_selection():
    regions = (ROOT / "WorldSession.Regions.cs").read_text(encoding="utf-8")
    assert 'var changed = !string.Equals(_activeSpatialRegionId, node.NodeId, StringComparison.Ordinal);' in regions
    assert 'var changed = !string.Equals(_activeLocalId, node.NodeId, StringComparison.Ordinal);' in regions
    assert 'if (changed) _activeInstanceId = "";' in regions


def test_edit_readout_shows_full_chain_and_explicit_edit_depth():
    component = (ROOT / "Components/UniversalInterface.razor").read_text(encoding="utf-8")
    assert "CurrentEditContextPath" in component
    assert "EDIT DEPTH:" in component
    assert 'Stage.WorldBuilderTier=>$"{CurrentEditContextPath} → TIER"' in component
    assert 'Stage.WorldBuilderLayer=>$"{CurrentEditContextPath} → LAYER"' in component
