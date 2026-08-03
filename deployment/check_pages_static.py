from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIST = REPO_ROOT / "dist"


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.references.append((name, value))


FETCH_RE = re.compile(r"fetch\(\s*['\"]([^'\"]+)['\"]")
CSS_URL_RE = re.compile(r"url\(\s*['\"]?([^)'\"]+)['\"]?\s*\)")


def url_to_file(dist: Path, url: str, base_path: str) -> Path | None:
    parsed = urlparse(url)
    if url.startswith("mailto:") or url.startswith("tel:") or url.startswith("data:"):
        return None
    if (parsed.scheme or parsed.netloc) and parsed.netloc != "example.invalid":
        return None
    path = parsed.path
    if path.startswith("/"):
        prefix = "/" + base_path.strip("/") + "/" if base_path.strip("/") else "/"
        if base_path.strip() and not path.startswith(prefix):
            return dist / "__outside_base__"
        path = path[len(prefix) :] if base_path.strip() else path[1:]
    if not path or path.endswith("/"):
        path = path + "index.html"
    return (dist / path).resolve()


def collect_html_references(path: Path) -> list[str]:
    parser = LinkParser()
    text = path.read_text(encoding="utf-8")
    parser.feed(text)
    refs = [value for _, value in parser.references]
    refs.extend(FETCH_RE.findall(text))
    return refs


def collect_css_references(path: Path) -> list[str]:
    return CSS_URL_RE.findall(path.read_text(encoding="utf-8"))


def check(dist: Path, base_path: str) -> dict:
    routes = ["/", "/app/", "/store/", "/docs/", "/lab/", "/build-info.json"]
    failures: list[dict] = []
    route_results = []
    base_url = "https://example.invalid/" + (base_path.strip("/") + "/" if base_path.strip("/") else "")
    for route in routes:
        resolved = url_to_file(dist, urljoin(base_url, route.lstrip("/")), base_path)
        exists = bool(resolved and resolved.exists())
        route_results.append({"route": route, "file": str(resolved) if resolved else None, "exists": exists})
        if not exists:
            failures.append({"type": "missing_route", "route": route, "file": str(resolved) if resolved else None})

    for html in sorted(dist.rglob("*.html")):
        page_url = base_url + html.relative_to(dist).as_posix()
        if page_url.endswith("index.html"):
            page_url = page_url[: -len("index.html")]
        for ref in collect_html_references(html):
            if ref.startswith("#"):
                continue
            target_url = urljoin(page_url, ref)
            target = url_to_file(dist, target_url, base_path)
            if target is None:
                continue
            if "__outside_base__" in str(target):
                failures.append({"type": "outside_base_path", "page": str(html), "reference": ref, "basePath": base_path})
                continue
            if not target.exists():
                failures.append({"type": "missing_reference", "page": str(html), "reference": ref, "target": str(target)})

    for css in sorted(dist.rglob("*.css")):
        css_url = base_url + css.relative_to(dist).as_posix()
        for ref in collect_css_references(css):
            if ref.startswith("#"):
                continue
            target_url = urljoin(css_url, ref)
            target = url_to_file(dist, target_url, base_path)
            if target and "__outside_base__" not in str(target) and not target.exists():
                failures.append({"type": "missing_css_reference", "page": str(css), "reference": ref, "target": str(target)})

    return {
        "basePath": base_path,
        "routes": route_results,
        "failures": failures,
        "passed": not failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", default=str(DEFAULT_DIST))
    parser.add_argument("--report", default="")
    args = parser.parse_args()
    dist = Path(args.dist).resolve()
    result = {
        "dist": str(dist),
        "root": check(dist, ""),
        "repositorySubpath": check(dist, "DicePage"),
    }
    result["passed"] = result["root"]["passed"] and result["repositorySubpath"]["passed"]
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.report:
        Path(args.report).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
