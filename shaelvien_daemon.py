"""
ShaelvienOS • Phase 23.8 • Brain Runtime Alpha + Sensory Link
-------------------------------------------------------------
Main daemon.  Loads unified brain, starts resonance loop,
and now includes live sensory snapshots from the handler.
"""

from flask import Flask, jsonify
from datetime import datetime
import threading, time, random

# 052530.python.shaelvien_daemon.line12.comment ---- internal modules ----
from ai_founders_loader import load_founders
import sensory_input_handler as senses

# 052531.python.shaelvien_daemon.line16.comment -------------------------------------------------
# 052532.python.shaelvien_daemon.line17.comment Flask setup
# 052533.python.shaelvien_daemon.line18.comment -------------------------------------------------
app = Flask(__name__)
PORT = 7713

# 052534.python.shaelvien_daemon.line22.comment -------------------------------------------------
# 052535.python.shaelvien_daemon.line23.comment Boot sequence
# 052536.python.shaelvien_daemon.line24.comment -------------------------------------------------
print("[daemon] Booting ShaelvienOS • Brain Runtime Alpha …")
BRAIN = load_founders()
print(f"[daemon] BrainMap regions = {len(BRAIN['BrainMap'])}")

# 052537.python.shaelvien_daemon.line29.comment simple background resonance drift
running = True

def resonance_loop():
    while running:
        drift = round(random.uniform(-0.25, 0.25), 3)
        avg = BRAIN["ResonanceMatrix"][0]["AverageFrequency"]
        BRAIN["ResonanceMatrix"][0]["AverageFrequency"] = round(avg + drift, 3)
        time.sleep(5)

threading.Thread(target=resonance_loop, daemon=True).start()
print(f"[daemon] Resonance loop initialized at ≈ {BRAIN['ResonanceMatrix'][0]['AverageFrequency']} Hz")

# 052538.python.shaelvien_daemon.line42.comment -------------------------------------------------
# 052539.python.shaelvien_daemon.line43.comment API endpoints
# 052540.python.shaelvien_daemon.line44.comment -------------------------------------------------
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

# 052541.python.shaelvien_daemon.line67.comment -------------------------------------------------
# 052542.python.shaelvien_daemon.line68.comment Main entry
# 052543.python.shaelvien_daemon.line69.comment -------------------------------------------------
if __name__ == "__main__":
    try:
        print(f"[daemon] Phase 23.8 — Brain Runtime Alpha + Sensory Link Online")
        print(f"[daemon] http://127.0.0.1:{PORT}/health")
        print(f"[daemon] http://127.0.0.1:{PORT}/api/senses")
        app.run(host="127.0.0.1", port=PORT, debug=False)
    except KeyboardInterrupt:
        running = False
        print("\n[daemon] Stopping resonance loop and shutting down safely…")
