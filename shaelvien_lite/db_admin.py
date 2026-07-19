"""Administrative database commands for Shaelvien Lite staging."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from .config import load_config, project_root, validate_startup
from .postgres_store import PostgresStorage
from .store import GameStore, initial_state, utc_now


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Shaelvien Lite database administration")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("migration-status", help="Show applied and pending PostgreSQL migrations.")
    sub.add_parser("migrate", help="Apply pending PostgreSQL migrations.")

    import_cmd = sub.add_parser("import-json", help="Import a local JSON store into PostgreSQL.")
    import_cmd.add_argument("--source", required=True, help="Path to local JSON state.")
    import_cmd.add_argument("--allow-existing", action="store_true", help="Allow replacing existing destination rows.")

    backup_cmd = sub.add_parser("backup", help="Create a local pg_dump backup outside the repository.")
    backup_cmd.add_argument("--output", required=True, help="Output .dump file path outside the repository.")

    args = parser.parse_args(argv)
    config = load_config()
    if config.storage_backend != "postgres":
        raise SystemExit("Set SHAELVIEN_STORAGE_BACKEND=postgres and DATABASE_URL for database commands.")
    validate_startup(config)
    store = PostgresStorage(
        config.database_url or "",
        connect_timeout_seconds=config.storage_connect_timeout_seconds,
        retry_attempts=config.storage_retry_attempts,
    )

    if args.command == "migration-status":
        return _print_json(store.migration_status())
    if args.command == "migrate":
        return _print_json(store.apply_migrations())
    if args.command == "import-json":
        return _import_json(store, Path(args.source), allow_existing=args.allow_existing)
    if args.command == "backup":
        return _backup(config.database_url or "", store, Path(args.output))
    raise SystemExit("Unknown command.")


def _import_json(store: PostgresStorage, source: Path, *, allow_existing: bool) -> int:
    state = GameStore(source).load()
    _validate_import_state(state)
    store.apply_migrations()
    existing = store.load()
    if existing.get("accounts") and not allow_existing:
        raise SystemExit("Destination database already has accounts. Re-run with --allow-existing only after Owner approval.")
    store.save(state)
    summary = {
        "imported": True,
        "source": str(source.name),
        "accounts": len(state.get("accounts", {})),
        "characters": len(state.get("characters", {})),
        "campaigns": len(state.get("campaigns", {})),
        "sessions": len(state.get("sessions", {})),
        "session_logs": len(state.get("session_logs", {})),
        "password_hashes_preserved": len([a for a in state.get("accounts", {}).values() if a.get("password_hash")]),
        "secret_values_printed": False,
    }
    return _print_json(summary)


def _validate_import_state(state: dict) -> None:
    baseline = initial_state()
    for key in ("accounts", "characters", "campaigns", "session_logs"):
        if key not in state or not isinstance(state[key], dict):
            raise SystemExit(f"JSON import failed validation: missing object '{key}'.")
    if state.get("version") != baseline["version"]:
        raise SystemExit("JSON import failed validation: unsupported state version.")


def _backup(database_url: str, store: PostgresStorage, output: Path) -> int:
    if not shutil.which("pg_dump"):
        raise SystemExit("pg_dump was not found. Install PostgreSQL client tools before running backup.")
    output = output.resolve()
    root = project_root().resolve()
    if output == root or root in output.parents:
        raise SystemExit("Backup output must be outside the Git repository.")
    output.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    _populate_pg_env(env, database_url)
    result = subprocess.run(
        ["pg_dump", "--format=custom", "--file", str(output)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit("pg_dump failed. Review local terminal stderr; do not paste secrets into reports.")
    if not output.exists() or output.stat().st_size <= 0:
        raise SystemExit("Backup failed validation: output file is empty.")
    manifest = output.with_suffix(output.suffix + ".manifest.json")
    manifest.write_text(
        json.dumps(
            {
                "created_at": utc_now(),
                "backup_file": output.name,
                "bytes": output.stat().st_size,
                "schema": store.migration_status(),
                "repository_path": False,
                "contains_credentials": False,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return _print_json({"backup_created": True, "file": str(output), "manifest": str(manifest), "bytes": output.stat().st_size})


def _populate_pg_env(env: dict[str, str], database_url: str) -> None:
    parsed = urlparse(database_url)
    env["PGHOST"] = parsed.hostname or ""
    env["PGPORT"] = str(parsed.port or 5432)
    env["PGUSER"] = parsed.username or ""
    env["PGPASSWORD"] = parsed.password or ""
    env["PGDATABASE"] = (parsed.path or "/").lstrip("/")
    env["PGSSLMODE"] = "require"


def _print_json(payload: dict) -> int:
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
