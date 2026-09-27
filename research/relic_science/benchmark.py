#!/usr/bin/env python3
"""Minimal reproducible benchmark utilities for ReLiC science experiments."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import statistics
import time
import tracemalloc
from pathlib import Path
from typing import Any, Callable


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def lock_prediction(prediction: Any, commitment_path: Path, metadata: dict | None = None) -> dict:
    payload = {
        "format": "ReLiC-Prediction-Commitment",
        "version": 1,
        "createdAtUnixMs": int(time.time() * 1000),
        "sha256": sha256_value(prediction),
        "metadata": metadata or {},
    }
    commitment_path.parent.mkdir(parents=True, exist_ok=True)
    commitment_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def verify_prediction(prediction: Any, commitment: dict) -> bool:
    return sha256_value(prediction) == commitment.get("sha256")


def measure_call(fn: Callable, *args, measured_joules: float | None = None, **kwargs) -> tuple[Any, dict]:
    tracemalloc.start()
    wall0 = time.perf_counter_ns()
    cpu0 = time.process_time_ns()
    result = fn(*args, **kwargs)
    cpu_ns = time.process_time_ns() - cpu0
    wall_ns = time.perf_counter_ns() - wall0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    report = {
        "wallTimeNs": wall_ns,
        "cpuTimeNs": cpu_ns,
        "peakPythonAllocatedBytes": peak,
        "resultSerializedBytes": len(canonical_json(result)),
        "measuredJoules": measured_joules,
        "energyStatus": "MEASURED" if measured_joules is not None else "NOT_MEASURED",
    }
    return result, report


def _same_length(actual: list[float], predicted: list[float]) -> None:
    if not actual or len(actual) != len(predicted):
        raise ValueError("actual and predicted must be non-empty and the same length")


def score_vectors(actual: list[float], predicted: list[float]) -> dict:
    _same_length(actual, predicted)
    errors = [p - a for a, p in zip(actual, predicted)]
    mae = sum(abs(x) for x in errors) / len(errors)
    rmse = math.sqrt(sum(x * x for x in errors) / len(errors))

    mean_a = statistics.fmean(actual)
    mean_p = statistics.fmean(predicted)
    num = sum((a - mean_a) * (p - mean_p) for a, p in zip(actual, predicted))
    den_a = math.sqrt(sum((a - mean_a) ** 2 for a in actual))
    den_p = math.sqrt(sum((p - mean_p) ** 2 for p in predicted))
    pearson = num / (den_a * den_p) if den_a and den_p else None

    return {"n": len(actual), "mae": mae, "rmse": rmse, "pearson": pearson}


def load_json(path: str | os.PathLike) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="ReLiC blind-prediction benchmark helper")
    sub = parser.add_subparsers(dest="command", required=True)

    lock = sub.add_parser("lock")
    lock.add_argument("prediction_json")
    lock.add_argument("commitment_json")
    lock.add_argument("--experiment", default="")

    verify = sub.add_parser("verify")
    verify.add_argument("prediction_json")
    verify.add_argument("commitment_json")

    compare = sub.add_parser("compare")
    compare.add_argument("actual_json")
    compare.add_argument("predicted_json")

    args = parser.parse_args()

    if args.command == "lock":
        prediction = load_json(args.prediction_json)
        out = lock_prediction(
            prediction,
            Path(args.commitment_json),
            {"experiment": args.experiment} if args.experiment else {},
        )
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0

    if args.command == "verify":
        ok = verify_prediction(load_json(args.prediction_json), load_json(args.commitment_json))
        print(json.dumps({"verified": ok}))
        return 0 if ok else 1

    if args.command == "compare":
        actual = [float(x) for x in load_json(args.actual_json)]
        predicted = [float(x) for x in load_json(args.predicted_json)]
        print(json.dumps(score_vectors(actual, predicted), indent=2, sort_keys=True))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
