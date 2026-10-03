#!/usr/bin/env python3
"""Public, non-interventional cancer-immunology hypothesis screen.

This analysis tests an association in public bulk RNA-seq data. It does not
alter cells, propose a clinical treatment, or establish a cure.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple
from urllib.parse import quote

import numpy as np
import pandas as pd
import requests
from scipy.stats import mannwhitneyu, spearmanr
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API = "https://www.cbioportal.org/api"
STUDY_ID = "skcm_tcga_pan_can_atlas_2018"
SAMPLE_LIST_ID = STUDY_ID + "_all"

GROUPS: Dict[str, List[str]] = {
    "anomaly_visibility": [
        "MICA", "MICB", "ULBP1", "ULBP2", "ULBP3",
        "HLA-A", "HLA-B", "HLA-C", "B2M",
    ],
    "danger_context_proxy": ["CALR", "HMGB1", "IFNB1", "CXCL10"],
    "cytotoxic_activity": ["CD8A", "NKG7", "GNLY", "GZMB", "PRF1", "IFNG"],
    "immune_evasion": ["CD274", "IDO1", "LGALS9"],
}


@dataclass
class Corr:
    name: str
    rho: float
    p: float
    ci_low: float
    ci_high: float
    n: int
    q: float = math.nan


def session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers["User-Agent"] = "ReLiC-public-immune-error-signal-screen/1.0"
    return s


def get_json(s: requests.Session, path: str, params=None):
    r = s.get(API + path, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def choose_expression_profile(profiles: Iterable[dict]) -> dict:
    candidates = [
        p for p in profiles
        if p.get("molecularAlterationType") == "MRNA_EXPRESSION"
        and p.get("datatype") == "CONTINUOUS"
    ]
    if not candidates:
        raise RuntimeError("No continuous mRNA expression profile found.")

    def score(p: dict) -> Tuple[int, str]:
        pid = (p.get("molecularProfileId") or "").lower()
        text = " ".join(str(p.get(k) or "") for k in ("name", "description")).lower()
        points = 0
        if "rna_seq_v2_mrna" in pid:
            points += 8
        if "rsem" in text or "rsem" in pid:
            points += 4
        if "batch" in text:
            points += 2
        if "zscore" in pid or "z-score" in text or "z score" in text:
            points -= 20
        return points, pid

    return max(candidates, key=score)


def resolve_gene(s: requests.Session, symbol: str) -> dict:
    gene = get_json(s, "/genes/" + quote(symbol))
    if not gene or "entrezGeneId" not in gene:
        raise RuntimeError(f"Could not resolve gene {symbol}")
    return gene


def fetch_expression(s: requests.Session, profile_id: str, symbol: str, entrez: int) -> pd.Series:
    rows = get_json(
        s,
        f"/molecular-profiles/{quote(profile_id)}/molecular-data",
        params={
            "entrezGeneId": int(entrez),
            "projection": "SUMMARY",
            "sampleListId": SAMPLE_LIST_ID,
        },
    )
    values = {}
    for row in rows:
        sample = row.get("sampleId")
        value = row.get("value")
        if sample is None or value is None:
            continue
        try:
            values[str(sample)] = float(value)
        except (TypeError, ValueError):
            pass
    if len(values) < 20:
        raise RuntimeError(f"Too few expression values for {symbol}: {len(values)}")
    return pd.Series(values, name=symbol, dtype=float)


def zscore(series: pd.Series) -> pd.Series:
    clean = series.astype(float)
    # Raw cBioPortal RSEM is non-negative. If the selected continuous profile
    # contains any negatives, preserve its scale instead of applying log2.
    transformed = np.log2(clean + 1.0) if (clean.dropna() >= 0).all() else clean
    sd = transformed.std(ddof=0)
    if not np.isfinite(sd) or sd == 0:
        return transformed * np.nan
    return (transformed - transformed.mean()) / sd


def signature(frame: pd.DataFrame, genes: List[str]) -> pd.Series:
    present = [g for g in genes if g in frame.columns]
    if len(present) < max(2, math.ceil(len(genes) * 0.5)):
        raise RuntimeError(f"Insufficient genes for signature: {genes}; present={present}")
    block = frame[present]
    minimum = max(2, math.ceil(len(present) * 0.6))
    return block.mean(axis=1, skipna=True).where(block.notna().sum(axis=1) >= minimum)


def bootstrap_spearman(x: pd.Series, y: pd.Series, seed=20261002, n_boot=1200) -> Tuple[float, float]:
    pair = pd.concat([x, y], axis=1).dropna().to_numpy(dtype=float)
    if len(pair) < 20:
        return math.nan, math.nan
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(pair), len(pair))
        rho = spearmanr(pair[idx, 0], pair[idx, 1]).statistic
        if np.isfinite(rho):
            vals.append(float(rho))
    if not vals:
        return math.nan, math.nan
    return float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))


def corr(name: str, x: pd.Series, y: pd.Series, seed: int) -> Corr:
    pair = pd.concat([x, y], axis=1).dropna()
    stat = spearmanr(pair.iloc[:, 0], pair.iloc[:, 1])
    lo, hi = bootstrap_spearman(pair.iloc[:, 0], pair.iloc[:, 1], seed=seed)
    return Corr(name, float(stat.statistic), float(stat.pvalue), lo, hi, len(pair))


def bh_adjust(items: List[Corr]) -> None:
    ordered = sorted(enumerate(items), key=lambda it: it[1].p)
    m = len(items)
    adjusted = [math.nan] * m
    running = 1.0
    for rank_from_end, (original, item) in enumerate(reversed(ordered), start=1):
        rank = m - rank_from_end + 1
        value = min(running, item.p * m / rank)
        running = value
        adjusted[original] = value
    for item, q in zip(items, adjusted):
        item.q = float(min(1.0, q))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="research/immune-error-signal/out")
    args = parser.parse_args()
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    s = session()
    profiles = get_json(s, f"/studies/{STUDY_ID}/molecular-profiles")
    profile = choose_expression_profile(profiles)
    profile_id = profile["molecularProfileId"]

    all_symbols = sorted({g for genes in GROUPS.values() for g in genes})
    expression = {}
    gene_meta = {}
    failures = {}
    for symbol in all_symbols:
        try:
            gene = resolve_gene(s, symbol)
            gene_meta[symbol] = {
                "entrezGeneId": int(gene["entrezGeneId"]),
                "hugoGeneSymbol": gene.get("hugoGeneSymbol", symbol),
            }
            expression[symbol] = fetch_expression(
                s, profile_id, symbol, int(gene["entrezGeneId"])
            )
        except Exception as exc:
            failures[symbol] = str(exc)

    if len(expression) < 12:
        raise RuntimeError(f"Too few genes retrieved: {len(expression)}; failures={failures}")

    raw = pd.DataFrame(expression)
    normalized = pd.DataFrame({name: zscore(raw[name]) for name in raw.columns})

    scores = pd.DataFrame(index=normalized.index)
    for name, genes in GROUPS.items():
        scores[name] = signature(normalized, genes)

    scores["visibility_plus_danger"] = scores[["anomaly_visibility", "danger_context_proxy"]].mean(axis=1)

    tests = [
        corr("anomaly_visibility_vs_cytotoxic", scores["anomaly_visibility"], scores["cytotoxic_activity"], 1),
        corr("danger_context_proxy_vs_cytotoxic", scores["danger_context_proxy"], scores["cytotoxic_activity"], 2),
        corr("visibility_plus_danger_vs_cytotoxic", scores["visibility_plus_danger"], scores["cytotoxic_activity"], 3),
        corr("immune_evasion_vs_cytotoxic", scores["immune_evasion"], scores["cytotoxic_activity"], 4),
    ]
    bh_adjust(tests)

    pair = scores[["visibility_plus_danger", "cytotoxic_activity"]].dropna()
    q1 = pair["visibility_plus_danger"].quantile(0.25)
    q3 = pair["visibility_plus_danger"].quantile(0.75)
    low = pair.loc[pair["visibility_plus_danger"] <= q1, "cytotoxic_activity"]
    high = pair.loc[pair["visibility_plus_danger"] >= q3, "cytotoxic_activity"]
    mw = mannwhitneyu(high, low, alternative="two-sided")

    primary = next(t for t in tests if t.name == "visibility_plus_danger_vs_cytotoxic")
    classification = (
        "association-supported-in-this-cohort"
        if primary.rho > 0 and primary.q < 0.05 and primary.ci_low > 0
        else "association-not-established-in-this-cohort"
    )

    result = {
        "analysis": "ReLiC Immune Error Signal Screen",
        "status": classification,
        "studyId": STUDY_ID,
        "sampleListId": SAMPLE_LIST_ID,
        "molecularProfileId": profile_id,
        "profileName": profile.get("name"),
        "profileDescription": profile.get("description"),
        "sampleCountWithAnyExpression": int(raw.shape[0]),
        "genesRetrieved": sorted(expression),
        "geneFailures": failures,
        "geneMetadata": gene_meta,
        "signatures": GROUPS,
        "tests": [
            {
                "name": t.name,
                "spearmanRho": t.rho,
                "pValue": t.p,
                "fdrQ": t.q,
                "bootstrap95CI": [t.ci_low, t.ci_high],
                "n": t.n,
            }
            for t in tests
        ],
        "quartileComparison": {
            "lowN": int(len(low)),
            "highN": int(len(high)),
            "lowMedianCytotoxicScore": float(low.median()),
            "highMedianCytotoxicScore": float(high.median()),
            "mannWhitneyU": float(mw.statistic),
            "pValue": float(mw.pvalue),
        },
        "interpretationBoundary": [
            "Exploratory association only; it does not establish causation, treatment efficacy, or a cure.",
            "Bulk RNA-seq mixes tumor and immune-cell expression.",
            "CALR and HMGB1 transcript abundance is only a proxy and does not demonstrate extracellular release or immunogenic cell death.",
            "A positive association can reflect immune infiltration or shared inflammatory regulation rather than tumor-cell anomaly recognition.",
            "Independent cohorts and mechanistic experiments would be required before any therapeutic interpretation.",
        ],
        "source": {
            "portal": "cBioPortal",
            "api": API,
            "study": f"https://www.cbioportal.org/study/summary?id={STUDY_ID}",
        },
    }

    (out / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    scores.sort_index().to_csv(out / "sample_scores.csv", index_label="sampleId")

    lines = [
        "# ReLiC Immune Error Signal Screen",
        "",
        f"**Status:** {classification}",
        f"**Study:** {STUDY_ID}",
        f"**Expression profile:** {profile_id}",
        f"**Samples with retrieved expression:** {raw.shape[0]}",
        "",
        "## Question",
        "",
        "Do expression proxies for abnormal/stressed-cell visibility and danger context associate with stronger cytotoxic immune activity in public melanoma bulk RNA-seq data?",
        "",
        "## Correlations",
        "",
        "| Test | Spearman rho | 95% bootstrap CI | p | FDR q | n |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for t in tests:
        lines.append(
            f"| {t.name} | {t.rho:.3f} | [{t.ci_low:.3f}, {t.ci_high:.3f}] | {t.p:.3g} | {t.q:.3g} | {t.n} |"
        )
    lines += [
        "",
        "## Quartile comparison",
        "",
        f"High visibility+danger quartile median cytotoxic score: **{high.median():.3f}** (n={len(high)})",
        f"Low visibility+danger quartile median cytotoxic score: **{low.median():.3f}** (n={len(low)})",
        f"Mann-Whitney p: **{mw.pvalue:.3g}**",
        "",
        "## Interpretation boundary",
        "",
        "- This is an exploratory association screen, not evidence of a cure or treatment efficacy.",
        "- Bulk RNA-seq mixes tumor and immune-cell expression.",
        "- CALR/HMGB1 transcript abundance does not prove immunogenic-cell-death signaling.",
        "- Positive correlation can arise from immune infiltration or shared inflammatory regulation.",
        "- Independent replication and controlled mechanistic experiments would be required before therapeutic interpretation.",
        "",
        "## Data provenance",
        "",
        f"- cBioPortal study: https://www.cbioportal.org/study/summary?id={STUDY_ID}",
        f"- API: {API}",
        f"- Sample list: {SAMPLE_LIST_ID}",
        "",
    ]
    (out / "results.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
