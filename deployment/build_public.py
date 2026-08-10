from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DIST = REPO_ROOT / "dist"
TACTICAL = REPO_ROOT / "apps" / "tactical"
SITE = REPO_ROOT / "site"


def run_git(args: list[str], fallback: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return fallback


def safe_rmtree(path: Path) -> None:
    resolved = path.resolve()
    root = REPO_ROOT.resolve()
    if resolved == root or root not in resolved.parents:
        raise RuntimeError(f"Refusing to remove path outside repository: {resolved}")
    if path.exists():
        shutil.rmtree(path)


def copy_tree(src: Path, dst: Path, ignore: shutil.IgnorePattern | None = None) -> None:
    if not src.exists():
        raise FileNotFoundError(src)
    shutil.copytree(src, dst, ignore=ignore)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sanitize_public_atlas(app_dst: Path) -> None:
    atlas_source = app_dst / "assets" / "atlas" / "source"
    atlas_manifest = app_dst / "data" / "atlas" / "atlas_source_manifest.json"
    atlas_detections = app_dst / "data" / "atlas" / "detections"
    for path in (atlas_source, atlas_detections):
        safe_rmtree(path)
    if atlas_manifest.exists():
        atlas_manifest.unlink()

    registry_path = app_dst / "data" / "atlas" / "atlas_asset_registry.json"
    if not registry_path.exists():
        return
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    public_assets = []
    for asset in registry.get("assets", []):
        public_asset = dict(asset)
        public_asset.pop("sourceImage", None)
        public_assets.append(public_asset)
    public_registry = {
        "schemaVersion": registry.get("schemaVersion", "shaelvien.atlas_asset_registry.v1"),
        "generatedAt": registry.get("generatedAt", ""),
        "sourceAuthority": registry.get("sourceAuthority", "google_drive"),
        "syncPolicy": registry.get("syncPolicy", {}),
        "layerOrder": registry.get("layerOrder", {}),
        "publicRuntimeRegistry": True,
        "sourceCacheIncluded": False,
        "sources": [],
        "assets": public_assets,
    }
    write_json(registry_path, public_registry)


def main() -> int:
    if not TACTICAL.exists():
        raise FileNotFoundError(f"Missing tactical source: {TACTICAL}")

    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    commit = run_git(["rev-parse", "HEAD"], "unknown")
    short_commit = commit[:8] if commit != "unknown" else "unknown"
    tactical_package = json.loads((TACTICAL / "package.json").read_text(encoding="utf-8"))
    build_id = f"live-alpha-0-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{short_commit}"

    safe_rmtree(DIST)
    DIST.mkdir(parents=True, exist_ok=True)

    shutil.copy2(SITE / "landing" / "index.html", DIST / "index.html")
    shutil.copy2(SITE / "site-shell.css", DIST / "site-shell.css")
    for route in ("store", "docs", "lab"):
        copy_tree(SITE / route, DIST / route)

    app_dst = DIST / "app"
    app_dst.mkdir(parents=True, exist_ok=True)
    for item in ("index.html", "styles.css"):
        shutil.copy2(TACTICAL / item, app_dst / item)
    for folder in ("assets", "data", "docs", "js"):
        copy_tree(
            TACTICAL / folder,
            app_dst / folder,
            ignore=shutil.ignore_patterns(
                "__pycache__",
                "dev_studio_snapshot.json",
                "*.pyc",
                "*.pyo",
                "*.log",
                ".env",
                ".env.*",
                "*.sqlite",
                "*.db",
                "*.zip",
                "*.tar",
                "*.7z",
                "*.bak",
                "*.pfx",
                "*.pem",
                "*.key",
            ),
        )
    sanitize_public_atlas(app_dst)

    build_info = {
        "applicationVersion": tactical_package.get("version", "0.0.0"),
        "buildId": build_id,
        "gitCommit": commit,
        "buildTimestamp": timestamp,
        "deploymentEnvironment": os.environ.get("RELIC_DEPLOYMENT_ENVIRONMENT", "repository-predeploy"),
        "protocolVersion": "shaelvien-tactical-web-0",
        "campaignSchemaVersion": "first-preset-campaign-1",
    }
    write_json(DIST / "build-info.json", build_info)
    print(json.dumps({"dist": str(DIST), "buildInfo": build_info}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
