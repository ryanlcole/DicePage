"""Browser verification for SHAELVIEN-PERCEPTION-1."""

from __future__ import annotations

import json
import time
from pathlib import Path

import cdp_verify as base


ROOT = Path(r"C:\Shaelvien")
REPORT_DIR = ROOT / "verify_reports" / "shaelvien_perception_1"
base.REPORT_DIR = REPORT_DIR


def evaluate(cdp: base.CDP, expression: str, timeout: float = 30):
    return cdp.evaluate(expression, timeout=timeout)


def dispatch_pointer(
    cdp: base.CDP,
    event_type: str,
    point: dict,
    *,
    pointer_id: int = 1,
    pointer_type: str = "mouse",
    button: int = 0,
    buttons: int = 0,
) -> None:
    cdp.evaluate(
        f"""
        (() => {{
          const canvas = document.getElementById("gameCanvas");
          canvas.dispatchEvent(new PointerEvent("{event_type}", {{
            bubbles: true,
            cancelable: true,
            pointerId: {pointer_id},
            pointerType: "{pointer_type}",
            clientX: {int(point["x"])},
            clientY: {int(point["y"])},
            button: {button},
            buttons: {buttons}
          }}));
        }})()
        """,
        timeout=5,
    )


def pointer_click(cdp: base.CDP, point: dict, *, pointer_type: str = "mouse") -> None:
    dispatch_pointer(cdp, "pointerdown", point, pointer_type=pointer_type, button=0, buttons=1)
    dispatch_pointer(cdp, "pointerup", point, pointer_type=pointer_type, button=0, buttons=0)


def workspace_point(cdp: base.CDP, map_id: str, coords: str) -> dict:
    return evaluate(cdp, f"window.shaelvienApp.workspacePointForCell('{map_id}', {coords})", timeout=5)


def menu_inside_viewport(cdp: base.CDP, selector: str) -> bool:
    return evaluate(
        cdp,
        f"""
        (() => {{
          const r = document.querySelector("{selector}").getBoundingClientRect();
          return r.left >= 0 && r.top >= 0 && r.right <= window.innerWidth && r.bottom <= window.innerHeight;
        }})()
        """,
        timeout=5,
    )


async_reset = """
window.shaelvienApp.resetApplication().then(() => {
  const s = window.shaelvienApp.getState();
  s.currentMapId = "map-tavern-main-floor";
  s.lastValidMapId = "map-tavern-main-floor";
  s.scene = "MAP_VIEW";
  s.role = "player";
  s.actorPlayerId = "player-a";
  s.selectedEntityId = "pc-lyra";
  s.editor.activeTool = "select";
  s.editor.viewportByMap["map-tavern-main-floor"] = { zoom: 2, offsetX: 40, offsetY: 40, rotationDeg: 0, fitMode: "custom", gridVisible: true, compassVisible: true, initialized: true };
  return true;
})
"""


def run_desktop(port: int, app_url: str) -> dict:
    cdp = base.new_tab(port, app_url)
    try:
        base.configure_viewport(cdp, 1440, 960, False)
        cdp.wait_for("Boolean(window.shaelvienApp && window.shaelvienApp.getState)", timeout=15)
        perception_acceptance = evaluate(
            cdp,
            "window.shaelvienApp.runPerceptionAcceptanceScript().then((result) => ({ ok: true, result })).catch((error) => ({ ok: false, error: error.message }))",
            timeout=45,
        )
        app_acceptance = evaluate(
            cdp,
            "window.shaelvienApp.runAcceptanceScript().then((result) => ({ ok: true, result })).catch((error) => ({ ok: false, error: error.message }))",
            timeout=45,
        )
        evaluate(cdp, async_reset, timeout=20)
        point = workspace_point(cdp, "map-tavern-main-floor", "{ x: 2, y: 4 }")
        before_pan = evaluate(cdp, "JSON.stringify(window.shaelvienApp.getState().editor.viewportByMap['map-tavern-main-floor'])", timeout=5)
        evaluate(cdp, "window.shaelvienApp.getState().editor.activeTool = 'pan'", timeout=5)
        dispatch_pointer(cdp, "pointerdown", point, pointer_type="mouse", button=0, buttons=1)
        dispatch_pointer(cdp, "pointermove", {"x": point["x"] + 90, "y": point["y"] + 30}, pointer_type="mouse", button=0, buttons=1)
        dispatch_pointer(cdp, "pointerup", {"x": point["x"] + 90, "y": point["y"] + 30}, pointer_type="mouse", button=0, buttons=0)
        after_pan = evaluate(cdp, "JSON.stringify(window.shaelvienApp.getState().editor.viewportByMap['map-tavern-main-floor'])", timeout=5)
        canvas = base.verify_canvas(cdp)
        return {
            "perceptionAcceptance": perception_acceptance,
            "appAcceptance": app_acceptance,
            "desktopPanWorks": before_pan != after_pan,
            "canvas": canvas,
            "consoleErrors": base.collect_console_errors(cdp),
            "screenshot": base.save_screenshot(cdp, "desktop_perception_1440x960.png"),
        }
    finally:
        cdp.close()


