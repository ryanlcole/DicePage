from pathlib import Path
from collections import deque
import hashlib
import json
import os
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
tactical = root / 'apps' / 'tactical'
web = root / 'apps' / 'rist-world' / 'wwwroot'
data_dir = web / 'data'
data_dir.mkdir(parents=True, exist_ok=True)

IMPORT_FORMATS = {'.jpg', '.jpeg', '.png', '.webp'}
LEGACY_IMPORT_FORMATS = {'.jpg', '.jpeg', '.webp'}


def _load_pillow():
    try:
        from PIL import Image
        return Image
    except ImportError:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install',
            '--disable-pip-version-check', 'Pillow==11.3.0'
        ])
        from PIL import Image
        return Image


def _median(values):
    ordered = sorted(values)
    return ordered[len(ordered) // 2] if ordered else 0


def _remove_edge_background(image):
    """Remove only background-colored pixels connected to the image edge."""
    rgba = image.convert('RGBA')
    width, height = rgba.size
    if width < 2 or height < 2:
        return rgba, False

    pixels = rgba.load()
    corners = ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1))
    if any(pixels[x, y][3] < 250 for x, y in corners):
        return rgba, True

    step = max(1, min(width, height) // 96)
    border = []
    for x in range(0, width, step):
        border.append(pixels[x, 0][:3])
        border.append(pixels[x, height - 1][:3])
    for y in range(0, height, step):
        border.append(pixels[0, y][:3])
        border.append(pixels[width - 1, y][:3])

    bg = tuple(_median([p[channel] for p in border]) for channel in range(3))
    threshold = 58
    feather_start = 24

    def distance(rgb):
        return (
            (rgb[0] - bg[0]) ** 2
            + (rgb[1] - bg[1]) ** 2
            + (rgb[2] - bg[2]) ** 2
        ) ** 0.5

    seen = bytearray(width * height)
    queue = deque()

    def seed(x, y):
        idx = y * width + x
        if seen[idx]:
            return
        if distance(pixels[x, y][:3]) <= threshold:
            seen[idx] = 1
            queue.append((x, y))

    for x in range(width):
        seed(x, 0)
        seed(x, height - 1)
    for y in range(height):
        seed(0, y)
        seed(width - 1, y)

    removed = 0
    while queue:
        x, y = queue.popleft()
        r, g, b, a = pixels[x, y]
        d = distance((r, g, b))
        if d <= feather_start:
            alpha = 0
        else:
            alpha = int(255 * (d - feather_start) / max(1, threshold - feather_start))
        alpha = min(a, max(0, min(255, alpha)))
        if alpha < a:
            removed += 1
            pixels[x, y] = (r, g, b, alpha)

        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if nx < 0 or ny < 0 or nx >= width or ny >= height:
                continue
            idx = ny * width + nx
            if seen[idx]:
                continue
            if distance(pixels[nx, ny][:3]) <= threshold:
                seen[idx] = 1
                queue.append((nx, ny))

    return rgba, removed > 0


def _image_digest(image):
    """Hash normalized visual content independent of source encoding."""
    width, height = image.size
    digest = hashlib.sha256()
    digest.update(f'{width}x{height}:RGBA:'.encode('ascii'))
    digest.update(image.tobytes())
    return digest.hexdigest()


def _unique_target(output_root, relative, digest, claimed_targets):
    target = (output_root / relative).with_suffix('.png')
    target_key = target.relative_to(output_root).as_posix().casefold()
    if target_key not in claimed_targets:
        claimed_targets.add(target_key)
        return target

    target = target.with_name(f'{target.stem}__{digest[:12]}.png')
    claimed_targets.add(target.relative_to(output_root).as_posix().casefold())
    return target


def normalize_imported_images():
    """Create one canonical transparent PNG for each unique imported image.

    Source files remain untouched during local development. In GitHub Actions,
    superseded JPG/JPEG/WebP copies are removed from the ephemeral checkout after
    successful normalization so dotnet publish and the CDN contain canonical PNGs.
    """
    source_root = web / 'assets' / 'chat-imports' / '2026-08-30'
    output_root = web / 'assets' / 'normalized' / 'chat-imports' / '2026-08-30'
    manifest_path = web / 'assets' / 'normalized' / 'manifest.json'

    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    Image = _load_pillow()
    manifest = []
    canonical_by_digest = {}
    claimed_targets = set()
    prune_legacy = os.environ.get('GITHUB_ACTIONS', '').lower() == 'true'

    for source in sorted(source_root.rglob('*')):
        if not source.is_file() or source.suffix.lower() not in IMPORT_FORMATS:
            continue
        relative = source.relative_to(source_root)
        try:
            with Image.open(source) as opened:
                opened.verify()
            with Image.open(source) as opened:
                normalized, transparent = _remove_edge_background(opened)
                digest = _image_digest(normalized)
        except Exception as exc:
            print(f'asset-normalize-reject source={source} error={type(exc).__name__}: {exc}')
            if prune_legacy and source.suffix.lower() in LEGACY_IMPORT_FORMATS:
                source.unlink(missing_ok=True)
            continue

        source_web = 'assets/chat-imports/2026-08-30/' + relative.as_posix()
        canonical_target = canonical_by_digest.get(digest)
        duplicate_of = None

        if canonical_target is None:
            target = _unique_target(output_root, relative, digest, claimed_targets)
            target.parent.mkdir(parents=True, exist_ok=True)
            normalized.save(target, 'PNG', optimize=True)
            canonical_by_digest[digest] = target
            canonical_target = target
        else:
            duplicate_of = (
                'assets/normalized/chat-imports/2026-08-30/'
                + canonical_target.relative_to(output_root).as_posix()
            )

        target_web = (
            'assets/normalized/chat-imports/2026-08-30/'
            + canonical_target.relative_to(output_root).as_posix()
        )
        entry = {
            'source': source_web,
            'png': target_web,
            'sourceFormat': source.suffix.lower().lstrip('.'),
            'transparent': transparent,
            'sha256': digest,
        }
        if duplicate_of is not None:
            entry['duplicateOf'] = duplicate_of
        manifest.append(entry)

        if prune_legacy and source.suffix.lower() in LEGACY_IMPORT_FORMATS:
            source.unlink()

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, separators=(',', ':')), encoding='utf-8')
    return manifest


