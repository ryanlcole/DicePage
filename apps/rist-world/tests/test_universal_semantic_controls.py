from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def text(path):
    return (REPO / path).read_text(encoding="utf-8")


def test_sheet14_semantic_contract_is_stable_and_rules_agnostic():
    contract = text("apps/rist-world/UniversalSemanticControls.cs")

    assert 'ContractId = "rist.semantic-controls.v1"' in contract
    for action in (
        'Intent = "intent"',
        'Target = "target"',
        'Method = "method"',
        'Modify = "modify"',
        'Confirm = "confirm"',
        'Resolve = "resolve"',
        'Outcome = "outcome"',
        'FollowUp = "followup"',
        'CustomProcedure = "custom.procedure"',
    ):
        assert action in contract

    assert "CanonicalPlayFlow" in contract
    assert "GenericTtrpgRulesAdapter" in contract
    assert '"UNKNOWN_RULES_REMAIN_UNKNOWN"' in contract
    assert '"manual-or-custom"' in contract


def test_universal_shell_routes_touch_keyboard_gamepad_through_semantic_bus():
    razor = text("apps/rist-world/Components/UniversalInterface.razor")
    semantic = text("apps/rist-world/Components/UniversalInterface.SemanticControls.cs")
    input_js = text("apps/rist-world/wwwroot/universal-interface-input.js")

    assert 'data-semantic-contract="@SemanticContractId"' in razor
    assert 'data-semantic-action="@CurrentLeftSemanticId"' in razor
    assert 'data-semantic-action="@UniversalSemanticControls.Action.Select"' in razor
    assert 'data-semantic-action="@CurrentRightSemanticId"' in razor
    assert "ReceiveSemanticHardwareInputAsync(control,direction)" in razor

    assert 'case "x":' in semantic
    assert "UniversalSemanticControls.Action.NavigateX" in semantic
    assert 'case "y":' in semantic
    assert "UniversalSemanticControls.Action.NavigateY" in semantic
    assert 'case "select":' in semantic
    assert "UniversalSemanticControls.Action.Select" in semantic
    assert 'case "left":' in semantic
    assert 'case "right":' in semantic

    assert 'edgeButton(gamepad, 0, "left")' in input_js
    assert 'edgeButton(gamepad, 1, "right")' in input_js
    assert 'edgeButton(gamepad, 10, "select")' in input_js


def test_sheet14_experience_and_control_representations_are_connected():
    razor = text("apps/rist-world/Components/UniversalInterface.razor")
    semantic = text("apps/rist-world/Components/UniversalInterface.SemanticControls.cs")
    css = text("apps/rist-world/wwwroot/css/universal-interface.css")

    assert '["ANALOG POSITION", "EXPERIENCE", "CONTROL SKIN"]' in semantic
    assert '["GUIDED", "STANDARD", "FAST"]' in semantic
    assert '["LINEAR", "QUICK DECK", "RADIAL", "DUAL RAIL"]' in semantic

    assert "ShowQuickDeck" in razor
    assert "SemanticQuickDeck" in razor
    assert "ShowRadialDeck" in razor
    assert "SemanticRadialDeck" in razor
    assert "SemanticCurrentValueCount" in razor
    assert "CycleSemanticSettingField(direction)" in razor
    assert "CycleSemanticSettingValue(direction)" in razor
    assert "SaveSemanticControlSettingsAsync()" in razor

    assert "Sheet 14 semantic controller overlays" in css
    assert ".semantic-quick-deck" in css
    assert ".semantic-radial-deck" in css
    assert ".semantic-skin-dual-rail" in css


def test_legacy_import_preserves_archive_and_attaches_semantic_control_profile():
    legacy = text("apps/rist-world/LegacyArchiveImport.cs")
    gate = text("apps/rist-world/Components/LegacyWorldGate.razor")
    input_js = text("apps/rist-world/wwwroot/universal-interface-input.js")

    assert 'ControlProfileKey(string worldId)' in legacy
    assert 'EnsureSemanticControlProfileAsync' in legacy
    assert 'UniversalSemanticControls.CreateLegacyImportProfile(worldId)' in legacy
    assert '"rist-legacy-archive",3' in legacy
    assert 'ControlContract=UniversalSemanticControls.ContractId' in legacy
    assert 'ControlProfileKey=controlProfileKey' in legacy
    assert 'await auth.UploadBytesAsync(sourceKey,zipBytes,"application/zip")' in legacy

    assert 'data-semantic-contract="@UniversalSemanticControls.ContractId"' in gate
    assert 'public async Task ReceiveControlAsync(string control,int direction)' in gate
    assert 'LegacyArchiveImport.EnsureSemanticControlProfileAsync(world.WorldId,Auth)' in gate
    assert 'id="legacy-import-zip"' in gate
    assert 'id="legacy-import-files"' in gate
    assert 'ristUniversalInput.openFilePicker' in gate
    assert "openFilePicker(id)" in input_js


def test_roleplayer_branch_no_longer_dead_ends_for_sandbox():
    interface = text("apps/rist-world/Components/UniversalInterface.razor")
    semantic = text("apps/rist-world/Components/UniversalInterface.SemanticControls.cs")
    auth = text("apps/rist-world/Components/AuthenticatedWorld.razor")

    assert "await OpenRoleplayerFromUniversalAsync();" in interface
    assert "OpenRoleplayerFromUniversalAsync()" in semantic
    assert "await OnRoleplay.InvokeAsync(label);" in semantic

    start = auth.index("async Task EnterUniversalRoleplayAsync")
    end = auth.index("async Task ReturnToStartAsync", start)
    roleplay_method = auth[start:end]
    assert "if(!Session.IsGeonaphWorld)return;" not in roleplay_method


def test_semantic_assets_are_cache_busted_together():
    index = text("apps/rist-world/wwwroot/index.html")

    assert "universal-interface.css?v=20260930-semantic-controls-2" in index
    assert "universal-interface-input.js?v=20260930-semantic-controls-2" in index
