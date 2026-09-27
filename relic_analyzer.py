# 052506.python.relic_analyzer.line1.comment relic_analyzer.py — ReLiC Intelligence Analyzer (waveforms → glyph classes)
from __future__ import annotations
from typing import List, Dict, Any, Optional
import os, json, time, random
from waveform_core import (now_ms, synth_tone, synth_chirp,
                           energy, bandpass_bins, frame_histogram,
                           cosine, jensen_shannon, wave_to_text)

STORE = os.path.join("logs","patterns")
os.makedirs(STORE, exist_ok=True)

# 052507.python.relic_analyzer.line12.comment ------- WaveGlyph data model -------
# 052508.python.relic_analyzer.line13.comment A class = {id, kind: 'audio'|'video', centroid: [floats], members: int, labels: [str]}
def _store_path(kind:str)->str: return os.path.join(STORE, f"{kind}_patterns.json")

def _load(kind:str)->List[Dict[str,Any]]:
    p=_store_path(kind)
    if not os.path.exists(p): return []
    try: return json.load(open(p,"r",encoding="utf-8"))
    except: return []

def _save(kind:str, arr:List[Dict[str,Any]]):
    json.dump(arr, open(_store_path(kind),"w",encoding="utf-8"), indent=2)

# 052509.python.relic_analyzer.line25.comment ------- ingestion helpers -------
def ingest_audio(samples: List[float], sr: int = 16000, label: Optional[str]=None)->Dict[str,Any]:
    vec = bandpass_bins(samples, sr, bins=12)
    feat = {"kind":"audio","ts":now_ms(),"vec":vec,"energy":energy(samples),
            "label":label or "unlabeled","code":wave_to_text(vec, k=8)}
    return feat

def ingest_video_frame(rgb_frame)->Dict[str,Any]:
    vec = frame_histogram(rgb_frame, buckets=12)
    feat={"kind":"video","ts":now_ms(),"vec":vec,"label":"unlabeled","code":wave_to_text(vec, k=8)}
    return feat

# 052510.python.relic_analyzer.line37.comment ------- learning (common denominators) -------
SIM_T = 0.92   # threshold to join a class
def _similarity(a:List[float], b:List[float])->float:
    return 0.5*cosine(a,b)+0.5*jensen_shannon(a,b)

def learn(kind:str, feat:Dict[str,Any])->Dict[str,Any]:
    classes=_load(kind)
    # 052512.python.relic_analyzer.line44.comment find best match
    best_i, best_s = -1, 0.0
    for i,c in enumerate(classes):
        s=_similarity(c["centroid"], feat["vec"])
        if s>best_s: best_s, best_i = s, i
    if best_s>=SIM_T and best_i>=0:
        # 052513.python.relic_analyzer.line50.comment update centroid (running mean)
        c=classes[best_i]
        n=max(1, int(c.get("members",1)))
        new=[(ci*n + vi)/(n+1) for ci,vi in zip(c["centroid"], feat["vec"])]
        c["centroid"]=new
        c["members"]=n+1
        if feat.get("label"): c.setdefault("labels",[]).append(feat["label"])
        _save(kind, classes)
        return {"joined": c["id"], "similarity": round(best_s,3), "members": c["members"], "code": wave_to_text(new,8)}
    else:
        # 052514.python.relic_analyzer.line60.comment create a new class
        cid=f"{kind}-{len(classes)+1:04d}"
        node={"id":cid,"kind":kind,"centroid":feat["vec"],"members":1,"labels":[feat.get('label',"seed")]}
        classes.append(node); _save(kind, classes)
        return {"created": cid, "members": 1, "code": wave_to_text(feat["vec"],8)}

def list_patterns(kind:str)->List[Dict[str,Any]]:
    return _load(kind)