def run_mobile(port: int, app_url: str) -> dict:
    cdp = base.new_tab(port, app_url)
    try:
        base.configure_viewport(cdp, 390, 844, True)
        cdp.wait_for("Boolean(window.shaelvienApp && window.shaelvienApp.getState)", timeout=15)
        evaluate(cdp, async_reset, timeout=20)
        point = workspace_point(cdp, "map-tavern-main-floor", "{ x: 2, y: 4 }")
        pointer_click(cdp, point, pointer_type="touch")
        tap_selects = evaluate(
            cdp,
            "window.shaelvienApp.getState().selection?.cellId === 'map-tavern-main-floor:square:2:4'",
            timeout=5,
        )
        before_drag = evaluate(cdp, "JSON.stringify(window.shaelvienApp.getState().editor.viewportByMap['map-tavern-main-floor'])", timeout=5)
        dispatch_pointer(cdp, "pointerdown", point, pointer_type="touch", pointer_id=10, button=0, buttons=1)
        dispatch_pointer(cdp, "pointermove", {"x": point["x"] + 70, "y": point["y"] + 44}, pointer_type="touch", pointer_id=10, button=0, buttons=1)
        dispatch_pointer(cdp, "pointerup", {"x": point["x"] + 70, "y": point["y"] + 44}, pointer_type="touch", pointer_id=10, button=0, buttons=0)
        after_drag = evaluate(cdp, "JSON.stringify(window.shaelvienApp.getState().editor.viewportByMap['map-tavern-main-floor'])", timeout=5)
        touch_release = evaluate(cdp, "window.shaelvienApp.getState().input.pointerActive === false", timeout=5)

        evaluate(
            cdp,
            """
            (() => {
              const s = window.shaelvienApp.getState();
              s.role = "gm";
              s.scene = "MAP_EDIT";
              s.currentMapId = "map-world";
              s.lastValidMapId = "map-world";
              s.editor.activeTool = "select";
              s.editor.viewportByMap["map-world"] = { zoom: 2, offsetX: 40, offsetY: 40, rotationDeg: 0, fitMode: "custom", gridVisible: true, compassVisible: true, initialized: true };
            })()
            """,
            timeout=5,
        )
        city_point = workspace_point(cdp, "map-world", "{ x: 7, y: 4 }")
        dispatch_pointer(cdp, "pointerdown", city_point, pointer_type="touch", pointer_id=11, button=0, buttons=1)
        time.sleep(0.72)
        long_press_menu = evaluate(cdp, "!document.getElementById('tileContextMenu').hidden", timeout=5)
        long_press_inside = menu_inside_viewport(cdp, "#tileContextMenu")
        dispatch_pointer(cdp, "pointerup", city_point, pointer_type="touch", pointer_id=11, button=0, buttons=0)

        evaluate(cdp, "window.shaelvienApp.runPerceptionAcceptanceScript().then(() => true)", timeout=45)
        pulse_ready = evaluate(cdp, "window.shaelvienApp.getState().perception?.current?.perceivedSounds?.length >= 0", timeout=5)
        return {
            "tapDistinctFromDrag": tap_selects,
            "touchDragPanWorks": before_drag != after_drag,
            "touchReleaseStopsInput": touch_release,
            "longPressContextMenu": long_press_menu,
            "longPressMenuInsideViewport": long_press_inside,
            "pulseDisplayStateAvailable": pulse_ready,
            "consoleErrors": base.collect_console_errors(cdp),
            "screenshot": base.save_screenshot(cdp, "mobile_perception_390x844.png"),
        }
    finally:
        cdp.close()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9225)
    parser.add_argument("--app-url", default="http://127.0.0.1:8780/")
    args = parser.parse_args()

    proc = base.ensure_chrome(args.port)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "schemaVersion": "shaelvien.perception.browser_verify.v1",
        "appUrl": args.app_url,
        "desktop": run_desktop(args.port, args.app_url),
        "mobile": run_mobile(args.port, args.app_url),
    }
    final_hash = report["desktop"]["appAcceptance"].get("result", {}).get("finalStateHash")
    report["pass"] = (
        report["desktop"]["perceptionAcceptance"].get("ok") is True
        and report["desktop"]["appAcceptance"].get("ok") is True
        and final_hash == "c7a4ac67"
        and report["desktop"]["desktopPanWorks"] is True
        and report["desktop"]["canvas"]["nonTransparent"] > 100
        and report["mobile"]["tapDistinctFromDrag"] is True
        and report["mobile"]["touchDragPanWorks"] is True
        and report["mobile"]["touchReleaseStopsInput"] is True
        and report["mobile"]["longPressContextMenu"] is True
        and report["mobile"]["longPressMenuInsideViewport"] is True
        and report["mobile"]["pulseDisplayStateAvailable"] is True
        and not report["desktop"]["consoleErrors"]
        and not report["mobile"]["consoleErrors"]
    )
    report_path = REPORT_DIR / "browser_perception_verification.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(report_path), "pass": report["pass"], "finalStateHash": final_hash}, indent=2))
    if proc is not None:
      proc.terminate()
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
