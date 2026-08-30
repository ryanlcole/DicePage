"""Browser verification for SHAELVIEN-TACTICAL-EDITOR-1."""

from __future__ import annotations

import json
import time
from pathlib import Path

import cdp_verify as base


ROOT = Path(r"C:\Shaelvien")
REPORT_DIR = ROOT / "verify_reports" / "shaelvien_tactical_editor_1"
base.REPORT_DIR = REPORT_DIR


def evaluate_async(cdp: base.CDP, expression: str, timeout: float = 30):
    return cdp.evaluate(expression, timeout=timeout)


def canvas_click_point(cdp: base.CDP, tile_id: str = "tile-world-city") -> dict:
    return cdp.evaluate(
        f"""
        (() => {{
          const s = window.shaelvienApp.getState();
          const map = s.maps["map-world"];
          const tile = map.placedTiles.find((item) => item.id === "{tile_id}");
          const viewport = s.editor.viewportByMap["map-world"] || {{ zoom: 1, offsetX: 0, offsetY: 0 }};
          const rect = document.getElementById("gameCanvas").getBoundingClientRect();
          const worldX = (tile.x + 0.5) * map.tileSize;
          const worldY = (tile.y + 0.5) * map.tileSize;
          return {{
            x: Math.round(rect.left + worldX * viewport.zoom + viewport.offsetX),
            y: Math.round(rect.top + worldY * viewport.zoom + viewport.offsetY),
            rect: {{ left: rect.left, top: rect.top, width: rect.width, height: rect.height }}
          }};
        }})()
        """,
        timeout=5,
    )


def dispatch_pointer(cdp: base.CDP, event_type: str, point: dict, *, pointer_id: int = 1, pointer_type: str = "mouse", button: int = 0, buttons: int = 0) -> None:
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


def dispatch_context_menu(cdp: base.CDP, point: dict) -> None:
    cdp.evaluate(
        f"""
        (() => {{
          const canvas = document.getElementById("gameCanvas");
          canvas.dispatchEvent(new PointerEvent("pointerdown", {{ bubbles: true, cancelable: true, pointerId: 2, pointerType: "mouse", clientX: {int(point["x"])}, clientY: {int(point["y"])}, button: 2, buttons: 2 }}));
          canvas.dispatchEvent(new MouseEvent("contextmenu", {{ bubbles: true, cancelable: true, clientX: {int(point["x"])}, clientY: {int(point["y"])}, button: 2, buttons: 2 }}));
          canvas.dispatchEvent(new PointerEvent("pointerup", {{ bubbles: true, cancelable: true, pointerId: 2, pointerType: "mouse", clientX: {int(point["x"])}, clientY: {int(point["y"])}, button: 2, buttons: 0 }}));
        }})()
        """,
        timeout=5,
    )


def dispatch_wheel(cdp: base.CDP, point: dict, delta_y: int) -> None:
    cdp.evaluate(
        f"""
        (() => {{
          const canvas = document.getElementById("gameCanvas");
          canvas.dispatchEvent(new WheelEvent("wheel", {{ bubbles: true, cancelable: true, clientX: {int(point["x"])}, clientY: {int(point["y"])}, deltaY: {delta_y}, deltaX: 0 }}));
        }})()
        """,
        timeout=5,
    )