normalized_assets = normalize_imported_images()

# The Drive/AWS catalog is the canonical Shaelvien asset registry for both
# visitors and authenticated users. Do not rebuild a second public catalog
# from the old tactical prototype registries.
canonical_catalog_path = web / 'assets' / 'drive-tiles' / 'catalog.json'
canonical_rows = json.loads(canonical_catalog_path.read_text(encoding='utf-8'))
if not isinstance(canonical_rows, list):
    raise ValueError('Canonical Shaelvien asset catalog must be a JSON array')

required = {'id', 'name', 'image', 'layer', 'directory', 'folder'}
seen_ids = set()
seen_images = set()
rows = []
duplicate_catalog_rows = 0

for asset in canonical_rows:
    if not isinstance(asset, dict):
        continue
    missing = required.difference(asset)
    if missing:
        raise ValueError(
            f"Asset {asset.get('id', '<unknown>')} is missing: {', '.join(sorted(missing))}"
        )

    asset_id = str(asset['id']).strip()
    image_key = str(asset['image']).strip().casefold()
    if not asset_id:
        continue
    if asset_id in seen_ids or (image_key and image_key in seen_images):
        duplicate_catalog_rows += 1
        continue

    seen_ids.add(asset_id)
    if image_key:
        seen_images.add(image_key)
    rows.append(asset)

# WorldSession currently reads atlas-public.json first and then the canonical
# Drive catalog. Publishing the same canonical rows to both locations keeps
# compatibility while ensuring the second load is a no-op after dedupe.
(data_dir / 'atlas-public.json').write_text(
    json.dumps(rows, separators=(',', ':')), encoding='utf-8'
)

# Do not regenerate the obsolete random-world / prototype-region configuration.
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

unique_normalized = len({item['sha256'] for item in normalized_assets})
duplicate_imports = len(normalized_assets) - unique_normalized
print(
    f'canonical_assets={len(rows)} '
    f'catalog_duplicates_removed={duplicate_catalog_rows} '
    f'cards={len(cards)} '
    f'normalized_imports={len(normalized_assets)} '
    f'unique_normalized={unique_normalized} '
    f'duplicate_imports={duplicate_imports} '
    'legacy_asset_catalog=disabled '
    'homepage_paypal=official-art '
    'footer_mark=transparent'
)
