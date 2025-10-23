import os, sys, threading, tkinter as tk
from tkinter import ttk
from shaelvien_daemon import ShaelvienDaemon
from shaelvien_tray import ShaelvienTray

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class ShaelvienApp:
    def __init__(self):
        self.daemon = ShaelvienDaemon()
        self.root = tk.Tk()
        self.root.title("ShaelvienOS Prototype")
        self.root.configure(bg="#101010")

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True)

        self.status_var = tk.StringVar(value="idle")
        self.cpu_var = tk.StringVar(value="CPU: 0.0%")
        self.mem_var = tk.StringVar(value="MEM: 0.0%")
        self.epoch_var = tk.StringVar(value="Epoch: 0")

        ttk.Label(frame, text="ShaelvienOS Ready", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, pady=(0, 8))
        ttk.Label(frame, textvariable=self.status_var, foreground="green").grid(row=1, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.cpu_var).grid(row=2, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.mem_var).grid(row=3, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.epoch_var).grid(row=4, column=0, sticky="w", pady=(0, 8))
        ttk.Button(frame, text="Quit", command=self.quit).grid(row=5, column=0, pady=(8, 0))

        # Start the tray icon
        self.tray = ShaelvienTray(self)
        self.tray.start()

        # Optional: start minimized
        self.root.withdraw()
        self.root.after(1000, self.root.iconify)

        self.update_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

    def update_ui(self):
        s = self.daemon.state
        self.status_var.set(s.get("status", "idle"))
        self.cpu_var.set(f"CPU: {s.get('cpu_pct', 0):.1f}%")
        self.mem_var.set(f"MEM: {s.get('mem_pct', 0):.1f}%")
        self.epoch_var.set(f"Epoch: {s.get('epoch', 0)}")
        self.root.after(500, self.update_ui)

    def run(self):
        threading.Thread(target=self.daemon.run, daemon=True).start()
        self.root.mainloop()

    def quit(self):
        self.daemon.stop()
        self.root.destroy()

if __name__ == "__main__":
    ShaelvienApp().run()
