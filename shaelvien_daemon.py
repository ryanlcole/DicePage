"""
ShaelvienOS • Phase 23.8 • Brain Runtime Alpha + Sensory Link
-------------------------------------------------------------
Main daemon.  Loads unified brain, starts resonance loop,
and now includes live sensory snapshots from the handler.
"""

from flask import Flask, jsonify
from datetime import datetime
import threading, time, random

# ---- internal modules ----
from ai_founders_loader import load_founders
import sensory_input_handler as senses

# -------------------------------------------------
# Flask setup
# -------------------------------------------------
app = Flask(__name__)
PORT = 7713

# -------------------------------------------------
# Boot sequence
# -------------------------------------------------
print("[daemon] Booting ShaelvienOS • Brain Runtime Alpha …")
BRAIN = load_founders()
print(f"[daemon] BrainMap regions = {len(BRAIN['BrainMap'])}")

# simple background resonance drift
running = True

def resonance_loop():
    while running:
        drift = round(random.uniform(-0.25, 0.25), 3)
        avg = BRAIN["ResonanceMatrix"][0]["AverageFrequency"]
        BRAIN["ResonanceMatrix"][0]["AverageFrequency"] = round(avg + drift, 3)
        time.sleep(5)

threading.Thread(target=resonance_loop, daemon=True).start()
print(f"[daemon] Resonance loop initialized at ≈ {BRAIN['ResonanceMatrix'][0]['AverageFrequency']} Hz")

# -------------------------------------------------
# API endpoints
# -------------------------------------------------
@app.route("/health")
def health():
    """Basic system heartbeat."""
    return jsonify({
        "status": "ok",
        "phase": "23.8",
        "regions": list(BRAIN["BrainMap"].keys()),
        "avg_resonance": BRAIN["ResonanceMatrix"][0]["AverageFrequency"],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

@app.route("/api/brainmap")
def brainmap():
    """Return unified brain structure."""
    return jsonify(BRAIN)

@app.route("/api/senses")
def senses_snapshot():
    """Live sensory snapshot from sensory_input_handler."""
    frame = senses.gather_sensory_snapshot()
    return jsonify(frame)

# -------------------------------------------------
# Main entry
# -------------------------------------------------
if __name__ == "__main__":
    try:
        print(f"[daemon] Phase 23.8 — Brain Runtime Alpha + Sensory Link Online")
        print(f"[daemon] http://127.0.0.1:{PORT}/health")
        print(f"[daemon] http://127.0.0.1:{PORT}/api/senses")
        app.run(host="127.0.0.1", port=PORT, debug=False)
    except KeyboardInterrupt:
        running = False
        print("\n[daemon] Stopping resonance loop and shutting down safely…")
