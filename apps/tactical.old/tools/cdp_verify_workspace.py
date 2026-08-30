"""Browser verification for SHAELVIEN-TACTICAL-WORKSPACE-1."""

from __future__ import annotations

import json
import time
from pathlib import Path

import cdp_verify as base


ROOT = Path(r"C:\Shaelvien")
REPORT_DIR = ROOT / "verify_reports" / "shaelvien_tactical_workspace_1"
base.REPORT_DIR = REPORT_DIR


def evaluate_async(cdp: base.CDP, expression: str, timeout: float = 30):
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


def workspace_point(cdp: base.CDP, map_id: str = "map-world", coords: str = "{ x: 7, y: 4 }") -> dict:
    return cdp.evaluate(
        f"window.shaelvienApp.workspacePointForCell('{map_id}', {coords})",
        timeout=5,
    )


def layout_metrics(cdp: base.CDP) -> dict:
    return cdp.evaluate(
        """
        (() => {
          const box = (selector) => {
            const r = document.querySelector(selector).getBoundingClientRect();
            return { left: r.left, top: r.top, right: r.right, bottom: r.bottom, width: r.width, height: r.height };
          };
          const viewport = box("#mapViewport");
          return {
            app: box(".app-shell"),
            appBar: box(".app-bar"),
            toolbar: box(".main-toolbar"),
            workspace: box(".workspace-shell"),
            mapViewport: viewport,
            inspector: box("#inspectorPanel"),
            status: box(".status-bar"),
            mapAreaRatio: (viewport.width * viewport.height) / (window.innerWidth * window.innerHeight),
            noVerticalPageScroll: document.documentElement.scrollHeight <= window.innerHeight + 1 && document.body.scrollHeight <= window.innerHeight + 1,
            noHorizontalOverflow: document.documentElement.scrollWidth <= window.innerWidth + 1,
            toolbarOverlap: !(box(".app-bar").bottom <= box(".main-toolbar").top + 1 && box(".main-toolbar").bottom <= viewport.top + 24),
            toolbarSingleRow: box(".main-toolbar").height <= 46,
            compassVisible: !document.getElementById("compassButton").hidden,
            zoomVisible: document.getElementById("zoomSelect").getBoundingClientRect().width > 0,
            statusText: document.getElementById("statusBar").innerText
          };
        })()
        """,
        timeout=5,
    )


def menu_inside_viewport(cdp: base.CDP, selector: str) -> bool:
    return cdp.evaluate(
        f"""
        (() => {{
          const r = document.querySelector("{selector}").getBoundingClientRect();
          return r.left >= 0 && r.top >= 0 && r.right <= window.innerWidth && r.bottom <= window.innerHeight;
        }})()
        """,
        timeout=5,
    )


