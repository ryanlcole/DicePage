from pathlib import Path
from collections import deque
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import urllib.request

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
        if source.stat().st_size < 256:
            continue

        relative = source.relative_to(source_root)
        try:
            with Image.open(source) as opened:
                normalized, transparent = _remove_edge_background(opened)
                digest = _image_digest(normalized)
        except Exception as exc:
            print(f'asset-normalize-skip source={source} error={type(exc).__name__}: {exc}')
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


def build_geonaph_upscale_representations():
    """Build derived 2x Geonaph viewer representations without changing world truth."""
    if os.environ.get('GITHUB_ACTIONS', '').lower() != 'true':
        return []

    Image = _load_pillow()
    from PIL import ImageFilter

    asset_base = os.environ.get(
        'ASSET_BASE_URL',
        'https://d2d6rnm6fnsp89.cloudfront.net/'
    ).rstrip('/') + '/'
    source_prefix = 'library/terrains/standard/world/whole_maps/geonaph/'
    files = (
        'geonaph_full_static_canonical_surface_v001.png',
        'geonaph_full_static_highlands_rivers_v001.png',
        'geonaph_full_static_mountain_volcanic_archipelago_v001.png',
    )
    output_root = web / 'prototype' / 'upscale'
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    manifest = []
    for filename in files:
        source_url = asset_base + source_prefix + filename
        output_name = filename.removesuffix('.png') + '_2x.png'
        output_path = output_root / output_name
        try:
            request = urllib.request.Request(
                source_url,
                headers={'User-Agent': 'Shaelvien-Geonaph-Upscale/1.0'}
            )
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = response.read()

            with Image.open(io.BytesIO(payload)) as opened:
                source = opened.convert('RGBA')
                source_width, source_height = source.size
                factor = min(2.0, 4096 / max(source_width, source_height))
                if factor <= 1.0:
                    derived = source.copy()
                else:
                    target = (
                        max(1, round(source_width * factor)),
                        max(1, round(source_height * factor)),
                    )
                    derived = source.resize(target, Image.Resampling.LANCZOS)
                    derived = derived.filter(
                        ImageFilter.UnsharpMask(radius=1.0, percent=105, threshold=2)
                    )

                derived.save(output_path, 'PNG', optimize=True)
                digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
                manifest.append({
                    'source': source_url,
                    'derived': f'prototype/upscale/{output_name}',
                    'sourceWidth': source_width,
                    'sourceHeight': source_height,
                    'derivedWidth': derived.width,
                    'derivedHeight': derived.height,
                    'scale': round(derived.width / source_width, 4),
                    'method': 'Lanczos + restrained unsharp mask',
                    'canonical': False,
                    'sha256': digest,
                })
                print(
                    f'geonaph-upscale source={filename} '
                    f'{source_width}x{source_height} -> {derived.width}x{derived.height}'
                )
        except Exception as exc:
            print(
                f'geonaph-upscale-skip source={filename} '
                f'error={type(exc).__name__}: {exc}'
            )

    (output_root / 'manifest.json').write_text(
        json.dumps(manifest, separators=(',', ':')),
        encoding='utf-8'
    )
    return manifest


geonaph_upscales = build_geonaph_upscale_representations()


