# shaelvien_field.py
# ShaelvienOS — Field engine (threaded), logger-integrated

import math
import random
import threading
import time
from shaelvien_logger import log


class RuneParticle:
    """Single rune-particle node with simple wave and flow dynamics."""
    def __init__(self, glyph):
        self.rune = glyph["rune"]
        self.name = glyph["name"]
        self.mass = glyph["mass"]
        self.flex = glyph["flex"]
        self.color = glyph["color"]
        self.symbol = glyph.get("symbol", "?")
        self.element = glyph.get("element", "Neutral")
        self.phase = glyph["phase_base"]
        self.amp = glyph["flex"]

        self.energy = 0.0
        self.flow = [0.0, 0.0, 0.0]
        self.time = 0.0

    def step(self, dt, global_phase):
        phi = self.phase + global_phase
        wave = math.sin(phi) * self.amp
        self.energy = abs(wave) * self.mass * 0.01
        self.flow[0] = math.cos(phi) * 0.1
        self.flow[1] = math.sin(phi) * 0.1
        self.flow[2] = math.sin(phi * 0.5) * 0.05
        self.time += dt


class ShaelvienField(threading.Thread):
    """Background simulation thread for all active glyph-particles."""
    def __init__(self, log_callback=None):
        super().__init__(daemon=True)
        self.log = log_callback or (lambda m: None)
        self.particles = []
        self.running = False
        self.global_phase = 0.0
        self.dt = 0.05

        # late import to avoid circular
        from glyph_core import GlyphCore
        self.glyphs = GlyphCore()

    def seed_from_glyphs(self, count=10):
        self.particles.clear()
        ids = list(self.glyphs.runes.keys())
        for _ in range(count):
            rid = random.choice(ids)
            p = RuneParticle(self.glyphs.to_particle(rid))
            self.particles.append(p)
        log.success("[GlyphEngine] Spawned %s rune-particles.", len(self.particles))

    def run(self):
        self.running = True
        log.success("[GlyphEngine] Field simulation started.")
        tick = 0
        while self.running:
            self.global_phase += self.dt
            for p in self.particles:
                p.step(self.dt, self.global_phase)
            tick += 1
            if tick % 40 == 0:
                avgE = sum(p.energy for p in self.particles) / max(1, len(self.particles))
                log.info("[Field] phase=%.2f, avgE=%.3f", self.global_phase, avgE)
            time.sleep(self.dt)
        log.warning("[GlyphEngine] Field simulation stopped.")

    def stop(self):
        self.running = False
