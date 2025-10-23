# shaelvien_logger.py
# ShaelvienOS Portable – Unified Logging Core (Resonant Log Mode)

import os, time, logging, threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGS_DIR = Path(__file__).resolve().parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)
LOG_PATH = LOGS_DIR / "daemon.log"

# ---------------------------------------------------------------------
# Custom level for "SUCCESS" (between INFO and WARNING)
SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")

def success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL):
        self._log(SUCCESS_LEVEL, message, args, **kwargs)

logging.Logger.success = success

# ---------------------------------------------------------------------
# Logger configuration
formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S"
)

handler = RotatingFileHandler(
    LOG_PATH, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
)
handler.setFormatter(formatter)

log = logging.getLogger("Shaelvien")
log.setLevel(logging.WARNING)  # Default: WARNING + ERROR + SUCCESS
log.addHandler(handler)
log.propagate = False

# ---------------------------------------------------------------------
# Adaptive verbosity (switch from tray)
def set_level(mode: str):
    """Change logging verbosity: silent / normal / verbose"""
    mode = mode.lower().strip()
    if mode in ("silent", "quiet"):
        log.setLevel(logging.WARNING)
        log.warning("Log level set to SILENT")
    elif mode in ("normal", "default"):
        log.setLevel(SUCCESS_LEVEL)
        log.success("Log level set to NORMAL")
    elif mode in ("verbose", "debug"):
        log.setLevel(logging.INFO)
        log.info("Log level set to VERBOSE")
    else:
        log.warning("Unknown log mode: %s", mode)

# ---------------------------------------------------------------------
# Cleanup daemon (runs in background)
def _cleanup_worker():
    while True:
        try:
            for f in LOGS_DIR.glob("*.log*"):
                if f.stat().st_mtime < time.time() - 14 * 86400:
                    f.unlink()
            # remove empty files (0 bytes)
            for f in LOGS_DIR.glob("*.log*"):
                if f.stat().st_size == 0:
                    f.unlink()
        except Exception:
            pass
        time.sleep(3600)  # run hourly

_cleanup_thread = threading.Thread(target=_cleanup_worker, daemon=True)
_cleanup_thread.start()

# ---------------------------------------------------------------------
# Helper wrappers for external use (drop-in replacement for _write_log)
def write(msg: str):
    """Legacy-style simple log (INFO level)."""
    log.info(msg)

def warn(msg: str):
    log.warning(msg)

def error(msg: str):
    log.error(msg)

def success_msg(msg: str):
    log.success(msg)
