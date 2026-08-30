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

# Homepage footer: keep the studio mark and PayPal control together above the
# copyright. Use PayPal-hosted official Donate button artwork rather than a
# locally imitated brand button. The existing managed PayPal destination is
# intentionally preserved.
home_path = root / 'site' / 'relic-home' / 'index.html'
home = home_path.read_text(encoding='utf-8')
old_footer = '<footer><div class="footer-relic-mark" role="img" aria-label="ReLiC ornamental mark"></div><p>© 2026 Ryan L. Cole / ReLiCGameMaster · Shaelvien · RIST · All rights reserved.</p><a class="paypal-donate" href="https://www.paypal.com/qrcodes/managed/c40871d1-e65b-4281-b970-0acacbdddbc9" target="_blank" rel="noopener noreferrer" aria-label="Donate to ReLiCGameMaster with PayPal">Donate with PayPal</a></footer>'
new_footer = '<footer class="relic-site-footer"><div class="footer-support-row"><div class="footer-relic-mark" role="img" aria-label="ReLiC ornamental mark"></div><a class="paypal-donate" href="https://www.paypal.com/qrcodes/managed/c40871d1-e65b-4281-b970-0acacbdddbc9" target="_blank" rel="noopener noreferrer" aria-label="Donate to ReLiCGameMaster with PayPal"><img src="https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif" alt="Donate with PayPal"></a></div><p class="footer-copyright">© 2026 Ryan L. Cole / ReLiCGameMaster · Shaelvien · RIST · All rights reserved.</p></footer>'
if old_footer not in home:
    raise ValueError('Homepage footer signature changed; update the footer migration before deploying')
home = home.replace(old_footer, new_footer, 1)

footer_css = '''<style id="paypal-footer-layout">
.relic-site-footer{display:flex!important;flex-direction:column!important;align-items:center!important;justify-content:center!important;gap:10px!important;text-align:center!important}
.footer-support-row{display:flex;align-items:center;justify-content:center;gap:16px;flex-wrap:nowrap}
.relic-site-footer .footer-relic-mark{background-color:transparent!important;border-radius:0!important;box-shadow:none!important;mix-blend-mode:screen!important}
.relic-site-footer .paypal-donate{display:inline-flex!important;align-items:center!important;justify-content:center!important;margin:0!important;padding:0!important;border:0!important;border-radius:0!important;background:transparent!important;box-shadow:none!important;line-height:0!important}
.relic-site-footer .paypal-donate img{display:block;width:auto;height:auto;max-width:147px;border:0}
.relic-site-footer .footer-copyright{width:100%;margin:0!important}
@media(max-width:420px){.footer-support-row{gap:12px}.relic-site-footer .paypal-donate img{max-width:132px}}
</style>'''
home = home.replace('</head>', footer_css + '</head>', 1)
home_path.write_text(home, encoding='utf-8')

print(f'canonical_assets={len(rows)} cards={len(cards)} legacy_asset_catalog=disabled homepage_paypal=official-art footer_mark=transparent')
