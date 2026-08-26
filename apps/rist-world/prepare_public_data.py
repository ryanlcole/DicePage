from pathlib import Path
import json
import shutil
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[2]
tactical = root / 'apps' / 'tactical'
web = root / 'apps' / 'rist-world' / 'wwwroot'
(web / 'assets' / 'atlas').mkdir(parents=True, exist_ok=True)
(web / 'assets' / 'world').mkdir(parents=True, exist_ok=True)
(web / 'data').mkdir(parents=True, exist_ok=True)

registry = json.loads((tactical / 'data' / 'atlas' / 'atlas_asset_registry.json').read_text())
rows = []
for asset in registry.get('assets', []):
    source = tactical / asset.get('derivedPath', '')
    if not source.exists():
        continue
    target = web / 'assets' / 'atlas' / source.name
    shutil.copy2(source, target)
    tags = asset.get('tags', [])
    layer = 'WORLD' if 'world_map' in tags else 'REGION' if 'region_map' in tags else 'UNIVERSAL'
    rows.append({
        'id': asset['assetId'],
        'name': asset.get('name', asset['assetId']),
        'image': 'assets/atlas/' + source.name,
        'layer': layer,
        'directory': str(asset.get('category', 'Atlas')).replace('_', ' ').title(),
        'folder': str(asset.get('collection', 'General')).replace('_', ' ').title(),
        'author': 'Shaelvien / owner-provided atlas'
    })

tile_registry = json.loads((tactical / 'data' / 'assets' / 'tile_asset_registry.json').read_text())
for asset in tile_registry.get('assets', []):
    if asset.get('type') != 'tile_image':
        continue
    source = tactical / asset.get('sourcePath', '')
    if not source.exists():
        continue
    target = web / 'assets' / 'tiles' / source.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    tags = [str(tag).lower() for tag in asset.get('tags', [])]
    if 'marker' in tags or any(tag in tags for tag in ('entrance', 'exit', 'trigger', 'player_start', 'enemy_start')):
        layer = 'ENCOUNTER'
    elif 'symbol' in tags or any(tag in tags for tag in ('city', 'town', 'village')):
        layer = 'WORLD'
    elif 'object' in tags or any(tag in tags for tag in ('table', 'chair', 'door', 'chest', 'barrel', 'bed')):
        layer = 'AREA'
    else:
        layer = 'LOCAL'
    directory = next((name for name in ('terrain', 'autotile', 'object', 'symbol', 'marker') if name in tags), 'tiles')
    folder = next((tag for tag in tags if tag not in {'shaelvien_woodcut_v1', 'original', directory, 'placeholder'}), 'general')
    rows.append({
        'id': asset['assetId'],
        'name': asset.get('name', asset['assetId']),
        'image': 'assets/tiles/' + source.name,
        'layer': layer,
        'directory': directory.title(),
        'folder': folder.replace('_', ' ').title(),
        'author': asset.get('author', 'Shaelvien')
    })

# Owner-provided sprite sheets added directly to the RIST public asset library.
# These remain as source sheets so the directional ordering is preserved for
# the sprite builder; individual frames can be generated from the sheet later.
static_sprite_sheets = [
    {
        'id': 'sprite-sheet-directional-humanoids',
        'name': 'Directional Humanoids',
        'image': 'assets/spritesheets/directional-humanoids.webp',
        'layer': 'UNIVERSAL',
        'directory': 'Sprites',
        'folder': 'Directional Tokens',
        'author': 'Shaelvien / owner-provided sprites'
    },
    {
        'id': 'sprite-sheet-magic-coins',
        'name': 'Magic Coin Sprites',
        'image': 'assets/spritesheets/magic-coins.webp',
        'layer': 'UNIVERSAL',
        'directory': 'Sprites',
        'folder': 'Coins',
        'author': 'Shaelvien / owner-provided sprites'
    },
    {
        'id': 'sprite-sheet-directional-creatures-a',
        'name': 'Directional Creatures A',
        'image': 'assets/spritesheets/directional-creatures-a.webp',
        'layer': 'UNIVERSAL',
        'directory': 'Sprites',
        'folder': 'Directional Tokens',
        'author': 'Shaelvien / owner-provided sprites'
    },
    {
        'id': 'sprite-sheet-directional-dragons',
        'name': 'Directional Dragons',
        'image': 'assets/spritesheets/directional-dragons.webp',
        'layer': 'UNIVERSAL',
        'directory': 'Sprites',
        'folder': 'Directional Tokens',
        'author': 'Shaelvien / owner-provided sprites'
    },
    {
        'id': 'sprite-sheet-directional-creatures-b',
        'name': 'Directional Creatures B',
        'image': 'assets/spritesheets/directional-creatures-b.webp',
        'layer': 'UNIVERSAL',
        'directory': 'Sprites',
        'folder': 'Directional Tokens',
        'author': 'Shaelvien / owner-provided sprites'
    }
]
for asset in static_sprite_sheets:
    if (web / asset['image']).exists():
        rows.append(asset)

(web / 'data' / 'atlas-public.json').write_text(json.dumps(rows))

# Verify the canonical AWS-hosted world map during every build and retain a
# packaged Pages copy as a backup artifact.
world_source = 'https://d2d6rnm6fnsp89.cloudfront.net/worlds/naeja/world.png?v=20260813-refresh'
request = Request(world_source, headers={'User-Agent': 'RIST-Pages-Build/1.0'})
with urlopen(request, timeout=30) as response:
    world_bytes = response.read()
if not world_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
    raise SystemExit('World map CDN source is not a PNG')
if len(world_bytes) < 100000:
    raise SystemExit(f'World map CDN source unexpectedly small: {len(world_bytes)}')
(web / 'assets' / 'world' / 'naeja.png').write_bytes(world_bytes)

# Runtime uses the verified CDN URL directly. This removes browser-relative
# path ambiguity while preserving the packaged same-origin copy above.
(web / 'data' / 'asset-config.json').write_text(json.dumps({
    'worldMapUrl': world_source
}))

cards = json.loads((tactical / 'data' / 'tabletop' / 'card_definitions.json').read_text()).get('cards', [])
(web / 'data' / 'cards-public.json').write_text(json.dumps([
    {'id': c['cardId'], 'name': c.get('name', 'Card'), 'type': c.get('cardType', 'card'), 'text': c.get('text', '')}
    for c in cards
]))
print(f'atlas={len(rows)} cards={len(cards)} world=cdn-runtime+pages-backup bytes={len(world_bytes)}')
