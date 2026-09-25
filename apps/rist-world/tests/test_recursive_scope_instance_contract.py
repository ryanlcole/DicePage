from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_instance_scope_is_registered_at_45_degrees():
    scope = read("WorldSession.RecursiveScopeEditor.cs")
    assert '["INSTANCE"] = new("INSTANCE", 45, "LOCAL")' in scope
    assert '"ENCOUNTER" or "TACTICAL" => "INSTANCE"' in scope


def test_instance_builder_only_uses_named_marker_kinds():
    model = read("WorldSession.Instances.cs")
    component = read("Components/InstanceBuilderWorkspace.razor")
    assert 'return value is "label" or "pin" or "marker";' in model
    assert "WorldSession.IsInstanceMarkerKind(item.Kind)" in component


def test_instance_contract_uses_explicit_marker_and_touched_asset_root():
    contract = read("INSTANCE_RECURSIVE_SCOPE_CONTRACT.md")
    model = read("WorldSession.Instances.cs")
    assert "named marker" in contract
    assert "TouchedAssetId" in model
    assert "MarkerAssetId" in model
    assert "The marker and touched asset must be separate stable identities." in model
    assert "Choose a saved Local label, pin, or marker as the named Instance marker." in model
    assert "IsInstanceMarkerKind(item.Kind)" in model
    assert "The touched asset is not part of the selected Local." in model


def test_instance_catalog_references_local_without_copying_parent_geometry():
    model = read("WorldSession.Instances.cs")
    assert 'ParentNodeId: $"local:{local.LocalId}"' in model
    assert "RecursiveScopeFormat: RecursiveScopeFormat" in model
    assert "ViewDegrees: 45" in model
    assert "LocalId: local.LocalId" in model


def test_instance_cells_own_signed_elevation_and_terrain_rules():
    model = read("WorldSession.Instances.cs")
    assert "int ElevationSteps = 0" in model
    assert "string TerrainType = """ in model
    assert "double MovementCost = 1" in model
    assert "bool BlocksMovement = false" in model
    assert "bool BlocksSight = false" in model
    assert "string Tags = """ in model
    assert "string Notes = """ in model


def test_every_ten_elevation_steps_crosses_one_parallax_band():
    model = read("WorldSession.Instances.cs")
    assert "public static int InstanceElevationParallaxBand(int elevationSteps) => elevationSteps / 10;" in model


def test_measurement_reuses_world_authority_without_rewriting_steps():
    model = read("WorldSession.Instances.cs")
    component = read("Components/InstanceBuilderWorkspace.razor")
    contract = read("INSTANCE_RECURSIVE_SCOPE_CONTRACT.md")
    assert "FormatInstanceElevationForCurrentMeasurement" in model
    formatter = model.split("public string FormatInstanceElevationForCurrentMeasurement", 1)[1].split(
        "public static bool IsInstanceMarkerKind", 1
    )[0]
    assert "elevationSteps * InstanceElevationUnitsPerStep" in formatter
    assert "MeasurementUnitName(value)" in formatter
    assert "ElevationSteps" not in formatter
    assert "InstanceElevationUnitsPerStep => Math.Max(MinMeasurementPerCell, GridDistance) / 10d;" in model
    assert "Session.InstanceElevationStepSummary" in component
    assert "Session.MeasurementCellSummary" in component
    assert "Session.FormatInstanceElevationForCurrentMeasurement(_cellElevation)" in component
    assert "SaveMeasurementAsync" not in component
    assert "reuses the world's existing physical/Measurefict measurement authority" in contract


def test_top_surface_identity_is_stable_and_exposed_sides_are_step_addressed():
    model = read("WorldSession.Instances.cs")
    surface = model.split("public static string InstanceSurfaceId", 1)[1].split(
        "public static IReadOnlyList<WorldInstanceSurface>", 1
    )[0]
    assert ':surface:top"' in surface
    assert ':surface:{normalizedFace}:step:{elevationStep}' in surface

    exposed = model.split("public static IReadOnlyList<WorldInstanceSurface>", 1)[1].split(
        "public static WorldInstanceCellState InstanceCellAt", 1
    )[0]
    assert "if (cellElevation <= neighborElevation) continue;" in exposed
    assert "for (var step = neighborElevation + 1; step <= cellElevation; step++)" in exposed


def test_instance_asset_tier_and_layer_are_separate_one_based_fields():
    model = read("WorldSession.Instances.cs")
    assert "Tier = WorldSession.NormalizeScopeTier(Tier)" in model
    assert "Layer = WorldSession.NormalizeScopeLayer(Layer)" in model

    component = read("Components/InstanceBuilderWorkspace.razor")
    layer_move = component.split("async Task MovePlacementLayerAsync", 1)[1].split(
        "async Task MovePlacementTierAsync", 1
    )[0]
    tier_move = component.split("async Task MovePlacementTierAsync", 1)[1].split(
        "async Task SetPlacementOpacityAsync", 1
    )[0]
    assert "Layer=Math.Max(1,asset.Layer+Math.Sign(delta))" in layer_move
    assert "Tier=" not in layer_move
    assert "Tier=Math.Max(1,asset.Tier+Math.Sign(delta))" in tier_move
    assert "Layer=" not in tier_move


def test_instance_asset_list_orders_by_layer_not_tier():
    component = read("Components/InstanceBuilderWorkspace.razor")
    assert "_map.Assets.OrderByDescending(x=>x.Layer).ThenBy(x=>x.PlacementId" in component
    assert "INSTANCE ASSETS · 45°" in component
    assert "Layer = appearance · Tier = depth" in component


def test_instance_permissions_are_server_authoritative():
    component = read("Components/InstanceBuilderWorkspace.razor")
    model = read("WorldSession.Instances.cs")
    assert "Authority.GetResourcePermissionsAsync" in component
    assert "Authority.SetResourcePermissionAsync" in component
    assert "PermissionResourceId" in model
    assert "RecursivePermissionResourceId(placementId)" in component


def test_instance_map_persists_separately_from_local_map():
    model = read("WorldSession.Instances.cs")
    assert 'InstanceMapFormat = "RIST_INSTANCE_MAP_V1"' in model
    assert 'WorldStoragePrefix}/instances/' in model
    assert "LoadInstanceMapAsync" in model
    assert "SaveInstanceMapAsync" in model
    assert "LoadLocalMapAsync(local.LocalId)" in model


def test_instance_launcher_and_router_use_dedicated_workspace():
    shell = read("Components/PublicAlphaShell.razor")
    router = read("Components/TaskWorkspaceRouter.razor")
    assert '@onclick="OpenInstance"' in shell
    assert 'OpenWorkspace("instance","INSTANCE BUILDER","LOCAL 30° → MARKER + ASSET → INSTANCE 45°")' in shell
    assert '"world","local","instance","accessibility"' in shell
    assert 'case "instance":_workspaceMode="instance"' in shell
    assert 'else if (Mode == "instance")' in router
    assert "<InstanceBuilderWorkspace" in router


def test_instance_builder_exposes_cell_rules_surfaces_and_gimp_asset_controls():
    component = read("Components/InstanceBuilderWorkspace.razor")
    for text in (
        "SAVE CELL RULES",
        "VALID SURFACES",
        "PLACE ON SELECTED SURFACE",
        "INSTANCE ASSETS · 45°",
        "PERMISSION FOR",
        "ELEVATION DISPLAY",
        "Every 10 steps = 1 parallax band",
    ):
        assert text in component


if __name__ == "__main__":
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
    print(f"recursive Instance scope contract: {len(tests)} checks passed")
