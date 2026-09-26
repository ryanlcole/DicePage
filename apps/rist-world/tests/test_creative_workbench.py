from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_creative_workplace_contract_locks_in_pipeline_and_assistance_gradient():
    contract = read("CREATIVE_WORKPLACE_CONTRACT.md")
    assert "CAPTURE → SHAPE → COMPARE → REFINE → COMBINE / IRON IN → PRODUCE → PLAY" in contract
    assert "Teach" in contract and "Help" in contract and "Suggest" in contract
    assert "Predict" in contract and "Quiet" in contract
    assert "Prediction prepares; it does not presume." in contract
    assert "current strength/capability" in contract
    assert "enjoyment/preference" in contract
    assert "growth interest" in contract
    assert "CREATE" in contract and "WORLD" in contract and "PLAY / RUN" in contract


def test_private_workbench_is_world_scoped_and_does_not_publish_implicitly():
    source = read("WorldSession.CreativeWorkbench.cs")
    assert 'CreativeWorkbenchStorageKey => $"{WorldStoragePrefix}/creative/workbench.json"' in source
    assert "CreativeWorkbenchLocalSaveKey" in source
    assert "LoadCreativeWorkbenchAsync" in source
    assert "SaveCreativeWorkbenchAsync" in source
    assert "Creative drafts are private account storage" in source
    assert '"Tabled", "Discarded", "Promoted", "Placeholder"' in source


def test_create_workspace_supports_medium_first_entry_comparison_and_fit_profile():
    source = read("Components/CreativeWorkbenchWorkspace.razor")
    for label in ("IDEA","WORDS","PICTURE","SOUND","MAP","MECHANIC","PLAYABLE"):
        assert f'"{label}"' in source
    for action in ("SAVE DRAFT","COMPARE","PLACEHOLDER","TABLE","DISCARD","IRON IN"):
        assert action in source
    assert "PROS · one per line" in source
    assert "CONS · one per line" in source
    assert "MY CREATIVE FIT" in source
    assert '["Teach","Help","Suggest","Predict","Quiet"]' in source
    assert "Prediction" not in source or "Predict" in source


def test_create_is_primary_gm_door_and_specialized_tools_remain_available():
    shell = read("Components/PublicAlphaShell.razor")
    router = read("Components/TaskWorkspaceRouter.razor")
    assert '<strong>CREATE</strong>' in shell
    assert '<strong>WORLD</strong>' in shell
    assert '<strong>RUN / PLAY</strong>' in shell
    assert '<strong>STUDIO TOOLS</strong>' in shell
    assert "WORLDBUILDER" in shell
    assert "REGION DEFINER" in shell
    assert "LOCAL STAGING" in shell
    assert 'Mode == "create"' in router
    assert "<CreativeWorkbenchWorkspace" in router
