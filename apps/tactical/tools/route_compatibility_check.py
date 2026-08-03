"""Route compatibility check for SHAELVIEN-TACTICAL-WEB-0.

The protected Mobile DevUI token is read locally and sent as a header only.
The report records status codes and byte counts, never response bodies or token
values.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(r"C:\Shaelvien")
SESSION_PATH = ROOT / "verify_reports" / "mobile_devui_session.json"
REPORT_DIR = ROOT / "verify_reports" / "shaelvien_tactical_editor_1"

MOBILE_DEVUI_BASE = "http://127.0.0.1:8765"
STATIC_BASE = "http://127.0.0.1:8780"

EXISTING_GET_ROUTES = [
    "/",
    "/classic",
    "/workspace/world",
    "/api/status",
    "/project-mind",
    "/download/project-mind-iphone-snapshot",
    "/project-mind-panel",
    "/api/project-mind-panel.json",
    "/bounded-phase-planner",
    "/api/bounded-phase-planner.json",
    "/nhc-organization",
    "/api/nhc-organization.json",
    "/nhc-hq",
    "/api/nhc-hq.json",
    "/nhc-build",
    "/api/nhc-build.json",
    "/shaelvien-hi",
    "/tavern-pixel-lab",
    "/api/shaelvien-hi.json",
    "/surface/world",
    "/api/d6-manifest",
    "/api/search?q=shaelvien",
    "/api/relic-search?q=shaelvien",
    "/api/chat",
    "/api/command-log",
    "/api/owner-admin/pending-requests",
    "/api/world-face/latest",
    "/api/reports-verify/latest",
    "/api/project-mind/level01/latest",
    "/api/atomic-pixel/status",
    "/api/tavern-remote/status",
    "/api/atomic-pixel/frame",
    "/api/tavern-pixel-lab/state",
    "/api/square-face-doctrine",
]

EXISTING_POST_ROUTES_RECORDED_NOT_MUTATED = [
    "/api/sql",
    "/api/action",
    "/api/nhc-organization/action",
    "/api/shaelvien-hi/action",
    "/api/operator-control",
    "/api/owner-admin/approve",
    "/api/owner-admin/decision",
    "/api/chat",
    "/api/navigation",
    "/api/atomic-pixel/lines",
    "/api/atomic-pixel/scene",
    "/api/atomic-pixel/tavern-beta",
    "/api/atomic-pixel/tavern-input",
    "/api/tavern-pixel-lab/patch",
    "/api/atomic-pixel/interaction",
    "/api/world-face/command",
    "/api/command",
    "/api/run-governor",
]

REPLACEMENT_ROUTES_USED = [
    "/",
    "/?acceptance=1",
    "/styles.css?v=shaelvien-tactical-editor-1",
    "/js/app.js?v=shaelvien-tactical-editor-1",
    "/js/state.js",
    "/js/maps.js",
    "/js/grid.js",
    "/js/actions.js",
    "/js/triggers.js",
    "/js/encounter.js",
    "/js/commander.js",
    "/js/replay.js",
    "/js/editor.js",
    "/js/input.js",
    "/js/api.js",
    "/js/assets.js",
    "/data/tile_manifest.json",
    "/data/assets/tile_asset_registry.json",
    "/data/maps/world.json",
    "/data/maps/city.json",
    "/data/maps/block.json",
    "/data/maps/tavern_exterior.json",
    "/data/maps/tavern_main_floor.json",
    "/data/maps/tavern_encounter.json",
    "/data/encounters/tavern_ambush.json",
    "/data/characters/players.json",
    "/data/creatures/monsters.json",
    "/assets/tiles/placeholder_tiles.json",
    "/assets/tiles/stone_floor_001.png",
    "/assets/tiles/tavern_table_001.png",
    "/assets/tiles/rune_trigger_001.png",
    "/assets/sprites/placeholder_sprites.json",
    "/assets/backgrounds/tavern_background.json",
    "/assets/ui/ui_tokens.json",
]


def load_token() -> str:
    payload = json.loads(SESSION_PATH.read_text(encoding="utf-8"))
    token = str(payload.get("token", ""))
    if not token:
        raise RuntimeError("Mobile DevUI session token is missing")
    return token


def request_status(url: str, token: str | None = None) -> dict:
    headers = {}
    if token:
        headers["X-Shaelvien-Token"] = token
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            content_length = response.headers.get("Content-Length")
            return {
                "status": response.status,
                "contentType": response.headers.get("Content-Type", ""),
                "bytes": int(content_length) if content_length and content_length.isdigit() else None,
            }
    except urllib.error.HTTPError as error:
        error.read()
        return {"status": error.code, "contentType": error.headers.get("Content-Type", ""), "bytes": 0}
    except Exception as exc:
        return {"status": None, "error": exc.__class__.__name__}


def main() -> int:
    token = load_token()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    existing = [
        {"route": route, **request_status(MOBILE_DEVUI_BASE + route, token=token)}
        for route in EXISTING_GET_ROUTES
    ]
    unauthenticated = [
        {"route": route, **request_status(MOBILE_DEVUI_BASE + route)}
        for route in ["/", "/api/status"]
    ]
    replacement = [
        {"route": route, **request_status(STATIC_BASE + route)}
        for route in REPLACEMENT_ROUTES_USED
    ]
    report = {
        "schemaVersion": "shaelvien.route_compatibility.v1",
        "activeFrontendEntrypoint": str(ROOT / "dev_studio_alpha" / "index.html"),
        "preservedProtectedServer": str(ROOT / "modules" / "mobile_devui_server.py"),
        "existingGetRoutes": existing,
        "existingPostRoutesRecordedNotMutated": EXISTING_POST_ROUTES_RECORDED_NOT_MUTATED,
        "replacementRoutesUsed": replacement,
        "unauthenticatedPermissionChecks": unauthenticated,
        "tokenValueRecorded": False,
    }
    report["existingRoutesStillRespond"] = all(item["status"] is not None and item["status"] != 404 for item in existing)
    report["replacementRoutesRespond"] = all(item["status"] == 200 for item in replacement)
    report["permissionsRemainEnforced"] = all(item["status"] == 403 for item in unauthenticated)
    report["pass"] = report["existingRoutesStillRespond"] and report["replacementRoutesRespond"] and report["permissionsRemainEnforced"]
    path = REPORT_DIR / "route_compatibility_report.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(path), "pass": report["pass"]}, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
