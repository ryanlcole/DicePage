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
    owner_bootstrap_token: str | None
    external_scheme: str
    external_host: str | None
    trust_proxy_headers: bool
    secure_cookies: bool
    max_request_bytes: int
    request_timeout_seconds: int
    storage_backend: str
    staging_allow_json: bool
    backup_path: Path | None
    verbose_http: bool


def load_config(environ: Mapping[str, str] | None = None) -> AppConfig:
    env = environ or os.environ
    mode = env.get("SHAELVIEN_LITE_ENV", "development").strip().lower()
    secure_default = mode in {"staging", "production"}
    state_default = project_root() / "data" / "shaelvien_lite_state.json"
    owner_token = env.get("SHAELVIEN_LITE_OWNER_BOOTSTRAP_TOKEN") or env.get("SHAELVIEN_LITE_OWNER_CODE")
    backup = env.get("SHAELVIEN_LITE_BACKUP_PATH")
    return AppConfig(
        mode=mode,
        host=env.get("SHAELVIEN_LITE_HOST", "127.0.0.1"),
        port=int(env.get("SHAELVIEN_LITE_PORT", "8790")),
        state_path=Path(env.get("SHAELVIEN_LITE_STATE", str(state_default))),
        owner_bootstrap_token=owner_token,
        external_scheme=env.get("SHAELVIEN_LITE_EXTERNAL_SCHEME", "https" if secure_default else "http").strip().lower(),
        external_host=env.get("SHAELVIEN_LITE_EXTERNAL_HOST"),
        trust_proxy_headers=parse_bool(env.get("SHAELVIEN_LITE_TRUST_PROXY_HEADERS"), False),
        secure_cookies=parse_bool(env.get("SHAELVIEN_LITE_SECURE_COOKIES"), secure_default),
        max_request_bytes=int(env.get("SHAELVIEN_LITE_MAX_REQUEST_BYTES", "128000")),
        request_timeout_seconds=int(env.get("SHAELVIEN_LITE_REQUEST_TIMEOUT_SECONDS", "30")),
        storage_backend=env.get("SHAELVIEN_LITE_STORAGE_BACKEND", "json").strip().lower(),
        staging_allow_json=parse_bool(env.get("SHAELVIEN_LITE_STAGING_ALLOW_JSON"), False),
        backup_path=Path(backup) if backup else None,
        verbose_http=parse_bool(env.get("SHAELVIEN_LITE_VERBOSE_HTTP"), False),
    )


def validate_startup(config: AppConfig) -> None:
    errors: list[str] = []
    if config.mode not in VALID_MODES:
        errors.append(f"Invalid SHAELVIEN_LITE_ENV '{config.mode}'. Expected one of: {', '.join(sorted(VALID_MODES))}.")
    if config.max_request_bytes < 1024:
        errors.append("SHAELVIEN_LITE_MAX_REQUEST_BYTES must be at least 1024.")
    if config.request_timeout_seconds < 1:
        errors.append("SHAELVIEN_LITE_REQUEST_TIMEOUT_SECONDS must be at least 1.")
    if config.mode in {"staging", "production"}:
        if not config.secure_cookies:
            errors.append("Secure cookies are required in staging and production.")
        if config.external_scheme != "https":
            errors.append("SHAELVIEN_LITE_EXTERNAL_SCHEME must be https in staging and production.")
        if not config.external_host:
            errors.append("SHAELVIEN_LITE_EXTERNAL_HOST is required in staging and production.")
        if not config.owner_bootstrap_token:
            errors.append("SHAELVIEN_LITE_OWNER_BOOTSTRAP_TOKEN is required in staging and production.")
        if config.storage_backend == "json" and config.mode == "staging":
            if not config.staging_allow_json:
                errors.append("Staging JSON storage requires SHAELVIEN_LITE_STAGING_ALLOW_JSON=1.")
            if not config.backup_path:
                errors.append("Staging JSON storage requires SHAELVIEN_LITE_BACKUP_PATH.")
        if config.mode == "production":
            errors.append("Production startup is blocked until a production database backend is implemented and configured.")
    if config.storage_backend != "json":
        errors.append("Only SHAELVIEN_LITE_STORAGE_BACKEND=json is implemented in this baseline.")
    if errors:
        raise RuntimeError("Shaelvien Lite startup configuration failed: " + " ".join(errors))