def run_desktop(port: int, app_url: str) -> dict:
    cdp = base.new_tab(port, app_url)
    try:
        base.configure_viewport(cdp, 1440, 960, False)
        cdp.wait_for("Boolean(window.shaelvienApp && window.shaelvienApp.getState)", timeout=15)
        workspace_acceptance = evaluate_async(
            cdp,
            "window.shaelvienApp.runWorkspaceAcceptanceScript().then((result) => ({ ok: true, result })).catch((error) => ({ ok: false, error: error.message }))",
            timeout=45,
        )
        app_acceptance = evaluate_async(
            cdp,
            "window.shaelvienApp.runAcceptanceScript().then((result) => ({ ok: true, result })).catch((error) => ({ ok: false, error: error.message }))",
            timeout=45,
        )
        evaluate_async(cdp, "window.shaelvienApp.runWorkspaceAcceptanceScript().then(() => true)", timeout=45)
        metrics = layout_metrics(cdp)

        cdp.evaluate(
            """
            (() => {
              const s = window.shaelvienApp.getState();
              s.currentMapId = "map-world";
              s.lastValidMapId = "map-world";
              s.role = "gm";
              s.scene = "MAP_EDIT";
              const v = s.editor.viewportByMap["map-world"];
              v.rotationDeg = 90;
              v.fitMode = "fit-map";
              v.initialized = false;
            })()
            """,
            timeout=5,
        )
        point = workspace_point(cdp)
        pointer_click(cdp, point)
        rotated_left_selects = cdp.evaluate("window.shaelvienApp.getState().selectedTileId === 'tile-world-city'", timeout=5)
        dispatch_context_menu(cdp, point)
        right_menu = cdp.evaluate("!document.getElementById('tileContextMenu').hidden", timeout=5)
        right_menu_inside = menu_inside_viewport(cdp, "#tileContextMenu")
        cdp.command("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape"})
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
        cdp.evaluate("document.getElementById('zoomSelect').value = 'fit-width'; document.getElementById('zoomSelect').dispatchEvent(new Event('change', { bubbles: true }));", timeout=5)
        zoom_menu = cdp.evaluate("window.shaelvienApp.getState().editor.viewportByMap['map-world'].fitMode === 'fit-width'", timeout=5)
        cdp.evaluate("document.getElementById('rotateRightButton').click()", timeout=5)
        rotated = cdp.evaluate("window.shaelvienApp.getState().editor.viewportByMap['map-world'].rotationDeg", timeout=5)
        cdp.evaluate("document.getElementById('compassButton').click()", timeout=5)
        compass_reset = cdp.evaluate("window.shaelvienApp.getState().editor.viewportByMap['map-world'].rotationDeg === 0", timeout=5)

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

        cdp.evaluate("document.getElementById('moreMenuButton').click()", timeout=5)
        more_menu_inside = menu_inside_viewport(cdp, "#moreMenu")
        cdp.command("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape"})

        handle_visible = cdp.evaluate("document.getElementById('inspectorResizeHandle').getBoundingClientRect().height > 0", timeout=5)
        canvas = base.verify_canvas(cdp)
        screenshot = base.save_screenshot(cdp, "desktop_workspace_1440x960.png")
        refresh = cdp.command("Page.navigate", {"url": app_url})
        cdp.wait_for("Boolean(window.shaelvienApp && window.shaelvienApp.getState)", timeout=15)
        refresh_state = cdp.evaluate(
            "(() => { const s = window.shaelvienApp.getState(); return { scene: s.scene, currentMapId: s.currentMapId, valid: Boolean(s.maps[s.currentMapId]), viewport: s.editor.viewportByMap[s.currentMapId] }; })()",
            timeout=5,
        )
        return {
            "workspaceAcceptance": workspace_acceptance,
            "appAcceptance": app_acceptance,
            "layout": metrics,
            "rotatedLeftClickSelects": rotated_left_selects,
            "rightClickMenu": right_menu,
            "rightClickMenuInsideViewport": right_menu_inside,
            "browserContextOutsideMapAvailable": outside_context_allowed,
            "wheelZoomWorks": after_zoom != before_zoom,
            "zoomMenuWorks": zoom_menu,
            "rotateButtonAngle": rotated,
            "compassResetWorks": compass_reset,
            "dragPanWorks": after_pan != before_pan,
            "keyboardGuardWhileTyping": shortcut_guard,
            "moreMenuInsideViewport": more_menu_inside,
            "inspectorResizeHandleVisible": handle_visible,
            "canvas": canvas,
            "screenshot": screenshot,
            "refreshState": refresh_state,
            "consoleErrors": base.collect_console_errors(cdp),
        }
    finally:
        cdp.close()


