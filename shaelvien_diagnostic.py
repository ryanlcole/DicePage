# ============================================================
# SHAELVIEN DIAGNOSTIC SHELL — Phase 8
# Real-time log and resource monitor
# ============================================================

import os, time, json, psutil, threading
import tkinter as tk
from tkinter import scrolledtext, ttk
from datetime import datetime

APP_NAME = "Shaelvien Diagnostic Shell"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_PATH = os.path.join(LOG_DIR, "launcher_error.log")
DAEMON_DIAG = os.path.join(LOG_DIR, "daemon_state.json")

os.makedirs(LOG_DIR, exist_ok=True)

class DiagnosticShell(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("850x500")
        self.configure(bg="#1a1a1a")

        # --- Frames ---
        self.top = tk.Frame(self, bg="#1a1a1a")
        self.top.pack(fill="x", pady=4)
        self.bottom = tk.Frame(self, bg="#1a1a1a")
        self.bottom.pack(fill="both", expand=True)

        self.cpu_var = tk.StringVar()
        self.mem_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Running...")

        tk.Label(self.top, textvariable=self.cpu_var, fg="#00ff99", bg="#1a1a1a", font=("Consolas", 10)).pack(side="left", padx=10)
        tk.Label(self.top, textvariable=self.mem_var, fg="#33ccff", bg="#1a1a1a", font=("Consolas", 10)).pack(side="left", padx=10)
        tk.Label(self.top, textvariable=self.status_var, fg="#ffff66", bg="#1a1a1a", font=("Consolas", 10)).pack(side="right", padx=10)

        self.text = scrolledtext.ScrolledText(self.bottom, bg="#0d0d0d", fg="#00ff99", font=("Consolas", 9))
        self.text.pack(fill="both", expand=True)

        self.after(1000, self.refresh)

    def refresh(self):
        try:
            # CPU + MEM
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
            self.cpu_var.set(f"CPU {cpu:.1f}%")
            self.mem_var.set(f"MEM {mem:.1f}%")

            # Daemon diagnostics
            if os.path.exists(DAEMON_DIAG):
                with open(DAEMON_DIAG, "r", encoding="utf-8") as f:
                    data = json.load(f)
                phase = data.get("phase", "unknown")
                self.status_var.set(f"Phase: {phase}")
            else:
                self.status_var.set("No daemon report detected")

            # Log tail
            if os.path.exists(LOG_PATH):
                with open(LOG_PATH, "r", encoding="utf-8") as f:
                    lines = f.readlines()[-30:]
                self.text.delete("1.0", tk.END)
                self.text.insert(tk.END, "".join(lines))
                self.text.see(tk.END)
        except Exception as e:
            self.text.insert(tk.END, f"[ERROR] {e}\n")

        self.after(2000, self.refresh)


if __name__ == "__main__":
    shell = DiagnosticShell()
    shell.mainloop()
