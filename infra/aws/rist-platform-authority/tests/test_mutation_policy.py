import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mutation_policy import (
    canonical_piece_state,
    canonical_tile_state,
    dynamo_safe,
    protects_piece,
    protects_tile,
)


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


class TileMutationPolicyTests(unittest.TestCase):
    def payload(self, **overrides):
        base = {
            "entityType": "tile",
            "placementId": "tile-abc123",
            "assetId": "terrain.ocean.deep",
            "name": "Deep ocean",
            "typeId": "ocean.depth.5",
            "assetKind": "tile",
            "shaepId": "shaep-0123456789abcdef0123456789abcdef",
            "authoredDepth": True,
            "x": 0.10,
            "y": 0.20,
            "placementZoom": 2.0,
            "cubeX": 3,
            "cubeY": 4,
            "cubeZ": 0,
            "planeIndex": 0,
            "tierIndex": 1,
            "layerOffset": 2,
            "rotationQuarterTurns": 0,
            "placementTreatment": "normal",
            "zoneId": "zone-a",
            "zoneLabel": "Shelf",
            "locked": False,
        }
        base.update(overrides)
        return base

    def test_only_manager_can_create_tile(self):
        with self.assertRaises(PermissionError):
            canonical_tile_state("tile.create", "tile-abc123", self.payload(), None, manager=False)

        state = canonical_tile_state("tile.create", "tile-abc123", self.payload(), None, manager=True)
        self.assertEqual(state["placementId"], "tile-abc123")
        self.assertEqual(state["assetId"], "terrain.ocean.deep")
        self.assertEqual(state["x"], Decimal("0.1"))
        self.assertFalse(state["removed"])

    def test_tile_update_preserves_immutable_semantic_identity(self):
        current = canonical_tile_state("tile.create", "tile-abc123", self.payload(), None, manager=True)
        tampered = self.payload(
            assetId="fake.asset",
            name="Fake",
            typeId="fake.type",
            shaepId="shaep-ffffffffffffffffffffffffffffffff",
            authoredDepth=False,
            x=0.75,
            y=0.8,
            placementZoom=4,
            rotationQuarterTurns=3,
            locked=True,
            zoneId="zone-b",
            zoneLabel="Updated",
        )
        updated = canonical_tile_state("tile.update", "tile-abc123", tampered, current, manager=False)
        self.assertEqual(updated["assetId"], "terrain.ocean.deep")
        self.assertEqual(updated["name"], "Deep ocean")
        self.assertEqual(updated["typeId"], "ocean.depth.5")
        self.assertEqual(updated["shaepId"], "shaep-0123456789abcdef0123456789abcdef")
        self.assertTrue(updated["authoredDepth"])
        self.assertEqual(updated["x"], Decimal("0.75"))
        self.assertEqual(updated["y"], Decimal("0.8"))
        self.assertEqual(updated["rotationQuarterTurns"], 3)
        self.assertTrue(updated["locked"])
        self.assertEqual(updated["zoneId"], "zone-b")
        self.assertEqual(updated["zoneLabel"], "Updated")

    def test_tile_remove_is_server_derived_tombstone(self):
        current = canonical_tile_state("tile.create", "tile-abc123", self.payload(), None, manager=True)
        removed = canonical_tile_state("tile.remove", "tile-abc123", self.payload(assetId="fake", x=0.99), current)
        self.assertTrue(removed["removed"])
        self.assertEqual(removed["assetId"], "terrain.ocean.deep")
        self.assertEqual(removed["x"], Decimal("0.1"))
        with self.assertRaises(ValueError):
            canonical_tile_state("tile.update", "tile-abc123", self.payload(), removed, manager=True)

    def test_tile_contracts_fail_closed(self):
        with self.assertRaises(ValueError):
            canonical_tile_state("tile.create", "tile-other", self.payload(), None, manager=True)
        with self.assertRaises(ValueError):
            canonical_tile_state("tile.rename", "tile-abc123", self.payload(), None, manager=True)
        with self.assertRaises(ValueError):
            canonical_tile_state("tile.create", "tile-abc123", self.payload(x=-0.01), None, manager=True)
        with self.assertRaises(ValueError):
            canonical_tile_state("tile.create", "tile-abc123", self.payload(rotationQuarterTurns=4), None, manager=True)
        with self.assertRaises(ValueError):
            canonical_tile_state("tile.remove", "tile-abc123", self.payload(), None, manager=True)

    def test_tile_entities_cannot_escape_tile_action_semantics(self):
        current = {"entityType": "tile", "placementId": "tile-abc123"}
        self.assertTrue(protects_tile("update", "tile-abc123", None))
        self.assertTrue(protects_tile("tile.update", "other", None))
        self.assertTrue(protects_tile("update", "other", current))
        self.assertFalse(protects_tile("update", "piece-1", {"entityType": "piece"}))


class SharedMutationPolicyTests(unittest.TestCase):
    def test_generic_float_payloads_are_dynamodb_safe(self):
        converted = dynamo_safe({"x": 0.5, "nested": [1.25, {"y": 2.5}]})
        self.assertEqual(converted["x"], Decimal("0.5"))
        self.assertEqual(converted["nested"][0], Decimal("1.25"))
        self.assertEqual(converted["nested"][1]["y"], Decimal("2.5"))


if __name__ == "__main__":
    unittest.main()
