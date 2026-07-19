"""Guarded AI Game Master response schema.

The first local build uses deterministic narration templates instead of an
external model. The schema and validator are in place so an AI service can be
added later without letting free-form narration mutate authoritative state.
"""

from __future__ import annotations

import html
import json
from typing import Any

from .seed_data import ATTRIBUTES, ITEMS, NPCS, SKILLS


AI_RESPONSE_KEYS = {
    "narration",
    "scene_updates",
    "proposed_checks",
    "proposed_state_changes",
    "npc_actions",
    "combat_actions",
    "rewards",
    "follow_up_options",
}

AI_MUTABLE_DOMAINS = {
    "scene",
    "npc_memory",
    "npc_disposition",
    "quest_hint",
}

NPC_ACTION_TYPES = {"say", "remember", "change_disposition"}
COMBAT_ACTION_TYPES = {"describe", "request_player_action"}
MAX_AI_RESPONSE_BYTES = 32_000
MAX_NARRATION_CHARS = 4_000

FORBIDDEN_AI_DOMAINS = {
    "account_permissions",
    "entitlements",
    "random_number_generation",
    "inventory_ownership",
    "currency_balances",
    "character_statistics",
    "payment_status",
    "authoritative_world_state",
}


def clean_text(value: Any) -> str:
    return html.escape(str(value), quote=False)


def empty_response(narration: str = "") -> dict[str, Any]:
    return {
        "narration": clean_text(narration),
        "scene_updates": [],
        "proposed_checks": [],
        "proposed_state_changes": [],
        "npc_actions": [],
        "combat_actions": [],
        "rewards": [],
        "follow_up_options": [],
    }


def build_response(
    narration: str,
    *,
    scene_updates: list[dict[str, Any]] | None = None,
    proposed_checks: list[dict[str, Any]] | None = None,
    proposed_state_changes: list[dict[str, Any]] | None = None,
    npc_actions: list[dict[str, Any]] | None = None,
    combat_actions: list[dict[str, Any]] | None = None,
    rewards: list[dict[str, Any]] | None = None,
    follow_up_options: list[str] | None = None,
) -> dict[str, Any]:
    payload = empty_response(narration)
    payload["scene_updates"] = scene_updates or []
    payload["proposed_checks"] = proposed_checks or []
    payload["proposed_state_changes"] = proposed_state_changes or []
    payload["npc_actions"] = npc_actions or []
    payload["combat_actions"] = combat_actions or []
    payload["rewards"] = rewards or []
    payload["follow_up_options"] = [clean_text(option) for option in (follow_up_options or [])]
    validate_ai_response(payload, allow_rewards=True)
    return payload


def parse_ai_response(raw: str) -> dict[str, Any]:
    if len(raw.encode("utf-8")) > MAX_AI_RESPONSE_BYTES:
        raise ValueError("AI response is too large.")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed AI JSON: {exc.msg}") from exc
    validate_ai_response(payload)
    return payload


def validate_ai_response(payload: dict[str, Any], *, allow_rewards: bool = False) -> None:
    if not isinstance(payload, dict):
        raise ValueError("AI response must be an object.")
    keys = set(payload.keys())
    missing = AI_RESPONSE_KEYS - keys
    unknown = keys - AI_RESPONSE_KEYS
    if missing:
        raise ValueError(f"AI response missing keys: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"AI response includes unknown keys: {', '.join(sorted(unknown))}")
    if not isinstance(payload.get("narration"), str):
        raise ValueError("AI narration must be text.")
    if len(payload["narration"]) > MAX_NARRATION_CHARS:
        raise ValueError("AI narration is too large.")
    if _discloses_hidden_instructions(payload["narration"]):
        raise ValueError("AI narration appears to disclose hidden instructions.")
    for key in AI_RESPONSE_KEYS - {"narration"}:
        if not isinstance(payload.get(key), list):
            raise ValueError(f"AI response field {key} must be a list.")
    if payload["rewards"] and not allow_rewards:
        raise ValueError("AI responses cannot directly grant rewards.")
    _validate_scene_updates(payload["scene_updates"])
    _validate_checks(payload["proposed_checks"])
    _validate_npc_actions(payload["npc_actions"])
    _validate_combat_actions(payload["combat_actions"])
    for change in payload["proposed_state_changes"]:
        domain = change.get("domain")
        if domain in FORBIDDEN_AI_DOMAINS or domain not in AI_MUTABLE_DOMAINS:
            raise ValueError(f"AI proposed unauthorized state domain: {domain}")
        if change.get("item_id") and change["item_id"] not in ITEMS:
            raise ValueError(f"AI proposed unknown item: {change['item_id']}")


def _validate_scene_updates(updates: list[dict[str, Any]]) -> None:
    seen: dict[str, Any] = {}
    for update in updates:
        if not isinstance(update, dict):
            raise ValueError("Scene updates must be objects.")
        key = update.get("key")
        value = update.get("value")
        if not key:
            raise ValueError("Scene update missing key.")
        if key in seen and seen[key] != value:
            raise ValueError(f"Contradictory scene update for {key}.")
        seen[key] = value


def _validate_checks(checks: list[dict[str, Any]]) -> None:
    for check in checks:
        if not isinstance(check, dict):
            raise ValueError("Proposed checks must be objects.")
        if check.get("attribute") and check["attribute"] not in ATTRIBUTES:
            raise ValueError(f"Unknown check attribute: {check['attribute']}")
        if check.get("skill") and check["skill"] not in SKILLS:
            raise ValueError(f"Unknown check skill: {check['skill']}")


def _validate_npc_actions(actions: list[dict[str, Any]]) -> None:
    for action in actions:
        if not isinstance(action, dict):
            raise ValueError("NPC actions must be objects.")
        if action.get("type") not in NPC_ACTION_TYPES:
            raise ValueError(f"Unknown NPC action type: {action.get('type')}")
        if action.get("npc_id") not in NPCS:
            raise ValueError(f"Invalid NPC identifier: {action.get('npc_id')}")


def _validate_combat_actions(actions: list[dict[str, Any]]) -> None:
    for action in actions:
        if not isinstance(action, dict):
            raise ValueError("Combat actions must be objects.")
        if action.get("type") not in COMBAT_ACTION_TYPES:
            raise ValueError(f"Unknown combat action type: {action.get('type')}")


def _discloses_hidden_instructions(narration: str) -> bool:
    lowered = narration.lower()
    markers = ["system prompt", "developer instruction", "hidden instruction", "chain of thought"]
    return any(marker in lowered for marker in markers)


def system_fallback(message: str) -> dict[str, Any]:
    return build_response(
        message,
        follow_up_options=[
            "Speak with Ilyra at the guild hall.",
            "Travel to the Forest Road.",
            "Return to camp.",
        ],
    )
