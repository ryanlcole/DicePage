from pathlib import Path
import unittest


class RegionMapPersistenceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")

    def test_region_post_writes_regionmap_not_worldsource(self):
        start = self.source.index('if method == "POST" and path == "/world/source/region":')
        end = self.source.index('if method == "GET" and path == "/world/regions":', start)
        block = self.source[start:end]
        self.assertIn("region_map_key(world_id, region_id)", block)
        self.assertIn('":entityType": "regionMap"', block)
        self.assertIn('"format": "RIST_REGION_MAP_V1"', block)
        self.assertNotIn("world.update_item(\n            Key=world_source_key(world_id)", block)

    def test_region_get_reads_regionmap_with_legacy_fallback(self):
        start = self.source.index('if method == "GET" and path == "/world/source/region":')
        end = self.source.index('if method == "POST" and path == "/world/source/region":', start)
        block = self.source[start:end]
        self.assertIn("Key=region_map_key(world_id, region_id)", block)
        self.assertIn("region_map_state = None", block)
        self.assertIn("parent_state, region_map_state", block)

    def test_parcel_release_archives_and_deletes_regionmap(self):
        self.assertIn("region_map_item = world.get_item(", self.source)
        self.assertIn('"Key": region_map_key(world_id, region_id)', self.source)


if __name__ == "__main__":
    unittest.main()