def build_geonaph_perceiver_representations():
    """Build transparent tier representations for Perceiver without changing canonical world art."""
    if os.environ.get('GITHUB_ACTIONS', '').lower() != 'true':
        return []

    Image = _load_pillow()
    from PIL import ImageChops, ImageFilter

    asset_base = os.environ.get(
        'ASSET_BASE_URL',
        'https://d2d6rnm6fnsp89.cloudfront.net/'
    ).rstrip('/') + '/'
    source_prefix = 'library/terrains/standard/world/whole_maps/geonaph/'
    files = (
        'geonaph_full_static_canonical_surface_v001.png',
        'geonaph_full_static_highlands_rivers_v001.png',
        'geonaph_full_static_mountain_volcanic_archipelago_v001.png',
    )
    output_names = (
        'endemar_tier_1_perceiver_v001.png',
        'endemar_tier_2_perceiver_v001.png',
        'endemar_tier_3_perceiver_v001.png',
    )
    output_root = web / 'assets' / 'perceiver'
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    prepared = []
    derived_sizes = []
    source_urls = []
    for filename in files:
        source_url = asset_base + source_prefix + filename
        source_urls.append(source_url)
        request = urllib.request.Request(
            source_url,
            headers={'User-Agent': 'Shaelvien-Perceiver-Transparency/1.0'}
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = response.read()

        with Image.open(io.BytesIO(payload)) as opened:
            source = opened.convert('RGBA')
            source_width, source_height = source.size
            factor = min(2.0, 4096 / max(source_width, source_height))
            target_size = (
                max(1, round(source_width * factor)),
                max(1, round(source_height * factor)),
            )
            # Compute alpha at canonical source resolution. The expensive connected-
            # background and structural-delta work does not need four times the pixels.
            prepared.append(source.copy())
            derived_sizes.append(target_size)

    def alpha_transparent_ratio(image):
        alpha_histogram = image.getchannel('A').histogram()
        total = max(1, image.width * image.height)
        return (total - alpha_histogram[255]) / total

    def histogram_percentile(histogram, percentile):
        total = max(1, sum(histogram))
        target = total * percentile
        running = 0
        for value, count in enumerate(histogram):
            running += count
            if running >= target:
                return value
        return len(histogram) - 1

    manifest = []
    previous = None
    for index, current in enumerate(prepared):
        if index == 0:
            layer = current.copy()
            method = 'base-preserved'
        else:
            alpha = current.getchannel('A')
            histogram = alpha.histogram()
            total = max(1, current.width * current.height)
            opaque_ratio = histogram[255] / total

            if opaque_ratio < 0.90:
                # Already-authored transparency is world art intent; preserve it.
                layer = current.copy()
                method = 'source-alpha-preserved'
            else:
                # First try removing only background connected to the outer edge.
                # This is ideal for authored overlay art that lost its alpha channel.
                edge_layer, edge_changed = _remove_edge_background(current)
                edge_ratio = alpha_transparent_ratio(edge_layer)

                if edge_changed and 0.12 <= edge_ratio <= 0.94:
                    layer = edge_layer
                    method = 'edge-alpha-restored'
                else:
                    # Full-frame cumulative tier renders can differ slightly across
                    # almost every pixel. Build an adaptive structural delta instead
                    # of treating every color shift as foreground.
                    under = previous
                    if under is None:
                        under = prepared[index - 1]
                    if under.size != current.size:
                        under = under.resize(current.size, Image.Resampling.LANCZOS)

                    delta = ImageChops.difference(
                        current.convert('RGB'),
                        under.convert('RGB')
                    )
                    dr, dg, db = delta.split()
                    mask = ImageChops.lighter(ImageChops.lighter(dr, dg), db)
                    mask = mask.filter(ImageFilter.GaussianBlur(radius=1.15))

                    mask_histogram = mask.histogram()
                    low = histogram_percentile(mask_histogram, 0.62)
                    high = histogram_percentile(mask_histogram, 0.91)
                    low = max(8, min(low, 210))
                    high = max(low + 12, min(high, 250))

                    mask = mask.point(
                        lambda value: (
                            0 if value <= low
                            else 255 if value >= high
                            else round((value - low) * 255 / (high - low))
                        )
                    )
                    mask = mask.filter(ImageFilter.MaxFilter(3))
                    mask = mask.filter(ImageFilter.GaussianBlur(radius=0.75))
                    mask = ImageChops.multiply(mask, current.getchannel('A'))

                    layer = current.copy()
                    layer.putalpha(mask)
                    method = f'adaptive-delta-alpha-{low}-{high}'

        target_size = derived_sizes[index]
        if layer.size != target_size:
            rgb = layer.convert('RGB').resize(target_size, Image.Resampling.LANCZOS)
            alpha = layer.getchannel('A').resize(target_size, Image.Resampling.LANCZOS)
            resized = rgb.convert('RGBA')
            resized.putalpha(alpha)
            layer = resized

        output_name = output_names[index]
        output_path = output_root / output_name
        layer.save(output_path, 'PNG', optimize=True)

        alpha_histogram = layer.getchannel('A').histogram()
        total = max(1, layer.width * layer.height)
        transparent_pixels = total - alpha_histogram[255]
        transparent_ratio = transparent_pixels / total
        digest = hashlib.sha256(output_path.read_bytes()).hexdigest()

        manifest.append({
            'tier': index + 1,
            'source': source_urls[index],
            'derived': f'assets/perceiver/{output_name}',
            'width': layer.width,
            'height': layer.height,
            'method': method,
            'transparentRatio': round(transparent_ratio, 6),
            'canonical': False,
            'sha256': digest,
        })
        print(
            f'perceiver-alpha tier={index + 1} method={method} '
            f'transparent={transparent_ratio:.1%} '
            f'{layer.width}x{layer.height}'
        )
        previous = current

    (output_root / 'manifest.json').write_text(
        json.dumps(manifest, separators=(',', ':')),
        encoding='utf-8'
    )
    return manifest


geonaph_perceiver_layers = build_geonaph_perceiver_representations()

# 000012.python.prepare_public_data.line213.comment The Drive/AWS catalog is the canonical Shaelvien asset registry for both
# 000013.python.prepare_public_data.line214.comment visitors and authenticated users. Do not rebuild a second public catalog
# 000014.python.prepare_public_data.line215.comment from the old tactical prototype registries.
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

# 000015.python.prepare_public_data.line249.comment WorldSession currently reads atlas-public.json first and then the canonical
# 000016.python.prepare_public_data.line250.comment Drive catalog. Publishing the same canonical rows to both locations keeps
# 000017.python.prepare_public_data.line251.comment compatibility while ensuring the second load is a no-op after dedupe.
(data_dir / 'atlas-public.json').write_text(
    json.dumps(rows, separators=(',', ':')), encoding='utf-8'
)

# 000018.python.prepare_public_data.line256.comment Do not regenerate the obsolete random-world / prototype-region configuration.
legacy_asset_config = data_dir / 'asset-config.json'
if legacy_asset_config.exists():
    legacy_asset_config.unlink()

# 000019.python.prepare_public_data.line261.comment Card definitions remain independent of the asset catalog for now.
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

# 000020.python.prepare_public_data.line278.comment Homepage footer: keep the studio mark and PayPal control together above the
# 000021.python.prepare_public_data.line279.comment copyright. Use PayPal-hosted official Donate button artwork rather than a
# 000022.python.prepare_public_data.line280.comment locally imitated brand button. The existing managed PayPal destination is
# 000023.python.prepare_public_data.line281.comment intentionally preserved.
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
    f'geonaph_upscales={len(geonaph_upscales)} '
    f'geonaph_perceiver_layers={len(geonaph_perceiver_layers)} '
    'legacy_asset_catalog=disabled '
    'homepage_paypal=official-art '
    'footer_mark=transparent'
)
