import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mutation_policy import canonical_piece_state, dynamo_safe, protects_piece


class PieceMutationPolicyTests(unittest.TestCase):
    def payload(self, **overrides):
        base = {
            "entityType": "piece",
            "pieceId": "abc123",
            "kind": "mini",
            "label": "Scout",
            "x": 0.25,
            "y": 0.75,
            "placementZoom": 1.0,
            "cubeX": 1,
            "cubeY": 2,
            "cubeZ": 3,
            "planeIndex": 0,
            "tierIndex": 1,
            "layerOffset": 2,
        }
        base.update(overrides)
        return base

    def test_only_manager_can_create_piece_through_move(self):
        with self.assertRaises(PermissionError):
            canonical_piece_state("piece.move", "piece-abc123", self.payload(), None, manager=False)

        state = canonical_piece_state("piece.move", "piece-abc123", self.payload(), None, manager=True)
        self.assertEqual(state["kind"], "mini")
        self.assertEqual(state["label"], "Scout")
        self.assertEqual(state["x"], Decimal("0.25"))
        self.assertFalse(state["removed"])

    def test_move_preserves_immutable_piece_fields(self):
        current = canonical_piece_state("piece.move", "piece-abc123", self.payload(), None, manager=True)
        tampered = self.payload(kind="dragon", label="Changed", x=0.5, y=0.5)
        moved = canonical_piece_state("piece.move", "piece-abc123", tampered, current, manager=False)
        self.assertEqual(moved["kind"], "mini")
        self.assertEqual(moved["label"], "Scout")
        self.assertEqual(moved["x"], Decimal("0.5"))
        self.assertEqual(moved["y"], Decimal("0.5"))

    def test_remove_is_server_derived_tombstone(self):
        current = canonical_piece_state("piece.move", "piece-abc123", self.payload(), None, manager=True)
        removed = canonical_piece_state("piece.remove", "piece-abc123", self.payload(x=0.99, kind="fake"), current)
        self.assertTrue(removed["removed"])
        self.assertEqual(removed["kind"], "mini")
        self.assertEqual(removed["x"], Decimal("0.25"))
        with self.assertRaises(ValueError):
            canonical_piece_state("piece.move", "piece-abc123", self.payload(), removed, manager=True)

    def test_identity_action_and_coordinate_contracts_fail_closed(self):
        with self.assertRaises(ValueError):
            canonical_piece_state("piece.move", "piece-other", self.payload(), None, manager=True)
        with self.assertRaises(ValueError):
            canonical_piece_state("piece.rename", "piece-abc123", self.payload(), None, manager=True)
        with self.assertRaises(ValueError):
            canonical_piece_state("piece.move", "piece-abc123", self.payload(x=1.01), None, manager=True)
        with self.assertRaises(ValueError):
            canonical_piece_state("piece.remove", "piece-abc123", self.payload(), None, manager=True)

    def test_piece_entities_cannot_escape_piece_action_semantics(self):
        current = {"entityType": "piece", "pieceId": "abc123"}
        self.assertTrue(protects_piece("update", "piece-abc123", None))
        self.assertTrue(protects_piece("piece.move", "other", None))
        self.assertTrue(protects_piece("update", "other", current))
        self.assertFalse(protects_piece("update", "tile-1", {"entityType": "tile"}))

    def test_generic_float_payloads_are_dynamodb_safe(self):
        converted = dynamo_safe({"x": 0.5, "nested": [1.25, {"y": 2.5}]})
        self.assertEqual(converted["x"], Decimal("0.5"))
        self.assertEqual(converted["nested"][0], Decimal("1.25"))
        self.assertEqual(converted["nested"][1]["y"], Decimal("2.5"))


if __name__ == "__main__":
    unittest.main()
