# ============================================================
# SHAELVIEN LAUNCHER — Phase 8.5
# Fault-tolerant subsystem controller with diagnostic reporting
# ============================================================

import os, sys, time, psutil, subprocess, json, traceback, threading
from datetime import datetime

APP_NAME = "ShaelvienOS Launcher"
BASE_DIR = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))
ASSETS = os.path.join(BASE_DIR, "assets")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_PATH = os.path.join(LOG_DIR, "launcher_error.log")
DAEMON = os.path.join(BASE_DIR, "shaelvien_daemon.exe")
TRAY = os.path.join(BASE_DIR, "shaelvien_tray.exe")
STATUS_JSON = os.path.join(LOG_DIR, "system_status.json")

os.makedirs(LOG_DIR, exist_ok=True)

HEARTBEAT_INTERVAL = 2
UPTIME_START = time.time()
SIMULATE_FAULTS = False  # Toggle manually or by diagnostic interface


def write_log(msg):
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%H:%M:%S}] {msg}\n")
    print(msg)


def json_report(state):
    """Write live system status for Diagnostic Shell."""
    data = {
        "timestamp": datetime.now().isoformat(),
        "cpu": psutil.cpu_percent(interval=None),
        "mem": psutil.virtual_memory().percent,
        "uptime_sec": round(time.time() - UPTIME_START, 1),
        "subsystems": state,
        "simulating_faults": SIMULATE_FAULTS
    }
    with open(STATUS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def is_running(name):
    count = 0
    for p in psutil.process_iter(["name"]):
        if p.info["name"] and name.lower() in p.info["name"].lower():
            count += 1
    return count


def start_subsystem(exe):
    try:
        if not os.path.exists(exe):
            write_log(f"[WARN] Missing target: {exe}")
            return None
        return subprocess.Popen([exe], creationflags=subprocess.CREATE_NEW_CONSOLE)
    except Exception as e:
        write_log(f"[ERROR] Failed to start {exe}: {e}")


def heartbeat():
    procs = {"daemon": None, "tray": None}
    while True:
        try:
            # Check if subsystems are alive
            for key, path in {"daemon": DAEMON, "tray": TRAY}.items():
                running = is_running(os.path.basename(path))
                if running == 0:
                    procs[key] = start_subsystem(path)
                    write_log(f"[RESTART] Relaunched {key}.exe")
                elif running > 1:
                    # kill extras (only 1 doppelgänger allowed)
                    write_log(f"[WARN] Multiple {key}.exe detected. Reducing to one.")
                    killed = 0
                    for p in psutil.process_iter(["name", "pid"]):
                        if p.info["name"] and key in p.info["name"].lower():
                            if killed == 0:
                                killed += 1
                                continue
                            try:
                                psutil.Process(p.info["pid"]).kill()
                            except Exception:
                                pass

            # Optional fault simulation
            if SIMULATE_FAULTS and int(time.time()) % 30 == 0:
                write_log("[FAULT] Simulated subsystem crash event.")
                for proc in list(psutil.process_iter(["name", "pid"])):
                    if "tray" in proc.info["name"].lower():
                        proc.kill()

            # System state report
            json_report({"daemon": is_running("shaelvien_daemon"),
                         "tray": is_running("shaelvien_tray")})
        except Exception as e:
            write_log(f"[ERROR][Heartbeat] {e}\n{traceback.format_exc()}")
        time.sleep(HEARTBEAT_INTERVAL)


if __name__ == "__main__":
    write_log(f"[INFO] {APP_NAME} starting...")
    t = threading.Thread(target=heartbeat, daemon=True)
    t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        write_log("[INFO] Exiting launcher and all subsystems.")
