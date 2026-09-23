import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from region_geometry import region_cell_for_point


class RegionGeometryTests(unittest.TestCase):
    def test_hex_visible_centers_resolve_to_original_selected_cell_ids(self):
        width, height = 30 * .75 + .25, 30 + .5
        for col, row in ((0,0), (1,0), (2,15), (19,10), (29,29)):
            x = (col * .75 + .5) / width
            y = (row + (col % 2) * .5 + .5) / height
            self.assertEqual(region_cell_for_point(x,y,"hex"), row * 30 + col)

    def test_square_region_coordinates_unchanged(self):
        self.assertEqual(region_cell_for_point(.5,.5,"square"), 15*30+15)

    def test_not_row_staggered(self):
        col, row = 19, 10
        x = (col*.75+.5)/(30*.75+.25)
        y = (row+.5+.5)/(30+.5)
        self.assertEqual(region_cell_for_point(x,y,"hex"),319)


if __name__ == "__main__":
    unittest.main()
