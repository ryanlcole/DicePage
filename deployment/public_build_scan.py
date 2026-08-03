from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIST = REPO_ROOT / "dist"
DEFAULT_REPORT_DIR = Path(r"C:\Shaelvien\verify_reports\relic_gamemaster_live_alpha_0")

FORBIDDEN_EXTENSIONS = {
    ".db",
    ".sqlite",
    ".sqlite3",
    ".env",
    ".bak",
    ".zip",
    ".tar",
    ".7z",
    ".pfx",
    ".pem",
    ".key",
    ".map",
}

PATTERNS = {
    "windows_drive_path": re.compile(rb"(?:C|A|P):\\"),
    "publish_profile": re.compile(rb"publishProfile|AZURE_PUBLISH_PROFILE|MSDeployPublishMethod", re.IGNORECASE),
    "connection_string": re.compile(rb"(DefaultEndpointsProtocol|AccountKey=|Server=tcp:|Data Source=)", re.IGNORECASE),
    "private_key": re.compile(rb"BEGIN (?:RSA |OPENSSH |EC |)PRIVATE KEY", re.IGNORECASE),
    "token": re.compile(rb"(?:password|passwd|secret|token|api[_-]?key)\s*[:=]\s*['\"][^'\"]{8,}", re.IGNORECASE),
    "project_mind": re.compile(rb"Project Mind|project_knowledge\.sqlite|TOME", re.IGNORECASE),
    "email_address": re.compile(rb"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE),
}


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def scan(dist: Path) -> dict:
    findings: list[dict] = []
    files = sorted([p for p in dist.rglob("*") if p.is_file()], key=lambda p: p.as_posix().lower())
    for path in files:
        rel = relative(path, dist)
        suffix = path.suffix.lower()
        if suffix in FORBIDDEN_EXTENSIONS or path.name.lower().startswith(".env"):
            findings.append({"severity": "critical", "type": "forbidden_file_type", "path": rel})
        try:
            data = path.read_bytes()
        except OSError as exc:
            findings.append({"severity": "critical", "type": "unreadable_file", "path": rel, "detail": str(exc)})
            continue
        if b"\x00" in data[:4096]:
            continue
        for name, pattern in PATTERNS.items():
            if pattern.search(data):
                findings.append({"severity": "critical", "type": name, "path": rel})

    return {
        "scannedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "dist": str(dist),
        "fileCount": len(files),
        "findings": findings,
        "passed": not any(item["severity"] == "critical" for item in findings),
    }


def write_reports(result: dict, report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "PUBLIC_BUILD_EXPOSURE_REPORT.json"
    md_path = report_dir / "PUBLIC_BUILD_EXPOSURE_REPORT.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Public Build Exposure Report",
        "",
        f"Scanned: `{result['dist']}`",
        f"Files scanned: {result['fileCount']}",
        f"Result: {'PASS' if result['passed'] else 'FAIL'}",
        "",
        "## Findings",
        "",
    ]
    if result["findings"]:
        for finding in result["findings"]:
            lines.append(f"- {finding['severity'].upper()}: {finding['type']} in `{finding['path']}`")
    else:
        lines.append("- No critical public exposure findings.")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", default=str(DEFAULT_DIST))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    args = parser.parse_args()

    dist = Path(args.dist).resolve()
    if not dist.exists():
        print(json.dumps({"passed": False, "error": f"Missing dist: {dist}"}), file=sys.stderr)
        return 2
    result = scan(dist)
    write_reports(result, Path(args.report_dir))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