def run_mobile(port: int, app_url: str) -> dict:
    cdp = base.new_tab(port, app_url)
    try:
        base.configure_viewport(cdp, 390, 844, True)
        cdp.wait_for("Boolean(window.shaelvienApp && window.shaelvienApp.getState)", timeout=15)
        workspace_acceptance = evaluate_async(
            cdp,
            "window.shaelvienApp.runWorkspaceAcceptanceScript().then((result) => ({ ok: true, result })).catch((error) => ({ ok: false, error: error.message }))",
            timeout=45,
        )
        metrics = layout_metrics(cdp)
        point = workspace_point(cdp)
        pointer_click(cdp, point, pointer_type="touch")
        tap_selects = cdp.evaluate("window.shaelvienApp.getState().selectedTileId === 'tile-world-city'", timeout=5)

        dispatch_pointer(cdp, "pointerdown", point, pointer_type="touch", pointer_id=11, button=0, buttons=1)
        time.sleep(0.75)
        long_press_menu = cdp.evaluate("!document.getElementById('tileContextMenu').hidden", timeout=5)
        long_press_inside = menu_inside_viewport(cdp, "#tileContextMenu")
        dispatch_pointer(cdp, "pointerup", point, pointer_type="touch", pointer_id=11, button=0, buttons=0)
        touch_released = cdp.evaluate("window.shaelvienApp.getState().input.pointerActive === false", timeout=5)

        before_zoom = cdp.evaluate("window.shaelvienApp.getState().editor.viewportByMap['map-world'].zoom", timeout=5)
        dispatch_pointer(cdp, "pointerdown", {"x": point["x"] - 20, "y": point["y"]}, pointer_type="touch", pointer_id=21, button=0, buttons=1)
        dispatch_pointer(cdp, "pointerdown", {"x": point["x"] + 20, "y": point["y"]}, pointer_type="touch", pointer_id=22, button=0, buttons=1)
        dispatch_pointer(cdp, "pointermove", {"x": point["x"] - 45, "y": point["y"]}, pointer_type="touch", pointer_id=21, button=0, buttons=1)
        dispatch_pointer(cdp, "pointermove", {"x": point["x"] + 45, "y": point["y"]}, pointer_type="touch", pointer_id=22, button=0, buttons=1)
        dispatch_pointer(cdp, "pointerup", {"x": point["x"] - 45, "y": point["y"]}, pointer_type="touch", pointer_id=21, button=0, buttons=0)
        dispatch_pointer(cdp, "pointerup", {"x": point["x"] + 45, "y": point["y"]}, pointer_type="touch", pointer_id=22, button=0, buttons=0)
        after_zoom = cdp.evaluate("window.shaelvienApp.getState().editor.viewportByMap['map-world'].zoom", timeout=5)

        cdp.evaluate("document.getElementById('toggleInspectorButton').click()", timeout=5)
        time.sleep(0.25)
        sheet_half = cdp.evaluate("document.body.dataset.sheetState === 'half' && document.getElementById('inspectorPanel').getBoundingClientRect().top < window.innerHeight", timeout=5)
        cdp.evaluate("document.querySelector('#inspectorPanel .inspector-title').click()", timeout=5)
        time.sleep(0.25)
        sheet_full = cdp.evaluate("document.body.dataset.sheetState === 'full' && document.getElementById('inspectorPanel').getBoundingClientRect().top < window.innerHeight / 3", timeout=5)
        cdp.evaluate("document.getElementById('closeInspectorButton').click()", timeout=5)
        sheet_collapsed = cdp.evaluate("document.body.dataset.sheetState === 'collapsed'", timeout=5)

        cdp.evaluate("window.shaelvienApp.getState().editor.viewportByMap['map-world'].rotationDeg = 0", timeout=5)
        cdp.evaluate("document.getElementById('rotateRightButton').click()", timeout=5)
        rotation_reachable = cdp.evaluate("window.shaelvienApp.getState().editor.viewportByMap['map-world'].rotationDeg === 90", timeout=5)
        cdp.evaluate("document.getElementById('compassButton').click()", timeout=5)
        compass_reset = cdp.evaluate("window.shaelvienApp.getState().editor.viewportByMap['map-world'].rotationDeg === 0", timeout=5)
        player_context_hidden = cdp.evaluate(
            "(() => { const s = window.shaelvienApp.getState(); s.role = 'player'; s.scene = 'MAP_VIEW'; return document.getElementById('tileContextMenu').hidden; })()",
            timeout=5,
        )
        screenshot = base.save_screenshot(cdp, "mobile_workspace_390x844.png")
        cdp.command("Page.navigate", {"url": app_url})
        cdp.wait_for("Boolean(window.shaelvienApp && window.shaelvienApp.getState)", timeout=15)
        refresh_state = cdp.evaluate(
            "(() => { const s = window.shaelvienApp.getState(); return { scene: s.scene, currentMapId: s.currentMapId, valid: Boolean(s.maps[s.currentMapId]), viewport: s.editor.viewportByMap[s.currentMapId], inspectorOpen: s.editor.inspectorOpen }; })()",
            timeout=5,
        )
        return {
            "workspaceAcceptance": workspace_acceptance,
            "layout": metrics,
            "tapSelectsExactTile": tap_selects,
            "longPressMenu": long_press_menu,
            "longPressMenuInsideViewport": long_press_inside,
            "touchReleaseStopsInput": touch_released,
            "pinchZoomWorks": after_zoom != before_zoom,
            "inspectorSheetHalf": sheet_half,
            "inspectorSheetFull": sheet_full,
            "inspectorSheetCollapsed": sheet_collapsed,
            "rotationControlReachable": rotation_reachable,
            "compassResetWorks": compass_reset,
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
    parser.add_argument("--port", type=int, default=9225)
    parser.add_argument("--app-url", default="http://127.0.0.1:8780/")
    args = parser.parse_args()

    proc = base.ensure_chrome(args.port)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "schemaVersion": "shaelvien.tactical.workspace.browser_verify.v1",
        "appUrl": args.app_url,
        "desktop": run_desktop(args.port, args.app_url),
        "mobile": run_mobile(args.port, args.app_url),
    }
    desktop = report["desktop"]
    mobile = report["mobile"]
    final_hash = desktop["appAcceptance"].get("result", {}).get("finalStateHash")
    report["pass"] = (
        desktop["workspaceAcceptance"].get("ok") is True
        and desktop["appAcceptance"].get("ok") is True
        and final_hash == "c7a4ac67"
        and desktop["layout"]["noVerticalPageScroll"] is True
        and desktop["layout"]["noHorizontalOverflow"] is True
        and desktop["layout"]["toolbarOverlap"] is False
        and desktop["layout"]["toolbarSingleRow"] is True
        and desktop["rotatedLeftClickSelects"] is True
        and desktop["rightClickMenu"] is True
        and desktop["rightClickMenuInsideViewport"] is True
        and desktop["browserContextOutsideMapAvailable"] is True
        and desktop["wheelZoomWorks"] is True
        and desktop["zoomMenuWorks"] is True
        and desktop["rotateButtonAngle"] in (0, 90, 180, 270)
        and desktop["compassResetWorks"] is True
        and desktop["dragPanWorks"] is True
        and desktop["keyboardGuardWhileTyping"] is True
        and desktop["moreMenuInsideViewport"] is True
        and desktop["inspectorResizeHandleVisible"] is True
        and desktop["canvas"]["nonTransparent"] > 100
        and mobile["workspaceAcceptance"].get("ok") is True
        and mobile["layout"]["noVerticalPageScroll"] is True
        and mobile["layout"]["noHorizontalOverflow"] is True
        and mobile["layout"]["toolbarOverlap"] is False
        and mobile["layout"]["mapAreaRatio"] > 0.62
        and mobile["tapSelectsExactTile"] is True
        and mobile["longPressMenu"] is True
        and mobile["longPressMenuInsideViewport"] is True
        and mobile["touchReleaseStopsInput"] is True
        and mobile["pinchZoomWorks"] is True
        and mobile["inspectorSheetHalf"] is True
        and mobile["inspectorSheetFull"] is True
        and mobile["inspectorSheetCollapsed"] is True
        and mobile["rotationControlReachable"] is True
        and mobile["compassResetWorks"] is True
        and mobile["playerContextActionsHidden"] is True
        and not desktop["consoleErrors"]
        and not mobile["consoleErrors"]
    )
    report_path = REPORT_DIR / "browser_workspace_verification.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(report_path), "pass": report["pass"], "finalStateHash": final_hash}, indent=2))
    if proc is not None:
        proc.terminate()
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
