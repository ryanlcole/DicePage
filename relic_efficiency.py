"""Privacy-preserving recursion and efficiency evidence for ReLiC.

The raw user question is not stored in this ledger. A keyed HMAC fingerprint
lets the same deployment recognize repeated requests without exposing plaintext
or a reusable unsalted hash.

Energy claims require measured joules from both the baseline and ReLiC path.
When those measurements are absent, ReLiC may report compute/context reduction
only and MUST NOT label it energy savings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import hmac
import json
import math
import statistics
from typing import Any, Iterable, Mapping


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")


def request_fingerprint(question: str, secret: bytes) -> str:
    """Return a keyed one-way identifier; plaintext question is never returned."""

    if not secret:
        raise ValueError("fingerprint secret is required")
    normalized = " ".join(str(question).split())
    return "rq." + hmac.new(secret, normalized.encode("utf-8"), sha256).hexdigest()


@dataclass(frozen=True)
class RecursionStep:
    id: str
    parent_id: str | None
    operation: str
    semantic_ids: tuple[str, ...] = ()
    cache_hit: bool = False
    model_call: bool = False
    tool_call: bool = False
    input_bytes: int = 0
    output_bytes: int = 0
    elapsed_ns: int | None = None
    measured_joules: float | None = None

    def __post_init__(self) -> None:
        if self.input_bytes < 0 or self.output_bytes < 0:
            raise ValueError("byte counts cannot be negative")
        if self.measured_joules is not None and self.measured_joules < 0:
            raise ValueError("measured joules cannot be negative")

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "parentId": self.parent_id,
            "operation": self.operation,
            "semanticIds": list(self.semantic_ids),
            "cacheHit": self.cache_hit,
            "modelCall": self.model_call,
            "toolCall": self.tool_call,
            "inputBytes": self.input_bytes,
            "outputBytes": self.output_bytes,
            "elapsedNs": self.elapsed_ns,
            "measuredJoules": self.measured_joules,
        }


@dataclass
class RecursionTrace:
    request_fingerprint: str
    semantic_request_id: str
    steps: list[RecursionStep] = field(default_factory=list)

    def add(self, step: RecursionStep) -> None:
        if any(existing.id == step.id for existing in self.steps):
            raise ValueError(f"duplicate recursion step id: {step.id}")
        if step.parent_id is not None and not any(existing.id == step.parent_id for existing in self.steps):
            raise ValueError(f"unknown recursion parent: {step.parent_id}")
        self.steps.append(step)

    def summary(self) -> dict[str, Any]:
        reused = sorted({
            semantic_id
            for step in self.steps
            if step.cache_hit
            for semantic_id in step.semantic_ids
        })
        return {
            "format": "ReLiC-Recursion-Trace",
            "version": 1,
            "requestFingerprint": self.request_fingerprint,
            "semanticRequestId": self.semantic_request_id,
            "rawQuestionStored": False,
            "steps": [step.as_dict() for step in self.steps],
            "totals": {
                "stepCount": len(self.steps),
                "cacheHits": sum(1 for step in self.steps if step.cache_hit),
                "modelCalls": sum(1 for step in self.steps if step.model_call),
                "toolCalls": sum(1 for step in self.steps if step.tool_call),
                "inputBytes": sum(step.input_bytes for step in self.steps),
                "outputBytes": sum(step.output_bytes for step in self.steps),
                "measuredJoules": (
                    sum(step.measured_joules or 0.0 for step in self.steps)
                    if all(step.measured_joules is not None for step in self.steps)
                    else None
                ),
            },
            "reusedSemanticIds": reused,
        }


@dataclass(frozen=True)
class TrialMeasurement:
    wall_time_ns: int
    cpu_time_ns: int | None = None
    peak_memory_bytes: int | None = None
    input_bytes: int | None = None
    output_bytes: int | None = None
    model_calls: int | None = None
    tool_calls: int | None = None
    measured_joules: float | None = None
    quality_score: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "wallTimeNs": self.wall_time_ns,
            "cpuTimeNs": self.cpu_time_ns,
            "peakMemoryBytes": self.peak_memory_bytes,
            "inputBytes": self.input_bytes,
            "outputBytes": self.output_bytes,
            "modelCalls": self.model_calls,
            "toolCalls": self.tool_calls,
            "measuredJoules": self.measured_joules,
            "qualityScore": self.quality_score,
        }


def _percent_reduction(baseline: float | int | None, relic: float | int | None) -> float | None:
    if baseline is None or relic is None or baseline <= 0:
        return None
    return (float(baseline) - float(relic)) / float(baseline) * 100.0


def compare_trial_pair(
    baseline: TrialMeasurement,
    relic: TrialMeasurement,
    *,
    minimum_quality_ratio: float = 0.98,
) -> dict[str, Any]:
    """Compare one matched baseline/ReLiC trial without overstating energy."""

    if baseline.quality_score is not None and relic.quality_score is not None:
        quality_equivalent = (
            baseline.quality_score == 0
            or relic.quality_score / baseline.quality_score >= minimum_quality_ratio
        )
    else:
        quality_equivalent = None

    energy_measured = baseline.measured_joules is not None and relic.measured_joules is not None
    energy_saved_joules = (
        baseline.measured_joules - relic.measured_joules if energy_measured else None
    )
    energy_saved_percent = _percent_reduction(
        baseline.measured_joules,
        relic.measured_joules,
    ) if energy_measured else None

    return {
        "format": "ReLiC-Efficiency-Trial",
        "version": 1,
        "baseline": baseline.as_dict(),
        "relic": relic.as_dict(),
        "qualityEquivalent": quality_equivalent,
        "minimumQualityRatio": minimum_quality_ratio,
        "computeEvidence": {
            "wallTimeReductionPercent": _percent_reduction(baseline.wall_time_ns, relic.wall_time_ns),
            "cpuTimeReductionPercent": _percent_reduction(baseline.cpu_time_ns, relic.cpu_time_ns),
            "peakMemoryReductionPercent": _percent_reduction(baseline.peak_memory_bytes, relic.peak_memory_bytes),
            "inputByteReductionPercent": _percent_reduction(baseline.input_bytes, relic.input_bytes),
            "outputByteReductionPercent": _percent_reduction(baseline.output_bytes, relic.output_bytes),
            "modelCallReductionPercent": _percent_reduction(baseline.model_calls, relic.model_calls),
            "toolCallReductionPercent": _percent_reduction(baseline.tool_calls, relic.tool_calls),
        },
        "energyEvidence": {
            "status": "MEASURED" if energy_measured else "UNMEASURED",
            "baselineJoules": baseline.measured_joules,
            "relicJoules": relic.measured_joules,
            "savedJoules": energy_saved_joules,
            "savedPercent": energy_saved_percent,
            "claimAllowed": bool(
                energy_measured
                and energy_saved_joules is not None
                and energy_saved_joules > 0
                and quality_equivalent is not False
            ),
        },
    }


def aggregate_energy_trials(trials: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate only trials that contain measured baseline and ReLiC joules."""

    savings: list[float] = []
    percentages: list[float] = []
    for trial in trials:
        energy = trial.get("energyEvidence") or {}
        if energy.get("status") != "MEASURED":
            continue
        baseline = energy.get("baselineJoules")
        relic = energy.get("relicJoules")
        if baseline is None or relic is None or baseline <= 0:
            continue
        savings.append(float(baseline) - float(relic))
        percentages.append((float(baseline) - float(relic)) / float(baseline) * 100.0)

    if not savings:
        return {
            "status": "UNMEASURED",
            "measuredTrials": 0,
            "claimAllowed": False,
        }

    mean_saved = statistics.fmean(savings)
    mean_percent = statistics.fmean(percentages)
    stdev = statistics.stdev(percentages) if len(percentages) > 1 else 0.0
    sem = stdev / math.sqrt(len(percentages)) if percentages else 0.0
    ci95 = 1.96 * sem

    return {
        "status": "MEASURED",
        "measuredTrials": len(savings),
        "meanSavedJoules": mean_saved,
        "meanSavedPercent": mean_percent,
        "ci95PercentPoints": ci95,
        "claimAllowed": mean_saved > 0,
    }
