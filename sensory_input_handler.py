"""
ShaelvienOS • Phase 23.8 • Sensory Input Handler
-------------------------------------------------
Perception layer using shaelvien_array for numeric work.
"""

import time, math, random
import shaelvien_array as np

# ---- visual ----
def capture_camera_frame(frame=None):
    brightness=random.uniform(0.2,0.9)
    color_balance=np.Array([random.uniform(0.3,0.8) for _ in range(3)])
    composition=color_balance.magnitude()/1.4
    return {
        "Brightness":round(brightness,3),
        "ColorBalance":[round(c,3) for c in color_balance],
        "Composition":round(min(composition,1.0),3)
    }

# ---- audio ----
def capture_audio_sample():
    amplitude=random.uniform(0.0,1.0)
    spectral=random.uniform(0.2,1.0)
    pitch=random.uniform(100,2000)
    waveform=np.Array.random(128)
    energy=np.fourier_amplitude(waveform)
    return {
        "Amplitude":round(amplitude,3),
        "SpectralComplexity":round(spectral,3),
        "Pitch":round(pitch,1),
        "Energy":round(energy,3)
    }

# ---- empathy ----
def read_keyboard_pattern(last_timestamps=None):
    now=time.time()
    if not last_timestamps: return {"Speed":0.0,"Aggression":0.0}
    interval=now-last_timestamps[-1]
    speed=1.0/max(interval,0.01)
    aggression=min(speed/10,1.0)
    return {"Speed":round(speed,3),"Aggression":round(aggression,3)}

def interpret_motion_to_empathy(motion_vector):
    vector=np.Array(motion_vector)
    magnitude=vector.magnitude()
    empathy=max(0.0,min(1.0-magnitude,1.0))
    return {"EmpathyWeight":round(empathy,3)}

# ---- olfactory ----
def visual_to_aroma(freq):
    aroma_map={261.6:"Citrus",329.6:"Floral",392.0:"Herbal",440.0:"Sweet",493.9:"Savory"}
    closest=min(aroma_map.keys(),key=lambda f:abs(f-freq))
    return {"Aroma":aroma_map[closest],"Frequency":freq}

# ---- tactile ----
def evaluate_environment_input(brightness,amplitude,aggression):
    stress=(brightness+amplitude+aggression)/3.0
    comfort=1.0-stress
    return {"StressLevel":round(stress,3),"ComfortLevel":round(comfort,3)}

# ---- master gather ----
def gather_sensory_snapshot():
    visual=capture_camera_frame()
    audio=capture_audio_sample()
    empathy=interpret_motion_to_empathy([random.uniform(0,0.5) for _ in range(3)])
    aroma=visual_to_aroma(random.choice([261.6,329.6,392.0,440.0,493.9]))
    tactile=evaluate_environment_input(
        visual["Brightness"],audio["Amplitude"],empathy["EmpathyWeight"]
    )
    return {
        "Timestamp":round(time.time(),3),
        "Visual":visual,
        "Audio":audio,
        "Empathy":empathy,
        "Aroma":aroma,
        "Tactile":tactile
    }

if __name__=="__main__":
    frame=gather_sensory_snapshot()
    print("[sensory] Snapshot:")
    for k,v in frame.items(): print(f"  {k}: {v}")
