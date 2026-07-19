"""PostgreSQL persistence for hosted Shaelvien Lite staging."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable

from . import STATE_VERSION
from .store import StorageUnavailable, apply_retention_limits, initial_state, utc_now

try:  # Imported lazily so local JSON development does not require Postgres.
    import psycopg
    from psycopg.rows import dict_row
    from psycopg.types.json import Jsonb
except Exception:  # pragma: no cover - exercised only when psycopg is absent.
    psycopg = None
    dict_row = None
    Jsonb = None


MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


class PostgresStorage:
    """Small transactional Postgres adapter for the current deterministic engine."""

    def __init__(
        self,
        database_url: str,
        *,
        connect_timeout_seconds: int = 5,
        retry_attempts: int = 2,
    ):
        self.database_url = database_url
        self.connect_timeout_seconds = int(connect_timeout_seconds)
        self.retry_attempts = int(retry_attempts)
        self.last_successful_connection_at: str | None = None
        self.connection_failure_count = 0

    def _connect(self):
        if psycopg is None:
            raise StorageUnavailable("PostgreSQL driver is not installed.")
        if not self.database_url:
            raise StorageUnavailable("PostgreSQL storage is not configured.")
        last_error: BaseException | None = None
        for attempt in range(self.retry_attempts + 1):
            try:
                conn = psycopg.connect(
                    self.database_url,
                    autocommit=False,
                    connect_timeout=self.connect_timeout_seconds,
                    row_factory=dict_row,
                )
                self.last_successful_connection_at = utc_now()
                return conn
            except Exception as exc:  # Do not expose DSNs or host details.
                self.connection_failure_count += 1
                last_error = exc
                if attempt < self.retry_attempts:
                    time.sleep(0.4 * (attempt + 1))
        raise StorageUnavailable("Shaelvien Lite is waking from rest. Try again in a moment.") from last_error

    def ready(self) -> bool:
        with self._connect() as conn:
            conn.execute("SELECT 1")
            self._require_schema(conn)
            conn.commit()
        return True

    def migration_status(self) -> dict[str, Any]:
        with self._connect() as conn:
            self._ensure_migration_table(conn)
            applied = {
                row["version"]: row
                for row in conn.execute("SELECT version, name, applied_at FROM schema_migrations ORDER BY version")
            }
            available = [path.name for path in _migration_files()]
            conn.commit()
        return {"applied": list(applied), "available": available, "pending": [name for name in available if name not in applied]}

    def apply_migrations(self) -> dict[str, Any]:
        applied_now: list[str] = []
        with self._connect() as conn:
            self._ensure_migration_table(conn)
            applied = {row["version"] for row in conn.execute("SELECT version FROM schema_migrations")}
            for path in _migration_files():
                if path.name in applied:
                    continue
                _execute_sql_script(conn, path.read_text(encoding="utf-8"))
                conn.execute(
                    "INSERT INTO schema_migrations (version, name, applied_at) VALUES (%s, %s, now())",
                    (path.name, path.stem),
                )
                applied_now.append(path.name)
            conn.commit()
        return {"applied": applied_now, "schema_current": len(applied_now) == 0}

    def load(self) -> dict[str, Any]:
        with self._connect() as conn:
            self._require_schema(conn)
            state = self._load_in_transaction(conn)
            conn.commit()
        return state

    def save(self, state: dict[str, Any]) -> None:
        with self._connect() as conn:
            self._require_schema(conn)
            self._save_in_transaction(conn, state)
            conn.commit()

    def update(self, callback: Callable[[dict[str, Any]], Any]) -> Any:
        with self._connect() as conn:
            self._require_schema(conn)
            state = self._load_in_transaction(conn)
            result = callback(state)
            self._save_in_transaction(conn, state)
            conn.commit()
            return result

    def _ensure_migration_table(self, conn) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )

    def _require_schema(self, conn) -> None:
        exists = conn.execute("SELECT to_regclass('public.schema_migrations') AS table_name").fetchone()
        if not exists or not exists["table_name"]:
            raise StorageUnavailable("Database schema has not been initialized.")
        rows = list(conn.execute("SELECT version FROM schema_migrations WHERE version = %s", ("001_initial_postgres.sql",)))
        if not rows:
            raise StorageUnavailable("Database schema migration is pending.")

    def _load_in_transaction(self, conn) -> dict[str, Any]:
        state = initial_state()
        state["version"] = STATE_VERSION

        for row in conn.execute("SELECT key, value FROM app_state_meta"):
            state[row["key"]] = _json(row["value"])

        state.setdefault("accounts", {})
        for row in conn.execute("SELECT * FROM accounts ORDER BY created_at"):
            profile = _json(row["profile"])
            profile.update(
                {
                    "account_id": row["account_id"],
                    "handle": row["handle"],
                    "role": row["role"],
                    "password_hash": row["password_hash"],
                    "created_at": _text_time(row["created_at"]),
                }
            )
            profile.setdefault("character_ids", [])
            profile.setdefault("campaign_ids", [])
            profile.setdefault("party_ids", [])
            state["accounts"][row["account_id"]] = profile

        entitlements = state.setdefault("entitlements", {}).setdefault("account_entitlements", {})
        for row in conn.execute("SELECT * FROM account_entitlements"):
            entitlements[row["account_id"]] = {
                "free_play": row["free_play"],
                "character_slots": row["character_slots"],
                "campaign_slots": row["campaign_slots"],
                "cosmetics": _json(row["cosmetics"]),
                "dev_flags": _json(row["dev_flags"]),
            }

        state["sessions"] = {}
        for row in conn.execute("SELECT * FROM sessions"):
            profile = _json(row["profile"])
            profile.update(
                {
                    "token": row["token"],
                    "account_id": row["account_id"],
                    "csrf_token": row["csrf_token"],
                    "created_at": _text_time(row["created_at"]),
                    "last_seen_at": _text_time(row["last_seen_at"]),
                }
            )
            state["sessions"][row["token"]] = profile

        state["characters"] = {}
        for row in conn.execute("SELECT * FROM characters ORDER BY character_id"):
            profile = _json(row["profile"])
            profile.update(
                {
                    "character_id": row["character_id"],
                    "player_id": row["account_id"],
                    "name": row["name"],
                    "role": row["role_name"],
                    "level": row["level"],
                    "experience": row["experience"],
                    "health": row["health"],
                    "max_health": row["max_health"],
                    "currency": row["currency"],
                    "active_campaign_id": row["active_campaign_id"],
                }
            )
            profile["inventory"] = {}
            profile["equipment"] = {}
            state["characters"][row["character_id"]] = profile
            account = state["accounts"].get(row["account_id"])
            if account is not None and row["character_id"] not in account.setdefault("character_ids", []):
                account["character_ids"].append(row["character_id"])

        for row in conn.execute("SELECT * FROM character_inventory ORDER BY character_id, item_id"):
            character = state["characters"].get(row["character_id"])
            if character:
                item = _json(row["item_json"])
                item["quantity"] = row["quantity"]
                character["inventory"][row["item_id"]] = item

        for row in conn.execute("SELECT * FROM character_equipment ORDER BY character_id, slot"):
            character = state["characters"].get(row["character_id"])
            if character:
                character["equipment"][row["slot"]] = _json(row["equipment_json"])

        state["campaigns"] = {}
        for row in conn.execute("SELECT * FROM campaigns ORDER BY created_at"):
            profile = _json(row["profile"])
            profile.update(
                {
                    "campaign_id": row["campaign_id"],
                    "owner_account_id": row["owner_account_id"],
                    "party_id": row["party_id"],
                    "region_id": row["region_id"],
                    "current_location": row["current_location"],
                    "created_at": _text_time(row["created_at"]),
                    "updated_at": _text_time(row["updated_at"]),
                }
            )
            profile.setdefault("scene_state", {})["active_quest_id"] = row["active_quest_id"]
            profile.setdefault("characters", [])
            profile["quests"] = {}
            profile["camp_progression"] = {}
            profile["completed_encounters"] = []
            state["campaigns"][row["campaign_id"]] = profile
            account = state["accounts"].get(row["owner_account_id"])
            if account is not None and row["campaign_id"] not in account.setdefault("campaign_ids", []):
                account["campaign_ids"].append(row["campaign_id"])

        for row in conn.execute("SELECT campaign_id, character_id FROM campaign_characters"):
            campaign = state["campaigns"].get(row["campaign_id"])
            if campaign and row["character_id"] not in campaign.setdefault("characters", []):
                campaign["characters"].append(row["character_id"])

        for row in conn.execute("SELECT * FROM campaign_quests ORDER BY campaign_id, quest_id"):
            campaign = state["campaigns"].get(row["campaign_id"])
            if campaign:
                quest = _json(row["quest_json"])
                quest.update({"quest_id": row["quest_id"], "status": row["status"], "completed_steps": _json(row["completed_steps"])})
                campaign["quests"][row["quest_id"]] = quest

        for row in conn.execute("SELECT * FROM campaign_camp_structures ORDER BY campaign_id, structure_id"):
            campaign = state["campaigns"].get(row["campaign_id"])
            if campaign:
                structure = _json(row["structure_json"])
                structure.update(
                    {
                        "structure_id": row["structure_id"],
                        "level": row["level"],
                        "max_level": row["max_level"],
                        "upgrade_state": row["upgrade_state"],
                        "upgrade_complete_at": _text_time(row["upgrade_complete_at"]) if row["upgrade_complete_at"] else None,
                    }
                )
                campaign["camp_progression"][row["structure_id"]] = structure

        for row in conn.execute("SELECT campaign_id, encounter_id FROM campaign_completed_encounters ORDER BY completed_at"):
            campaign = state["campaigns"].get(row["campaign_id"])
            if campaign:
                campaign["completed_encounters"].append(row["encounter_id"])

        state["session_logs"] = {}
        for row in conn.execute("SELECT * FROM session_logs ORDER BY created_at"):
            entry = _json(row["payload"])
            entry.update(
                {
                    "log_id": row["log_id"],
                    "campaign_id": row["campaign_id"],
                    "type": row["entry_type"],
                    "text": row["text"],
                    "roll_result": _json(row["roll_result"]) if row["roll_result"] is not None else None,
                    "created_at": _text_time(row["created_at"]),
                }
            )
            state["session_logs"][row["log_id"]] = entry

        state["ai_proposals"] = {}
        for row in conn.execute("SELECT * FROM ai_validation_records ORDER BY created_at"):
            state["ai_proposals"][row["proposal_id"]] = {
                "proposal_id": row["proposal_id"],
                "campaign_id": row["campaign_id"],
                "character_id": row["character_id"],
                "request": _json(row["request_json"]),
                "response": _json(row["response_json"]),
                "created_at": _text_time(row["created_at"]),
            }

        state["validated_state_changes"] = {}
        for row in conn.execute("SELECT proposal_id, changes_json FROM validated_state_changes"):
            state["validated_state_changes"][row["proposal_id"]] = _json(row["changes_json"])

        state["validation_failures"] = []
        for row in conn.execute("SELECT * FROM validation_failures ORDER BY failure_id"):
            payload = _json(row["payload"])
            payload.update({"at": _text_time(row["at"]), "route": row["route"], "status": row["status"], "message": row["message"]})
            state["validation_failures"].append(payload)

        state["admin_events"] = []
        for row in conn.execute("SELECT * FROM admin_events ORDER BY event_id"):
            payload = _json(row["payload"])
            payload.setdefault("type", row["event_type"])
            payload.setdefault("at", _text_time(row["at"]))
            state["admin_events"].append(payload)

        state["parties"] = {}
        for row in conn.execute("SELECT * FROM parties"):
            state["parties"][row["party_id"]] = _json(row["party_json"])

        return state

    def _save_in_transaction(self, conn, state: dict[str, Any]) -> None:
        apply_retention_limits(state)
        state["updated_at"] = utc_now()
        _clear_tables(conn)

        for key in ("settings", "setup", "entitlements", "npc_templates"):
            conn.execute(
                "INSERT INTO app_state_meta (key, value, updated_at) VALUES (%s, %s, now())",
                (key, _jsonb(state.get(key, {}))),
            )

        for account in state.get("accounts", {}).values():
            conn.execute(
                """
                INSERT INTO accounts (account_id, handle, role, password_hash, created_at, profile)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    account["account_id"],
                    account["handle"],
                    account.get("role", "player"),
                    account.get("password_hash") or "",
                    account.get("created_at") or utc_now(),
                    _jsonb(account),
                ),
            )

        for account_id, entitlement in state.get("entitlements", {}).get("account_entitlements", {}).items():
            if account_id not in state.get("accounts", {}):
                continue
            conn.execute(
                """
                INSERT INTO account_entitlements
                    (account_id, free_play, character_slots, campaign_slots, cosmetics, dev_flags)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    account_id,
                    bool(entitlement.get("free_play", True)),
                    int(entitlement.get("character_slots", 2)),
                    int(entitlement.get("campaign_slots", 1)),
                    _jsonb(entitlement.get("cosmetics", [])),
                    _jsonb(entitlement.get("dev_flags", [])),
                ),
            )

        for token, session in state.get("sessions", {}).items():
            if session.get("account_id") not in state.get("accounts", {}):
                continue
            conn.execute(
                """
                INSERT INTO sessions (token, account_id, csrf_token, created_at, last_seen_at, profile)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    token,
                    session["account_id"],
                    session.get("csrf_token", ""),
                    session.get("created_at") or utc_now(),
                    session.get("last_seen_at") or utc_now(),
                    _jsonb(session),
                ),
            )

        for character in state.get("characters", {}).values():
            conn.execute(
                """
                INSERT INTO characters
                    (character_id, account_id, name, role_name, level, experience, health, max_health,
                     currency, active_campaign_id, profile)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    character["character_id"],
                    character["player_id"],
                    character["name"],
                    character["role"],
                    int(character.get("level", 1)),
                    int(character.get("experience", 0)),
                    int(character.get("health", 0)),
                    int(character.get("max_health", 1)),
                    int(character.get("currency", 0)),
                    character.get("active_campaign_id"),
                    _jsonb(character),
                ),
            )
            for item_id, item in character.get("inventory", {}).items():
                conn.execute(
                    """
                    INSERT INTO character_inventory
                        (character_id, item_id, name, category, quantity, value, item_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        character["character_id"],
                        item_id,
                        item.get("name", item_id),
                        item.get("category", "misc"),
                        int(item.get("quantity", 0)),
                        int(item.get("value", 0)),
                        _jsonb(item),
                    ),
                )
            for slot, value in character.get("equipment", {}).items():
                item_id = value if isinstance(value, str) else None
                conn.execute(
                    """
                    INSERT INTO character_equipment (character_id, slot, item_id, equipment_json)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (character["character_id"], slot, item_id, _jsonb(value)),
                )

        for campaign in state.get("campaigns", {}).values():
            scene = campaign.get("scene_state", {})
            primary_character_id = (campaign.get("characters") or [None])[0]
            conn.execute(
                """
                INSERT INTO campaigns
                    (campaign_id, owner_account_id, party_id, primary_character_id, region_id,
                     current_location, active_quest_id, combat_active, created_at, updated_at, profile)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    campaign["campaign_id"],
                    campaign["owner_account_id"],
                    campaign.get("party_id"),
                    primary_character_id,
                    campaign.get("region_id", "shaelvien_emberhall_region"),
                    campaign.get("current_location", "emberhall_outpost"),
                    scene.get("active_quest_id"),
                    bool(campaign.get("combat")),
                    campaign.get("created_at") or utc_now(),
                    campaign.get("updated_at") or utc_now(),
                    _jsonb(campaign),
                ),
            )
            for character_id in campaign.get("characters", []):
                if character_id in state.get("characters", {}):
                    conn.execute(
                        "INSERT INTO campaign_characters (campaign_id, character_id) VALUES (%s, %s)",
                        (campaign["campaign_id"], character_id),
                    )
            for quest_id, quest in campaign.get("quests", {}).items():
                conn.execute(
                    """
                    INSERT INTO campaign_quests
                        (campaign_id, quest_id, status, completed_steps, quest_json)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        campaign["campaign_id"],
                        quest_id,
                        quest.get("status", "locked"),
                        _jsonb(quest.get("completed_steps", [])),
                        _jsonb(quest),
                    ),
                )
            for structure_id, structure in campaign.get("camp_progression", {}).items():
                conn.execute(
                    """
                    INSERT INTO campaign_camp_structures
                        (campaign_id, structure_id, level, max_level, upgrade_state, upgrade_complete_at, structure_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        campaign["campaign_id"],
                        structure_id,
                        int(structure.get("level", 0)),
                        int(structure.get("max_level", 0)),
                        structure.get("upgrade_state", "ready"),
                        structure.get("upgrade_complete_at"),
                        _jsonb(structure),
                    ),
                )
            for encounter_id in campaign.get("completed_encounters", []):
                conn.execute(
                    """
                    INSERT INTO campaign_completed_encounters (campaign_id, encounter_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (campaign["campaign_id"], encounter_id),
                )
            for key, value in campaign.get("processed_action_keys", {}).items():
                conn.execute(
                    """
                    INSERT INTO idempotency_records
                        (campaign_id, idempotency_key, proposal_id, action_text, created_at, payload)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        campaign["campaign_id"],
                        key,
                        value.get("proposal_id"),
                        value.get("action", ""),
                        value.get("at") or utc_now(),
                        _jsonb(value),
                    ),
                )

        for party_id, party in state.get("parties", {}).items():
            conn.execute(
                "INSERT INTO parties (party_id, owner_account_id, party_json) VALUES (%s, %s, %s)",
                (party_id, party.get("party_owner"), _jsonb(party)),
            )

        for log in state.get("session_logs", {}).values():
            conn.execute(
                """
                INSERT INTO session_logs (log_id, campaign_id, entry_type, text, roll_result, created_at, payload)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    log["log_id"],
                    log.get("campaign_id"),
                    log.get("type", "system"),
                    log.get("text", ""),
                    _jsonb(log.get("roll_result")) if log.get("roll_result") is not None else None,
                    log.get("created_at") or utc_now(),
                    _jsonb(log),
                ),
            )

        for proposal_id, proposal in state.get("ai_proposals", {}).items():
            conn.execute(
                """
                INSERT INTO ai_validation_records
                    (proposal_id, campaign_id, character_id, request_json, response_json, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    proposal_id,
                    proposal.get("campaign_id"),
                    proposal.get("character_id"),
                    _jsonb(proposal.get("request", {})),
                    _jsonb(proposal.get("response", {})),
                    proposal.get("created_at") or utc_now(),
                ),
            )
            changes = state.get("validated_state_changes", {}).get(proposal_id)
            if changes is not None:
                conn.execute(
                    "INSERT INTO validated_state_changes (proposal_id, changes_json) VALUES (%s, %s)",
                    (proposal_id, _jsonb(changes)),
                )
            for index, reward in enumerate(proposal.get("response", {}).get("rewards", []) or []):
                conn.execute(
                    """
                    INSERT INTO rewards (reward_id, campaign_id, character_id, source, payload, granted_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        f"reward_{proposal_id}_{index}",
                        proposal.get("campaign_id"),
                        proposal.get("character_id"),
                        reward.get("source", "ai_response"),
                        _jsonb(reward),
                        proposal.get("created_at") or utc_now(),
                    ),
                )

        for failure in state.get("validation_failures", [])[-200:]:
            conn.execute(
                """
                INSERT INTO validation_failures (at, route, status, message, payload)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    failure.get("at") or utc_now(),
                    failure.get("route"),
                    failure.get("status"),
                    failure.get("message") or failure.get("detail") or "validation failure",
                    _jsonb(failure),
                ),
            )

        for event in state.get("admin_events", [])[-200:]:
            conn.execute(
                "INSERT INTO admin_events (at, event_type, payload) VALUES (%s, %s, %s)",
                (event.get("at") or utc_now(), event.get("type", "admin_event"), _jsonb(event)),
            )


def _migration_files() -> list[Path]:
    return sorted(MIGRATIONS_DIR.glob("*.sql"))


def _execute_sql_script(conn, script: str) -> None:
    for statement in script.split(";"):
        sql = statement.strip()
        if sql:
            conn.execute(sql)


def _jsonb(value: Any):
    if Jsonb is None:
        raise StorageUnavailable("PostgreSQL JSON support is not available.")
    return Jsonb(value)


def _json(value: Any) -> Any:
    if value is None:
        return {}
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _text_time(value: Any) -> str | None:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _clear_tables(conn) -> None:
    for table in (
        "validated_state_changes",
        "ai_validation_records",
        "idempotency_records",
        "rewards",
        "session_logs",
        "validation_failures",
        "admin_events",
        "campaign_completed_encounters",
        "campaign_camp_structures",
        "campaign_quests",
        "campaign_characters",
        "parties",
        "campaigns",
        "character_equipment",
        "character_inventory",
        "characters",
        "sessions",
        "account_entitlements",
        "accounts",
        "app_state_meta",
    ):
        conn.execute(f"DELETE FROM {table}")
