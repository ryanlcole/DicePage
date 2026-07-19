"""Deterministic Shaelvien Lite game engine."""

from __future__ import annotations

import copy
import hmac
import random
import re
from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash

from .ai_gm import build_response, system_fallback
from .seed_data import ATTRIBUTES, CAMP_STRUCTURES, ENEMIES, ITEMS, NPCS, QUESTS, REGION, ROLES, SKILLS
from .store import new_id, new_secret, utc_now

RANGE_BANDS = ["Engaged", "Near", "Far"]
QUEST_TRANSITIONS = {
    "locked": {"available"},
    "available": {"active"},
    "active": {"completed", "failed"},
    "completed": set(),
    "failed": {"available"},
}


class GameError(ValueError):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def ability_modifier(score: int) -> int:
    return (int(score) - 10) // 2


def clone_item(item_id: str, quantity: int = 1) -> dict[str, Any]:
    if item_id not in ITEMS:
        raise GameError(f"Unknown item: {item_id}")
    item = copy.deepcopy(ITEMS[item_id])
    item["quantity"] = int(quantity)
    return item


def normalize_handle(handle: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_.-]+", "-", handle.strip()).strip("-")
    if len(value) < 2:
        raise GameError("Enter a handle with at least two usable characters.")
    return value[:40]


def create_or_enter_account(
    state: dict[str, Any],
    handle: str,
    *,
    password: str,
    owner_bootstrap_token: str | None = None,
    configured_owner_token: str | None = None,
    env_mode: str = "development",
) -> dict[str, Any]:
    normalized = normalize_handle(handle)
    _validate_password(password)
    for account in state["accounts"].values():
        if account["handle"].lower() == normalized.lower():
            password_hash = account.get("password_hash")
            if not password_hash or not check_password_hash(password_hash, password):
                raise GameError("Invalid account credentials.", 401)
            return _issue_session(state, account)
    account_id = new_id("acct")
    role = _new_account_role(
        state,
        owner_bootstrap_token=owner_bootstrap_token,
        configured_owner_token=configured_owner_token,
        env_mode=env_mode,
    )
    account = {
        "account_id": account_id,
        "handle": normalized,
        "role": role,
        "password_hash": generate_password_hash(password),
        "created_at": utc_now(),
        "character_ids": [],
        "campaign_ids": [],
        "party_ids": [],
    }
    state["accounts"][account_id] = account
    state["entitlements"]["account_entitlements"][account_id] = {
        "free_play": True,
        "character_slots": 2,
        "campaign_slots": 1,
        "cosmetics": [],
        "dev_flags": ["local_vertical_slice"] if role == "owner" else [],
    }
    return _issue_session(state, account)


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise GameError("Password must be at least 8 characters.")


def _new_account_role(
    state: dict[str, Any],
    *,
    owner_bootstrap_token: str | None,
    configured_owner_token: str | None,
    env_mode: str,
) -> str:
    setup = state.setdefault("setup", {})
    first_account = len(state["accounts"]) == 0
    if configured_owner_token and owner_bootstrap_token and not setup.get("owner_bootstrap_used"):
        if hmac.compare_digest(owner_bootstrap_token, configured_owner_token):
            setup["owner_bootstrap_used"] = True
            setup["owner_bootstrap_mode"] = "environment-token"
            return "owner"
    if env_mode.lower() == "production":
        setup["owner_bootstrap_mode"] = "production-fail-closed"
        return "player"
    if first_account:
        setup["owner_bootstrap_used"] = True
        setup["owner_bootstrap_mode"] = "development-first-account"
        return "owner"
    return "player"


def _issue_session(state: dict[str, Any], account: dict[str, Any]) -> dict[str, Any]:
    token = new_secret("sess")
    csrf_token = new_secret("csrf")
    state["sessions"][token] = {
        "token": token,
        "account_id": account["account_id"],
        "csrf_token": csrf_token,
        "created_at": utc_now(),
        "last_seen_at": utc_now(),
    }
    return {"token": token, "csrf_token": csrf_token, "account": account}


def invalidate_session(state: dict[str, Any], token: str | None) -> None:
    if token and token in state["sessions"]:
        del state["sessions"][token]


def require_session(state: dict[str, Any], token: str | None) -> dict[str, Any]:
    if not token or token not in state["sessions"]:
        raise GameError("Authentication required.", 401)
    session = state["sessions"][token]
    session["last_seen_at"] = utc_now()
    account = state["accounts"].get(session["account_id"])
    if not account:
        raise GameError("Invalid session.", 401)
    return account


def require_csrf(state: dict[str, Any], token: str | None, csrf_token: str | None) -> None:
    if not token or token not in state["sessions"]:
        raise GameError("Authentication required.", 401)
    expected = state["sessions"][token].get("csrf_token")
    if not expected or not csrf_token or not hmac.compare_digest(expected, csrf_token):
        raise GameError("Invalid request token.", 403)


def require_owner(account: dict[str, Any]) -> None:
    if account.get("role") != "owner":
        raise GameError("Owner access required.", 403)


