"""Runtime configuration for Shaelvien Lite."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


VALID_MODES = {"development", "testing", "staging", "production"}


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class AppConfig:
    mode: str
    host: str
    port: int
    state_path: Path
    database_url: str | None
    owner_bootstrap_token: str | None
    invite_code: str | None
    invite_required: bool
    session_secret: str | None
    csrf_secret: str | None
    external_scheme: str
    external_host: str | None
    trust_proxy_headers: bool
    secure_cookies: bool
    max_request_bytes: int
    request_timeout_seconds: int
    storage_backend: str
    storage_connect_timeout_seconds: int
    storage_retry_attempts: int
    staging_allow_json: bool
    backup_path: Path | None
    verbose_http: bool
    deployment_version: str
    run_migrations_on_startup: bool
    max_staging_accounts: int
    max_campaigns_per_account: int
    max_characters_per_account: int
    max_retained_combat_logs: int
    max_retained_ai_records: int


def _first(env: Mapping[str, str], *names: str, default: str | None = None) -> str | None:
    for name in names:
        value = env.get(name)
        if value not in (None, ""):
            return value
    return default


def load_config(environ: Mapping[str, str] | None = None) -> AppConfig:
    env = environ or os.environ
    mode = (_first(env, "SHAELVIEN_ENV", "SHAELVIEN_LITE_ENV", default="development") or "development").strip().lower()
    secure_default = mode in {"staging", "production"}
    state_default = project_root() / "data" / "shaelvien_lite_state.json"
    owner_token = _first(env, "SHAELVIEN_OWNER_BOOTSTRAP_TOKEN", "SHAELVIEN_LITE_OWNER_BOOTSTRAP_TOKEN", "SHAELVIEN_LITE_OWNER_CODE")
    backup = _first(env, "SHAELVIEN_BACKUP_PATH", "SHAELVIEN_LITE_BACKUP_PATH")
    storage_backend = (_first(env, "SHAELVIEN_STORAGE_BACKEND", "SHAELVIEN_LITE_STORAGE_BACKEND", default="json") or "json").strip().lower()
    return AppConfig(
        mode=mode,
        host=_first(env, "SHAELVIEN_HOST", "SHAELVIEN_LITE_HOST", default="127.0.0.1") or "127.0.0.1",
        port=int(_first(env, "PORT", "SHAELVIEN_PORT", "SHAELVIEN_LITE_PORT", default="8790") or "8790"),
        state_path=Path(_first(env, "SHAELVIEN_STATE", "SHAELVIEN_LITE_STATE", default=str(state_default)) or str(state_default)),
        database_url=_first(env, "DATABASE_URL", "SHAELVIEN_DATABASE_URL", "SHAELVIEN_LITE_DATABASE_URL"),
        owner_bootstrap_token=owner_token,
        invite_code=_first(env, "SHAELVIEN_INVITE_CODE", "SHAELVIEN_LITE_INVITE_CODE"),
        invite_required=parse_bool(_first(env, "SHAELVIEN_INVITE_REQUIRED", "SHAELVIEN_LITE_INVITE_REQUIRED"), secure_default),
        session_secret=_first(env, "SHAELVIEN_SESSION_SECRET", "SHAELVIEN_LITE_SESSION_SECRET"),
        csrf_secret=_first(env, "SHAELVIEN_CSRF_SECRET", "SHAELVIEN_LITE_CSRF_SECRET"),
        external_scheme=(_first(env, "SHAELVIEN_EXTERNAL_SCHEME", "SHAELVIEN_LITE_EXTERNAL_SCHEME", default="https" if secure_default else "http") or "http").strip().lower(),
        external_host=_first(env, "SHAELVIEN_EXTERNAL_HOST", "SHAELVIEN_LITE_EXTERNAL_HOST"),
        trust_proxy_headers=parse_bool(_first(env, "SHAELVIEN_TRUST_PROXY_HEADERS", "SHAELVIEN_LITE_TRUST_PROXY_HEADERS"), False),
        secure_cookies=parse_bool(_first(env, "SHAELVIEN_SECURE_COOKIES", "SHAELVIEN_LITE_SECURE_COOKIES"), secure_default),
        max_request_bytes=int(_first(env, "SHAELVIEN_MAX_REQUEST_BYTES", "SHAELVIEN_LITE_MAX_REQUEST_BYTES", default="128000") or "128000"),
        request_timeout_seconds=int(_first(env, "SHAELVIEN_REQUEST_TIMEOUT_SECONDS", "SHAELVIEN_LITE_REQUEST_TIMEOUT_SECONDS", default="30") or "30"),
        storage_backend=storage_backend,
        storage_connect_timeout_seconds=int(_first(env, "SHAELVIEN_STORAGE_CONNECT_TIMEOUT_SECONDS", "SHAELVIEN_LITE_STORAGE_CONNECT_TIMEOUT_SECONDS", default="5") or "5"),
        storage_retry_attempts=int(_first(env, "SHAELVIEN_STORAGE_RETRY_ATTEMPTS", "SHAELVIEN_LITE_STORAGE_RETRY_ATTEMPTS", default="2") or "2"),
        staging_allow_json=parse_bool(_first(env, "SHAELVIEN_STAGING_ALLOW_JSON", "SHAELVIEN_LITE_STAGING_ALLOW_JSON"), False),
        backup_path=Path(backup) if backup else None,
        verbose_http=parse_bool(_first(env, "SHAELVIEN_VERBOSE_HTTP", "SHAELVIEN_LITE_VERBOSE_HTTP"), False),
        deployment_version=_first(env, "SHAELVIEN_DEPLOYMENT_VERSION", "SHAELVIEN_LITE_DEPLOYMENT_VERSION", default="local") or "local",
        run_migrations_on_startup=parse_bool(_first(env, "SHAELVIEN_RUN_MIGRATIONS_ON_STARTUP", "SHAELVIEN_LITE_RUN_MIGRATIONS_ON_STARTUP"), False),
        max_staging_accounts=int(_first(env, "SHAELVIEN_MAX_STAGING_ACCOUNTS", "SHAELVIEN_LITE_MAX_STAGING_ACCOUNTS", default="25") or "25"),
        max_campaigns_per_account=int(_first(env, "SHAELVIEN_MAX_CAMPAIGNS_PER_ACCOUNT", "SHAELVIEN_LITE_MAX_CAMPAIGNS_PER_ACCOUNT", default="2") or "2"),
        max_characters_per_account=int(_first(env, "SHAELVIEN_MAX_CHARACTERS_PER_ACCOUNT", "SHAELVIEN_LITE_MAX_CHARACTERS_PER_ACCOUNT", default="4") or "4"),
        max_retained_combat_logs=int(_first(env, "SHAELVIEN_MAX_RETAINED_COMBAT_LOGS", "SHAELVIEN_LITE_MAX_RETAINED_COMBAT_LOGS", default="500") or "500"),
        max_retained_ai_records=int(_first(env, "SHAELVIEN_MAX_RETAINED_AI_RECORDS", "SHAELVIEN_LITE_MAX_RETAINED_AI_RECORDS", default="200") or "200"),
    )


def validate_startup(config: AppConfig) -> None:
    errors: list[str] = []
    if config.mode not in VALID_MODES:
        errors.append(f"Invalid SHAELVIEN_LITE_ENV '{config.mode}'. Expected one of: {', '.join(sorted(VALID_MODES))}.")
    if config.max_request_bytes < 1024:
        errors.append("SHAELVIEN_LITE_MAX_REQUEST_BYTES must be at least 1024.")
    if config.request_timeout_seconds < 1:
        errors.append("SHAELVIEN_LITE_REQUEST_TIMEOUT_SECONDS must be at least 1.")
    if config.storage_connect_timeout_seconds < 1:
        errors.append("SHAELVIEN_STORAGE_CONNECT_TIMEOUT_SECONDS must be at least 1.")
    if config.storage_retry_attempts < 0:
        errors.append("SHAELVIEN_STORAGE_RETRY_ATTEMPTS cannot be negative.")
    if config.mode in {"staging", "production"}:
        if not config.secure_cookies:
            errors.append("Secure cookies are required in staging and production.")
        if config.external_scheme != "https":
            errors.append("SHAELVIEN_LITE_EXTERNAL_SCHEME must be https in staging and production.")
        if not config.external_host:
            errors.append("SHAELVIEN_LITE_EXTERNAL_HOST is required in staging and production.")
        if not config.owner_bootstrap_token:
            errors.append("SHAELVIEN_LITE_OWNER_BOOTSTRAP_TOKEN is required in staging and production.")
        if config.invite_required and not config.invite_code:
            errors.append("SHAELVIEN_INVITE_CODE is required when invite-gated staging registration is enabled.")
        if not config.session_secret:
            errors.append("SHAELVIEN_SESSION_SECRET is required in staging and production.")
        if not config.csrf_secret:
            errors.append("SHAELVIEN_CSRF_SECRET is required in staging and production.")
        if config.mode == "staging" and config.storage_backend != "postgres":
            errors.append("Hosted staging must use SHAELVIEN_STORAGE_BACKEND=postgres.")
        if config.storage_backend == "json" and config.mode == "staging":
            if not config.staging_allow_json:
                errors.append("Staging JSON storage requires SHAELVIEN_LITE_STAGING_ALLOW_JSON=1.")
            if not config.backup_path:
                errors.append("Staging JSON storage requires SHAELVIEN_LITE_BACKUP_PATH.")
    if config.storage_backend == "postgres" and not config.database_url:
        errors.append("DATABASE_URL is required when SHAELVIEN_STORAGE_BACKEND=postgres.")
    if config.storage_backend == "postgres" and config.database_url and "sslmode=require" not in config.database_url.lower():
        errors.append("DATABASE_URL must require SSL with sslmode=require.")
    if config.storage_backend not in {"json", "postgres"}:
        errors.append("SHAELVIEN_STORAGE_BACKEND must be json or postgres.")
    if errors:
        raise RuntimeError("Shaelvien Lite startup configuration failed: " + " ".join(errors))
