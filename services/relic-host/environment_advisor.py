"""Advisory-only environment analysis for ReLiC Projects.

Telemetry is supplied by an authorized connector/agent. This module does not
probe hardware, change process priority, throttle workloads, terminate
processes, or rewrite code. Thresholds are project/operator policy inputs; they
are not universal claims about safe hardware operating limits.
"""
from __future__ import annotations

from typing import Any


def analyze(snapshot: dict[str, Any], policy: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    policy = policy or {}
    warnings: list[dict[str, Any]] = []

    cpu = snapshot.get("cpu_percent")
    memory = snapshot.get("memory_percent")
    disk = snapshot.get("disk_percent")
    temp = snapshot.get("temperature_c")
    cores = snapshot.get("logical_cores")
    process_cpu = snapshot.get("process_cpu_percent")

    _threshold_warning(warnings, "MEMORY_PRESSURE", memory, policy.get("memory_warn_percent"),
                       "Consider partitioning/bounding the workload or reducing concurrency.")
    _threshold_warning(warnings, "DISK_PRESSURE", disk, policy.get("disk_warn_percent"),
                       "Reduce temporary output or provision capacity before continuing growth.")
    _threshold_warning(warnings, "THERMAL_POLICY", temp, policy.get("temperature_warn_c"),
                       "Configured thermal warning threshold was reached; consider reducing concurrency or workload rate.")

    if (
        isinstance(cpu, (int, float)) and isinstance(process_cpu, (int, float))
        and isinstance(cores, int) and cores > 1
        and cpu < policy.get("underuse_cpu_percent", 35)
        and process_cpu < policy.get("underuse_process_cpu_percent", 120)
    ):
        warnings.append({
            "code": "POSSIBLE_COMPUTE_UNDERUSE",
            "severity": "OPTIMIZATION",
            "fact": "Observed utilization is below configured optimization thresholds.",
            "inference": "Additional parallelism may be useful if profiling shows CPU-bound independent work.",
            "recommendation": "Profile first; do not rewrite or parallelize solely from utilization telemetry.",
            "hardware_harm_established": False,
        })

    bottleneck = snapshot.get("profile_bottleneck")
    if bottleneck:
        warnings.append({
            "code": "PROFILE_BOTTLENECK",
            "severity": "OPTIMIZATION",
            "fact": f"Profiler-reported bottleneck: {bottleneck}",
            "recommendation": "Compare algorithm, library/vectorization, concurrency, native extension, accelerator, and language alternatives using benchmarks before a language rewrite.",
            "language_change_justified": False,
        })

    return warnings


def _threshold_warning(
    warnings: list[dict[str, Any]],
    code: str,
    observed: Any,
    threshold: Any,
    recommendation: str,
) -> None:
    if not isinstance(observed, (int, float)) or not isinstance(threshold, (int, float)):
        return
    if observed < threshold:
        return
    warnings.append({
        "code": code,
        "severity": "WARNING",
        "fact": f"Observed value {observed} reached configured threshold {threshold}.",
        "recommendation": recommendation,
        "hardware_harm_established": False,
        "threshold_source": "PROJECT_OR_OPERATOR_POLICY",
    })
