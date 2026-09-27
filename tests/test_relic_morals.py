from __future__ import annotations

import json

import pytest

from relic_morals import (
    MoralCandidate,
    candidate_from_observation,
    export_registry,
    merge_candidates,
)


def _observation(text: str, *, source_id: str, contradiction: bool = False):
    return {
        "statement": "Human agency must remain meaningful.",
        "rationale": "Systems should assist rather than silently control.",
        "sourceId": source_id,
        "observedAt": "2026-09-27T18:00:00-04:00",
        "speakerRole": "user",
        "supportClass": "EXPLICIT",
        "provenance": "HUMAN",
        "scope": "PROJECT",
        "text": text,
        "contradiction": contradiction,
    }


def test_raw_chat_text_is_not_persisted():
    secret_text = "private source sentence that must not be stored"
    candidate = candidate_from_observation(_observation(secret_text, source_id="chat-1"))
    payload = json.dumps(candidate.as_dict(), sort_keys=True)
    assert secret_text not in payload
    assert candidate.evidence[0].source_digest


def test_duplicate_evidence_is_deduplicated_by_digest():
    a = candidate_from_observation(_observation("same text", source_id="chat-1"))
    b = candidate_from_observation(_observation("same text", source_id="chat-1"))
    merged = merge_candidates([a, b])
    assert len(merged) == 1
    assert len(merged[0].evidence) == 1


def test_contradiction_is_preserved_separately():
    support = candidate_from_observation(_observation("agency matters", source_id="chat-1"))
    conflict = candidate_from_observation(
        _observation("agency should not matter", source_id="chat-2", contradiction=True)
    )
    merged = merge_candidates([support, conflict])[0]
    assert len(merged.evidence) == 1
    assert len(merged.contradictions) == 1


def test_ai_candidate_cannot_promote_without_human_confirmation():
    candidate = candidate_from_observation(_observation("agency matters", source_id="chat-1"))
    with pytest.raises(PermissionError):
        candidate.promote_project_canon()
    candidate.confirm()
    candidate.promote_project_canon()
    assert candidate.status == "PROJECT_CANON"


def test_sensitive_trait_inference_is_rejected():
    value = _observation("content", source_id="chat-1")
    value["sensitiveInference"] = True
    with pytest.raises(ValueError):
        candidate_from_observation(value)


def test_registry_declares_privacy_and_no_automatic_promotion():
    candidate = candidate_from_observation(_observation("agency matters", source_id="chat-1"))
    registry = export_registry([candidate])
    assert registry["rawChatPersisted"] is False
    assert registry["automaticCanonPromotion"] is False
    assert registry["sensitiveTraitInference"] is False
