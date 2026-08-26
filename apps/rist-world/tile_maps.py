from pathlib import Path
import json
import math
import shutil
from PIL import Image

root = Path(__file__).resolve().parents[2]
web = root / 'apps' / 'rist-world' / 'wwwroot'
world_dir = web / 'assets' / 'world'
data_dir = web / 'data'
map_data_dir = data_dir / 'maps'
map_data_dir.mkdir(parents=True, exist_ok=True)

atlas_path = data_dir / 'atlas-public.json'
rows = json.loads(atlas_path.read_text()) if atlas_path.exists() else []
rows = [r for r in rows if not str(r.get('id', '')).startswith('maptile-')]

TILE = 512
maps = []

for source in sorted(world_dir.iterdir()):
    if not source.is_file() or source.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp'}:
        continue
    map_id = source.stem.lower().replace(' ', '-').replace('_', '-')
    name = source.stem.replace('_', ' ').replace('-', ' ').title()
    tile_dir = world_dir / map_id / 'tiles'
    if tile_dir.exists():
        shutil.rmtree(tile_dir)
    tile_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as image:
        image.load()
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGBA' if 'A' in image.getbands() else 'RGB')
        width, height = image.size
        cols = math.ceil(width / TILE)
        tile_rows = math.ceil(height / TILE)
        tiles = []
        for row in range(tile_rows):
            for col in range(cols):
                x = col * TILE
                y = row * TILE
                w = min(TILE, width - x)
                h = min(TILE, height - y)
                crop = image.crop((x, y, x + w, y + h))
                filename = f'r{row:03d}-c{col:03d}.webp'
                target = tile_dir / filename
                crop.save(target, 'WEBP', quality=72, method=5)
                rel = f'assets/world/{map_id}/tiles/{filename}'
                tile = {'row': row, 'col': col, 'x': x, 'y': y, 'width': w, 'height': h, 'image': rel}
                tiles.append(tile)
                rows.append({
                    'id': f'maptile-{map_id}-{row}-{col}',
                    'name': f'{name} {row + 1},{col + 1}',
                    'image': rel,
                    'layer': 'WORLD',
                    'directory': 'Maps',
                    'folder': name,
                    'author': 'Shaelvien / map tile'
                })

    # Center-out order makes the map visibly appear from the middle while
    # requests still happen strictly one packet at a time in the browser.
    cr = (tile_rows - 1) / 2
    cc = (cols - 1) / 2
    tiles.sort(key=lambda t: (t['row'] - cr) ** 2 + (t['col'] - cc) ** 2)
    manifest = {
        'id': map_id,
        'name': name,
        'width': width,
        'height': height,
        'tileSize': TILE,
        'columns': cols,
        'rows': tile_rows,
        'tiles': tiles
    }
    manifest_path = map_data_dir / f'{map_id}.json'
    manifest_path.write_text(json.dumps(manifest, separators=(',', ':')))
    maps.append({'id': map_id, 'name': name, 'manifest': f'data/maps/{map_id}.json', 'width': width, 'height': height})

atlas_path.write_text(json.dumps(rows, separators=(',', ':')))
(map_data_dir / 'index.json').write_text(json.dumps(maps, separators=(',', ':')))

config_path = data_dir / 'asset-config.json'
config = json.loads(config_path.read_text()) if config_path.exists() else {}
if maps:
    preferred = next((m for m in maps if m['id'] == 'naeja'), maps[0])
    config['worldMapManifestUrl'] = preferred['manifest']
config_path.write_text(json.dumps(config, separators=(',', ':')))

print(f'map_tiles={sum(len(json.loads((map_data_dir / (m["id"] + ".json")).read_text())["tiles"]) for m in maps)} maps={len(maps)} atlas={len(rows)}')
