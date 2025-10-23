# relic_analyzer.py — ReLiC Intelligence Analyzer (waveforms → glyph classes)
from __future__ import annotations
from typing import List, Dict, Any, Optional
import os, json, time, random
from waveform_core import (now_ms, synth_tone, synth_chirp,
                           energy, bandpass_bins, frame_histogram,
                           cosine, jensen_shannon, wave_to_text)

STORE = os.path.join("logs","patterns")
os.makedirs(STORE, exist_ok=True)

# ------- WaveGlyph data model -------
# A class = {id, kind: 'audio'|'video', centroid: [floats], members: int, labels: [str]}
def _store_path(kind:str)->str: return os.path.join(STORE, f"{kind}_patterns.json")

def _load(kind:str)->List[Dict[str,Any]]:
    p=_store_path(kind)
    if not os.path.exists(p): return []
    try: return json.load(open(p,"r",encoding="utf-8"))
    except: return []

def _save(kind:str, arr:List[Dict[str,Any]]):
    json.dump(arr, open(_store_path(kind),"w",encoding="utf-8"), indent=2)

# ------- ingestion helpers -------
def ingest_audio(samples: List[float], sr: int = 16000, label: Optional[str]=None)->Dict[str,Any]:
    vec = bandpass_bins(samples, sr, bins=12)
    feat = {"kind":"audio","ts":now_ms(),"vec":vec,"energy":energy(samples),
            "label":label or "unlabeled","code":wave_to_text(vec, k=8)}
    return feat

def ingest_video_frame(rgb_frame)->Dict[str,Any]:
    vec = frame_histogram(rgb_frame, buckets=12)
    feat={"kind":"video","ts":now_ms(),"vec":vec,"label":"unlabeled","code":wave_to_text(vec, k=8)}
    return feat

# ------- learning (common denominators) -------
SIM_T = 0.92   # threshold to join a class
def _similarity(a:List[float], b:List[float])->float:
    return 0.5*cosine(a,b)+0.5*jensen_shannon(a,b)

def learn(kind:str, feat:Dict[str,Any])->Dict[str,Any]:
    classes=_load(kind)
    # find best match
    best_i, best_s = -1, 0.0
    for i,c in enumerate(classes):
        s=_similarity(c["centroid"], feat["vec"])
        if s>best_s: best_s, best_i = s, i
    if best_s>=SIM_T and best_i>=0:
        # update centroid (running mean)
        c=classes[best_i]
        n=max(1, int(c.get("members",1)))
        new=[(ci*n + vi)/(n+1) for ci,vi in zip(c["centroid"], feat["vec"])]
        c["centroid"]=new
        c["members"]=n+1
        if feat.get("label"): c.setdefault("labels",[]).append(feat["label"])
        _save(kind, classes)
        return {"joined": c["id"], "similarity": round(best_s,3), "members": c["members"], "code": wave_to_text(new,8)}
    else:
        # create a new class
        cid=f"{kind}-{len(classes)+1:04d}"
        node={"id":cid,"kind":kind,"centroid":feat["vec"],"members":1,"labels":[feat.get('label',"seed")]}
        classes.append(node); _save(kind, classes)
        return {"created": cid, "members": 1, "code": wave_to_text(feat["vec"],8)}

def list_patterns(kind:str)->List[Dict[str,Any]]:
    return _load(kind)

# ------- built-in “browser” placeholders -------
# Real implementation can plug: requests + yt-dlp + librosa/opencv frame readers.
def fetch_demo(kind:str="audio")->Dict[str,Any]:
    if kind=="audio":
        f = synth_tone(random.choice([220,330,440,660]), dur_s=0.6)
        return ingest_audio(f, label="tone")
    else:
        # fake frame: random colored dots -> brightness histogram
        import random
        frame=[(random.randint(0,255),random.randint(0,255),random.randint(0,255)) for _ in range(600)]
        return ingest_video_frame(frame)
