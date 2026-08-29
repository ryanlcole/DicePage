#!/usr/bin/env python3
"""Recover ChatGPT-generated images from saved ChatGPT share HTML files.

Usage:
    python tools/recover_chatgpt_media_assets.py "G:/My Drive/Shaelvien/07_Media"

The tool walks the directory recursively, finds HTML share records, extracts the
full-resolution public-content attachment URL embedded by ChatGPT image shares,
downloads the image beside the source HTML, and writes a JSON manifest.

Source HTML files are never deleted. Existing recovered images are not replaced
unless --overwrite is supplied.
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import mimetypes
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable

PUBLIC_CONTENT_RE = re.compile(
    r'url\\?",\\?"(https://chatgpt\.com/backend-api/estuary/public_content/enc/[^"\\]+)',
    re.IGNORECASE | re.DOTALL,
)
POST_ID_RE = re.compile(r'https://chatgpt\.com/s/(m_[A-Za-z0-9_]+)', re.IGNORECASE)
GENERATION_ID_RE = re.compile(r'generation_id\\?",\\?"([^"\\]+)', re.IGNORECASE)
WIDTH_RE = re.compile(r'width\\?",(\d+)', re.IGNORECASE)
HEIGHT_RE = re.compile(r'height\\?",(\d+)', re.IGNORECASE)

EXTENSIONS = {
    'image/png': '.png',
    'image/webp': '.webp',
    'image/jpeg': '.jpg',
    'image/gif': '.gif',
}


def sniff_extension(data: bytes, content_type: str | None) -> str:
    if content_type:
        base = content_type.split(';', 1)[0].strip().lower()
        if base in EXTENSIONS:
            return EXTENSIONS[base]
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return '.png'
    if data.startswith(b'RIFF') and data[8:12] == b'WEBP':
        return '.webp'
    if data.startswith(b'\xff\xd8\xff'):
        return '.jpg'
    if data.startswith((b'GIF87a', b'GIF89a')):
        return '.gif'
    return '.bin'


def clean_url(value: str) -> str:
    return html_lib.unescape(value).replace('\\u0026', '&').replace('\\/', '/')


def extract_record(path: Path) -> dict:
    text = path.read_text(encoding='utf-8', errors='ignore')
    urls = []
    seen = set()
    for match in PUBLIC_CONTENT_RE.finditer(text):
        url = clean_url(match.group(1))
        # The first attachment-level public-content URL is normally the original.
        # Deduplicate while preserving order because share HTML also contains md,
        # thumbnail and unfurl variants later in the payload.
        if url not in seen:
            seen.add(url)
            urls.append(url)
    post = POST_ID_RE.search(text)
    generation = GENERATION_ID_RE.search(text)
    width = WIDTH_RE.search(text)
    height = HEIGHT_RE.search(text)
    return {
        'source_html': str(path),
        'post_id': post.group(1) if post else path.stem,
        'generation_id': generation.group(1) if generation else None,
        'width': int(width.group(1)) if width else None,
        'height': int(height.group(1)) if height else None,
        'candidate_urls': urls,
    }


def fetch(url: str, timeout: float) -> tuple[bytes, str | None, str]:
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 ShaelvienMediaRecovery/1.0',
            'Accept': 'image/avif,image/webp,image/png,image/jpeg,image/*,*/*;q=0.8',
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        data = response.read()
        return data, response.headers.get('Content-Type'), response.geturl()


def unique_destination(html_path: Path, stem: str, ext: str, overwrite: bool) -> Path:
    candidate = html_path.with_name(stem + ext)
    if overwrite or not candidate.exists():
        return candidate
    i = 2
    while True:
        alt = html_path.with_name(f'{stem}_{i:02d}{ext}')
        if not alt.exists():
            return alt
        i += 1


def recover_one(path: Path, overwrite: bool, timeout: float) -> dict:
    record = extract_record(path)
    record['status'] = 'no-image-pointer'
    record['output'] = None
    record['resolved_url'] = None
    record['error'] = None
    if not record['candidate_urls']:
        return record

    errors = []
    for url in record['candidate_urls']:
        try:
            data, content_type, resolved = fetch(url, timeout)
            if not data:
                raise ValueError('empty response')
            ext = sniff_extension(data, content_type)
            if ext == '.bin':
                raise ValueError(f'non-image response ({content_type or "unknown content type"})')
            stem = record['post_id'] or path.stem
            dest = unique_destination(path, stem, ext, overwrite)
            if overwrite or not dest.exists():
                dest.write_bytes(data)
            record.update(
                status='recovered',
                output=str(dest),
                resolved_url=resolved,
                content_type=content_type,
                bytes=len(data),
            )
            return record
        except Exception as exc:  # keep trying alternate encodings/variants
            errors.append(f'{type(exc).__name__}: {exc}')
    record['status'] = 'download-failed'
    record['error'] = ' | '.join(errors)
    return record


def html_files(root: Path) -> Iterable[Path]:
    for path in root.rglob('*'):
        if path.is_file() and path.suffix.lower() in {'.html', '.htm'}:
            yield path


def main() -> int:
    parser = argparse.ArgumentParser(description='Recover Shaelvien ChatGPT image-share assets')
    parser.add_argument('root', type=Path, help='local/synced Shaelvien 07_Media folder')
    parser.add_argument('--overwrite', action='store_true')
    parser.add_argument('--timeout', type=float, default=45.0)
    parser.add_argument('--delay', type=float, default=0.20, help='seconds between downloads')
    parser.add_argument('--manifest', type=Path, default=None)
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f'Not a directory: {root}', file=sys.stderr)
        return 2

    manifest = args.manifest or root / 'shaelvien_media_recovery_manifest.json'
    results = []
    files = list(html_files(root))
    print(f'Found {len(files)} HTML files under {root}')
    for index, path in enumerate(files, 1):
        print(f'[{index}/{len(files)}] {path.relative_to(root)}')
        result = recover_one(path, args.overwrite, args.timeout)
        results.append(result)
        print(f'  -> {result["status"]}{": " + result["output"] if result.get("output") else ""}')
        manifest.write_text(json.dumps(results, indent=2), encoding='utf-8')
        if result['status'] == 'recovered' and args.delay:
            time.sleep(args.delay)

    counts = {}
    for item in results:
        counts[item['status']] = counts.get(item['status'], 0) + 1
    print(json.dumps(counts, indent=2))
    print(f'Manifest: {manifest}')
    return 0 if not counts.get('download-failed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
