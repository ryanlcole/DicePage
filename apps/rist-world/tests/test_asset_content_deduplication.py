from __future__ import annotations

import hashlib
from collections import defaultdict
from pathlib import Path

ASSET_ROOT = Path(__file__).resolve().parents[1] / "wwwroot" / "assets"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".b64"}


def content_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    groups: dict[str, list[Path]] = defaultdict(list)
    for path in ASSET_ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            groups[content_hash(path)].append(path.relative_to(ASSET_ROOT))

    duplicates = [paths for paths in groups.values() if len(paths) > 1]
    if duplicates:
        print("Exact duplicate asset payloads violate ATOMIC_RELATIONAL_ASSET_CONTRACT.md:")
        for paths in duplicates:
            print("  " + " == ".join(str(path) for path in sorted(paths)))
        raise SystemExit(1)

    print(f"Asset identity deduplication verified across {sum(len(v) for v in groups.values())} tracked image payloads.")


if __name__ == "__main__":
    main()
