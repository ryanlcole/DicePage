import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from region_projection import project


class RegionProjectionTests(unittest.TestCase):
    def setUp(self):
        self.deed = {"tierIndex": 1, "gridShape": "square",
                     "parentNodeId": "world:world-a",
                     "selectedCells": [31, 32],
                     "sourceLayerOffsets": [0, 1, 2]}
        self.world = {
            "worldId": "world-a",
            "tierImages": ["", "https://assets.example/full-world.png"],
            "sourceTileIndex": [
                {"cellIndex": 31, "tierIndex": 1, "layerOffset": 0, "image": "selected-31.webp"},
                {"cellIndex": 32, "tierIndex": 1, "layerOffset": 1, "image": "selected-32.webp"},
                {"cellIndex": 33, "tierIndex": 1, "layerOffset": 0, "image": "secret-33.webp"},
                {"cellIndex": 31, "tierIndex": 0, "layerOffset": 0, "image": "other-tier.webp"}],
            "tiles": [
                {"id": "lake", "tierIndex": 1, "layerOffset": 1, "x": 1.5/30, "y": 1.5/30},
                {"id": "elsewhere", "tierIndex": 1, "layerOffset": 1, "x": 15.5/30, "y": 15.5/30}],
            "userLayers": [
                {"id": "city", "regionId": "region-a", "tier": 1},
                {"id": "other-owner", "regionId": "region-b", "tier": 1}],
        }

    def test_only_selected_source_tiles_cross_projection_boundary(self):
        result = project("world-a", "region-a", self.deed, self.world)
        self.assertEqual([x["id"] for x in result["tiles"]], ["lake"])
        self.assertEqual([x["image"] for x in result["sourceTileIndex"]],
                         ["selected-31.webp", "selected-32.webp"])
        self.assertNotIn("tierImages", result)
        self.assertEqual(result["parentTierIndex"], 1)
        self.assertEqual([x["cellIndex"] for x in result["sourceCells"]], [31,32])
        self.assertEqual(result["userLayers"][0]["relativeTier"], 0)

    def test_child_map_is_separate_but_keeps_world_parent_id(self):
        child = {"userLayers": [{"id": "city", "relativeTier": 2, "regionId": "region-a"}],
                 "relativeTiers": [{"id": "region-a:tier:2", "index": 2}]}
        result = project("world-a", "region-a", self.deed, self.world, child)
        self.assertEqual(result["userLayers"], child["userLayers"])
        self.assertEqual(result["relativeTiers"], child["relativeTiers"])
        self.assertEqual(result["parentNodeId"], "world:world-a")

    def test_legacy_full_world_bitmap_cannot_be_delivered_to_region(self):
        self.world["sourceTileIndex"] = []
        result = project("world-a", "region-a", self.deed, self.world)
        self.assertTrue(result["requiresRasterIndex"])
        self.assertTrue(result["sourceBitmapWasOmitted"])
        self.assertNotIn("full-world.png", repr(result))

    def test_empty_or_corrupted_deed_fails_closed(self):
        for cells in ([], [-1, 1000]):
            with self.assertRaises(ValueError):
                project("world-a", "region-a", {**self.deed, "selectedCells": cells}, self.world)


if __name__ == "__main__":
    unittest.main()
