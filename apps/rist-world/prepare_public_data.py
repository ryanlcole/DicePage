from pathlib import Path
import json

root = Path(__file__).resolve().parents[2]
tactical = root / 'apps' / 'tactical'
web = root / 'apps' / 'rist-world' / 'wwwroot'
data_dir = web / 'data'
data_dir.mkdir(parents=True, exist_ok=True)

# The Drive/AWS catalog is the canonical Shaelvien asset registry for both
# visitors and authenticated users. Do not rebuild a second public catalog
# from the old tactical prototype registries: doing so reclassified assets by
# guessed tags and mixed obsolete prototype content into the live browser.
canonical_catalog_path = web / 'assets' / 'drive-tiles' / 'catalog.json'
canonical_rows = json.loads(canonical_catalog_path.read_text(encoding='utf-8'))
if not isinstance(canonical_rows, list):
    raise ValueError('Canonical Shaelvien asset catalog must be a JSON array')

required = {'id', 'name', 'image', 'layer', 'directory', 'folder'}
seen = set()
rows = []
for asset in canonical_rows:
    if not isinstance(asset, dict):
        continue
    missing = required.difference(asset)
    if missing:
        raise ValueError(f"Asset {asset.get('id', '<unknown>')} is missing: {', '.join(sorted(missing))}")
    asset_id = str(asset['id']).strip()
    if not asset_id or asset_id in seen:
        continue
    seen.add(asset_id)
    rows.append(asset)

# WorldSession currently reads atlas-public.json first and then the canonical
# Drive catalog. Publishing the same canonical rows to both locations keeps
# compatibility while ensuring the second load is a no-op after ID dedupe.
(data_dir / 'atlas-public.json').write_text(
    json.dumps(rows, separators=(',', ':')),
    encoding='utf-8'
)

# Do not regenerate the obsolete random-world / prototype-region configuration.
# The live recursive world topology is owned by the RIST application itself.
legacy_asset_config = data_dir / 'asset-config.json'
if legacy_asset_config.exists():
    legacy_asset_config.unlink()

# Card definitions remain independent of the asset catalog for now.
cards = json.loads(
    (tactical / 'data' / 'tabletop' / 'card_definitions.json').read_text(encoding='utf-8')
).get('cards', [])
(data_dir / 'cards-public.json').write_text(
    json.dumps([
        {
            'id': card['cardId'],
            'name': card.get('name', 'Card'),
            'type': card.get('cardType', 'card'),
            'text': card.get('text', '')
        }
        for card in cards
    ], separators=(',', ':')),
    encoding='utf-8'
)

print(f'canonical_assets={len(rows)} cards={len(cards)} legacy_asset_catalog=disabled')