def run_desktop_editor(port: int, app_url: str) -> dict:
    cdp = base.new_tab(port, app_url)
    try:
        base.configure_viewport(cdp, 1440, 960, False)
        cdp.wait_for("Boolean(window.shaelvienApp && window.shaelvienApp.getState)", timeout=15)
        editor_acceptance = evaluate_async(
            cdp,
            "window.shaelvienApp.runEditorAcceptanceScript().then((result) => ({ ok: true, result })).catch((error) => ({ ok: false, error: error.message }))",
            timeout=40,
        )
        pointy_show = cdp.evaluate("window.shaelvienApp.showMapForVerification('map-editor-hex-pointy')", timeout=5)
        pointy_canvas = base.verify_canvas(cdp)
        pointy_screenshot = base.save_screenshot(cdp, "desktop_hex_pointy.png")
        flat_show = cdp.evaluate("window.shaelvienApp.showMapForVerification('map-editor-hex-flat')", timeout=5)
        flat_canvas = base.verify_canvas(cdp)
        flat_screenshot = base.save_screenshot(cdp, "desktop_hex_flat.png")
        app_acceptance = evaluate_async(
            cdp,
            "window.shaelvienApp.runAcceptanceScript().then((result) => ({ ok: true, result })).catch((error) => ({ ok: false, error: error.message }))",
            timeout=40,
        )
        evaluate_async(
            cdp,
            "window.shaelvienApp.runEditorAcceptanceScript().then(() => true)",
            timeout=40,
        )
        point = canvas_click_point(cdp)
        pointer_click(cdp, point)
        left_selected = cdp.evaluate("window.shaelvienApp.getState().selectedTileId === 'tile-world-city'", timeout=5)

        dispatch_context_menu(cdp, point)
        right_menu = cdp.evaluate("!document.getElementById('tileContextMenu').hidden", timeout=5)
        menu_inside = cdp.evaluate(
            "(() => { const r = document.getElementById('tileContextMenu').getBoundingClientRect(); return r.left >= 0 && r.top >= 0 && r.right <= window.innerWidth && r.bottom <= window.innerHeight; })()",
            timeout=5,
        )

        outside_context_allowed = cdp.evaluate(
            """
            (() => {
              const event = new MouseEvent("contextmenu", { bubbles: true, cancelable: true, clientX: 2, clientY: 2 });
              document.body.dispatchEvent(event);
              return event.defaultPrevented === false;
            })()
            """,
            timeout=5,
        )

        before_zoom = cdp.evaluate("window.shaelvienApp.getState().editor.viewportByMap['map-world'].zoom", timeout=5)
        dispatch_wheel(cdp, point, -240)
        after_zoom = cdp.evaluate("window.shaelvienApp.getState().editor.viewportByMap['map-world'].zoom", timeout=5)

        before_pan = cdp.evaluate("JSON.stringify(window.shaelvienApp.getState().editor.viewportByMap['map-world'])", timeout=5)
        cdp.evaluate("window.shaelvienApp.getState().editor.activeTool = 'pan'", timeout=5)
        dispatch_pointer(cdp, "pointerdown", point, pointer_type="mouse", button=0, buttons=1)
        dispatch_pointer(cdp, "pointermove", {"x": point["x"] + 80, "y": point["y"] + 40}, pointer_type="mouse", button=0, buttons=1)
        dispatch_pointer(cdp, "pointerup", {"x": point["x"] + 80, "y": point["y"] + 40}, pointer_type="mouse", button=0, buttons=0)
        after_pan = cdp.evaluate("JSON.stringify(window.shaelvienApp.getState().editor.viewportByMap['map-world'])", timeout=5)

        cdp.evaluate("document.getElementById('mapSettingsButton').click(); document.getElementById('settingsMapName').focus(); window.shaelvienApp.getState().editor.activeTool = 'pan';", timeout=5)
        cdp.command("Input.dispatchKeyEvent", {"type": "keyDown", "key": "v", "code": "KeyV"})
        cdp.command("Input.dispatchKeyEvent", {"type": "keyUp", "key": "v", "code": "KeyV"})
        shortcut_guard = cdp.evaluate("window.shaelvienApp.getState().editor.activeTool === 'pan'", timeout=5)
        cdp.evaluate("document.getElementById('mapSettingsDialog').close()", timeout=5)

        canvas = base.verify_canvas(cdp)
        overflow = cdp.evaluate("document.documentElement.scrollWidth <= window.innerWidth", timeout=5)
        screenshot = base.save_screenshot(cdp, "desktop_editor_1440x960.png")
        refresh = cdp.command("Page.navigate", {"url": app_url})
        cdp.wait_for("Boolean(window.shaelvienApp && window.shaelvienApp.getState)", timeout=15)
        refresh_state = cdp.evaluate(
            "(() => { const s = window.shaelvienApp.getState(); return { scene: s.scene, currentMapId: s.currentMapId, valid: Boolean(s.maps[s.currentMapId]), selection: s.selection }; })()",
            timeout=5,
        )
        return {
            "editorAcceptance": editor_acceptance,
            "appAcceptance": app_acceptance,
            "pointyHexRender": {"show": pointy_show, "canvas": pointy_canvas, "screenshot": pointy_screenshot},
            "flatHexRender": {"show": flat_show, "canvas": flat_canvas, "screenshot": flat_screenshot},
            "leftClickSelects": left_selected,
            "rightClickMenu": right_menu,
            "contextMenuInsideViewport": menu_inside,
            "browserContextOutsideMapAvailable": outside_context_allowed,
            "wheelZoomWorks": after_zoom != before_zoom,
            "dragPanWorks": after_pan != before_pan,
            "keyboardGuardWhileTyping": shortcut_guard,
            "canvas": canvas,
            "noHorizontalOverflow": overflow,
            "screenshot": screenshot,
            "refreshState": refresh_state,
            "consoleErrors": base.collect_console_errors(cdp),
        }
    finally:
        cdp.close()


