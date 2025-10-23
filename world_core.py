# world_core.py
# Phase 11.3 Final — Region ambient system + health linkage

from __future__ import annotations
import math, time
from typing import Dict
import glyph_core

ANCHORS = {
    "solar": (0.70, 0.52),
    "lunar": (0.50, 0.24),
    "spark": (0.30, 0.52),
    "stone": (0.50, 0.80),
}

def _clamp(x): return max(0.0, min(1.0, x))

def _ambient(h: float) -> dict:
    """Simple ambient simulation based on subsystem health."""
    return {
        "brightness": round(0.4 + 0.6 * h, 3),
        "haze": round(0.3 + 0.7 * (1 - h), 3),
        "saturation": round(0.3 + 0.7 * h, 3)
    }

# ------------------------------------------------------------
def build_world(flags: Dict[str, float]) -> Dict[str, dict]:
    """Global ambient synthesis."""
    health = glyph_core.compute_health()
    regions = []
    for rid, pos in ANCHORS.items():
        h = health.get(rid, 1.0)
        amb = _ambient(h)
        regions.append({
            "id": rid,
            "name": glyph_core.RUNES[rid]["name"],
            "pos": pos,
            "health": round(h, 2),
            "ambient": amb,
        })
    g_bright = sum(r["ambient"]["brightness"] for r in regions) / len(regions)
    g_haze = sum(r["ambient"]["haze"] for r in regions) / len(regions)
    return {
        "regions": regions,
        "global": {"brightness": g_bright, "haze": g_haze},
        "ts": int(time.time() * 1000),
    }

# ------------------------------------------------------------
def get_region(rid: str, flags: Dict[str, float]) -> dict:
    """Return detailed info for one region (used by /region)."""
    rid = rid.lower().strip()
    if rid not in ANCHORS:
        return {"id": rid, "status": "unknown", "health": 0, "ambient": {}}
    health = glyph_core.compute_health().get(rid, 1.0)
    amb = _ambient(health)
    return {
        "id": rid,
        "name": glyph_core.RUNES[rid]["name"],
        "status": "ok" if health > 0 else "placeholder",
        "health": round(health, 2),
        "ambient": {
            "brightness": amb["brightness"],
            "haze": amb["haze"]
        },
        "ts": int(time.time() * 1000)
    }
