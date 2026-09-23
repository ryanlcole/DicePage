"""Offline roundtrip test for the official source-cell extraction pipeline."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from region_source_tiles import extract_one, build_tiles, COLS, ROWS
from PIL import Image


class TileExtractionTests(unittest.TestCase):
    def test_square_source_cell_is_not_neighboring_pixel_data(self):
        image = Image.new("RGB", (300,300), (255,0,0))
        image.paste((0,0,255), (10,10,30,30))
        patch = extract_one(image,31,"square")
        self.assertEqual(patch.size, (10,10))
        self.assertEqual(patch.getpixel((5,5)), (0,0,255,255))

    def test_flat_top_hex_has_transparent_corners_and_real_center(self):
        image = Image.new("RGB", (910,1220), (50,100,150))
        patch = extract_one(image,31,"hex")
        self.assertEqual(patch.getpixel((0,0))[3], 0)
        self.assertEqual(patch.getpixel((patch.width//2,patch.height//2))[3],255)

    def test_asset_id_is_exact_parent_cell_and_tier(self):
        with tempfile.TemporaryDirectory() as root:
            img = Image.new("RGB",(300,300),(10,20,30))
            source=Path(root)/"world.png";img.save(source)
            count=build_tiles(source,Path(root)/"tiles",1)
            self.assertEqual(count,2*COLS*ROWS)
            self.assertTrue((Path(root)/"tiles"/"hex"/"1"/"031.webp").is_file())
            self.assertTrue((Path(root)/"tiles"/"square"/"1"/"031.webp").is_file())


if __name__=="__main__":
    unittest.main()
