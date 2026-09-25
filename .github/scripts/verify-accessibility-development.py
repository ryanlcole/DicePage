#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "knowledge/project/accessibility-development.json"


def fail(message: str) -> None:
    raise SystemExit("ACCESSIBILITY DEVELOPMENT FAILED: " + message)


if not CONTRACT.is_file():
    fail("machine-readable accessibility development contract is missing")

data = json.loads(CONTRACT.read_text(encoding="utf-8"))
if data.get("contract") != "shaelvien.accessibility-development":
    fail("unexpected accessibility contract identity")
if data.get("status") != "project-wide-owner-directed-rule":
    fail("project-wide accessibility rule is not authoritative")
if data.get("sameTruth") is not True or data.get("separateAccessibilityAuthority") is not False:
    fail("accessibility must remain another representation of the same truth, not a second authority")

required = data.get("required") or {}
for key in (
    "keyboard",
    "pointerIndependentEssentialActions",
    "semanticNamesRolesStates",
    "visibleFocus",
    "logicalFocusOrder",
    "nonColorInformation",
    "reducedMotion",
    "zoomReflow",
    "accessibleStatusAnnouncements",
    "sharedAuthoritativeState",
    "sharedRecursiveAuthority",
):
    if required.get(key) is not True:
        fail("required accessibility invariant is not enabled: " + key)

agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
for phrase in (
    "docs/ACCESSIBILITY_DEVELOPMENT_CONTRACT.md",
    "Every future Shaelvien/RIST change is both normal development and accessibility development.",
    "A user-facing change is not complete until its accessibility impact",
):
    if phrase not in agents:
        fail("AGENTS.md no longer carries the accessibility development rule: " + phrase)

shell = (ROOT / "apps/rist-world/Components/AccessibilityShell.razor").read_text(encoding="utf-8")
for phrase in (
    "same world truth used by the visual table",
    'aria-live="polite"',
    "PlaceAccessibleStaged",
    "MoveAccessiblePieceAsync",
    "PlaceAccessibleFeature",
    "prefers-reduced-motion:reduce",
):
    if phrase not in shell:
        fail("Accessibility Shell lost a semantic-accessibility invariant: " + phrase)

try:
    parent = subprocess.check_output(
        ["git", "rev-parse", "--verify", "HEAD^"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
    ).strip()
except subprocess.CalledProcessError:
    parent = ""

if parent:
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", parent, "HEAD"], cwd=ROOT, text=True
    ).splitlines()

    runtime_ext = {".razor", ".cs", ".js", ".css", ".html"}
    runtime = [
        p for p in changed
        if (p.startswith("apps/rist-world/") or p.startswith("site/relic-home/"))
        and Path(p).suffix.lower() in runtime_ext
        and "/tests/" not in p
        and "/obj/" not in p
        and "/bin/" not in p
    ]

    if runtime:
        accessibility_path = any(
            any(token in p.lower() for token in (
                "accessibility", "a11y", "keyboard", "caption",
                "transcript", "screen-reader", "screenreader"
            ))
            for p in changed
        )
        diff = subprocess.check_output(
            ["git", "diff", "--unified=0", parent, "HEAD", "--", *runtime],
            cwd=ROOT, text=True, errors="replace"
        )
        added = "\n".join(
            line[1:] for line in diff.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ).lower()
        accessibility_marker = any(marker in added for marker in (
            "aria-", 'role="', "tabindex", "focus", "keyboard",
            "accessibility", "screen reader", "screen-reader",
            "prefers-reduced-motion", "caption", "transcript",
            "semantic", "pointer-independent", "touch-action"
        ))
        if not accessibility_path and not accessibility_marker:
            fail(
                "user-facing runtime files changed without accessibility-equivalent evidence in the same commit: "
                + ", ".join(runtime[:12])
            )

print("Accessibility development verified: shared truth/authority, semantic shell invariants, and same-commit accessibility evidence for user-facing runtime changes.")
