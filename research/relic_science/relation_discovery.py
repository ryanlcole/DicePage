#!/usr/bin/env python3
"""Unsupervised typed-relation discovery for ReLiC scientific experiments.

Candidate relations are generated from observations only. Hidden reference
relations are used solely by the evaluation step, never by discovery.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import statistics
from pathlib import Path
from typing import Any


def _finite(value: Any) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3 or len(xs) != len(ys):
        return None
    mx = statistics.fmean(xs)
    my = statistics.fmean(ys)
    dx = [x - mx for x in xs]
    dy = [y - my for y in ys]
    den = math.sqrt(sum(x*x for x in dx) * sum(y*y for y in dy))
    if not den:
        return None
    return sum(x*y for x, y in zip(dx, dy)) / den


def discover_numeric_relations(
    observations: list[dict[str, Any]],
    *,
    min_support: int = 3,
    min_abs_correlation: float = 0.70,
) -> list[dict[str, Any]]:
    """Discover correlations without access to any relation labels."""
    keys = sorted({
        key
        for row in observations
        for key, value in (row.get("features") or {}).items()
        if _finite(value) is not None
    })
    candidates: list[dict[str, Any]] = []
    for left, right in itertools.combinations(keys, 2):
        xs: list[float] = []
        ys: list[float] = []
        for row in observations:
            features = row.get("features") or {}
            x = _finite(features.get(left))
            y = _finite(features.get(right))
            if x is None or y is None:
                continue
            xs.append(x)
            ys.append(y)
        if len(xs) < min_support:
            continue
        r = _pearson(xs, ys)
        if r is None or abs(r) < min_abs_correlation:
            continue
        candidates.append({
            "left": left,
            "relation": "correlates_with",
            "right": right,
            "direction": "positive" if r >= 0 else "negative",
            "score": abs(r),
            "signedCorrelation": r,
            "support": len(xs),
            "truthDomain": "HYPOTHESIS",
            "provenance": "derived-from-observations",
        })
    candidates.sort(key=lambda x: (-x["score"], -x["support"], x["left"], x["right"]))
    return candidates


def _pair_key(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((str(left), str(right))))


def evaluate_hidden_relations(
    candidates: list[dict[str, Any]],
    hidden_relations: list[dict[str, Any]],
    *,
    top_k: int | None = None,
) -> dict[str, Any]:
    """Evaluate discovery after hidden relations are revealed."""
    predicted = candidates[:top_k] if top_k else candidates
    predicted_pairs = {_pair_key(x["left"], x["right"]) for x in predicted}
    truth_pairs = {
        _pair_key(x["left"], x["right"])
        for x in hidden_relations
        if x.get("left") is not None and x.get("right") is not None
    }
    tp = len(predicted_pairs & truth_pairs)
    fp = len(predicted_pairs - truth_pairs)
    fn = len(truth_pairs - predicted_pairs)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    return {
        "candidateCount": len(predicted_pairs),
        "hiddenRelationCount": len(truth_pairs),
        "truePositive": tp,
        "falsePositive": fp,
        "falseNegative": fn,
        "precision": precision,
        "recall": recall,
        "boundary": (
            "Discovery used observations only. Hidden relations were consulted only after "
            "candidate generation. Unmatched candidates remain HYPOTHESIS."
        ),
    }


def _load(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="ReLiC unsupervised relation discovery")
    sub = parser.add_subparsers(dest="command", required=True)

    discover = sub.add_parser("discover")
    discover.add_argument("observations_json")
    discover.add_argument("--min-support", type=int, default=3)
    discover.add_argument("--min-correlation", type=float, default=0.70)

    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("candidates_json")
    evaluate.add_argument("hidden_relations_json")
    evaluate.add_argument("--top-k", type=int)

    args = parser.parse_args()
    if args.command == "discover":
        rows = _load(args.observations_json)
        result = discover_numeric_relations(
            rows,
            min_support=args.min_support,
            min_abs_correlation=args.min_correlation,
        )
    else:
        result = evaluate_hidden_relations(
            _load(args.candidates_json),
            _load(args.hidden_relations_json),
            top_k=args.top_k,
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
