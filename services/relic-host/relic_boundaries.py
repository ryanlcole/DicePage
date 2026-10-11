"""ReLiC knowledge and telemetry boundary policy.

ReLiC Universal may contain only sanitized, reusable engineering knowledge.
ReLiC Projects contains project-scoped continuity and is isolated by owner and
project. Environment observations belong to the project boundary by default.
Nothing in this module grants execution or mutation authority.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

SCHEMA = "RELIC-BOUNDARIES/1"

UNIVERSAL = "UNIVERSAL"
PROJECT = "PROJECT"
ENVIRONMENT = "ENVIRONMENT"

# Conservative keys. Values are removed before any project/environment record
# can be generalized into Universal knowledge.
SENSITIVE_KEY = re.compile(
    r"(?i)(password|passwd|secret|token|api[_-]?key|authorization|cookie|session|"
    r"email|phone|address|username|user_name|hostname|machine_name|ip_address|"
    r"environment|env|command_line|argv|private_path|home_path|credential)"
)

WINDOWS_USER_PATH = re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s]+")
POSIX_HOME_PATH = re.compile(r"/(?:home|Users)/[^/\s]+")
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")


class BoundaryViolation(ValueError):
    pass


def stable_project_key(owner_id: str, project_id: str) -> str:
    """Opaque routing key; raw owner identity need not be exposed in records."""
    return hashlib.sha256(f"{owner_id}\0{project_id}".encode()).hexdigest()


def _redact_text(value: str) -> str:
    value = EMAIL.sub("[REDACTED_EMAIL]", value)
    value = BEARER.sub("[REDACTED_AUTH]", value)
    value = WINDOWS_USER_PATH.sub("[REDACTED_USER_PATH]", value)
    value = POSIX_HOME_PATH.sub("[REDACTED_USER_PATH]", value)
    value = IPV4.sub("[REDACTED_IP]", value)
    return value


def sanitize_for_universal(value: Any) -> Any:
    """Remove obvious PII/security/environment identifiers recursively.

    Sanitization is a promotion gate, not proof that content is safe. Promotion
    still requires explicit review/approval before Universal storage.
    """
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            if SENSITIVE_KEY.search(str(key)):
                clean[str(key)] = "[REDACTED]"
            else:
                clean[str(key)] = sanitize_for_universal(item)
        return clean
    if isinstance(value, list):
        return [sanitize_for_universal(item) for item in value]
    if isinstance(value, str):
        return _redact_text(value)
    return value


def contains_obvious_sensitive_data(value: Any) -> bool:
    return sanitize_for_universal(value) != value


@dataclass(frozen=True)
class ProjectScope:
    owner_id: str
    project_id: str

    @property
    def key(self) -> str:
        return stable_project_key(self.owner_id, self.project_id)


def assert_same_project(requested: ProjectScope, stored_project_key: str) -> None:
    if requested.key != stored_project_key:
        raise BoundaryViolation("project isolation boundary denied")


def classify_environment_observation(observation: dict[str, Any]) -> dict[str, Any]:
    """Normalize advisory telemetry without claiming causation or hardware harm."""
    return {
        "schema": SCHEMA,
        "domain": ENVIRONMENT,
        "authority": "ADVISORY_ONLY",
        "hardware_harm_established": False,
        "causation_established": False,
        "observation": observation,
    }


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
