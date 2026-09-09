from __future__ import annotations

import importlib.util
import io
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))
SPEC = importlib.util.spec_from_file_location(
    "terrain_asset_repair",
    APP_ROOT / "terrain_asset_repair.py",
)
assert SPEC and SPEC.loader
repair = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repair)


class TerrainAssetRepairTests(unittest.TestCase):
    def test_regular_sheet_yields_36_inset_panels(self) -> None:
        boxes = repair._regular_grid_boxes(1254, 1254)

        self.assertEqual(36, len(boxes))
        self.assertEqual((25, 25, 184, 184), boxes[0])
        self.assertEqual((1070, 1070, 1229, 1229), boxes[-1])

    def test_irregular_sheet_splits_only_on_complete_gutters(self) -> None:
        dark = np.zeros((300, 300), dtype=bool)
        dark[145:155, :] = True
        dark[:, 145:155] = True

        boxes = repair._recursive_separator_boxes(dark, 0.95)

        self.assertCountEqual(
            [(0, 0, 145, 145), (155, 0, 300, 145), (0, 155, 145, 300), (155, 155, 300, 300)],
            boxes,
        )

    def test_saved_ocean_texture_wraps_after_jpeg_encoding(self) -> None:
        size = 159
        yy, xx = np.mgrid[0:size, 0:size]
        vignette = 72 - 26 * ((xx - size / 2) ** 2 + (yy - size / 2) ** 2) / (size**2 / 2)
        waves = 18 * np.sin(yy / 3.7) + 7 * np.sin((xx + yy) / 8.0)
        pixels = np.stack((vignette + waves + 45, vignette + waves + 22, vignette + waves), axis=2)
        source = Image.fromarray(np.uint8(np.clip(pixels, 0, 255)))

        seamless = repair._seamless_texture(source)
        encoded = io.BytesIO()
        seamless.save(encoded, "JPEG", quality=95, subsampling=0)
        encoded.seek(0)
        with Image.open(encoded) as reopened:
            self.assertLess(repair._edge_error(reopened), 4.0)
            self.assertLess(repair._seam_band_error(reopened), 2.0)


if __name__ == "__main__":
    unittest.main()