def require_character(state: dict[str, Any], account: dict[str, Any], character_id: str) -> dict[str, Any]:
    character = state["characters"].get(character_id)
    if not character or character.get("player_id") != account["account_id"]:
        raise GameError("Character not found for this account.", 404)
    return character


def require_campaign(state: dict[str, Any], account: dict[str, Any], campaign_id: str) -> dict[str, Any]:
    campaign = state["campaigns"].get(campaign_id)
    if not campaign or campaign.get("owner_account_id") != account["account_id"]:
        raise GameError("Campaign not found for this account.", 404)
    return campaign


def create_character(
    state: dict[str, Any],
    account: dict[str, Any],
    name: str,
    role_id: str,
    *,
    ancestry: str | None = None,
) -> dict[str, Any]:
    role = ROLES.get(role_id)
    if not role:
        raise GameError("Unknown character role.")
    entitlements = state["entitlements"]["account_entitlements"].setdefault(
        account["account_id"], {"free_play": True, "character_slots": 2}
    )
    if len(account.get("character_ids", [])) >= int(entitlements.get("character_slots", 2)):
        raise GameError("Character slot limit reached.")
    clean_name = name.strip()[:40]
    if len(clean_name) < 2:
        raise GameError("Character name must be at least two characters.")
    character_id = new_id("char")
    inventory = {}
    equipment = {
        "weapon": None,
        "off_hand": None,
        "head": None,
        "body": None,
        "hands": None,
        "feet": None,
        "accessory": None,
        "consumables": [],
    }
    for slot, item_value in role["equipment"].items():
        if isinstance(item_value, list):
            equipment[slot] = list(item_value)
            for item_id in item_value:
                inventory[item_id] = clone_item(item_id, 1)
        else:
            equipment[slot] = item_value
            inventory[item_value] = clone_item(item_value, 1)
    inventory["trail_rations"] = clone_item("trail_rations", 2)
    max_health = 18 + ability_modifier(role["attributes"]["Endurance"]) * 2
    max_stamina = 10 + ability_modifier(role["attributes"]["Endurance"]) + ability_modifier(role["attributes"]["Agility"])
    character = {
        "character_id": character_id,
        "player_id": account["account_id"],
        "name": clean_name,
        "portrait": role["portrait"],
        "ancestry_or_origin": ancestry.strip()[:40] if ancestry else role["origin"],
        "role_id": role_id,
        "role": role["name"],
        "rarity_or_progression_tier": role["tier"],
        "level": 1,
        "experience": 0,
        "biography": role["biography"],
        "alignment_or_disposition": "unproven ally",
        "attributes": copy.deepcopy(role["attributes"]),
        "attribute_names": list(ATTRIBUTES),
        "vitals": {
            "health": max_health,
            "maximum_health": max_health,
            "stamina": max_stamina,
            "maximum_stamina": max_stamina,
            "mana": 8 if role_id == "arcanist" else 0,
            "injuries": [],
            "conditions": [],
            "status_effects": [],
        },
        "skills": {skill: int(role["skills"].get(skill, 0)) for skill in SKILLS},
        "equipment": equipment,
        "inventory": inventory,
        "currency": 20,
        "resources": {"timber": 1, "ore": 0, "ember": 0},
        "current_assignment": "Arriving at Emberhall Outpost",
        "created_at": utc_now(),
    }
    state["characters"][character_id] = character
    account.setdefault("character_ids", []).append(character_id)
    return character


