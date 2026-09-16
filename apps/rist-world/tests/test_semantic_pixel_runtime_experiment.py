import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
COMPONENT = ROOT / "Components" / "WorldBuilderSemanticPixelTest.razor"
ROUTER = ROOT / "Components" / "TaskWorkspaceRouter.razor"
MODULE = ROOT / "wwwroot" / "worldbuilder-semantic-pixel-test.js"
DOC = REPO / "docs" / "SEMANTIC_PIXEL_RUNTIME_EXPERIMENT.md"
REGISTRY = REPO / ".code-index" / "semantic_units.json"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_experimental_semantic_ids_are_namespaced_and_not_promoted_to_canonical_registry():
    component = read(COMPONENT)
    registry_text = read(REGISTRY)
    registry = json.loads(registry_text)

    for semantic_id in (
        "EXP:SEM:OCEAN.DEPTH.5",
        "EXP:SEM:COAST.SHORE.1",
        "EXP:SEM:PLAINS.LOW.1",
        "EXP:UNKNOWN:NOT-REGISTERED",
    ):
        assert semantic_id in component
        assert semantic_id not in registry_text

    assert registry is not None
    assert 'data-truth-domain="HYPOTHESIS"' in component


def test_resolver_uses_exact_semantic_identity_not_visual_properties():
    component = read(COMPONENT)
    module = read(MODULE)

    assert "Resolve(_observation.SemanticId)" in component
    assert "string.Equals(unit.Id,semanticId,StringComparison.Ordinal)" in component
    assert "Resolve(_proof.SemanticId)" in component
    assert "semantic ID is unknown, so no meaning was guessed" in component

    assert "element.dataset.semanticId" in module
    assert "getComputedStyle(element)" in module
    assert "samples.every(sample => sample.semanticId === semanticId)" in module
    assert "background" in module
    assert "semanticId" in module


def test_visual_invariance_proof_mutates_representation_and_restores_original_style():
    module = read(MODULE)

    assert 'capture(element, "baseline")' in module
    assert 'capture(element, "palette")' in module
    assert 'capture(element, "size")' in module
    assert 'capture(element, "position")' in module
    assert 'element.style.background = "linear-gradient' in module
    assert 'element.style.width = "137px"' in module
    assert 'element.style.transform = "translate(-91px, 57px) rotate(7deg)"' in module
    assert "finally" in module
    assert "element.setAttribute(\"style\", originalStyle)" in module


def test_lab_is_query_isolated_and_normal_worldbuilder_remains_default():
    router = read(ROUTER)

    assert "SemanticPixelLabRequested" in router
    assert "semanticpixellab=1" in router
    assert "WorldBuilderSemanticPixelTest" in router
    assert "WorldBuilderStudio" in router
    assert router.index("WorldBuilderSemanticPixelTest") < router.index("WorldBuilderStudio")


def test_lab_has_no_world_state_writer_or_network_fallback():
    component = read(COMPONENT)
    module = read(MODULE)
    doc = read(DOC)

    assert "@inject WorldSession" not in component
    assert "Session." not in component
    assert "fetch(" not in module
    assert "XMLHttpRequest" not in module
    assert "writes no world state" in doc
    assert "Do not silently reinterpret these `EXP:` references as canonical language forms." in doc
