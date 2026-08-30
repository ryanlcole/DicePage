"""Browser verification for the Shaelvien Atlas asset pipeline slice."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cdp_verify as base


REPORT_DIR = Path(r"C:\Shaelvien") / "verify_reports" / "shaelvien_atlas_asset_pipeline_2"
base.REPORT_DIR = REPORT_DIR


def evaluate(cdp: base.CDP, expression: str, timeout: float = 30):
    return cdp.evaluate(expression, timeout=timeout)


def run_atlas(port: int, app_url: str) -> dict:
    cdp = base.new_tab(port, app_url)
    try:
        base.configure_viewport(cdp, 1440, 960, False)
        cdp.wait_for("Boolean(window.shaelvienApp && window.shaelvienApp.getState && window.shaelvienApp.runAtlasAcceptanceScript)", timeout=60)
        atlas_acceptance = evaluate(
            cdp,
            "window.shaelvienApp.runAtlasAcceptanceScript().then((result) => ({ ok: true, result })).catch((error) => ({ ok: false, error: error.message }))",
            timeout=60,
        )
        evaluate(
            cdp,
            """
            (() => {
              const app = window.shaelvienApp;
              const state = app.getState();
              state.currentMapId = "map-atlas-region-stream-demo";
              state.lastValidMapId = "map-atlas-region-stream-demo";
              state.role = "gm";
              state.scene = "MAP_EDIT";
              state.editor.inspectorOpen = true;
              return true;
            })()
            """,
            timeout=5,
        )
        browser = evaluate(
            cdp,
            """
            (() => {
              const cards = [...document.querySelectorAll("[data-atlas-asset-id]")].map((node) => node.dataset.atlasAssetId);
              const state = window.shaelvienApp.getState();
              const map = state.maps["map-atlas-region-stream-demo"];
              const waterfallRefs = map.atlasInstances.filter((instance) => instance.assetId === "atlas.wonder.waterfall.001").length;
              const streamRefs = map.atlasInstances.filter((instance) => instance.assetId === "atlas.region.water.stream.straight.001").length;
              const streamAssets = state.atlasRegistry.assets.filter((asset) => asset.collection === "streams_and_small_watercourses").length;
              return {
                cards,
                sourceCount: state.atlasRegistry.sources.length,
                assetCount: state.atlasRegistry.assets.length,
                waterfallRefs,
                streamRefs,
                streamAssets,
                currentMapId: state.currentMapId,
                selectedSummary: document.getElementById("selectedAtlasInstanceSummary")?.textContent || "",
                noHorizontalOverflow: document.documentElement.scrollWidth <= window.innerWidth + 1,
                noVerticalOverflow: document.documentElement.scrollHeight <= window.innerHeight + 1
              };
            })()
            """,
            timeout=10,
        )
        canvas = base.verify_canvas(cdp)
        return {
            "atlasAcceptance": atlas_acceptance,
            "browser": browser,
            "canvas": canvas,
            "consoleErrors": base.collect_console_errors(cdp),
            "screenshot": base.save_screenshot(cdp, "atlas_demo_desktop.png"),
        }
    finally:
        cdp.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9231)
    parser.add_argument("--app-url", default="http://127.0.0.1:8793/")
    args = parser.parse_args()

    proc = base.ensure_chrome(args.port)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "schemaVersion": "shaelvien.atlas.browser_verify.v1",
        "appUrl": args.app_url,
        "desktop": run_atlas(args.port, args.app_url),
    }
    browser = report["desktop"]["browser"]
    report["pass"] = (
        report["desktop"]["atlasAcceptance"].get("ok") is True
        and browser["sourceCount"] == 3
        and browser["assetCount"] == 11
        and browser["streamRefs"] >= 2
        and browser["streamAssets"] == 5
        and browser["currentMapId"] == "map-atlas-region-stream-demo"
        and len(browser["cards"]) >= 5
        and browser["noHorizontalOverflow"] is True
        and browser["noVerticalOverflow"] is True
        and report["desktop"]["canvas"]["nonTransparent"] > 100
        and not report["desktop"]["consoleErrors"]
    )
    report_path = REPORT_DIR / "ATLAS_BROWSER_VERIFICATION.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(report_path), "pass": report["pass"]}, indent=2))
    if proc is not None:
        proc.terminate()
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