def start_tutorial_campaign(state: dict[str, Any], account: dict[str, Any], character_id: str) -> dict[str, Any]:
    character = require_character(state, account, character_id)
    existing_id = character.get("active_campaign_id")
    if existing_id and existing_id in state["campaigns"]:
        return state["campaigns"][existing_id]
    campaign_id = new_id("campgn")
    party_id = new_id("party")
    campaign = {
        "campaign_id": campaign_id,
        "owner_account_id": account["account_id"],
        "party_id": party_id,
        "region_id": REGION["region_id"],
        "current_location": "emberhall_outpost",
        "unlocked_locations": ["emberhall_outpost", "forest_road"],
        "completed_encounters": [],
        "world_state": {
            "settlement_alert": "Road closures have strained Emberhall Outpost.",
            "tutorial_stage": "arrived",
        },
        "scene_state": {
            "active_npc_id": "npc_guild_rep",
            "active_quest_id": "q_forest_road",
            "scene_clock": 1,
            "last_action": "arrived",
        },
        "characters": [character_id],
        "secondary_heroes": [],
        "quests": {
            quest_id: {"quest_id": quest_id, "status": data["initial_status"], "completed_steps": []}
            for quest_id, data in QUESTS.items()
        },
        "npcs": copy.deepcopy(NPCS),
        "camp_progression": {
            key: {
                "structure_id": key,
                "name": value["name"],
                "level": value["level"],
                "max_level": value["max_level"],
                "benefit": value["benefit"],
                "upgrade_requirements": copy.deepcopy(value["upgrade_requirements"]),
                "prerequisites": copy.deepcopy(value.get("prerequisites", {})),
                "upgrade_state": "ready",
                "upgrade_complete_at": None,
            }
            for key, value in CAMP_STRUCTURES.items()
        },
        "combat": None,
        "processed_action_keys": {},
        "session_log_ids": [],
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    state["campaigns"][campaign_id] = campaign
    state["parties"][party_id] = {
        "party_id": party_id,
        "party_owner": account["account_id"],
        "party_members": [account["account_id"]],
        "invite_status": {},
        "character_assignments": {account["account_id"]: character_id},
        "shared_scene": campaign["scene_state"],
        "turn_ownership": account["account_id"],
        "party_chat": [],
        "action_queue": [],
        "group_decisions": [],
        "shared_rewards": [],
        "individual_rewards": {},
        "reconnection": {},
    }
    account.setdefault("campaign_ids", []).append(campaign_id)
    account.setdefault("party_ids", []).append(party_id)
    character["active_campaign_id"] = campaign_id
    character["current_assignment"] = "Tutorial campaign"
    _append_log(
        state,
        campaign,
        "system",
        "You arrive at Emberhall Outpost as the guild lanterns are being lit.",
    )
    return campaign


def process_player_action(
    state: dict[str, Any],
    account: dict[str, Any],
    campaign_id: str,
    character_id: str,
    action: str,
    *,
    idempotency_key: str | None = None,
    target_id: str | None = None,
    rng: random.Random | None = None,
) -> dict[str, Any]:
    rng = rng or random.SystemRandom()
    campaign = require_campaign(state, account, campaign_id)
    character = require_character(state, account, character_id)
    if character_id not in campaign["characters"]:
        raise GameError("Character is not assigned to this campaign.", 403)
    text = action.strip()
    if len(text) < 2:
        raise GameError("Action text is required.")
    if idempotency_key:
        processed = campaign.setdefault("processed_action_keys", {})
        if idempotency_key in processed:
            prior = processed[idempotency_key]
            return {
                "campaign": campaign,
                "character": character,
                "ai_response": build_response(
                    "That action was already processed. The saved campaign state has not changed again.",
                    follow_up_options=_follow_up_options(campaign),
                ),
                "roll": None,
                "validated_state_changes": [{"type": "idempotent_replay", "prior_proposal_id": prior.get("proposal_id")}],
                "proposal_id": prior.get("proposal_id"),
                "replayed": True,
            }
    _validate_target(campaign, target_id)
    lower = text.lower()
    validated_changes: list[dict[str, Any]] = []
    rewards: list[dict[str, Any]] = []
    roll_result = None

    if campaign.get("combat"):
        result = _process_combat_action(campaign, character, lower, rng)
        narration = result["narration"]
        validated_changes.extend(result["changes"])
        rewards.extend(result.get("rewards", []))
    elif _matches(lower, ["return", "town", "camp", "outpost", "emberhall"]):
        campaign["current_location"] = "emberhall_outpost"
        campaign["scene_state"]["active_npc_id"] = "npc_guild_rep"
        character["current_assignment"] = "At Emberhall Outpost"
        _complete_step(campaign, "q_forest_road", "return_camp")
        narration = "You return to Emberhall Outpost. Smoke rises from cookfires, and your personal camp waits inside the palisade."
        validated_changes.append({"type": "location_changed", "location_id": "emberhall_outpost"})
    elif _matches(lower, ["travel", "go to", "road", "mine", "shrine", "bandit"]):
        location_id = _location_from_text(lower)
        narration = _travel_to_location(campaign, character, location_id)
        validated_changes.append({"type": "location_changed", "location_id": location_id})
    elif _matches(lower, ["speak", "talk", "ask", "greet"]):
        npc_id = _npc_from_text(campaign, lower)
        narration = _speak_with_npc(campaign, npc_id, text)
        validated_changes.append({"type": "npc_memory", "npc_id": npc_id})
    elif _matches(lower, ["accept", "quest", "contract"]):
        quest_id = campaign["scene_state"].get("active_quest_id", "q_forest_road")
        narration = _accept_quest(campaign, quest_id)
        validated_changes.append({"type": "quest_status", "quest_id": quest_id, "status": "active"})
    elif _matches(lower, ["inspect", "investigate", "search", "track", "study", "scout", "climb"]):
        roll_result, narration = _resolve_location_check(campaign, character, text, rng)
        validated_changes.append({"type": "check_resolved", "result_band": roll_result["result_band"]})
    elif _matches(lower, ["upgrade", "build", "improve"]):
        structure_id = _structure_from_text(lower)
        narration = upgrade_camp_structure(campaign, character, structure_id)
        validated_changes.append({"type": "camp_upgrade", "structure_id": structure_id})
        _complete_step(campaign, "q_outpost_rebuild", "upgrade_structure")
    elif _matches(lower, ["heal", "potion", "draught"]):
        narration = _use_healing_draught(character)
        validated_changes.append({"type": "item_used", "item_id": "healing_draught"})
    elif _matches(lower, ["fight", "attack", "strike", "ambush"]):
        narration = _start_location_combat(campaign, character, rng)
        validated_changes.append({"type": "combat_started"})
    else:
        narration = "The Game Master weighs the action against the scene, but nothing certain changes yet. Try speaking, traveling, investigating, attacking, healing, or upgrading camp."

    campaign["scene_state"]["scene_clock"] += 1
    campaign["scene_state"]["last_action"] = text
    campaign["updated_at"] = utc_now()

    ai_payload = build_response(
        narration,
        proposed_checks=[roll_result] if roll_result else [],
        rewards=rewards,
        follow_up_options=_follow_up_options(campaign),
    )
    proposal_id = new_id("ai")
    state["ai_proposals"][proposal_id] = {
        "proposal_id": proposal_id,
        "campaign_id": campaign_id,
        "character_id": character_id,
        "request": {"action": text, "location": campaign["current_location"]},
        "response": ai_payload,
        "created_at": utc_now(),
    }
    state["validated_state_changes"][proposal_id] = validated_changes
    if idempotency_key:
        campaign.setdefault("processed_action_keys", {})[idempotency_key] = {
            "proposal_id": proposal_id,
            "action": text,
            "at": utc_now(),
        }
        campaign["processed_action_keys"] = dict(list(campaign["processed_action_keys"].items())[-100:])
    _append_log(state, campaign, "player", text)
    _append_log(state, campaign, "gm", ai_payload["narration"], roll_result=roll_result)
    return {
        "campaign": campaign,
        "character": character,
        "ai_response": ai_payload,
        "roll": roll_result,
        "validated_state_changes": validated_changes,
        "proposal_id": proposal_id,
    }


def _validate_target(campaign: dict[str, Any], target_id: str | None) -> None:
    if not target_id:
        return
    combat = campaign.get("combat")
    if not combat:
        raise GameError("No target can be selected outside combat.")
    valid_targets = {enemy.get("instance_id") for enemy in combat.get("enemies", [])}
    if target_id not in valid_targets:
        raise GameError("Invalid combat target.")


def _matches(text: str, words: list[str]) -> bool:
    return any(word in text for word in words)


def _location_from_text(text: str) -> str:
    if "mine" in text:
        return "abandoned_mine"
    if "shrine" in text:
        return "ruined_shrine"
    if "bandit" in text or "camp" in text and "upgrade" not in text:
        return "bandit_camp"
    return "forest_road"


def _structure_from_text(text: str) -> str:
    options = {
        "quarters": ["quarters", "room", "bunk"],
        "storage": ["storage", "storehouse", "stash"],
        "workshop": ["workshop", "craft", "repair"],
        "training_yard": ["training", "yard"],
        "healing_tent": ["healing", "tent", "medicine"],
        "planning_table": ["planning", "table", "map"],
    }
    for structure_id, terms in options.items():
        if any(term in text for term in terms):
            return structure_id
    return "quarters"


def _npc_from_text(campaign: dict[str, Any], text: str) -> str:
    npc_terms = {
        "npc_innkeeper": ["inn", "mara", "innkeeper"],
        "npc_blacksmith": ["smith", "brannic", "blacksmith"],
        "npc_healer": ["healer", "sella"],
        "npc_merchant": ["merchant", "tovin"],
        "npc_guild_rep": ["guild", "ilyra", "representative"],
        "npc_guard_scout": ["guard", "scout", "oren"],
    }
    for npc_id, terms in npc_terms.items():
        if any(term in text for term in terms):
            return npc_id
    return campaign["scene_state"].get("active_npc_id", "npc_guild_rep")


def _travel_to_location(campaign: dict[str, Any], character: dict[str, Any], location_id: str) -> str:
    if location_id not in campaign["unlocked_locations"]:
        raise GameError("That location is not unlocked yet.")
    if location_id == "emberhall_outpost":
        campaign["current_location"] = location_id
        return "You step back through Emberhall's gate and hear the settlement settle around you."
    location = REGION["locations"][location_id]
    campaign["current_location"] = location_id
    character["current_assignment"] = location["name"]
    if location_id == "forest_road":
        _complete_step(campaign, "q_forest_road", "travel_forest_road")
    return f"{location['name']}: {location['summary']} {location['exploration_event']}"


def _speak_with_npc(campaign: dict[str, Any], npc_id: str, action: str) -> str:
    npc = campaign["npcs"][npc_id]
    memory = {
        "at": utc_now(),
        "summary": f"Player asked: {action[:120]}",
    }
    npc["conversation_memory"].append(memory)
    npc["conversation_memory"] = npc["conversation_memory"][-8:]
    campaign["scene_state"]["active_npc_id"] = npc_id
    if npc_id == "npc_guild_rep":
        _complete_step(campaign, "q_forest_road", "speak_guild")
        return "Ilyra Dain lays a stamped token on the table. The Forest Road is the first problem: find what stopped the courier, survive contact, and report back."
    fact = npc["known_facts"][0] if npc.get("known_facts") else "They have no useful fact to add yet."
    return f"{npc['name']} keeps to what their role permits: {fact}"


def _accept_quest(campaign: dict[str, Any], quest_id: str) -> str:
    quest = campaign["quests"].get(quest_id)
    if not quest:
        raise GameError("Quest not found.")
    if quest["status"] == "completed":
        return "That quest is already complete."
    if quest["status"] != "active":
        _transition_quest(campaign, quest_id, "active")
    if quest_id == "q_forest_road":
        _complete_step(campaign, quest_id, "speak_guild")
    return f"Quest accepted: {QUESTS[quest_id]['name']}."


def _transition_quest(campaign: dict[str, Any], quest_id: str, next_status: str) -> None:
    quest = campaign["quests"].get(quest_id)
    if not quest:
        raise GameError("Quest not found.")
    current = quest["status"]
    if next_status not in QUEST_TRANSITIONS.get(current, set()):
        raise GameError(f"Invalid quest transition: {current} to {next_status}.")
    quest["status"] = next_status


def _resolve_location_check(
    campaign: dict[str, Any],
    character: dict[str, Any],
    action: str,
    rng: random.Random,
) -> tuple[dict[str, Any], str]:
    location_id = campaign["current_location"]
    if location_id == "emberhall_outpost":
        rule = {"attribute": "Presence", "skill": "Persuasion", "difficulty": 10}
        context = "You read the mood around Emberhall's hall."
    else:
        location = REGION["locations"][location_id]
        rule = location["check"]
        context = location["social_event"]
    roll = resolve_check(character, action, rule, rng=rng)
    if location_id == "forest_road":
        _complete_step(campaign, "q_forest_road", "investigate_tracks")
    if roll["result_band"] in ("Success", "Critical Success") and location_id != "emberhall_outpost":
        narration = f"{context} The check succeeds, revealing enough to act before the threat fully controls the scene."
    elif roll["result_band"] == "Partial Success" and location_id != "emberhall_outpost":
        narration = f"{context} You learn the key detail, but the delay draws danger closer."
    else:
        narration = f"{context} The result leaves gaps, and the scene grows less forgiving."
    return roll, narration


def resolve_check(
    character: dict[str, Any],
    original_action: str,
    rule: dict[str, Any],
    *,
    situational_modifier: int = 0,
    rng: random.Random | None = None,
) -> dict[str, Any]:
    rng = rng or random.SystemRandom()
    attribute = rule["attribute"]
    skill = rule["skill"]
    difficulty = int(rule["difficulty"])
    d20 = rng.randint(1, 20)
    attr_mod = ability_modifier(character["attributes"].get(attribute, 10))
    skill_mod = int(character["skills"].get(skill, 0))
    total = d20 + attr_mod + skill_mod + int(situational_modifier)
    if d20 == 1 or total <= difficulty - 8:
        band = "Critical Failure"
    elif d20 == 20 or total >= difficulty + 10:
        band = "Critical Success"
    elif total >= difficulty:
        band = "Success"
    elif total >= difficulty - 3:
        band = "Partial Success"
    else:
        band = "Failure"
    return {
        "original_player_action": original_action,
        "selected_rule": "1d20 + Attribute Modifier + Skill Modifier + Situational Modifier",
        "attribute": attribute,
        "skill": skill,
        "roll": d20,
        "modifiers": {
            "attribute_modifier": attr_mod,
            "skill_modifier": skill_mod,
            "situational_modifier": int(situational_modifier),
        },
        "total": total,
        "difficulty": difficulty,
        "result_band": band,
        "resulting_state_changes": [],
        "ai_narration": "",
    }


def _start_location_combat(campaign: dict[str, Any], character: dict[str, Any], rng: random.Random) -> str:
    location_id = campaign["current_location"]
    if location_id == "emberhall_outpost":
        raise GameError("There is no hostile encounter in the settlement.")
    location = REGION["locations"][location_id]
    if location["enemy"] in campaign.get("completed_encounters", []):
        raise GameError("That encounter has already been completed.")
    return _create_combat(campaign, character, location["enemy"], rng)


def _create_combat(campaign: dict[str, Any], character: dict[str, Any], enemy_id: str, rng: random.Random) -> str:
    if campaign.get("combat"):
        return "Combat is already underway."
    enemy_template = ENEMIES[enemy_id]
    player_initiative = rng.randint(1, 20) + ability_modifier(character["attributes"].get("Agility", 10))
    enemy_initiative = rng.randint(1, 20) + int(enemy_template["attack_bonus"])
    first = "player" if player_initiative >= enemy_initiative else "enemy"
    enemy = copy.deepcopy(enemy_template)
    enemy["instance_id"] = new_id("enemy")
    enemy["maximum_health"] = enemy["health"]
    campaign["combat"] = {
        "combat_id": new_id("combat"),
        "round": 1,
        "turn": first,
        "range_band": enemy["range_band"],
        "initiative": {"player": player_initiative, "enemy": enemy_initiative},
        "enemies": [enemy],
        "combat_log": [],
    }
    if first == "enemy":
        enemy_text = _enemy_turn(campaign, character, rng)
        if campaign.get("combat"):
            campaign["combat"]["turn"] = "player"
        return f"{enemy['name']} acts first. {enemy_text}"
    return f"Initiative is yours against {enemy['name']}. The enemy is {enemy['range_band'].lower()}."


def _process_combat_action(
    campaign: dict[str, Any],
    character: dict[str, Any],
    action: str,
    rng: random.Random,
) -> dict[str, Any]:
    if campaign["combat"].get("turn") != "player":
        raise GameError("It is not the player's turn.")
    if "retreat" in action or "flee" in action:
        campaign["combat"] = None
        campaign["current_location"] = "emberhall_outpost"
        return {
            "narration": "You retreat to Emberhall Outpost. The enemy survives, but your campaign state is preserved.",
            "changes": [{"type": "combat_retreat"}],
        }
    if "heal" in action or "potion" in action or "draught" in action:
        narration = _use_healing_draught(character)
        enemy_text = _enemy_turn(campaign, character, rng)
        return {
            "narration": f"{narration} {enemy_text}",
            "changes": [{"type": "item_used", "item_id": "healing_draught"}],
        }
    if "defend" in action or "guard" in action:
        character["vitals"]["stamina"] = min(
            character["vitals"]["maximum_stamina"], character["vitals"]["stamina"] + 2
        )
        enemy_text = _enemy_turn(campaign, character, rng, defended=True)
        return {
            "narration": f"You brace and recover stamina. {enemy_text}",
            "changes": [{"type": "defended"}],
        }
    if not _matches(action, ["attack", "strike", "fight", "shoot", "cast"]):
        return {
            "narration": "Combat is active. Attack, defend, heal, or retreat.",
            "changes": [],
        }
    combat = campaign["combat"]
    enemy = combat["enemies"][0]
    weapon_id = character["equipment"].get("weapon")
    weapon = ITEMS.get(weapon_id or "", ITEMS["field_knife"])
    attribute = weapon["mechanical_effects"].get("attack_attribute", "Strength")
    rule = {"attribute": attribute, "skill": "Athletics" if attribute == "Strength" else "Survival", "difficulty": enemy["defense"]}
    attack = resolve_check(character, action, rule, rng=rng)
    damage = 0
    if attack["result_band"] in ("Success", "Critical Success", "Partial Success"):
        die_count, die_size = _parse_die(weapon["mechanical_effects"].get("damage", "1d4"))
        damage = sum(rng.randint(1, die_size) for _ in range(die_count))
        if attack["result_band"] == "Critical Success":
            damage += die_size
        if attack["result_band"] == "Partial Success":
            damage = max(1, damage // 2)
        enemy["health"] = max(0, enemy["health"] - damage)
    combat["combat_log"].append({"actor": "player", "roll": attack, "damage": damage})
    if enemy["health"] <= 0:
        rewards = _complete_combat(campaign, character, enemy)
        return {
            "narration": f"Your attack lands for {damage} damage. {enemy['name']} is defeated. Rewards are added to your character.",
            "changes": [{"type": "combat_defeated", "enemy_id": enemy["enemy_id"]}],
            "rewards": rewards,
        }
    enemy_text = _enemy_turn(campaign, character, rng)
    if campaign.get("combat"):
        campaign["combat"]["turn"] = "player"
    return {
        "narration": f"Your attack {attack['result_band'].lower()} deals {damage} damage. {enemy['name']} has {enemy['health']} health left. {enemy_text}",
        "changes": [{"type": "combat_damage", "enemy_id": enemy["enemy_id"], "damage": damage}],
    }


def _enemy_turn(
    campaign: dict[str, Any],
    character: dict[str, Any],
    rng: random.Random,
    *,
    defended: bool = False,
) -> str:
    combat = campaign["combat"]
    enemy = combat["enemies"][0]
    defense = 10 + ability_modifier(character["attributes"].get("Agility", 10))
    if defended:
        defense += 2
    attack_roll = rng.randint(1, 20) + int(enemy["attack_bonus"])
    if attack_roll >= defense:
        die_count, die_size = _parse_die(enemy["damage"])
        damage = sum(rng.randint(1, die_size) for _ in range(die_count))
        if defended:
            damage = max(0, damage - 2)
        character["vitals"]["health"] = max(0, character["vitals"]["health"] - damage)
        if character["vitals"]["health"] <= 0:
            if "defeated" not in character["vitals"]["conditions"]:
                character["vitals"]["conditions"].append("defeated")
            if "injured" not in character["vitals"]["injuries"]:
                character["vitals"]["injuries"].append("injured")
            campaign["combat"] = None
            campaign["current_location"] = "emberhall_outpost"
            return f"{enemy['name']} hits for {damage}. You are defeated and carried back to camp with an injury."
        return f"{enemy['name']} hits for {damage}."
    return f"{enemy['name']} misses."


def _complete_combat(
    campaign: dict[str, Any],
    character: dict[str, Any],
    enemy: dict[str, Any],
) -> list[dict[str, Any]]:
    rewards = enemy.get("rewards", {})
    if enemy["enemy_id"] in campaign.get("completed_encounters", []):
        campaign["combat"] = None
        return []
    _grant_rewards(character, rewards)
    campaign["completed_encounters"].append(enemy["enemy_id"])
    if enemy["enemy_id"] == "road_cutpurse":
        _complete_step(campaign, "q_forest_road", "defeat_road_cutpurse")
        _complete_quest_if_ready(campaign, character, "q_forest_road")
        _make_quest_available(campaign, "q_mine_echoes")
        if "abandoned_mine" not in campaign["unlocked_locations"]:
            campaign["unlocked_locations"].append("abandoned_mine")
    if enemy["enemy_id"] == "mine_skulk":
        _make_quest_available(campaign, "q_shrine_marks")
        if "ruined_shrine" not in campaign["unlocked_locations"]:
            campaign["unlocked_locations"].append("ruined_shrine")
    if enemy["enemy_id"] == "hollow_prowler":
        _make_quest_available(campaign, "q_bandit_pressure")
        if "bandit_camp" not in campaign["unlocked_locations"]:
            campaign["unlocked_locations"].append("bandit_camp")
    campaign["combat"] = None
    return [{"source": "combat", "enemy_id": enemy["enemy_id"], "rewards": rewards}]


def _grant_rewards(character: dict[str, Any], rewards: dict[str, Any]) -> None:
    character["experience"] += int(rewards.get("experience", 0))
    character["currency"] += int(rewards.get("currency", 0))
    for resource, amount in rewards.get("resources", {}).items():
        character["resources"][resource] = character["resources"].get(resource, 0) + int(amount)
    for item_id, qty in rewards.get("items", {}).items():
        if item_id in character["inventory"]:
            character["inventory"][item_id]["quantity"] += int(qty)
        else:
            character["inventory"][item_id] = clone_item(item_id, int(qty))
    while character["experience"] >= character["level"] * 100:
        character["experience"] -= character["level"] * 100
        character["level"] += 1
        character["vitals"]["maximum_health"] += 4
        character["vitals"]["health"] = character["vitals"]["maximum_health"]


def _make_quest_available(campaign: dict[str, Any], quest_id: str) -> None:
    quest = campaign["quests"].get(quest_id)
    if quest and quest["status"] == "locked":
        _transition_quest(campaign, quest_id, "available")


def _complete_step(campaign: dict[str, Any], quest_id: str, step: str) -> None:
    quest = campaign["quests"].get(quest_id)
    if not quest:
        return
    if step not in quest["completed_steps"]:
        quest["completed_steps"].append(step)


def _complete_quest_if_ready(campaign: dict[str, Any], character: dict[str, Any], quest_id: str) -> None:
    quest = campaign["quests"][quest_id]
    required = set(QUESTS[quest_id]["steps"]) - {"return_camp"}
    if quest["status"] != "completed" and required.issubset(set(quest["completed_steps"])):
        if quest["status"] == "available":
            _transition_quest(campaign, quest_id, "active")
        _transition_quest(campaign, quest_id, "completed")
        _grant_rewards(character, QUESTS[quest_id]["rewards"])


def upgrade_camp_structure(campaign: dict[str, Any], character: dict[str, Any], structure_id: str) -> str:
    structure = campaign["camp_progression"].get(structure_id)
    if not structure:
        raise GameError("Unknown camp structure.")
    if structure["level"] >= structure["max_level"]:
        return f"{structure['name']} is already at maximum level."
    for prereq, needed_level in structure.get("prerequisites", {}).items():
        prereq_structure = campaign["camp_progression"].get(prereq)
        if not prereq_structure or prereq_structure["level"] < int(needed_level):
            raise GameError(f"{structure['name']} requires {prereq} level {needed_level}.")
    req = structure["upgrade_requirements"]
    currency = int(req.get("currency", 0))
    if character["currency"] < currency:
        raise GameError("Not enough currency for that upgrade.")
    for resource, amount in req.get("resources", {}).items():
        if character["resources"].get(resource, 0) < int(amount):
            raise GameError(f"Not enough {resource} for that upgrade.")
    character["currency"] -= currency
    for resource, amount in req.get("resources", {}).items():
        character["resources"][resource] -= int(amount)
    structure["level"] += 1
    structure["upgrade_state"] = "complete"
    structure["upgrade_complete_at"] = utc_now()
    if structure_id == "planning_table" and "abandoned_mine" not in campaign["unlocked_locations"]:
        campaign["unlocked_locations"].append("abandoned_mine")
    return f"{structure['name']} reaches level {structure['level']}. Benefit active: {structure['benefit']}"


def _use_healing_draught(character: dict[str, Any]) -> str:
    item = character["inventory"].get("healing_draught")
    if not item or item.get("quantity", 0) <= 0:
        raise GameError("No healing draught is available.")
    item["quantity"] -= 1
    healed = ITEMS["healing_draught"]["mechanical_effects"]["heal"]
    vitals = character["vitals"]
    before = vitals["health"]
    vitals["health"] = min(vitals["maximum_health"], vitals["health"] + healed)
    return f"You use a healing draught and recover {vitals['health'] - before} health."


def _parse_die(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)d(\d+)", value)
    if not match:
        return 1, 4
    return int(match.group(1)), int(match.group(2))


def _append_log(
    state: dict[str, Any],
    campaign: dict[str, Any],
    entry_type: str,
    text: str,
    *,
    roll_result: dict[str, Any] | None = None,
) -> None:
    log_id = new_id("log")
    entry = {
        "log_id": log_id,
        "campaign_id": campaign["campaign_id"],
        "type": entry_type,
        "text": text,
        "roll_result": roll_result,
        "created_at": utc_now(),
    }
    state["session_logs"][log_id] = entry
    campaign["session_log_ids"].append(log_id)
    campaign["session_log_ids"] = campaign["session_log_ids"][-100:]


def _follow_up_options(campaign: dict[str, Any]) -> list[str]:
    if campaign.get("combat"):
        return ["Attack", "Defend", "Use a healing draught", "Retreat"]
    if campaign["current_location"] == "emberhall_outpost":
        return ["Speak with Ilyra at the guild hall", "Travel to the Forest Road", "Upgrade Quarters"]
    location = REGION["locations"][campaign["current_location"]]
    return [f"Investigate {location['name']}", "Attack if threatened", "Return to Emberhall Outpost"]


def summarize_state(state: dict[str, Any], account: dict[str, Any] | None = None) -> dict[str, Any]:
    if not account:
        return {
            "region": REGION,
            "roles": ROLES,
            "attributes": ATTRIBUTES,
            "skills": SKILLS,
            "items": ITEMS,
            "early_access": True,
        }
    character_ids = account.get("character_ids", [])
    campaign_ids = account.get("campaign_ids", [])
    return {
        "account": {
            "account_id": account["account_id"],
            "handle": account["handle"],
            "role": account["role"],
        },
        "characters": [state["characters"][cid] for cid in character_ids if cid in state["characters"]],
        "campaigns": [state["campaigns"][cid] for cid in campaign_ids if cid in state["campaigns"]],
        "region": REGION,
        "roles": ROLES,
        "attributes": ATTRIBUTES,
        "skills": SKILLS,
        "items": ITEMS,
        "early_access": True,
        "settings": state["settings"],
        "entitlements": state["entitlements"]["account_entitlements"].get(account["account_id"], {}),
    }


def reset_development_campaign(state: dict[str, Any], account: dict[str, Any], campaign_id: str) -> dict[str, Any]:
    require_owner(account)
    campaign = require_campaign(state, account, campaign_id)
    for character_id in list(campaign.get("characters", [])):
        character = state["characters"].get(character_id)
        if character:
            character.pop("active_campaign_id", None)
    account["campaign_ids"] = [cid for cid in account.get("campaign_ids", []) if cid != campaign_id]
    del state["campaigns"][campaign_id]
    state["admin_events"].append(
        {"type": "reset_campaign", "campaign_id": campaign_id, "account_id": account["account_id"], "at": utc_now()}
    )
    return {"reset": True, "campaign_id": campaign_id}


def grant_dev_item(state: dict[str, Any], account: dict[str, Any], character_id: str, item_id: str, quantity: int) -> dict[str, Any]:
    require_owner(account)
    quantity = int(quantity)
    if quantity <= 0 or quantity > 99:
        raise GameError("Development item quantity must be between 1 and 99.")
    character = require_character(state, account, character_id)
    if item_id in character["inventory"]:
        character["inventory"][item_id]["quantity"] += quantity
    else:
        character["inventory"][item_id] = clone_item(item_id, quantity)
    state["admin_events"].append(
        {"type": "grant_item", "character_id": character_id, "item_id": item_id, "quantity": quantity, "at": utc_now()}
    )
    return character


def admin_snapshot(state: dict[str, Any], account: dict[str, Any]) -> dict[str, Any]:
    require_owner(account)
    return {
        "accounts": [_admin_account(account_record) for account_record in state["accounts"].values()],
        "characters": list(state["characters"].values()),
        "campaigns": list(state["campaigns"].values()),
        "ai_proposals": list(state["ai_proposals"].values())[-50:],
        "validation_failures": state["validation_failures"][-50:],
        "session_logs": list(state["session_logs"].values())[-100:],
        "settings": state["settings"],
        "admin_events": state["admin_events"][-50:],
    }


def _admin_account(account: dict[str, Any]) -> dict[str, Any]:
    return {
        "account_id": account["account_id"],
        "handle": account["handle"],
        "role": account["role"],
        "created_at": account["created_at"],
        "character_ids": account.get("character_ids", []),
        "campaign_ids": account.get("campaign_ids", []),
        "party_ids": account.get("party_ids", []),
        "has_password_hash": bool(account.get("password_hash")),
    }


def maintenance_toggle(state: dict[str, Any], account: dict[str, Any], enabled: bool) -> dict[str, Any]:
    require_owner(account)
    state["settings"]["maintenance_mode"] = bool(enabled)
    return state["settings"]


def ai_toggle(state: dict[str, Any], account: dict[str, Any], enabled: bool) -> dict[str, Any]:
    require_owner(account)
    state["settings"]["ai_enabled"] = bool(enabled)
    return state["settings"]


def fallback_response() -> dict[str, Any]:
    return system_fallback("The local Game Master is unavailable. Deterministic rules remain active.")