def run_mobile_editor(port: int, app_url: str) -> dict:
    cdp = base.new_tab(port, app_url)
    try:
        base.configure_viewport(cdp, 390, 844, True)
        cdp.wait_for("Boolean(window.shaelvienApp && window.shaelvienApp.getState)", timeout=15)
        evaluate_async(cdp, "window.shaelvienApp.runEditorAcceptanceScript().then(() => true)", timeout=40)
        point = canvas_click_point(cdp)
        pointer_click(cdp, point, pointer_type="touch")
        tap_selects = cdp.evaluate("window.shaelvienApp.getState().selectedTileId === 'tile-world-city'", timeout=5)

        dispatch_pointer(cdp, "pointerdown", point, pointer_type="touch", pointer_id=11, button=0, buttons=1)
        time.sleep(0.75)
        long_press_menu = cdp.evaluate("!document.getElementById('tileContextMenu').hidden", timeout=5)
        menu_inside = cdp.evaluate(
            "(() => { const r = document.getElementById('tileContextMenu').getBoundingClientRect(); return r.left >= 0 && r.top >= 0 && r.right <= window.innerWidth && r.bottom <= window.innerHeight; })()",
            timeout=5,
        )
        dispatch_pointer(cdp, "pointerup", point, pointer_type="touch", pointer_id=11, button=0, buttons=0)
        touch_released = cdp.evaluate("window.shaelvienApp.getState().input.pointerActive === false", timeout=5)

        before_pan = cdp.evaluate("JSON.stringify(window.shaelvienApp.getState().editor.viewportByMap['map-world'])", timeout=5)
        cdp.evaluate("window.shaelvienApp.getState().editor.activeTool = 'pan'", timeout=5)
        dispatch_pointer(cdp, "pointerdown", point, pointer_type="touch", pointer_id=12, button=0, buttons=1)
        dispatch_pointer(cdp, "pointermove", {"x": point["x"] + 55, "y": point["y"] + 20}, pointer_type="touch", pointer_id=12, button=0, buttons=1)
        dispatch_pointer(cdp, "pointerup", {"x": point["x"] + 55, "y": point["y"] + 20}, pointer_type="touch", pointer_id=12, button=0, buttons=0)
        after_pan = cdp.evaluate("JSON.stringify(window.shaelvienApp.getState().editor.viewportByMap['map-world'])", timeout=5)

        before_zoom = cdp.evaluate("window.shaelvienApp.getState().editor.viewportByMap['map-world'].zoom", timeout=5)
        dispatch_pointer(cdp, "pointerdown", {"x": point["x"] - 20, "y": point["y"]}, pointer_type="touch", pointer_id=21, button=0, buttons=1)
        dispatch_pointer(cdp, "pointerdown", {"x": point["x"] + 20, "y": point["y"]}, pointer_type="touch", pointer_id=22, button=0, buttons=1)
        dispatch_pointer(cdp, "pointermove", {"x": point["x"] - 45, "y": point["y"]}, pointer_type="touch", pointer_id=21, button=0, buttons=1)
        dispatch_pointer(cdp, "pointermove", {"x": point["x"] + 45, "y": point["y"]}, pointer_type="touch", pointer_id=22, button=0, buttons=1)
        dispatch_pointer(cdp, "pointerup", {"x": point["x"] - 45, "y": point["y"]}, pointer_type="touch", pointer_id=21, button=0, buttons=0)
        dispatch_pointer(cdp, "pointerup", {"x": point["x"] + 45, "y": point["y"]}, pointer_type="touch", pointer_id=22, button=0, buttons=0)
        after_zoom = cdp.evaluate("window.shaelvienApp.getState().editor.viewportByMap['map-world'].zoom", timeout=5)

        rect = cdp.evaluate(
            "(() => { const r = document.getElementById('mapViewport').getBoundingClientRect(); return { width: r.width, height: r.height, areaRatio: (r.width * r.height) / (window.innerWidth * window.innerHeight) }; })()",
            timeout=5,
        )
        bottom_sheet = cdp.evaluate(
            "(() => { document.body.classList.add('inspector-open'); const visible = document.getElementById('inspectorPanel').getBoundingClientRect().top < window.innerHeight; document.body.classList.remove('inspector-open'); return visible; })()",
            timeout=5,
        )
        overflow = cdp.evaluate("document.documentElement.scrollWidth <= window.innerWidth", timeout=5)
        screenshot = base.save_screenshot(cdp, "mobile_editor_390x844.png")
        cdp.command("Page.navigate", {"url": app_url})
        cdp.wait_for("Boolean(window.shaelvienApp && window.shaelvienApp.getState)", timeout=15)
        refresh_state = cdp.evaluate(
            "(() => { const s = window.shaelvienApp.getState(); return { scene: s.scene, currentMapId: s.currentMapId, valid: Boolean(s.maps[s.currentMapId]), selection: s.selection }; })()",
            timeout=5,
        )
        player_context_hidden = cdp.evaluate(
            "(() => { const s = window.shaelvienApp.getState(); s.role = 'player'; s.scene = 'MAP_VIEW'; return document.querySelectorAll('#tileContextMenu [data-context-action]').length > 0 && document.getElementById('tileContextMenu').hidden; })()",
            timeout=5,
        )
        return {
            "tapSelectsExactTile": tap_selects,
            "longPressMenu": long_press_menu,
            "contextMenuInsideViewport": menu_inside,
            "touchReleaseStopsInput": touch_released,
            "panDoesNotSelectAccidentally": after_pan != before_pan,
            "pinchZoomWorks": after_zoom != before_zoom,
            "mapViewport": rect,
            "bottomSheetOpens": bottom_sheet,
            "noHorizontalOverflow": overflow,
            "playerContextActionsHidden": player_context_hidden,
            "screenshot": screenshot,
            "refreshState": refresh_state,
            "consoleErrors": base.collect_console_errors(cdp),
        }
    finally:
        cdp.close()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9224)
    parser.add_argument("--app-url", default="http://127.0.0.1:8780/")
    args = parser.parse_args()

    proc = base.ensure_chrome(args.port)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "schemaVersion": "shaelvien.tactical.editor.browser_verify.v1",
        "appUrl": args.app_url,
        "desktop": run_desktop_editor(args.port, args.app_url),
        "mobile": run_mobile_editor(args.port, args.app_url),
    }
    desktop = report["desktop"]
    mobile = report["mobile"]
    report["pass"] = (
        desktop["editorAcceptance"].get("ok") is True
        and desktop["appAcceptance"].get("ok") is True
        and desktop["pointyHexRender"]["show"].get("ok") is True
        and desktop["pointyHexRender"]["canvas"]["nonTransparent"] > 100
        and desktop["flatHexRender"]["show"].get("ok") is True
        and desktop["flatHexRender"]["canvas"]["nonTransparent"] > 100
        and desktop["leftClickSelects"] is True
        and desktop["rightClickMenu"] is True
        and desktop["browserContextOutsideMapAvailable"] is True
        and desktop["wheelZoomWorks"] is True
        and desktop["dragPanWorks"] is True
        and desktop["keyboardGuardWhileTyping"] is True
        and desktop["noHorizontalOverflow"] is True
        and mobile["tapSelectsExactTile"] is True
        and mobile["longPressMenu"] is True
        and mobile["touchReleaseStopsInput"] is True
        and mobile["pinchZoomWorks"] is True
        and mobile["bottomSheetOpens"] is True
        and mobile["noHorizontalOverflow"] is True
        and mobile["playerContextActionsHidden"] is True
        and not desktop["consoleErrors"]
        and not mobile["consoleErrors"]
    )
    report_path = REPORT_DIR / "browser_editor_verification.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(report_path), "pass": report["pass"]}, indent=2))
    if proc is not None:
        proc.terminate()
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
