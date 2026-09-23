"""Deterministic, per-cell immutable raster index for official Geonaph tiers.

The world bitmap is read only in the frontend build pipeline. Claimed-region
sessions fetch only their chosen cell-specific WebP assets, never the parent
PNG. This is a public asset registry, not a substitute for private uploaded
worlds' separately published tile indexes.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageChops

COLS = ROWS = 30


def cell_box(column, row, shape):
    if shape == "hex":
        return (column * .75, row + (column % 2) * .5,
                column * .75 + 1, row + (column % 2) * .5 + 1,
                COLS * .75 + .25, ROWS + .5)
    return (float(column), float(row), float(column+1), float(row+1),
            float(COLS), float(ROWS))


def extract_one(image, cell, shape):
    column, row = cell % COLS, cell // COLS
    left, top, right, bottom, span_x, span_y = cell_box(column, row, shape)
    px1 = round(left / span_x * image.width)
    py1 = round(top / span_y * image.height)
    px2 = round(right / span_x * image.width)
    py2 = round(bottom / span_y * image.height)
    patch = image.crop((px1, py1, max(px1 + 1, px2), max(py1 + 1, py2))).convert("RGBA")
    if shape == "hex":
        # Reuse RegionDefiner's exact flat-top source-cell geometry.
        width, height = patch.size
        mask = Image.new("L", patch.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.polygon([(width*.25, 0), (width*.75, 0), (width, height*.5),
                      (width*.75, height), (width*.25, height),
                      (0, height*.5)], fill=255)
        patch.putalpha(ImageChops.multiply(patch.getchannel("A"), mask))
    return patch


def build_tiles(source, destination, tier):
    image = Image.open(source).convert("RGBA")
    generated = 0
    for shape in ("hex", "square"):
        folder = Path(destination) / shape / str(tier)
        folder.mkdir(parents=True, exist_ok=True)
        for cell in range(COLS*ROWS):
            target = folder / f"{cell:03d}.webp"
            extract_one(image, cell, shape).save(target, "WEBP", quality=88, method=4)
            generated += 1
    return generated


def build_public_geonaph_tiles(webroot):
    webroot = Path(webroot)
    tier_prefix = (
        "geonaph_full_static_canonical_surface_v001",
        "geonaph_full_static_highlands_rivers_v001",
        "geonaph_full_static_mountain_volcanic_archipelago_v001",
    )
    output = webroot / "prototype" / "region-cells" / "geonaph"
    count = 0
    for tier, stem in enumerate(tier_prefix):
        source = webroot / "prototype" / "upscale" / (stem + "_2x.png")
        if not source.is_file():
            print(f"region-cell-index-unavailable tier={tier} source={source}")
            continue
        count += build_tiles(source, output, tier)
    (output / "manifest.json").write_text(json.dumps({
        "version": 1, "world": "shaelvien-geonaph-alpha-001",
        "source": "official-geonaph-upscale",
        "columns": COLS, "rows": ROWS, "tierCount": 3,
        "generatedTileCount": count,
        "urlPattern": "./region-cells/geonaph/{shape}/{parentTier}/{cell:03d}.webp",
    }, separators=(",", ":")), encoding="utf-8")
    print(f"region-cell-index generated={count} expected={3*2*COLS*ROWS}")
    return count
