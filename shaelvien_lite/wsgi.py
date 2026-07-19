"""WSGI entrypoint for Koyeb/Gunicorn staging deployments."""

from __future__ import annotations

import json
import mimetypes
import time
from collections import defaultdict, deque
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

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
from .store import StorageUnavailable, create_store, utc_now


STATIC_ROOT = Path(__file__).parent / "static"
SESSION_COOKIE = "shaelvien_lite_session"
SESSION_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 30
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_ACTIONS = 30
AUTH_RATE_LIMIT_MAX = 10
RATE_BUCKETS: dict[str, deque[float]] = defaultdict(deque)


class ShaelvienLiteWSGIApp:
    def __init__(self):
        self.config = load_config()
        validate_startup(self.config)
        self.store = create_store(self.config)
        if self.config.run_migrations_on_startup and hasattr(self.store, "apply_migrations"):
            self.store.apply_migrations()
        self.store.ready()

    def __call__(self, environ: dict[str, Any], start_response):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/") or "/"
        query = parse_qs(environ.get("QUERY_STRING", ""))
        try:
            if method == "OPTIONS":
                return self._respond(start_response, 204, b"", [("Content-Type", "text/plain")], environ)
            if method == "GET":
                if path == "/health":
                    return self._json(start_response, {"status": "ok"}, environ=environ)
                if path == "/ready":
                    self.store.ready()
                    return self._json(
                        start_response,
                        {
                            "status": "ready",
                            "version": "0.1",
                            "mode": self.config.mode,
                            "storage": "available",
                            "storage_backend": self.config.storage_backend,
                            "deployment_version": self.config.deployment_version,
                            "last_storage_connection_at": getattr(self.store, "last_successful_connection_at", None),
                        },
                        environ=environ,
                    )
                if path.startswith("/api/"):
                    return self._get_api(start_response, environ, path, query)
                return self._static(start_response, environ, path)
            if method == "POST":
                if not path.startswith("/api/"):
                    raise GameError("Unknown route.", 404)
                return self._post_api(start_response, environ, path, self._read_json(environ))
            raise GameError("Unsupported method.", 405)
        except GameError as exc:
            self._record_validation_failure(path, exc)
            return self._json(start_response, {"error": str(exc)}, status=exc.status, environ=environ)
        except StorageUnavailable as exc:
            return self._json(start_response, {"error": str(exc)}, status=503, environ=environ)
        except Exception:
            return self._json(start_response, {"error": "Internal server error."}, status=500, environ=environ)

    def _get_api(self, start_response, environ: dict[str, Any], path: str, query: dict[str, list[str]]):
        if path == "/api/bootstrap":
            token = _client_token(environ)

            def op(state: dict[str, Any]) -> dict[str, Any]:
                account = require_session(state, token) if token else None
                data = summarize_state(state, account)
                if token and token in state["sessions"]:
                    data["csrf_token"] = state["sessions"][token].get("csrf_token")
                return data

            return self._json(start_response, self.store.update(op), environ=environ)
        if path == "/api/session-log":
            token = _client_token(environ)
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

            return self._json(start_response, self.store.update(op), environ=environ)
        if path == "/api/admin":
            token = _client_token(environ)

            def op(state: dict[str, Any]) -> dict[str, Any]:
                account = require_session(state, token)
                snapshot = admin_snapshot(state, account)
                snapshot["runtime"] = {
                    "deployment_version": self.config.deployment_version,
                    "mode": self.config.mode,
                    "storage_backend": self.config.storage_backend,
                    "last_storage_connection_at": getattr(self.store, "last_successful_connection_at", None),
                    "storage_failure_count": getattr(self.store, "connection_failure_count", 0),
                }
                return snapshot

            return self._json(start_response, self.store.update(op), environ=environ)
        raise GameError("Unknown API route.", 404)

    def _post_api(self, start_response, environ: dict[str, Any], path: str, payload: dict[str, Any]):
        if path == "/api/account/enter":
            _check_rate(environ, "auth", AUTH_RATE_LIMIT_MAX)

            def op(state: dict[str, Any]) -> dict[str, Any]:
                result = create_or_enter_account(
                    state,
                    str(payload.get("handle", "")),
                    password=str(payload.get("password", "")),
                    owner_bootstrap_token=str(payload.get("owner_bootstrap_token", "")) or None,
                    configured_owner_token=self.config.owner_bootstrap_token,
                    invite_code=str(payload.get("invite_code", "")) or None,
                    configured_invite_code=self.config.invite_code,
                    invite_required=self.config.invite_required,
                    max_accounts=self.config.max_staging_accounts if self.config.mode == "staging" else None,
                    env_mode=self.config.mode,
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
            return self._json(
                start_response,
                result,
                headers=[("Set-Cookie", _session_cookie_header(token, self.config.secure_cookies))],
                environ=environ,
            )
        if path == "/api/account/logout":
            token = _client_token(environ)
            csrf = _client_csrf(environ)

            def op(state: dict[str, Any]) -> dict[str, Any]:
                require_csrf(state, token, csrf)
                invalidate_session(state, token)
                return {"ok": True}

            return self._json(
                start_response,
                self.store.update(op),
                headers=[("Set-Cookie", _session_cookie_header("", self.config.secure_cookies, clear=True))],
                environ=environ,
            )
        if path == "/api/characters":
            token = _client_token(environ)
            csrf = _client_csrf(environ)

            def op(state: dict[str, Any]) -> dict[str, Any]:
                require_csrf(state, token, csrf)
                account = require_session(state, token)
                return {
                    "character": create_character(
                        state,
                        account,
                        str(payload.get("name", "")),
                        str(payload.get("role_id", "")),
                        ancestry=str(payload.get("ancestry", "")).strip() or None,
                    )
                }

            return self._json(start_response, self.store.update(op), status=201, environ=environ)
        if path == "/api/campaigns/tutorial/start":
            token = _client_token(environ)
            csrf = _client_csrf(environ)

            def op(state: dict[str, Any]) -> dict[str, Any]:
                require_csrf(state, token, csrf)
                account = require_session(state, token)
                return {"campaign": start_tutorial_campaign(state, account, str(payload.get("character_id", "")))}

            return self._json(start_response, self.store.update(op), status=201, environ=environ)
        if path == "/api/game/action":
            _check_rate(environ, "game_action", RATE_LIMIT_MAX_ACTIONS)
            token = _client_token(environ)
            csrf = _client_csrf(environ)

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

            return self._json(start_response, self.store.update(op), environ=environ)
        return self._post_admin_api(start_response, environ, path, payload)

    def _post_admin_api(self, start_response, environ: dict[str, Any], path: str, payload: dict[str, Any]):
        token = _client_token(environ)
        csrf = _client_csrf(environ)

        if path == "/api/admin/reset-campaign":
            def op(state: dict[str, Any]) -> dict[str, Any]:
                require_csrf(state, token, csrf)
                account = require_session(state, token)
                return reset_development_campaign(state, account, str(payload.get("campaign_id", "")))

            return self._json(start_response, self.store.update(op), environ=environ)
        if path == "/api/admin/grant-item":
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

            return self._json(start_response, self.store.update(op), environ=environ)
        if path == "/api/admin/camp-level":
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

            return self._json(start_response, self.store.update(op), environ=environ)
        if path == "/api/admin/settings":
            def op(state: dict[str, Any]) -> dict[str, Any]:
                require_csrf(state, token, csrf)
                account = require_session(state, token)
                if "ai_enabled" in payload:
                    ai_toggle(state, account, bool(payload["ai_enabled"]))
                if "maintenance_mode" in payload:
                    maintenance_toggle(state, account, bool(payload["maintenance_mode"]))
                return {"settings": state["settings"]}

            return self._json(start_response, self.store.update(op), environ=environ)
        raise GameError("Unknown API route.", 404)

    def _read_json(self, environ: dict[str, Any]) -> dict[str, Any]:
        length = int(environ.get("CONTENT_LENGTH") or "0")
        if length <= 0:
            return {}
        if length > self.config.max_request_bytes:
            raise GameError("Request body too large.", 413)
        raw = environ["wsgi.input"].read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise GameError(f"Invalid JSON: {exc.msg}") from exc
        if not isinstance(payload, dict):
            raise GameError("JSON body must be an object.")
        return payload

    def _static(self, start_response, environ: dict[str, Any], request_path: str):
        relative = "index.html" if request_path in ("", "/") else request_path.lstrip("/")
        target = (STATIC_ROOT / relative).resolve()
        if STATIC_ROOT.resolve() not in target.parents and target != STATIC_ROOT.resolve():
            raise GameError("Invalid path.", 400)
        if not target.exists() or not target.is_file():
            target = STATIC_ROOT / "index.html"
        data = target.read_bytes()
        headers = [
            ("Content-Type", mimetypes.guess_type(str(target))[0] or "application/octet-stream"),
            ("Cache-Control", "no-store" if target.name == "index.html" else "public, max-age=3600"),
        ]
        return self._respond(start_response, 200, data, headers, environ)

    def _json(
        self,
        start_response,
        payload: dict[str, Any],
        *,
        status: int = 200,
        headers: list[tuple[str, str]] | None = None,
        environ: dict[str, Any],
    ):
        data = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        return self._respond(start_response, status, data, [("Content-Type", "application/json; charset=utf-8")] + (headers or []), environ)

    def _respond(self, start_response, status: int, data: bytes, headers: list[tuple[str, str]], environ: dict[str, Any]):
        response_headers = list(headers)
        response_headers.extend(_cors_headers(environ, self.config))
        response_headers.append(("Content-Length", str(len(data))))
        response_headers.append(("Cache-Control", "no-store"))
        start_response(f"{status} {_reason(status)}", response_headers)
        return [data]

    def _record_validation_failure(self, route: str, exc: GameError) -> None:
        def op(state: dict[str, Any]) -> None:
            state.setdefault("validation_failures", []).append(
                {"at": utc_now(), "route": route, "status": exc.status, "message": str(exc)}
            )
            state["validation_failures"] = state["validation_failures"][-200:]

        try:
            self.store.update(op)
        except Exception:
            pass


def _client_token(environ: dict[str, Any]) -> str | None:
    cookie_token = _cookie_value(environ, SESSION_COOKIE)
    if cookie_token:
        return cookie_token
    auth = environ.get("HTTP_AUTHORIZATION", "")
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return environ.get("HTTP_X_SESSION_TOKEN")


def _client_csrf(environ: dict[str, Any]) -> str | None:
    return environ.get("HTTP_X_CSRF_TOKEN")


def _cookie_value(environ: dict[str, Any], name: str) -> str | None:
    raw = environ.get("HTTP_COOKIE")
    if not raw:
        return None
    cookie = SimpleCookie()
    try:
        cookie.load(raw)
    except Exception:
        return None
    morsel = cookie.get(name)
    return morsel.value if morsel else None


def _check_rate(environ: dict[str, Any], bucket_name: str, limit: int) -> None:
    remote = environ.get("REMOTE_ADDR", "local")
    token = _client_token(environ) or remote
    key = f"{bucket_name}:{token}"
    now = time.monotonic()
    bucket = RATE_BUCKETS[key]
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW:
        bucket.popleft()
    if len(bucket) >= limit:
        raise GameError("Too many actions. Wait a moment before sending another.", 429)
    bucket.append(now)


def _session_cookie_header(token: str, secure: bool, *, clear: bool = False) -> str:
    parts = [f"{SESSION_COOKIE}={token if not clear else ''}", "Path=/", "HttpOnly", "SameSite=Lax"]
    if not clear:
        parts.append(f"Max-Age={SESSION_COOKIE_MAX_AGE_SECONDS}")
    if secure:
        parts.append("Secure")
    if clear:
        parts.append("Max-Age=0")
    return "; ".join(parts)


def _cors_headers(environ: dict[str, Any], config) -> list[tuple[str, str]]:
    origin = environ.get("HTTP_ORIGIN")
    configured_origin = f"{config.external_scheme}://{config.external_host}" if config.external_host else None
    allowed = {"http://127.0.0.1:8790", "http://localhost:8790", "http://localhost"}
    if configured_origin:
        allowed.add(configured_origin)
    headers: list[tuple[str, str]] = []
    if origin in allowed:
        headers.append(("Access-Control-Allow-Origin", origin))
        headers.append(("Access-Control-Allow-Credentials", "true"))
    else:
        headers.append(("Access-Control-Allow-Origin", configured_origin or "http://127.0.0.1:8790"))
    headers.append(("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Session-Token, X-CSRF-Token"))
    headers.append(("Access-Control-Allow-Methods", "GET, POST, OPTIONS"))
    return headers


def _reason(status: int) -> str:
    return {
        200: "OK",
        201: "Created",
        204: "No Content",
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        413: "Payload Too Large",
        429: "Too Many Requests",
        500: "Internal Server Error",
        503: "Service Unavailable",
    }.get(status, "OK")


app = ShaelvienLiteWSGIApp()
