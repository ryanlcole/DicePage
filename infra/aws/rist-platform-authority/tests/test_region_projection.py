import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from region_projection import merge_region_layers, project, region_z100


class RegionProjectionTests(unittest.TestCase):
    def setUp(self):
        self.deed = {
            "tierIndex": 1,
            "gridShape": "square",
            "parentNodeId": "world:world-a",
            "selectedCells": [31, 32],
            "sourceLayerOffsets": [0, 1, 2],
        }
        self.world = {
            "worldId": "world-a",
            "tierImages": ["", "https://assets.example/full-world.png"],
            "sourceTileIndex": [
                {"cellIndex": 31, "tierIndex": 1, "layerOffset": 0, "image": "selected-31.webp"},
                {"cellIndex": 32, "tierIndex": 1, "layerOffset": 1, "image": "selected-32.webp"},
                {"cellIndex": 33, "tierIndex": 1, "layerOffset": 0, "image": "secret-33.webp"},
                {"cellIndex": 31, "tierIndex": 0, "layerOffset": 0, "image": "other-tier.webp"},
            ],
            "tiles": [
                {"id": "lake", "tierIndex": 1, "layerOffset": 1, "x": 1.5 / 30, "y": 1.5 / 30},
                {"id": "elsewhere", "tierIndex": 1, "layerOffset": 1, "x": 15.5 / 30, "y": 15.5 / 30},
            ],
            "userLayers": [
                {
                    "id": "world-road",
                    "tier": 1,
                    "layer": 2,
                    "x": 1.5 / 30,
                    "y": 1.5 / 30,
                    "kind": "image",
                    "originalSrc": "road.webp",
                },
                {
                    "id": "city",
                    "regionId": "region-a",
                    "tier": 1,
                    "worldLayer": 2,
                    "layer": 2,
                    "regionLayer": 1,
                    "z100": 201,
                    "x": 1.5 / 30,
                    "y": 1.5 / 30,
                    "kind": "image",
                    "originalSrc": "city.webp",
                },
                {
                    "id": "other-region",
                    "regionId": "region-b",
                    "tier": 1,
                    "worldLayer": 2,
                    "layer": 2,
                    "regionLayer": 1,
                    "z100": 201,
                    "x": 1.5 / 30,
                    "y": 1.5 / 30,
                },
            ],
        }

    def test_only_selected_worldbuilder_coordinates_cross_projection(self):
        result = project("world-a", "region-a", self.deed, self.world)
        self.assertEqual(result["projection"], "region-world-z-v2")
        self.assertEqual([x["id"] for x in result["tiles"]], ["lake"])
        self.assertEqual(
            [x["image"] for x in result["sourceTileIndex"]],
            ["selected-31.webp", "selected-32.webp"],
        )
        self.assertNotIn("tierImages", result)
        self.assertEqual(result["parentTierIndex"], 1)
        self.assertEqual([x["cellIndex"] for x in result["sourceCells"]], [31, 32])
        self.assertEqual([x["id"] for x in result["sourceUserLayers"]], ["world-road"])
        self.assertEqual([x["id"] for x in result["userLayers"]], ["city"])
        self.assertEqual(result["userLayers"][0]["z100"], 201)
        self.assertEqual(result["userLayers"][0]["parallaxMode"], "anchored")

    def test_regionmap_child_state_overrides_legacy_parent_overlay(self):
        child = {
            "format": "RIST_REGION_MAP_V1",
            "worldId": "world-a",
            "regionId": "region-a",
            "userLayers": [{
                "id": "child-city",
                "regionId": "region-a",
                "tier": 1,
                "worldLayer": 3,
                "layer": 3,
                "regionLayer": 2,
                "z100": 302,
                "x": 1.5 / 30,
                "y": 1.5 / 30,
                "kind": "image",
                "originalSrc": "child.webp",
            }],
        }
        result = project("world-a", "region-a", self.deed, self.world, child)
        self.assertEqual([x["id"] for x in result["userLayers"]], ["child-city"])
        self.assertEqual(result["userLayers"][0]["z100"], 302)

    def test_existing_empty_regionmap_clears_legacy_parent_overlay(self):
        child = {
            "format": "RIST_REGION_MAP_V1",
            "worldId": "world-a",
            "regionId": "region-a",
            "userLayers": [],
        }
        result = project("world-a", "region-a", self.deed, self.world, child)
        self.assertEqual(result["userLayers"], [])

    def test_region_z_is_exact_hundredth_above_world_z(self):
        self.assertEqual(region_z100(0, 1), 1)
        self.assertEqual(region_z100(0, 9), 9)
        self.assertEqual(region_z100(9, 1), 901)
        self.assertEqual(region_z100(9, 9), 909)
        with self.assertRaises(ValueError):
            region_z100(10, 1)
        with self.assertRaises(ValueError):
            region_z100(0, 10)

    def test_region_save_patches_worldbuilder_source_not_a_child_map(self):
        incoming = [{
            "id": "replacement-city",
            "regionId": "region-a",
            "tier": 1,
            "worldLayer": 4,
            "layer": 4,
            "regionLayer": 7,
            "z100": 407,
            "x": 1.5 / 30,
            "y": 1.5 / 30,
            "kind": "image",
            "originalSrc": "replacement.webp",
        }]
        merged, normalized = merge_region_layers(
            self.world, self.deed, "region-a", incoming
        )
        ids = [x["id"] for x in merged["userLayers"]]
        self.assertIn("world-road", ids)
        self.assertIn("other-region", ids)
        self.assertIn("replacement-city", ids)
        self.assertNotIn("city", ids)
        self.assertEqual(normalized[0]["z100"], 407)
        self.assertEqual(normalized[0]["tier"], 1)
        self.assertEqual(normalized[0]["worldLayer"], 4)
        self.assertEqual(normalized[0]["regionLayer"], 7)

    def test_overlay_cannot_escape_deed_or_selected_parent_tier(self):
        outside = {
            "id": "bad",
            "tier": 1,
            "worldLayer": 0,
            "regionLayer": 1,
            "x": .95,
            "y": .95,
        }
        with self.assertRaises(PermissionError):
            merge_region_layers(self.world, self.deed, "region-a", [outside])

        wrong_tier = {
            "id": "bad-tier",
            "tier": 0,
            "worldLayer": 0,
            "regionLayer": 1,
            "x": 1.5 / 30,
            "y": 1.5 / 30,
        }
        with self.assertRaises(PermissionError):
            merge_region_layers(self.world, self.deed, "region-a", [wrong_tier])

    def test_legacy_full_world_bitmap_is_not_delivered(self):
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
