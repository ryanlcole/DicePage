#!/usr/bin/env python3
# Shaelvien Knowledge Core — Phase 12.0
# Local persistent memory + subsystem knowledge registry.

import json, os, time
from typing import Dict, Any, List

BASE = os.path.dirname(os.path.abspath(__file__))
STORE_PATH = os.path.join(BASE, "logs", "knowledge_store.json")

# ---------------- Defaults ----------------
DEFAULT_KNOWLEDGE: Dict[str, Any] = {
    "meta": {
        "created": int(time.time()),
        "updated": int(time.time()),
        "version": "1.0",
        "entries": 0
    },
    "subsystems": {
        "solar": {
            "role": "Core processing engine; provides energy and synchronization to all nodes.",
            "status": "stable",
            "notes": [],
            "health": []
        },
        "lunar": {
            "role": "I/O balancer; regulates flow between external devices and internal glyphs.",
            "status": "stable",
            "notes": [],
            "health": []
        },
        "spark": {
            "role": "Computation surge node; handles transient operations and impulses.",
            "status": "stable",
            "notes": [],
            "health": []
        },
        "stone": {
            "role": "Foundation memory; stores persistent data and stabilizes runtime integrity.",
            "status": "stable",
            "notes": [],
            "health": []
        },
        "daemon": {
            "role": "System orchestrator; manages background processes and inter-link harmony.",
            "status": "active",
            "notes": [],
            "health": []
        },
        "tray": {
            "role": "User interface bridge; exposes controls and runtime indicators.",
            "status": "active",
            "notes": [],
            "health": []
        },
        "hud": {
            "role": "Visual layer; renders glyphs and world topology for the user.",
            "status": "active",
            "notes": [],
            "health": []
        },
    }
}

# ---------------- Utilities ----------------
def _load() -> Dict[str, Any]:
    if not os.path.exists(STORE_PATH):
        os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
        _save(DEFAULT_KNOWLEDGE)
    try:
        with open(STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_KNOWLEDGE.copy()

def _save(data: Dict[str, Any]):
    data["meta"]["updated"] = int(time.time())
    data["meta"]["entries"] = sum(len(v.get("notes", [])) for v in data["subsystems"].values())
    tmp = STORE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, STORE_PATH)

# ---------------- Public API ----------------
def learn(subsystem: str, note: str):
    """Add a note or observation to a subsystem."""
    data = _load()
    s = data["subsystems"].setdefault(subsystem, {"role": "", "status": "unknown", "notes": [], "health": []})
    timestamp = int(time.time())
    s["notes"].append({"ts": timestamp, "text": note})
    if len(s["notes"]) > 50:
        s["notes"] = s["notes"][-50:]  # keep recent notes
    _save(data)

def update_health(subsystem: str, health_value: float):
    """Record a health sample (0–1) for trend tracking."""
    data = _load()
    s = data["subsystems"].setdefault(subsystem, {"role": "", "status": "unknown", "notes": [], "health": []})
    timestamp = int(time.time())
    s["health"].append({"ts": timestamp, "value": round(float(health_value), 3)})
    if len(s["health"]) > 200:
        s["health"] = s["health"][-200:]
    _save(data)

def recall(subsystem: str) -> Dict[str, Any]:
    """Return all known info for one subsystem."""
    data = _load()
    return data["subsystems"].get(subsystem, {})

def summarize() -> str:
    """Return a short textual summary of all subsystems."""
    data = _load()
    out = []
    for k,v in data["subsystems"].items():
        status = v.get("status","unknown")
        role = v.get("role","")
        out.append(f"{k.title()}: {status} — {role}")
    return "\n".join(out)

def all_data() -> Dict[str, Any]:
    """Return the full knowledge store."""
    return _load()

# ---------------- CLI Debug ----------------
if __name__ == "__main__":
    print("=== Shaelvien Knowledge Core ===")
    print("Summary:")
    print(summarize())
    learn("solar", "Diagnostic initialized; energy flow nominal.")
    update_health("solar", 0.96)
    print("\nAfter update:")
    print(json.dumps(recall("solar"), indent=2))
