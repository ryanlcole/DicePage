import json
import unittest
from runecore_language import Ring
from next_pattern_model import (
    SCHEMA, STATUS, rotation_key, generate, fit, predict, evaluate, experiment
)


class NextPatternTests(unittest.TestCase):
    def test_training_is_deterministic_and_reproducible(self):
        a, report_a = experiment()
        b, report_b = experiment()
        self.assertEqual(a, b)
        self.assertEqual(report_a, report_b)
        self.assertEqual(a["schema"], SCHEMA)
        self.assertEqual(a["classification"], STATUS)

    def test_unseen_ring_widths_and_structures(self):
        _, report = experiment()
        self.assertFalse(set(report["train_widths"]) & set(report["heldout_widths"]))
        self.assertGreater(report["heldout_structures"], 0)
        self.assertGreater(report["heldout_sequences"], 500)
        self.assertEqual(report["unknown_bits"], 0)
        self.assertEqual(report["learned_bit_accuracy"], 1.0)
        self.assertEqual(report["learned_exact_sequences"], report["heldout_sequences"])
        self.assertGreater(report["learned_bit_accuracy"], report["copy_baseline_accuracy"])
        self.assertEqual(report["scope"], "GENERATED_ROTATING_BITS_NOT_REAL_LANGUAGE_OR_PHYSICS")

    def test_hydrogen_and_oxygen_bit_patterns_without_chemistry_claim(self):
        model, _ = experiment()
        for ring in (Ring(1, "CW", "1000"),
                     Ring(1, "CW", "1010"),
                     Ring(2, "CCW", "11101110")):
            for step in range(ring.repeat() * 2):
                self.assertEqual(
                    predict(model, ring.direction, ring.at(step)),
                    ring.at(step + 1),
                )

    def test_rotate_equivalence_is_separated_by_width(self):
        self.assertEqual(rotation_key("1000"), rotation_key("0100"))
        self.assertNotEqual(rotation_key("1000"), rotation_key("10000"))
        with self.assertRaises(ValueError):
            rotation_key("010X")

    def test_leakage_guard_rejects_shared_structure_and_shared_width(self):
        train = generate(range(7, 8), examples_per_width=4, seed=5)
        m = fit(train)
        with self.assertRaisesRegex(ValueError, "DATA_LEAKAGE_SAME_STRUCTURE"):
            evaluate(m, train, train)
        another = generate(range(7, 8), examples_per_width=4, seed=19)
        # Even with different sampled structures, reusing train width is rejected.
        try:
            evaluate(m, another, train)
        except ValueError as exc:
            self.assertTrue(str(exc).startswith("DATA_LEAKAGE_"))
        else:
            self.fail("Expected leakage guard")

    def test_trainable_weights_change_when_labels_change(self):
        train = generate(range(7, 8), examples_per_width=5, seed=7)
        first = fit(train)
        altered = tuple({**x, "next": "0" * len(x["next"])} for x in train)
        second = fit(altered)
        self.assertNotEqual(first["counts"], second["counts"])

    def test_serialized_weights_round_trip(self):
        model, _ = experiment()
        loaded = json.loads(json.dumps(model))
        self.assertEqual(loaded, model)
        self.assertEqual(predict(loaded, "CW", "00101"),
                         predict(model, "CW", "00101"))

    def test_unseen_feature_reports_unknown_not_invented_prediction(self):
        empty = {"schema": SCHEMA, "classification": STATUS, "counts": {}}
        self.assertEqual(predict(empty, "CW", "11001"), "?????")
        with self.assertRaises(ValueError):
            predict({"schema": "FAKE", "counts": {}}, "CW", "11001")

    def test_bad_training_provenance_is_rejected(self):
        rec = generate(range(7, 8), examples_per_width=1)
        bad = tuple({**x, "source": "PRIVATE_OWNER_RECORD"} for x in rec)
        with self.assertRaisesRegex(ValueError, "provenance"):
            fit(bad)

    def test_untrained_helper_does_not_change_rune_slots(self):
        train = generate(range(8, 9), examples_per_width=4, seed=27)
        before = json.dumps(train, sort_keys=True)
        _ = fit(train)
        self.assertEqual(json.dumps(train, sort_keys=True), before)


if __name__ == "__main__":
    unittest.main()
