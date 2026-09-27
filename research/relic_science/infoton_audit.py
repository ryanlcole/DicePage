#!/usr/bin/env python3
"""Deterministic audit helpers for January Walker / Infoton claims.

This module does not decide whether the Infoton hypothesis is physically true.
It separates algebraic identity from independently predictive evidence.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass

BOLTZMANN = 1.380649e-23
LIGHT_SPEED = 299_792_458.0
PLANCK = 6.62607015e-34
ELEMENTARY_CHARGE = 1.602176634e-19
LN2 = math.log(2.0)


def landauer_energy(temperature_k: float) -> float:
    if temperature_k <= 0:
        raise ValueError("temperature must be > 0 K")
    return BOLTZMANN * temperature_k * LN2


def infoton_mass(temperature_k: float) -> float:
    return landauer_energy(temperature_k) / (LIGHT_SPEED ** 2)


def temperature_for_mass(mass_kg: float) -> float:
    if mass_kg <= 0:
        raise ValueError("mass must be > 0 kg")
    return mass_kg * (LIGHT_SPEED ** 2) / (BOLTZMANN * LN2)


def identity_intercept_log10() -> float:
    return math.log10((LIGHT_SPEED ** 2) / (BOLTZMANN * LN2))


def identity_residual(mass_kg: float) -> float:
    """Residual after deriving T from the same mass.

    This should be ~0 by construction and therefore is not an independent
    validation of the hypothesis.
    """
    t = temperature_for_mass(mass_kg)
    return math.log10(t) - math.log10(mass_kg) - identity_intercept_log10()


def photon_equivalent_mass(wavelength_m: float) -> float:
    if wavelength_m <= 0:
        raise ValueError("wavelength must be > 0 m")
    return PLANCK / (wavelength_m * LIGHT_SPEED)


def photon_landauer_bit_ratio(wavelength_m: float, temperature_k: float) -> float:
    """Photon energy divided by the Landauer erasure bound per bit."""
    photon_energy = PLANCK * LIGHT_SPEED / wavelength_m
    return photon_energy / landauer_energy(temperature_k)


def energy_equivalent_frequency(voltage_v: float) -> float:
    """f = eV / h.

    This is an energy-equivalent frequency. It is not evidence that a biological
    system physically oscillates at this frequency.
    """
    if voltage_v < 0:
        raise ValueError("voltage must be >= 0")
    return ELEMENTARY_CHARGE * voltage_v / PLANCK


def p30_arithmetic_reduction(before: int = 584, after: int = 3) -> float:
    if before <= 0 or after < 0 or after > before:
        raise ValueError("require 0 <= after <= before and before > 0")
    return 100.0 * (1.0 - after / before)


@dataclass(frozen=True)
class AuditResult:
    claim: str
    numerical_result: object
    evidence_class: str
    conclusion: str


def audit() -> list[AuditResult]:
    electron_mass = 9.1093837139e-31
    proton_mass = 1.67262192595e-27
    arbitrary_mass = 1.23456789e-20

    return [
        AuditResult(
            claim="Infoton log10 temperature-mass line",
            numerical_result={
                "intercept": identity_intercept_log10(),
                "electronResidual": identity_residual(electron_mass),
                "protonResidual": identity_residual(proton_mass),
                "arbitraryMassResidual": identity_residual(arbitrary_mass),
            },
            evidence_class="ALGEBRAIC_IDENTITY",
            conclusion=(
                "When T is computed from m using T = mc^2/(k_B ln2), every positive mass "
                "lies on the same log line by construction. Agreement of known masses with "
                "that line is therefore not an independent prediction."
            ),
        ),
        AuditResult(
            claim="P30 584-to-3 reduction",
            numerical_result={"countReductionPercent": p30_arithmetic_reduction()},
            evidence_class="ARITHMETIC_ONLY",
            conclusion=(
                "The percentage follows from the two asserted counts. It does not establish "
                "equivalent workload, actual instruction counts, heat, water use, or measured "
                "electrical energy reduction."
            ),
        ),
        AuditResult(
            claim="150 mV mitochondrial energy-equivalent frequency",
            numerical_result={
                "voltageV": 0.150,
                "frequencyHz": energy_equivalent_frequency(0.150),
                "frequencyTHz": energy_equivalent_frequency(0.150) / 1e12,
            },
            evidence_class="UNIT_CONVERSION",
            conclusion=(
                "e*V/h maps an electrochemical energy scale to a frequency scale. The "
                "calculation alone does not demonstrate a physical mitochondrial oscillator "
                "or spectral peak at that frequency."
            ),
        ),
        AuditResult(
            claim="700 nm photon Landauer-bit ratio at 2.725 K",
            numerical_result={
                "ratio": photon_landauer_bit_ratio(700e-9, 2.725),
                "equivalentMassKg": photon_equivalent_mass(700e-9),
            },
            evidence_class="DERIVED_RATIO",
            conclusion=(
                "The ratio is reproducible from photon energy and the Landauer bound, but "
                "calling the quotient a measured number of physical information particles "
                "requires independent experimental evidence."
            ),
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    payload = {"results": [asdict(x) for x in audit()]}
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
