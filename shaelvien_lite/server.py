"""Local PC-hosted HTTP server for Shaelvien Lite."""

from __future__ import annotations

import json
import mimetypes
import time
import traceback
from http.cookies import SimpleCookie
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .config import load_config, validate_startup
from .engine import (
    GameError,
    admin_snapshot,
    ai_toggle,
    create_character,
    create_or_enter_account,
    grant_dev_item,
    invalidate_session,
    maintenance_toggle,
    process_player_action,
    require_campaign,
    require_csrf,
    require_owner,
    require_session,
    reset_development_campaign,
    start_tutorial_campaign,
    summarize_state,
)
from .store import GameStore, utc_now

STATIC_ROOT = Path(__file__).parent / "static"
ERROR_LOG = Path.cwd() / "logs" / "shaelvien_lite_errors.jsonl"
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_ACTIONS = 30
AUTH_RATE_LIMIT_MAX = 10
RATE_BUCKETS: dict[str, deque[float]] = defaultdict(deque)
SESSION_COOKIE = "shaelvien_lite_session"
SESSION_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 30


def read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length") or "0")
    if length <= 0:
        return {}
    if length > load_config().max_request_bytes:
        raise GameError("Request body too large.", 413)
    raw = handler.rfile.read(length)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise GameError(f"Invalid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise GameError("JSON body must be an object.")
    return payload


def write_error_log(route: str, exc: BaseException) -> None:
    ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "at": utc_now(),
        "route": route,
        "error": str(exc),
        "type": exc.__class__.__name__,
        "traceback": traceback.format_exc(limit=6),
    }
    with ERROR_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def record_validation_failure(store: GameStore, route: str, exc: GameError) -> None:
    def op(state: dict[str, Any]) -> None:
        state.setdefault("validation_failures", []).append(
            {
                "at": utc_now(),
                "route": route,
                "status": exc.status,
                "message": str(exc),
            }
        )
        state["validation_failures"] = state["validation_failures"][-200:]

    try:
        store.update(op)
    except Exception:
        write_error_log(route, exc)


def client_token(handler: BaseHTTPRequestHandler) -> str | None:
    cookie_token = cookie_value(handler, SESSION_COOKIE)
    if cookie_token:
        return cookie_token
    auth = handler.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return handler.headers.get("X-Session-Token")


def client_csrf(handler: BaseHTTPRequestHandler) -> str | None:
    return handler.headers.get("X-CSRF-Token")


def cookie_value(handler: BaseHTTPRequestHandler, name: str) -> str | None:
    raw = handler.headers.get("Cookie")
    if not raw:
        return None
    cookie = SimpleCookie()
    try:
        cookie.load(raw)
    except Exception:
        return None
    morsel = cookie.get(name)
    return morsel.value if morsel else None


def check_rate(handler: BaseHTTPRequestHandler, bucket_name: str) -> None:
    remote = handler.client_address[0] if handler.client_address else "local"
    token = client_token(handler) or remote
    key = f"{bucket_name}:{token}"
    now = time.monotonic()
    bucket = RATE_BUCKETS[key]
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_MAX_ACTIONS:
        raise GameError("Too many actions. Wait a moment before sending another.", 429)
    bucket.append(now)


def check_auth_rate(handler: BaseHTTPRequestHandler) -> None:
    remote = handler.client_address[0] if handler.client_address else "local"
    key = f"auth:{remote}"
    now = time.monotonic()
    bucket = RATE_BUCKETS[key]
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW:
        bucket.popleft()
    if len(bucket) >= AUTH_RATE_LIMIT_MAX:
        raise GameError("Too many account attempts. Wait a moment before trying again.", 429)
    bucket.append(now)


