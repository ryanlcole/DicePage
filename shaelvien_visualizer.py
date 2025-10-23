# shaelvien_visualizer.py
# ShaelvienOS — Tkinter visualizer (elemental gravity + orbit + resonance)

import threading, time, random, math, tkinter as tk
from tkinter import Canvas
from shaelvien_logger import log


class ShaelFieldVisualizer(threading.Thread):
    """Tkinter visualizer for rune particles with motion & resonance."""
    def __init__(self, field_ref, log_callback=None):
        super().__init__(daemon=True)
        self.field_ref = field_ref
        self.log = log_callback or (lambda m: None)
        self.running = False
        self.root = None
        self.canvas = None
        self.width, self.height = 720, 520
        self.center = [self.width / 2, self.height / 2]
        self.particle_items = {}
        self.bond_lines = {}
        self.bg_intensity = 0
        self.element_bias = {"Fire": (0.0, -0.02), "Water": (0.0, 0.02), "Air": (0.02, 0.0), "Earth": (-0.02, 0.0)}

    def run(self):
        try:
            self.running = True
            self.root = tk.Tk()
            self.root.title("Shaelvien Field – Energy Resonance")
            self.root.configure(bg="#000011")
            self.root.protocol("WM_DELETE_WINDOW", self._on_close)
            self.canvas = Canvas(self.root, width=self.width, height=self.height, bg="#000011", highlightthickness=0)
            self.canvas.pack(fill="both", expand=True)
            self._update_canvas()
            self.root.mainloop()
        except Exception as e:
            log.warning("[Visualizer] Thread error: %s", e)

    def _update_canvas(self):
        if not self.running:
            return
        field = getattr(self.field_ref, "particles", [])
        if not field:
            self.canvas.delete("all")
        else:
            avgE = sum(p.energy for p in field) / max(1, len(field))
            self.bg_intensity = 0.9 * self.bg_intensity + 0.1 * avgE
            shade = int(10 + self.bg_intensity * 60)
            self.canvas.config(bg=f"#{shade:02x}{shade:02x}{(shade+5):02x}")

            for i, p in enumerate(field):
                if i not in self.particle_items:
                    x = random.randint(60, self.width - 60)
                    y = random.randint(60, self.height - 60)
                    vx = (random.random() - 0.5) * 2
                    vy = (random.random() - 0.5) * 2
                    self.particle_items[i] = {
                        "pos": [x, y],
                        "vel": [vx, vy],
                        "obj": self.canvas.create_oval(x-5, y-5, x+5, y+5, fill=p.color, outline=""),
                        "label": self.canvas.create_text(x, y, text=p.symbol, fill="#ffffff", font=("Arial", 10, "bold")),
                    }

                item = self.particle_items[i]
                x, y = item["pos"]
                vx, vy = item["vel"]

                speed = 0.5 + min(2.0, p.energy * 3)
                vx += p.flow[0] * 0.05
                vy += p.flow[1] * 0.05
                bx, by = self.element_bias.get(p.element, (0.0, 0.0))
                vx += bx; vy += by

                dx = self.center[0] - x; dy = self.center[1] - y
                dist = math.sqrt(dx*dx + dy*dy) + 1e-6
                vx += dx / dist * 0.02; vy += dy / dist * 0.02
                vx += -dy / dist * 0.005; vy += dx / dist * 0.005

                x += vx * speed; y += vy * speed
                if x < 20 or x > self.width - 20: vx *= -0.8; x = max(20, min(self.width-20, x))
                if y < 20 or y > self.height - 20: vy *= -0.8; y = max(20, min(self.height-20, y))
                item["pos"] = [x, y]; item["vel"] = [vx * 0.98, vy * 0.98]

            self._apply_resonance(field)
            self._draw_bonds()

        self.root.after(60, self._update_canvas)

    def _apply_resonance(self, field):
        for i, p in enumerate(field):
            item = self.particle_items.get(i)
            if not item: continue
            neighbors = 0; sync = 0
            for j, q in enumerate(field):
                if i == j: continue
                dx = item["pos"][0] - self.particle_items[j]["pos"][0]
                dy = item["pos"][1] - self.particle_items[j]["pos"][1]
                d = math.sqrt(dx*dx + dy*dy)
                if d < 120:
                    neighbors += 1
                    sync += math.cos(p.phase - q.phase)
            resonance = (sync / neighbors + 1) / 2 if neighbors > 0 else 0.5
            pulse = 0.5 + 0.5 * math.sin(p.phase * 2 + resonance * math.pi)
            brightness = min(1.0, p.energy * 0.8 + pulse * 0.4)
            base_col = self._phase_to_color(p.phase)
            mod_col = self._modulate_color(base_col, brightness)
            r = max(3, min(25, int(p.energy * 10)))
            x, y = item["pos"]
            self.canvas.coords(item["obj"], x - r, y - r, x + r, y + r)
            self.canvas.itemconfig(item["obj"], fill=mod_col)
            self.canvas.coords(item["label"], x, y)

    def _draw_bonds(self):
        for line in self.bond_lines.values():
            self.canvas.delete(line)
        self.bond_lines.clear()
        ids = list(self.particle_items.keys())
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                xi, yi = self.particle_items[ids[i]]["pos"]
                xj, yj = self.particle_items[ids[j]]["pos"]
                dx, dy = xi - xj, yi - yj
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < 150:
                    fade = max(30, min(255, int(255 - dist * 1.2)))
                    col = f"#{fade:02x}{fade:02x}{fade:02x}"
                    self.bond_lines[(i, j)] = self.canvas.create_line(xi, yi, xj, yj, fill=col, width=1)

    def _phase_to_color(self, phase):
        v = (math.sin(phase) + 1) / 2
        r = int(120 + v * 120)
        g = int(80 + v * 175)
        b = int(180 + (1 - v) * 60)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _modulate_color(self, hex_color, factor):
        r = int(hex_color[1:3], 16); g = int(hex_color[3:5], 16); b = int(hex_color[5:7], 16)
        r = int(min(255, r * (0.6 + factor * 0.8)))
        g = int(min(255, g * (0.6 + factor * 0.8)))
        b = int(min(255, b * (0.6 + factor * 0.8)))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _on_close(self):
        self.running = False
        try:
            self.root.destroy()
        except Exception:
            pass
        log.warning("[Visualizer] Closed.")
