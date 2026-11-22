"""RuneCore/1 learned next-Rion transition baseline (NOT an LLM).

Synthetic ring transitions only. No physical electron trajectories, molecular
forces, real-world scientific claims, owner authority, or hidden source data.
The evaluator holds out entire ring structures AND unseen ring widths.
"""
from __future__ import annotations
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
import argparse
import json
import random
from runecore_language import Ring

SCHEMA = "runecore.next-rion-baseline.v1"
STATUS = "TRAINED_SYNTHETIC_SYMBOLIC_BASELINE_NOT_LLM"


def rotation_key(seed: str) -> str:
    if not seed or set(seed) - {"0", "1"}:
        raise ValueError("binary string required")
    return min(seed[i:] + seed[:i] for i in range(len(seed)))


def generate(widths: range, *, examples_per_width: int = 24,
             seed: int = 923) -> tuple[dict, ...]:
    """Synthetic Ring.at labels; disjoint width ranges => structure holdout."""
    if examples_per_width < 1 or examples_per_width > 200:
        raise ValueError("invalid synthetic dataset bound")
    rng = random.Random(seed)
    records = []
    for width in widths:
        if width < 3 or width > 32:
            raise ValueError("unsupported ring width")
        used = set()
        attempts = 0
        while len(used) < examples_per_width:
            attempts += 1
            if attempts > examples_per_width * 2000:
                raise ValueError("not enough unique rotation classes")
            bits = "".join(str(rng.randrange(2)) for _ in range(width))
            if bits.count("1") in (0, width):
                continue
            key = rotation_key(bits)
            if key in used:
                continue
            used.add(key)
            structure = sha256(f"{width}:{key}".encode()).hexdigest()
            for direction, index in (("CW", 1), ("CCW", 2)):
                ring = Ring(index, direction, bits)
                for tick in (0, 1, 2, 3):
                    records.append({
                        "source": "SYNTHETIC_RING_AT_INTERPRETER",
                        "structure": structure,
                        "width": width,
                        "direction": direction,
                        "current": ring.at(tick),
                        "next": ring.at(tick + 1),
                    })
    return tuple(records)


def _features(direction: str, bits: str, position: int) -> str:
    if direction not in ("CW", "CCW") or not bits or set(bits) - {"0", "1"}:
        raise ValueError("invalid predictor input")
    i, n = position, len(bits)
    if i < 0 or i >= n:
        raise ValueError("out of range")
    return f"{direction}:{bits[(i-1)%n]}{bits[i]}{bits[(i+1)%n]}"


def fit(records: tuple[dict, ...]) -> dict:
    votes: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    structures = set()
    for record in records:
        if record["source"] != "SYNTHETIC_RING_AT_INTERPRETER":
            raise ValueError("unknown or unlicensed training provenance")
        x, y, direction = record["current"], record["next"], record["direction"]
        if len(x) != len(y) or not x:
            raise ValueError("invalid transition")
        structures.add(record["structure"])
        for i, bit in enumerate(y):
            votes[_features(direction, x, i)][int(bit)] += 1
    if not votes:
        raise ValueError("empty model")
    return {
        "schema": SCHEMA, "classification": STATUS,
        "training_structures": len(structures),
        "provenance": "SYNTHETIC_NONCANONICAL",
        "counts": {k: votes[k] for k in sorted(votes)},
    }


def predict(model: dict, direction: str, bits: str) -> str:
    if model.get("schema") != SCHEMA or model.get("classification") != STATUS:
        raise ValueError("unverified model")
    result = []
    for i in range(len(bits)):
        counts = model["counts"].get(_features(direction, bits, i))
        if not counts or sum(counts) == 0:
            result.append("?")  # Honest unknown, never fake confidence.
        else:
            result.append(str(int(counts[1] > counts[0])))
    return "".join(result)


def evaluate(model: dict, test: tuple[dict, ...], train: tuple[dict, ...]) -> dict:
    train_ids = {x["structure"] for x in train}
    test_ids = {x["structure"] for x in test}
    if train_ids & test_ids:
        raise ValueError("DATA_LEAKAGE_SAME_STRUCTURE")
    train_widths = {x["width"] for x in train}
    test_widths = {x["width"] for x in test}
    if train_widths & test_widths:
        raise ValueError("DATA_LEAKAGE_SAME_WIDTH")
    total = correct = copied = unknown = exact = 0
    for item in test:
        predicted = predict(model, item["direction"], item["current"])
        target = item["next"]
        total += len(target)
        correct += sum(a == b for a, b in zip(predicted, target))
        copied += sum(a == b for a, b in zip(item["current"], target))
        unknown += predicted.count("?")
        exact += predicted == target
    if not total:
        raise ValueError("empty evaluation")
    return {
        "classification": STATUS,
        "training_structures": len(train_ids),
        "heldout_structures": len(test_ids),
        "train_widths": sorted(train_widths),
        "heldout_widths": sorted(test_widths),
        "heldout_sequences": len(test),
        "learned_bit_accuracy": correct / total,
        "copy_baseline_accuracy": copied / total,
        "learned_exact_sequences": exact,
        "unknown_bits": unknown,
        "deterministic_oracle_accuracy": 1.0,
        "scope": "GENERATED_ROTATING_BITS_NOT_REAL_LANGUAGE_OR_PHYSICS",
    }


def experiment() -> tuple[dict, dict]:
    train = generate(range(6, 13), examples_per_width=20, seed=17)
    heldout = generate(range(13, 19), examples_per_width=20, seed=29)
    model = fit(train)
    return model, evaluate(model, heldout, train)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a tiny RuneCore symbolic baseline")
    parser.add_argument("--out", type=Path, help="optional output model file")
    args = parser.parse_args()
    model, metrics = experiment()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(model, sort_keys=True, indent=2), encoding="utf-8")
    print(json.dumps(metrics, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
