# shaelvien_sound.py
# ShaelvienOS — Analog-like continuous output (sounddevice) with silent fallback

import threading, time, math

from shaelvien_logger import log

try:
    import numpy as np
    import sounddevice as sd
    AUDIO_MODE = "analog_stream"
except Exception:
    AUDIO_MODE = "silent"


class ShaelvienSound(threading.Thread):
    """Continuously streams field resonance as a smooth analog-like waveform."""
    def __init__(self, field_ref, log_callback=None):
        super().__init__(daemon=True)
        self.field_ref = field_ref
        self.running = False
        self.sample_rate = 44100
        self.freq_base = 110.0
        self.freq_max = 1320.0
        self.volume = 0.25

    def run(self):
        self.running = True
        log.success("[Sound] Core started (%s).", AUDIO_MODE)
        if AUDIO_MODE != "analog_stream":
            # Silent mode: keep thread alive but do nothing
            while self.running:
                time.sleep(0.2)
            log.warning("[Sound] Core stopped (silent mode).")
            return

        with sd.OutputStream(samplerate=self.sample_rate, channels=1, callback=self._callback):
            while self.running:
                time.sleep(0.1)
        log.warning("[Sound] Core stopped.")

    def _callback(self, outdata, frames, time_info, status):
        import numpy as np
        if not self.running:
            outdata[:] = np.zeros((frames, 1)); return

        f = getattr(self.field_ref, "particles", [])
        if not f:
            outdata[:] = np.zeros((frames, 1)); return

        avgE = sum(p.energy for p in f) / len(f)
        sync = sum(math.cos(p.phase) for p in f) / len(f)
        freq = self.freq_base + (self.freq_max - self.freq_base) * avgE

        t = np.arange(frames) / self.sample_rate
        wave = np.sin(2 * math.pi * freq * t + sync * math.pi) * self.volume
        drift = np.sin(t * 2 * math.pi * 0.3) * 0.02
        outdata[:] = (wave + drift).reshape(-1, 1)

    def stop(self):
        self.running = False