class ShaelvienLiteHandler(BaseHTTPRequestHandler):
    store = GameStore()
    server_version = "ShaelvienLite/0.1"

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(load_config().request_timeout_seconds)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:
        try:
            parsed = urlparse(self.path)
            if parsed.path == "/health":
                self._json({"status": "ok"})
            elif parsed.path == "/ready":
                self._ready()
            elif parsed.path.startswith("/api/"):
                self._handle_get_api(parsed.path, parse_qs(parsed.query))
            else:
                self._serve_static(parsed.path)
        except GameError as exc:
            record_validation_failure(self.store, self.path, exc)
            self._json({"error": str(exc)}, exc.status)
        except Exception as exc:
            write_error_log(self.path, exc)
            self._json({"error": "Internal server error."}, 500)

    def do_POST(self) -> None:
        try:
            parsed = urlparse(self.path)
            if not parsed.path.startswith("/api/"):
                raise GameError("Unknown route.", 404)
            payload = read_json(self)
            self._handle_post_api(parsed.path, payload)
        except GameError as exc:
            record_validation_failure(self.store, self.path, exc)
            self._json({"error": str(exc)}, exc.status)
        except Exception as exc:
            write_error_log(self.path, exc)
            self._json({"error": "Internal server error."}, 500)

    def _handle_get_api(self, path: str, query: dict[str, list[str]]) -> None:
        if path == "/api/bootstrap":
            token = client_token(self)

            def op(state: dict[str, Any]) -> dict[str, Any]:
                account = require_session(state, token) if token else None
                data = summarize_state(state, account)
                if token and token in state["sessions"]:
                    data["csrf_token"] = state["sessions"][token].get("csrf_token")
                return data

            self._json(self.store.update(op))
            return
        if path == "/api/session-log":
            token = client_token(self)
            campaign_id = (query.get("campaign_id") or [""])[0]

            def op(state: dict[str, Any]) -> dict[str, Any]:
                account = require_session(state, token)
                campaign = require_campaign(state, account, campaign_id)
                logs = [
                    state["session_logs"][log_id]
                    for log_id in campaign.get("session_log_ids", [])
                    if log_id in state["session_logs"]
                ]
                return {"logs": logs}

            self._json(self.store.update(op))
            return
        if path == "/api/admin":
            token = client_token(self)

            def op(state: dict[str, Any]) -> dict[str, Any]:
                account = require_session(state, token)
                return admin_snapshot(state, account)

            self._json(self.store.update(op))
            return
        raise GameError("Unknown API route.", 404)

    def _handle_post_api(self, path: str, payload: dict[str, Any]) -> None:
        if path == "/api/account/enter":
            check_auth_rate(self)
            config = load_config()
            configured_owner_token = config.owner_bootstrap_token
            env_mode = config.mode

            def op(state: dict[str, Any]) -> dict[str, Any]:
                result = create_or_enter_account(
                    state,
                    str(payload.get("handle", "")),
                    password=str(payload.get("password", "")),
                    owner_bootstrap_token=str(payload.get("owner_bootstrap_token", "")) or None,
                    configured_owner_token=configured_owner_token,
                    env_mode=env_mode,
                )
                return {
                    "csrf_token": result["csrf_token"],
                    "account": {
                        "account_id": result["account"]["account_id"],
                        "handle": result["account"]["handle"],
                        "role": result["account"]["role"],
                    },
                    "_session_token": result["token"],
                }

            result = self.store.update(op)
            token = result.pop("_session_token")
            self._json(result, extra_headers={"Set-Cookie": self._session_cookie_header(token)})
            return
        if path == "/api/account/logout":
            token = client_token(self)
            csrf = client_csrf(self)

            def op(state: dict[str, Any]) -> dict[str, Any]:
                require_csrf(state, token, csrf)
                invalidate_session(state, token)
                return {"ok": True}

            self._json(self.store.update(op), extra_headers={"Set-Cookie": self._session_cookie_header("", clear=True)})
            return
        if path == "/api/characters":
            token = client_token(self)
            csrf = client_csrf(self)

            def op(state: dict[str, Any]) -> dict[str, Any]:
                require_csrf(state, token, csrf)
                account = require_session(state, token)
                character = create_character(
                    state,
                    account,
                    str(payload.get("name", "")),
                    str(payload.get("role_id", "")),
                    ancestry=str(payload.get("ancestry", "")).strip() or None,
                )
                return {"character": character}

            self._json(self.store.update(op), 201)
            return
        if path == "/api/campaigns/tutorial/start":
            token = client_token(self)
            csrf = client_csrf(self)

            def op(state: dict[str, Any]) -> dict[str, Any]:
                require_csrf(state, token, csrf)
                account = require_session(state, token)
                campaign = start_tutorial_campaign(state, account, str(payload.get("character_id", "")))
                return {"campaign": campaign}

            self._json(self.store.update(op), 201)
            return
        if path == "/api/game/action":
            check_rate(self, "game_action")
            token = client_token(self)
            csrf = client_csrf(self)

            def op(state: dict[str, Any]) -> dict[str, Any]:
                require_csrf(state, token, csrf)
                account = require_session(state, token)
                if state["settings"].get("maintenance_mode") and account.get("role") != "owner":
                    raise GameError("The game is in maintenance mode.", 503)
                return process_player_action(
                    state,
                    account,
                    str(payload.get("campaign_id", "")),
                    str(payload.get("character_id", "")),
                    str(payload.get("action", "")),
                    idempotency_key=str(payload.get("idempotency_key", "")) or None,
                    target_id=str(payload.get("target_id", "")) or None,
                )

            self._json(self.store.update(op))
            return
        if path == "/api/admin/reset-campaign":
            token = client_token(self)
            csrf = client_csrf(self)

            def op(state: dict[str, Any]) -> dict[str, Any]:
                require_csrf(state, token, csrf)
                account = require_session(state, token)
                return reset_development_campaign(state, account, str(payload.get("campaign_id", "")))

            self._json(self.store.update(op))
            return
        if path == "/api/admin/grant-item":
            token = client_token(self)
            csrf = client_csrf(self)

            def op(state: dict[str, Any]) -> dict[str, Any]:
                require_csrf(state, token, csrf)
                account = require_session(state, token)
                return {
                    "character": grant_dev_item(
                        state,
                        account,
                        str(payload.get("character_id", "")),
                        str(payload.get("item_id", "")),
                        int(payload.get("quantity", 1)),
                    )
                }

            self._json(self.store.update(op))
            return
        if path == "/api/admin/camp-level":
            token = client_token(self)
            csrf = client_csrf(self)

            def op(state: dict[str, Any]) -> dict[str, Any]:
                require_csrf(state, token, csrf)
                account = require_session(state, token)
                require_owner(account)
                campaign = require_campaign(state, account, str(payload.get("campaign_id", "")))
                structure_id = str(payload.get("structure_id", ""))
                if structure_id not in campaign["camp_progression"]:
                    raise GameError("Unknown camp structure.")
                level = max(0, min(int(payload.get("level", 0)), campaign["camp_progression"][structure_id]["max_level"]))
                campaign["camp_progression"][structure_id]["level"] = level
                return {"campaign": campaign}

            self._json(self.store.update(op))
            return
        if path == "/api/admin/settings":
            token = client_token(self)
            csrf = client_csrf(self)

            def op(state: dict[str, Any]) -> dict[str, Any]:
                require_csrf(state, token, csrf)
                account = require_session(state, token)
                if "ai_enabled" in payload:
                    ai_toggle(state, account, bool(payload["ai_enabled"]))
                if "maintenance_mode" in payload:
                    maintenance_toggle(state, account, bool(payload["maintenance_mode"]))
                return {"settings": state["settings"]}

            self._json(self.store.update(op))
            return
        raise GameError("Unknown API route.", 404)

    def _serve_static(self, request_path: str) -> None:
        if request_path in ("", "/"):
            relative = "index.html"
        else:
            relative = request_path.lstrip("/")
        target = (STATIC_ROOT / relative).resolve()
        if STATIC_ROOT.resolve() not in target.parents and target != STATIC_ROOT.resolve():
            raise GameError("Invalid path.", 400)
        if not target.exists() or not target.is_file():
            target = STATIC_ROOT / "index.html"
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store" if target.name == "index.html" else "public, max-age=3600")
        self.end_headers()
        self.wfile.write(data)

    def _ready(self) -> None:
        def op(state: dict[str, Any]) -> dict[str, Any]:
            return {
                "status": "ready",
                "version": state.get("version"),
                "mode": load_config().mode,
                "storage": "available",
            }

        self._json(self.store.update(op))

    def _json(self, payload: dict[str, Any], status: int = 200, extra_headers: dict[str, str] | None = None) -> None:
        data = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def _session_cookie_header(self, token: str, *, clear: bool = False) -> str:
        secure = load_config().secure_cookies
        parts = [f"{SESSION_COOKIE}={token if not clear else ''}", "Path=/", "HttpOnly", "SameSite=Lax"]
        if not clear:
            parts.append(f"Max-Age={SESSION_COOKIE_MAX_AGE_SECONDS}")
        if secure:
            parts.append("Secure")
        if clear:
            parts.append("Max-Age=0")
        return "; ".join(parts)

    def _cors(self) -> None:
        origin = self.headers.get("Origin")
        config = load_config()
        configured_origin = f"{config.external_scheme}://{config.external_host}" if config.external_host else None
        allowed = {"http://127.0.0.1:8790", "http://localhost:8790", "http://localhost"}
        if configured_origin:
            allowed.add(configured_origin)
        if origin in allowed:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Credentials", "true")
        else:
            self.send_header("Access-Control-Allow-Origin", configured_origin or "http://127.0.0.1:8790")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Session-Token, X-CSRF-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def log_message(self, fmt: str, *args: Any) -> None:
        if load_config().verbose_http:
            super().log_message(fmt, *args)


def run(host: str | None = None, port: int | None = None, state_path: str | None = None) -> None:
    config = load_config()
    if host is not None:
        config.host = host
    if port is not None:
        config.port = int(port)
    if state_path:
        config.state_path = Path(state_path)
    validate_startup(config)
    ShaelvienLiteHandler.store = GameStore(config.state_path)
    address = (config.host, int(config.port))
    httpd = ThreadingHTTPServer(address, ShaelvienLiteHandler)
    print(f"Shaelvien Lite serving at http://{config.host}:{config.port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Stopping Shaelvien Lite.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    run()