# 052515.python.relic_analyzer.line69.comment ------- built-in “browser” placeholders -------
# 052516.python.relic_analyzer.line70.comment Real implementation can plug: requests + yt-dlp + librosa/opencv frame readers.
def fetch_demo(kind:str="audio")->Dict[str,Any]:
    if kind=="audio":
        f = synth_tone(random.choice([220,330,440,660]), dur_s=0.6)
        return ingest_audio(f, label="tone")
    else:
        # 052517.python.relic_analyzer.line76.comment fake frame: random colored dots -> brightness histogram
        import random
        frame=[(random.randint(0,255),random.randint(0,255),random.randint(0,255)) for _ in range(600)]
        return ingest_video_frame(frame)


# ------- Rune/Glyph/Shaep system weakness analysis -------------------------
# This path is deterministic and structured. Natural-language observations may
# be supplied by an AI source, but the analyzer does not silently promote them
# to FACT or mutate the analyzed system.

from relic_core import Glyph, Rune, Weakness, build_shaep

CANON_FIXES = {
    "duplicate_identity": (
        "RELIC.IDENTITY.REUSE_BEFORE_DUPLICATE",
        "Resolve the existing stable semantic identity and attach the new representation/observation to it.",
    ),
    "fact_without_provenance": (
        "RELIC.PROVENANCE.PERSISTENT",
        "Attach adequate source provenance or downgrade the claim to UNKNOWN/HYPOTHESIS.",
    ),
    "representation_as_truth": (
        "RELIC.REPRESENTATION.NOT_TRUTH",
        "Separate the representation from the represented identity/state and validate the underlying truth independently.",
    ),
    "authority_gap": (
        "RELIC.AUTH.AMBIGUITY_DENIES",
        "Obtain an explicit capability/authority path before the state-changing action is allowed.",
    ),
    "human_harm": (
        "RELIC.SAFETY.HUMAN_NONHARM",
        "Deny the machine action and redesign it so the machine is not authorized to harm a human.",
    ),
    "ecological_harm": (
        "RELIC.SAFETY.ECOLOGICAL_COUNTERMEASURE",
        "Prefer prevention; otherwise require a credible, proportionate, monitorable countermeasure and explicit residual-risk review.",
    ),
    "unproven_scope": (
        "RELIC.VERIFICATION.PROOF_WITHIN_FIVE_MINUTES",
        "Report only the scope actually observed. Publish verifiable proof within five minutes or mark the broader claim UNKNOWN and alert.",
    ),
}


def _weakness(kind: str, summary: str, evidence: list[str], *, severity: str = "review") -> Weakness:
    canon_id, remediation = CANON_FIXES[kind]
    digest = __import__("hashlib").sha256(
        (kind + "|" + summary + "|" + "|".join(sorted(evidence))).encode("utf-8")
    ).hexdigest()[:20]
    return Weakness(
        id=f"weakness-{digest}",
        category=kind,
        summary=summary,
        evidence_runes=tuple(evidence),
        canon_ids=(canon_id,),
        severity=severity,
        remediation=remediation,
    )


