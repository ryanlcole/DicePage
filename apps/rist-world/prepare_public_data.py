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
for asset in registry.get('assets', [])[:40]:
    source = tactical / asset.get('derivedPath', '')
    if not source.exists():
        continue
    target = web / 'assets' / 'atlas' / source.name
    shutil.copy2(source, target)
    rows.append({'id': asset['assetId'], 'name': asset.get('name', asset['assetId']), 'image': 'assets/atlas/' + source.name})
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
