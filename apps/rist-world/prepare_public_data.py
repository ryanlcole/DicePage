from pathlib import Path
import json
import shutil

root = Path(__file__).resolve().parents[2]
tactical = root / 'apps' / 'tactical'
web = root / 'apps' / 'rist-world' / 'wwwroot'
(web / 'assets' / 'atlas').mkdir(parents=True, exist_ok=True)
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

cards = json.loads((tactical / 'data' / 'tabletop' / 'card_definitions.json').read_text()).get('cards', [])
(web / 'data' / 'cards-public.json').write_text(json.dumps([
    {'id': c['cardId'], 'name': c.get('name', 'Card'), 'type': c.get('cardType', 'card'), 'text': c.get('text', '')}
    for c in cards
]))
print(f'atlas={len(rows)} cards={len(cards)}')