def analyze_system_manifest(manifest: Dict[str, Any], now_unix_ms: Optional[int] = None) -> Dict[str, Any]:
    """Analyze a structured system description and return a canon-grounded Shaep.

    Expected sections are intentionally generic: identities, claims, actions,
    and changes. The analyzer reports weaknesses; it does not rewrite the
    target system or treat its own report as authority.
    """
    system_id = str(manifest.get("systemId") or manifest.get("name") or "unknown-system")
    now_ms = int(now_unix_ms if now_unix_ms is not None else time.time() * 1000)
    shaep = build_shaep(system_id, [])

    identities = manifest.get("identities") or []
    semantic_keys: Dict[str, List[str]] = {}
    for item in identities:
        identity_id = str(item.get("id") or "").strip()
        semantic_key = str(item.get("semanticKey") or "").strip()
        if not identity_id:
            continue
        rune_id = f"rune.system.identity.{identity_id}"
        shaep.add_rune(Rune(rune_id, item, "UNKNOWN", str(item.get("provenance") or "UNKNOWN")))
        if semantic_key:
            semantic_keys.setdefault(semantic_key, []).append(identity_id)

    for semantic_key, ids in semantic_keys.items():
        if len(set(ids)) > 1:
            evidence = [f"rune.system.identity.{x}" for x in ids]
            shaep.report_weakness(_weakness(
                "duplicate_identity",
                f"Multiple identities claim semantic key {semantic_key}: {', '.join(ids)}",
                evidence,
            ))

    for index, claim in enumerate(manifest.get("claims") or []):
        claim_id = str(claim.get("id") or f"claim-{index}")
        domain = str(claim.get("truthDomain") or "UNKNOWN")
        provenance = str(claim.get("provenance") or "UNKNOWN")
        rune_id = f"rune.system.claim.{claim_id}"
        shaep.add_rune(Rune(rune_id, claim, domain if domain in {"FACT","HYPOTHESIS","FICTION","UNKNOWN"} else "UNKNOWN", provenance))
        if domain == "FACT" and provenance in {"", "UNKNOWN", "None", "null"}:
            shaep.report_weakness(_weakness(
                "fact_without_provenance",
                f"Claim {claim_id} is marked FACT without adequate provenance.",
                [rune_id],
            ))
        if bool(claim.get("representationOnly")) and domain == "FACT":
            shaep.report_weakness(_weakness(
                "representation_as_truth",
                f"Claim {claim_id} promotes a representation to factual state.",
                [rune_id],
            ))

    for index, action in enumerate(manifest.get("actions") or []):
        action_id = str(action.get("id") or f"action-{index}")
        rune_id = f"rune.system.action.{action_id}"
        shaep.add_rune(Rune(rune_id, action, "HYPOTHESIS", str(action.get("provenance") or "SYSTEM")))
        if bool(action.get("changesState")) and str(action.get("authority") or "") != "explicit-capability":
            shaep.report_weakness(_weakness(
                "authority_gap",
                f"State-changing action {action_id} lacks an explicit authority capability.",
                [rune_id],
                severity="block",
            ))
        if bool(action.get("humanHarmRisk")):
            shaep.report_weakness(_weakness(
                "human_harm",
                f"Machine action {action_id} carries a declared human-harm risk.",
                [rune_id],
                severity="block",
            ))
        if bool(action.get("ecologicalHarm")) and not action.get("countermeasure"):
            shaep.report_weakness(_weakness(
                "ecological_harm",
                f"Action {action_id} has foreseeable ecological harm without a countermeasure.",
                [rune_id],
                severity="block",
            ))

    for index, change in enumerate(manifest.get("changes") or []):
        change_id = str(change.get("id") or f"change-{index}")
        rune_id = f"rune.system.change.{change_id}"
        shaep.add_rune(Rune(rune_id, change, "UNKNOWN", str(change.get("provenance") or "SYSTEM")))
        claimed_scope = str(change.get("claimedScope") or "unknown").lower()
        proven_scope = str(change.get("provenScope") or "unknown").lower()
        created_ms = int(change.get("createdAtUnixMs") or now_ms)
        proof_at_ms = change.get("proofAtUnixMs")
        overdue = (now_ms - created_ms) > 300_000 and proof_at_ms is None
        scope_mismatch = claimed_scope == "global" and proven_scope != "global"
        if overdue or scope_mismatch:
            reason = "proof deadline exceeded" if overdue else f"proven scope is only {proven_scope}"
            shaep.report_weakness(_weakness(
                "unproven_scope",
                f"Change {change_id} claims {claimed_scope} effect but {reason}.",
                [rune_id],
                severity="alert",
            ))

    evidence_runes = tuple(sorted(shaep.runes))
    if evidence_runes:
        shaep.add_glyph(Glyph(
            id=f"glyph.system.analysis.{system_id}",
            rune_ids=evidence_runes,
            relation="analyzed_under_relic_canon",
            truth_domain="UNKNOWN",
        ))

    result = shaep.as_dict()
    result["reportingBoundary"] = {
        "mode": "analyze-report-propose",
        "mutatesTargetSystem": False,
        "canonIsGuidanceUnlessTargetAdoptsIt": True,
        "unknownIsPreserved": True,
    }
    result["alertCount"] = sum(1 for w in shaep.weaknesses if w.severity in {"alert", "block"})
    return result
