from __future__ import annotations

from relic_core import ChangeProof, Shaep, glyph, rune
from relic_analyzer import analyze_system


def test_rune_glyph_shaep_preserves_identity_and_relationships():
    shaep = Shaep.for_subject("demo")
    system = rune("entity", {"name": "demo"}, identity="entity.demo", truth_domain="FACT", provenance="SYSTEM")
    claim = rune("claim", "demo exists", identity="claim.demo.exists", truth_domain="FACT", provenance="SYSTEM")
    shaep.add_rune(system)
    shaep.add_rune(claim)
    shaep.add_glyph(glyph("asserts", [system, claim], truth_domain="FACT"))
    payload = shaep.as_dict()
    assert payload["format"] == "ReLiC-Shaep"
    assert {x["id"] for x in payload["runes"]} == {"entity.demo", "claim.demo.exists"}
    assert payload["glyphs"][0]["relation"] == "asserts"


def test_analyzer_reports_canon_repairs_without_mutating_subject():
    report = analyze_system({
        "subject": "example-ai",
        "identities": [
            {"stableId": "entity.1", "semanticKey": "same-thing", "representation": "A"},
            {"stableId": "entity.2", "semanticKey": "same-thing", "representation": "B"},
        ],
        "claims": [
            {"text": "uses 90% less energy", "truthDomain": "FACT", "energyReductionClaim": 0.90}
        ],
        "capabilities": [
            {
                "name": "physical actuator",
                "authorityBasis": "authenticated-only",
                "intendedHumanHarm": False,
                "foreseeableEcologicalHarm": True,
            }
        ],
        "changeClaims": [
            {
                "description": "changed all AI",
                "claimedScope": ["global-ai"],
                "observedScope": ["model-a", "model-b"],
                "evidence": ["model-a:test", "model-b:test"],
            }
        ],
    })
    categories = {x["category"] for x in report["shaep"]["weaknesses"]}
    assert {
        "duplicate_identity",
        "fact_without_provenance",
        "authority_ambiguous",
        "ecological_harm",
        "global_claim_unproven",
        "energy_claim_unmeasured",
    }.issubset(categories)
    assert report["mode"] == "analyze-report-propose"
    assert report["mutationAuthority"] is False


def test_five_minute_change_proof_separates_claimed_and_observed_scope():
    proof = ChangeProof(
        id="change.1",
        description="test propagation",
        claimed_scope=("model-a", "model-b"),
        started_at_ms=1_000,
    )
    partial = proof.add_proof(["model-a"], ["evidence-a"], now_ms=2_000)
    assert partial.status == "PARTIAL"
    assert not proof.verified

    expired = proof.evaluate(now_ms=proof.deadline_ms)
    assert expired.status == "UNPROVEN"
    assert expired.alert is True

    verified = proof.add_proof(["model-b"], ["evidence-b"], now_ms=proof.deadline_ms + 1)
    assert verified.status == "VERIFIED"
    assert proof.verified
    assert set(proof.observed_scope) == {"model-a", "model-b"}
