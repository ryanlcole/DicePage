# waveform_core.py — minimal waveform primitives with graceful fallbacks
from __future__ import annotations
import math, random, time, json, os
from typing import List, Dict, Tuple, Optional

# soft optional deps (all code must run without them)
try:
    import numpy as np
except Exception:
    np = None

def now_ms() -> int:
    return int(time.time()*1000)

# ---------- synthetic generators ----------
def synth_tone(freq: float = 440.0, dur_s: float = 1.0, sr: int = 16000) -> List[float]:
    n = int(dur_s*sr)
    out = []
    for i in range(n):
        out.append(math.sin(2*math.pi*freq * (i/sr)))
    return out

def synth_chirp(f0=220.0, f1=1760.0, dur_s=1.0, sr=16000) -> List[float]:
    n=int(dur_s*sr); out=[]
    for i in range(n):
        t=i/sr; f=f0+(f1-f0)*(t/dur_s)
        out.append(math.sin(2*math.pi*f*t))
    return out

# ---------- features (audio) ----------
def energy(sig: List[float]) -> float:
    if not sig: return 0.0
    s = sum(x*x for x in sig) / len(sig)
    return min(1.0, max(0.0, s))  # normalize-ish

def bandpass_bins(sig: List[float], sr: int = 16000, bins: int = 8) -> List[float]:
    """Very coarse ‘spectrum’. If numpy is available use real FFT; else cheap segment RMS."""
    if not sig: return [0.0]*bins
    if np is not None:
        arr = np.asarray(sig, dtype=np.float32)
        spec = np.abs(np.fft.rfft(arr))  # linear bins
        chunk = max(1, len(spec)//bins)
        v = [float(spec[i*chunk:(i+1)*chunk].mean()) for i in range(bins)]
    else:
        seg = max(1, len(sig)//(bins))
        v = []
        for i in range(bins):
            part = sig[i*seg:(i+1)*seg]
            if not part: part=[0.0]
            v.append(sum(abs(x) for x in part)/len(part))
    s = sum(v) or 1e-6
    return [x/s for x in v]  # unit-sum histogram

# ---------- features (video) ----------
def frame_histogram(rgb_frame: List[Tuple[int,int,int]], buckets: int = 8) -> List[float]:
    """Accepts list of (r,g,b). Without cv/numpy, approximate brightness histogram."""
    if not rgb_frame: return [0.0]*buckets
    H=[0]*buckets
    for (r,g,b) in rgb_frame:
        y = int((0.2126*r + 0.7152*g + 0.0722*b)/255 * (buckets-1))
        H[max(0,min(buckets-1,y))]+=1
    tot = sum(H) or 1
    return [h/tot for h in H]

# ---------- similarity metrics ----------
def cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a)!=len(b): return 0.0
    num=sum(x*y for x,y in zip(a,b))
    da=math.sqrt(sum(x*x for x in a)); db=math.sqrt(sum(y*y for y in b))
    if da*db==0: return 0.0
    return max(0.0, min(1.0, num/(da*db)))

def jensen_shannon(p: List[float], q: List[float]) -> float:
    # similarity (1 - divergence)
    import math
    def _kl(a,b):
        eps=1e-12
        return sum(ai*math.log((ai+eps)/(bi+eps)) for ai,bi in zip(a,b))
    m=[0.5*(pi+qi) for pi,qi in zip(p,q)]
    js=0.5*_kl(p,m)+0.5*_kl(q,m)
    return 1.0/(1.0+js)

# ---------- compact “wave-text” encoder ----------
ALPH = "abcdefghijklmnopqrstuvwxyz0123456789"
def wave_to_text(vec: List[float], k: int = 6) -> str:
    """Quantize feature vector into stable short code (for logs only)."""
    if not vec: return "…"
    out=[]
    for i,v in enumerate(vec[:k]):
        idx=int(max(0,min(len(ALPH)-1, round(v*(len(ALPH)-1)))))
        out.append(ALPH[idx])
    return "".join(out)
