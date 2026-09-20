from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_public_alpha_includes_five_private_sandbox_worlds():
    source = read("WorldSession.Commerce.cs")
    assert "public const int IncludedOwnedWorldSlots = 5;" in source
    assert "CountOwnedCommercialWorlds" in source
    assert "!string.Equals(world.WorldId, GeonaphWorldId, StringComparison.Ordinal)" in source
    assert "CountOwnedCommercialWorlds(worlds) < limit.Value" in source


def test_world_gate_uses_the_session_allowance_instead_of_a_hardcoded_ui_limit():
    gate = read("Components/WorldGate.razor")
    assert "Session.CanCreateAdditionalOwnedWorld(_worlds)" in gate
    assert "Session.WorldSlotCommercialLabel" in gate
    assert "ADDITIONAL WORLD SLOT REQUIRED" in gate
