"""Browser verification for the public static Atlas preview build."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cdp_verify as base


REPORT_DIR = Path(r"C:\Shaelvien") / "verify_reports" / "shaelvien_atlas_asset_pipeline_2"
base.REPORT_DIR = REPORT_DIR


def run_public_atlas(port: int, app_url: str) -> dict:
    cdp = base.new_tab(port, app_url)
    try:
        base.configure_viewport(cdp, 1440, 960, False)
        cdp.wait_for("Boolean(window.shaelvienApp && window.shaelvienApp.getState)", timeout=60)
        details = cdp.evaluate(
            """
            (async () => {
              const app = window.shaelvienApp;
              app.showMapForVerification("map-atlas-region-stream-demo");
              await new Promise((resolve) => setTimeout(resolve, 900));
              const state = app.getState();
              const registry = state.atlasRegistry;
              const map = state.maps["map-atlas-region-stream-demo"];
              const child = state.maps["map-atlas-region-stream-source"];
              const streamAssets = registry.assets.filter((asset) => asset.collection === "streams_and_small_watercourses");
              const cards = [...document.querySelectorAll("[data-atlas-asset-id]")].map((node) => node.dataset.atlasAssetId);
              const text = JSON.stringify({ registry, map, child });
              const fetches = await Promise.all(streamAssets.map(async (asset) => {
                try {
                  const response = await fetch(asset.derivedPath, { cache: "no-store" });
                  return { assetId: asset.assetId, path: asset.derivedPath, status: response.status, ok: response.ok };
                } catch (error) {
                  return { assetId: asset.assetId, path: asset.derivedPath, status: 0, ok: false, error: error.message };
                }
              }));
              return {
                publicRuntimeRegistry: registry.publicRuntimeRegistry === true,
                sourceCacheIncluded: registry.sourceCacheIncluded === true,
                sourceCount: registry.sources.length,
                assetCount: registry.assets.length,
                streamAssetCount: streamAssets.length,
                streamShapeModels: [...new Set(streamAssets.map((asset) => asset.shapeModel))],
                streamStorageEnvelopeFlags: streamAssets.map((asset) => asset.rectIsStorageEnvelope === true),
                fetches,
                cards,
                mapId: map?.id || null,
                currentMapId: state.currentMapId,
                streamInstances: map?.atlasInstances?.filter((instance) => instance.assetId.startsWith("atlas.region.water.stream.")).length || 0,
                reusedStraight001: map?.atlasInstances?.filter((instance) => instance.assetId === "atlas.region.water.stream.straight.001").length || 0,
                rotatedInstances: map?.atlasInstances?.filter((instance) => instance.rotationDeg !== 0).length || 0,
                childMapLinked: map?.atlasInstances?.some((instance) => instance.childMapId === "map-atlas-region-stream-source") === true,
                childReverseLink: child?.parentMapId === "map-atlas-region-stream-demo" && child?.parentAtlasInstanceId === "atlas-region-stream-pool-001",
                noWindowsPath: !text.includes("C:\\\\") && !text.includes("A:\\\\") && !text.includes("P:\\\\"),
                noSourceImageFields: !text.includes("sourceImage"),
                noLocalSourcePath: !text.includes("localSourcePath"),
                noHorizontalOverflow: document.documentElement.scrollWidth <= window.innerWidth + 1,
                noVerticalOverflow: document.documentElement.scrollHeight <= window.innerHeight + 1
              };
            })()
            """,
            timeout=30,
        )
        canvas = base.verify_canvas(cdp)
        console_errors = [
            error for error in base.collect_console_errors(cdp)
            if "ERR_NO_BUFFER_SPACE" not in error
        ]
        return {
            "details": details,
            "canvas": canvas,
            "consoleErrors": console_errors,
            "screenshot": base.save_screenshot(cdp, "atlas_public_preview_desktop.png"),
        }
    finally:
        cdp.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9251)
    parser.add_argument("--app-url", default="http://127.0.0.1:8794/app/")
    args = parser.parse_args()

    proc = base.ensure_chrome(args.port)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "schemaVersion": "shaelvien.atlas.public_browser_verify.v1",
        "appUrl": args.app_url,
        "desktop": run_public_atlas(args.port, args.app_url),
    }
    details = report["desktop"]["details"]
    report["pass"] = (
        details["publicRuntimeRegistry"] is True
        and details["sourceCacheIncluded"] is False
        and details["sourceCount"] == 0
        and details["assetCount"] == 11
        and details["streamAssetCount"] == 5
        and details["streamShapeModels"] == ["irregular_alpha_mask"]
        and all(details["streamStorageEnvelopeFlags"])
        and all(item["ok"] for item in details["fetches"])
        and details["currentMapId"] == "map-atlas-region-stream-demo"
        and details["streamInstances"] >= 5
        and details["reusedStraight001"] >= 2
        and details["rotatedInstances"] >= 1
        and details["childMapLinked"] is True
        and details["childReverseLink"] is True
        and details["noWindowsPath"] is True
        and details["noSourceImageFields"] is True
        and details["noLocalSourcePath"] is True
        and details["noHorizontalOverflow"] is True
        and details["noVerticalOverflow"] is True
        and report["desktop"]["canvas"]["nonTransparent"] > 100
        and not report["desktop"]["consoleErrors"]
    )
    report_path = REPORT_DIR / "ATLAS_PUBLIC_BROWSER_VERIFICATION.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(report_path), "pass": report["pass"]}, indent=2))
    if proc is not None:
        proc.terminate()
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
