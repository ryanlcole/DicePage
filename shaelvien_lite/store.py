"""JSON persistence for the local Shaelvien Lite vertical slice."""

from __future__ import annotations

import copy
import json
import os
import secrets
import tempfile
import threading
from datetime import datetime, timezone
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from . import STATE_VERSION
from .seed_data import NPCS, PRODUCT_CATALOG_PLACEHOLDERS


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def new_secret(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"


def default_state_path() -> Path:
    env_path = os.getenv("SHAELVIEN_LITE_STATE")
    if env_path:
        return Path(env_path)
    return Path.cwd() / "data" / "shaelvien_lite_state.json"


def initial_state() -> dict[str, Any]:
    now = utc_now()
    return {
        "version": STATE_VERSION,
        "created_at": now,
        "updated_at": now,
        "accounts": {},
        "sessions": {},
        "characters": {},
        "campaigns": {},
        "parties": {},
        "session_logs": {},
        "ai_proposals": {},
        "validated_state_changes": {},
        "validation_failures": [],
        "admin_events": [],
        "settings": {
            "ai_enabled": True,
            "maintenance_mode": False,
            "auth_mode": os.getenv("SHAELVIEN_LITE_ENV", "development"),
        },
        "setup": {
            "owner_bootstrap_used": False,
            "owner_bootstrap_mode": "development-first-account",
        },
        "idempotency": {},
        "entitlements": {
            "catalog": copy.deepcopy(PRODUCT_CATALOG_PLACEHOLDERS),
            "account_entitlements": {},
            "dev_test_entitlements": {},
        },
        "npc_templates": copy.deepcopy(NPCS),
    }


class GameStore:
    """Small atomic JSON store.

    This is intentionally conservative for PC hosting. It is not a replacement
    for a production database, but it preserves the save/reload loop and keeps
    all state transitions inspectable.
    """

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else default_state_path()
        self._lock = threading.RLock()

    def load(self) -> dict[str, Any]:
        with self._lock:
            if not self.path.exists():
                state = initial_state()
                self.save(state)
                return state
            try:
                with self.path.open("r", encoding="utf-8") as handle:
                    state = json.load(handle)
            except JSONDecodeError:
                corrupt_path = self.path.with_suffix(f"{self.path.suffix}.corrupt.{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
                os.replace(self.path, corrupt_path)
                state = initial_state()
                state["validation_failures"].append(
                    {
                        "at": utc_now(),
                        "type": "malformed_state_recovered",
                        "detail": f"Malformed state moved to {corrupt_path.name}.",
                    }
                )
                self.save(state)
                return state
            if state.get("version") != STATE_VERSION:
                state["version"] = STATE_VERSION
            self._ensure_shape(state)
            return state

    def save(self, state: dict[str, Any]) -> None:
        with self._lock:
            state["updated_at"] = utc_now()
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, temp_path = tempfile.mkstemp(
                prefix=f".{self.path.name}.", suffix=".tmp", dir=str(self.path.parent)
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(state, handle, indent=2, sort_keys=True)
                os.replace(temp_path, self.path)
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def update(self, callback: Callable[[dict[str, Any]], Any]) -> Any:
        with self._lock:
            state = self.load()
            result = callback(state)
            self.save(state)
            return result

    def _ensure_shape(self, state: dict[str, Any]) -> None:
        baseline = initial_state()
        for key, value in baseline.items():
            state.setdefault(key, copy.deepcopy(value))
        state.setdefault("settings", {}).setdefault("auth_mode", os.getenv("SHAELVIEN_LITE_ENV", "development"))
        state.setdefault("setup", {}).setdefault("owner_bootstrap_used", False)
        state.setdefault("setup", {}).setdefault("owner_bootstrap_mode", "development-first-account")
        state.setdefault("idempotency", {})
        for account in state.get("accounts", {}).values():
            account.setdefault("role", "player")
            account.setdefault("character_ids", [])
            account.setdefault("campaign_ids", [])
            account.setdefault("party_ids", [])
            account.setdefault("password_hash", None)
        for campaign in state.get("campaigns", {}).values():
            campaign.setdefault("processed_action_keys", {})


def public_account(account: dict[str, Any]) -> dict[str, Any]:
    return {
        "account_id": account["account_id"],
        "handle": account["handle"],
        "role": account["role"],
        "created_at": account["created_at"],
    }
