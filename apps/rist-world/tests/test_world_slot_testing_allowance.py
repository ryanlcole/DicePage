from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_public_alpha_includes_five_private_sandbox_worlds():
    source = read("WorldSession.Commerce.cs")
    assert "public const int IncludedOwnedWorldSlots = 5;" in source
    assert "CountOwnedCommercialWorlds" in source
    assert "IsSandboxWorldReference(world)" in source
    assert "CountOwnedCommercialWorlds(worlds) < limit.Value" in source


def test_world_gate_uses_the_session_allowance_instead_of_a_hardcoded_ui_limit():
    gate = read("Components/WorldGate.razor")
    assert "Session.CanCreateAdditionalOwnedWorld(_worlds)" in gate
    assert "Session.WorldSlotCommercialLabel" in gate
    assert "ADDITIONAL WORLD SLOT REQUIRED" in gate


def test_mmo_and_sandbox_world_navigation_are_separate():
    relationships = read("WorldSession.WorldRelationships.cs")
    gate = read("Components/WorldGate.razor")
    shell = read("Components/PublicAlphaShell.razor")
    authenticated = read("Components/AuthenticatedWorld.razor")

    assert 'public const string MmoWorldEnvironment = "mmo";' in relationships
    assert 'public const string SandboxWorldEnvironment = "sandbox";' in relationships
    assert "IsMmoWorldReference" in relationships
    assert "IsSandboxWorldReference" in relationships
    assert 'RestoreOperatingMode("sandbox");' in relationships
    assert 'imported.OperatingMode = "sandbox";' in relationships
    assert 'IsGeonaphWorld ? "Shaelvien" : "RIST Sandbox"' in relationships

    assert "CHOOSE A SANDBOX WORLD" in gate
    assert "SANDBOX WORLDS" in gate
    assert "directory.Worlds.Where(WorldSession.IsSandboxWorldReference)" in gate
    assert "SHAELVIEN MMO · PROPERTY SPACE" not in gate

    assert "MMO WORLD" in shell
    assert "SELECT MMO WORLD" in shell
    assert "directory.Worlds.Where(WorldSession.IsMmoWorldReference)" in shell
    assert "CREATE / IMPORT…" not in shell
    assert "SANDBOX WORLDS" in shell

    assert "await EnterMmoLandingAsync();" in authenticated
    assert "directory.Worlds.Where(WorldSession.IsMmoWorldReference)" in authenticated
    assert 'RequireSelection="true"' not in authenticated
