from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_campaign_is_behavior_not_geometry():
    contract = read("CAMPAIGN_BEHAVIOR_CONTRACT.md")
    model = read("WorldSession.CampaignBehavior.cs")
    record = model.split("public sealed record CampaignBehaviorRule(", 1)[1].split(");", 1)[0]
    assert "Campaign Builder is **not** another geometry editor." in contract
    for field in (" X,", " Y,", "Elevation", "Tier", "Layer", "GridShape", "Column", "Row"):
        assert field not in record


def test_campaign_behavior_vocabulary_matches_canonical_boundary():
    model = read("WorldSession.CampaignBehavior.cs")
    for kind in (
        "PERCEPTION_THRESHOLD",
        "CONTEXTUAL_INTERACTION",
        "TRAP",
        "ENEMY_TRIGGER",
        "INITIATIVE_PRESENTATION",
        "NPC",
        "LOOT",
        "ENCOUNTER",
    ):
        assert f'"{kind}"' in model


def test_campaign_rule_identity_and_target_identity_are_stable_fields():
    model = read("WorldSession.CampaignBehavior.cs")
    assert "string RuleId" in model
    assert "string TargetKind" in model
    assert "string TargetId" in model
    assert 'RuleId: $"campaign-rule-{Guid.NewGuid():N}"' in model
    assert 'TargetId = (rule.TargetId ?? "").Trim()' in model


def test_campaign_target_kinds_cover_recursive_identity_graph():
    model = read("WorldSession.CampaignBehavior.cs")
    assert '"WORLD" or "REGION" or "LOCAL" or "INSTANCE" or "ASSET" or "CELL" or "SURFACE"' in model


def test_campaign_behavior_persists_outside_map_geometry():
    model = read("WorldSession.CampaignBehavior.cs")
    assert 'CampaignBehaviorFormat = "RIST_CAMPAIGN_BEHAVIOR_V1"' in model
    assert 'campaign/behavior.json' in model
    assert "SaveCampaignBehaviorAsync" in model
    assert "UpsertCampaignBehaviorRuleAsync" in model
    assert "DeleteCampaignBehaviorRuleAsync" in model


def test_campaign_workspace_exposes_behavior_editor_without_geometry_controls():
    component = read("Components/CampaignWorkspace.razor")
    assert ">BEHAVIORS</button>" in component
    assert 'Campaign references geometry; it does not own it.' in component
    assert "WorldSession.CampaignBehaviorKinds" in component
    assert "UpsertCampaignBehaviorRuleAsync" in component
    assert "DeleteCampaignBehaviorRuleAsync" in component
    assert "TARGET KIND" in component
    assert "TARGET ID" in component
    assert "THRESHOLD" in component
    assert "TRIGGER" in component
    assert "ACTION / RESULT" in component
    assert "PAYLOAD REFERENCE" in component


def test_campaign_quick_targets_include_every_instance_cell_and_surface():
    component = read("Components/CampaignWorkspace.razor")
    target_loader = component.split("async Task LoadBehaviorTargetsAsync", 1)[1].split(
        "void CollectBehaviorAssetTargets", 1
    )[0]
    assert "for(var row=0;row<source.State.GridRows;row++)" in target_loader
    assert "for(var column=0;column<source.State.GridColumns;column++)" in target_loader
    assert 'AddBehaviorTarget("CELL",cellId' in target_loader
    assert "WorldSession.InstanceSurfacesForCell(source.State,column,row)" in target_loader
    assert 'AddBehaviorTarget("SURFACE",surface.SurfaceId' in target_loader
    assert 'AddBehaviorTarget("ASSET",asset.PlacementId' in target_loader


def test_campaign_permission_directory_includes_instance_placements():
    component = read("Components/CampaignWorkspace.razor")
    loader = component.split("async Task LoadAssetResourcesAsync", 1)[1].split(
        "void CollectAssetResources", 1
    )[0]
    assert "await Session.LoadInstancesAsync()" in loader
    assert "Session.DefinedInstances" in loader
    assert "Session.LoadInstanceMapAsync(instance.InstanceId)" in loader
    assert "CollectInstanceAssetResources(source.State,instance.Name)" in loader
    helper = component.split("void CollectInstanceAssetResources", 1)[1].split(
        "async Task ChangeAssetResourceAsync", 1
    )[0]
    assert "asset.PermissionResourceId" in helper
    assert "WorldSession.RecursivePermissionResourceId(asset.PlacementId)" in helper


if __name__ == "__main__":
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
    print(f"Campaign behavior contract: {len(tests)} checks passed")
