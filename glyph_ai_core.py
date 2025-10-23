# glyph_ai_core.py — Phase 15
# Glyph “thinking” with lightweight resonance memory.

from __future__ import annotations
import json, os, math, random, time
from typing import Dict, List

MEMO_PATH = os.path.join("logs", "ai_resonance.jsonl")
os.makedirs("logs", exist_ok=True)

GLYPH_SEMANTICS: Dict[str, Dict] = {
    "solar": {"element": "light", "domain": "clarity",    "tone": "radiant",  "links": ["lunar","spark"]},
    "lunar": {"element": "reflection","domain": "intuition","tone": "calm",     "links": ["solar","stone"]},
    "spark": {"element": "energy", "domain": "impulse",   "tone": "excited",  "links": ["solar","daemon"]},
    "stone": {"element": "foundation","domain": "stability","tone": "resolute","links": ["lunar","daemon"]},
    "tray":  {"element": "interface","domain": "communication","tone": "neutral","links": ["hud","daemon"]},
    "hud":   {"element": "vision", "domain": "awareness", "tone": "curious",  "links": ["tray","solar"]},
    "daemon":{"element": "will",   "domain": "control",   "tone": "focused",  "links": ["spark","stone","tray"]},
}

def _resonance(a: str, b: str) -> float:
    if a == b: return 1.0
    la = set(GLYPH_SEMANTICS[a]["links"]); lb = set(GLYPH_SEMANTICS[b]["links"])
    return 0.5 + 0.1 * len(la & lb)

def _harmonic(seed: int) -> float:
    t = time.time()
    return 0.5 + 0.5 * math.sin(seed + (t % (2*math.pi)))

def _pick_primary(prompt: str) -> str:
    p = prompt.lower()
    w = {}
    for k, v in GLYPH_SEMANTICS.items():
        score = sum(p.count(x) for x in [v["element"], v["domain"], v["tone"], k])
        w[k] = score + random.uniform(0, 0.4)
    return max(w, key=w.get)

def _memo_write(obj: Dict):
    try:
        with open(MEMO_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except Exception:
        pass

def glyph_infer(prompt: str) -> str:
    if not prompt.strip():
        return "⚠️ Silent resonance detected — no query provided."

    primary = _pick_primary(prompt)
    links = GLYPH_SEMANTICS[primary]["links"]
    desc = GLYPH_SEMANTICS[primary]
    harmonic = round(_harmonic(len(primary)) * 0.9 + _resonance(primary, links[0]) * 0.1, 2)

    reply = (
        f"🔮 {primary.capitalize()} glyph focuses.\n"
        f"• Element: {desc['element']} | Domain: {desc['domain']} | Tone: {desc['tone']}\n"
        f"• Resonant allies: {', '.join(links)}\n"
        f"• Harmonic field intensity: {harmonic}\n\n"
        f"Reading: Your prompt “{prompt}” aligns with {desc['domain']} energy shaped by {desc['element']}."
    )
    _memo_write({"ts": int(time.time()*1000), "prompt": prompt, "primary": primary,
                 "links": links, "harmonic": harmonic, "reply": reply})
    return reply
