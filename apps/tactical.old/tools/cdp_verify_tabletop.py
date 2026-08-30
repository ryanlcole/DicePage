"""Browser verification for SHAELVIEN-DIGITAL-TABLETOP-1."""

from __future__ import annotations

import json
import time
from pathlib import Path

import cdp_verify as base


REPORT_DIR = Path(r"C:\Shaelvien") / "verify_reports" / "shaelvien_digital_tabletop_1"
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


def click_point(cdp: base.CDP, point: dict, *, pointer_type: str = "mouse") -> None:
    dispatch_pointer(cdp, "pointerdown", point, pointer_type=pointer_type, button=0, buttons=1)
    dispatch_pointer(cdp, "pointerup", point, pointer_type=pointer_type, button=0, buttons=0)


def workspace_point(cdp: base.CDP, map_id: str, coords: str) -> dict:
    return evaluate(cdp, f"window.shaelvienApp.workspacePointForCell('{map_id}', {coords})", timeout=5)


def layout_metrics(cdp: base.CDP) -> dict:
    return evaluate(
        cdp,
        """
        (() => {
          const rect = (selector) => {
            const el = document.querySelector(selector);
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return { left: r.left, top: r.top, right: r.right, bottom: r.bottom, width: r.width, height: r.height };
          };
          const viewport = rect("#mapViewport");
          const overlay = rect("#tabletopOverlay");
          const noPageScroll = document.documentElement.scrollHeight <= window.innerHeight + 1
            && document.body.scrollHeight <= window.innerHeight + 1;
          const noHorizontalOverflow = document.documentElement.scrollWidth <= window.innerWidth + 1
            && document.body.scrollWidth <= window.innerWidth + 1;
          return {
            app: rect(".app-shell"),
            mapViewport: viewport,
            appBar: rect(".app-bar"),
            toolbar: rect(".main-toolbar"),
            bottomTray: rect(".tabletop-bottom"),
            overlay,
            mapAreaRatio: (viewport.width * viewport.height) / (window.innerWidth * window.innerHeight),
            noPageScroll,
            noHorizontalOverflow,
            overlayHidden: document.getElementById("tabletopOverlay").hidden,
            diceCount: document.querySelectorAll("[data-die-id]").length,
            playerDeckExists: document.getElementById("tabletopPlayerDeck")?.innerText.includes("Player A Deck") || false,
            monsterDeckExists: document.getElementById("tabletopMonsterDeck")?.innerText.includes("Orc Deck") || false,
            loreScrollExists: Boolean(document.getElementById("tabletopLoreScroll")),
            initiativeEntries: document.querySelectorAll(".initiative-entry").length,
            clockExists: Boolean(document.getElementById("tabletopClockPauseButton"))
          };
        })()
        """,
        timeout=5,
    )


def tabletop_acceptance(cdp: base.CDP) -> dict:
    return evaluate(
        cdp,
        "window.shaelvienApp.runTabletopAcceptanceScript().then((result) => ({ ok: true, result })).catch((error) => ({ ok: false, error: error.message }))",
        timeout=45,
    )


def app_acceptance(cdp: base.CDP) -> dict:
    return evaluate(
        cdp,
        "window.shaelvienApp.runAcceptanceScript().then((result) => ({ ok: true, result })).catch((error) => ({ ok: false, error: error.message }))",
        timeout=45,
    )


def overlay_centered(cdp: base.CDP) -> bool:
    return evaluate(
        cdp,
        """
        (() => {
          const r = document.getElementById("tabletopOverlay").getBoundingClientRect();
          const centerX = window.innerWidth / 2;
          const centerY = window.innerHeight / 2;
          return Math.abs((r.left + r.width / 2) - centerX) < window.innerWidth * 0.12
            && Math.abs((r.top + r.height / 2) - centerY) < window.innerHeight * 0.12
            && r.left >= 0 && r.top >= 0 && r.right <= window.innerWidth && r.bottom <= window.innerHeight;
        })()
        """,
        timeout=5,
    )


def run_desktop(port: int, app_url: str) -> dict:
    cdp = base.new_tab(port, app_url)
    try:
        base.configure_viewport(cdp, 1440, 960, False)
        cdp.wait_for("Boolean(window.shaelvienApp && window.shaelvienApp.getState)", timeout=60)
        tabletop = tabletop_acceptance(cdp)
        evaluate(cdp, "window.shaelvienApp.showMapForVerification('map-world'); window.shaelvienApp.getState().role = 'gm'; window.shaelvienApp.getState().scene = 'MAP_EDIT'; window.shaelvienApp.getState().editor.activeTool = 'select'; window.shaelvienApp.getState().editor.inspectorOpen = false;", timeout=5)
        metrics = layout_metrics(cdp)
        point = workspace_point(cdp, "map-world", "{ x: 7, y: 4 }")
        before = evaluate(cdp, "JSON.stringify(window.shaelvienApp.getState().editor.viewportByMap['map-world'])", timeout=5)
        evaluate(cdp, "window.shaelvienApp.getState().editor.activeTool = 'pan'", timeout=5)
        dispatch_pointer(cdp, "pointerdown", point, pointer_type="mouse", button=0, buttons=1)
        dispatch_pointer(cdp, "pointermove", {"x": point["x"] + 90, "y": point["y"] + 44}, pointer_type="mouse", button=0, buttons=1)
        dispatch_pointer(cdp, "pointerup", {"x": point["x"] + 90, "y": point["y"] + 44}, pointer_type="mouse", button=0, buttons=0)
        after = evaluate(cdp, "JSON.stringify(window.shaelvienApp.getState().editor.viewportByMap['map-world'])", timeout=5)
        evaluate(cdp, "window.shaelvienApp.showMapForVerification('map-world'); window.shaelvienApp.getState().role = 'gm'; window.shaelvienApp.getState().scene = 'MAP_EDIT'; window.shaelvienApp.getState().editor.activeTool = 'select';", timeout=5)
        point = workspace_point(cdp, "map-world", "{ x: 7, y: 4 }")
        click_point(cdp, point)
        time.sleep(0.08)
        click_point(cdp, point)
        double_click_child = evaluate(cdp, "window.shaelvienApp.getState().currentMapId === 'map-city'", timeout=5)
        evaluate(cdp, "window.shaelvienApp.openTabletopOverlay('dice')", timeout=5)
        menu_open = evaluate(cdp, "!document.getElementById('tabletopOverlay').hidden", timeout=5)
        menu_centered = overlay_centered(cdp)
        evaluate(cdp, "document.getElementById('closeTabletopOverlayButton').click()", timeout=5)
        closed_intercepts = evaluate(
            cdp,
            """
            (() => {
              const overlay = document.getElementById("tabletopOverlay");
              return !overlay.hidden && getComputedStyle(overlay).pointerEvents !== "none";
            })()
            """,
            timeout=5,
        )
        evaluate(cdp, "window.shaelvienApp.openTabletopOverlay('map')", timeout=5)
        evaluate(cdp, "document.querySelector('[data-tabletop-action=\"close-menu\"]').click()", timeout=5)
        button_responds = evaluate(cdp, "document.getElementById('tabletopOverlay').hidden", timeout=5)
        canvas = base.verify_canvas(cdp)
        screenshot = base.save_screenshot(cdp, "desktop_tabletop_1440x960.png")
        app = app_acceptance(cdp)
        return {
            "tabletopAcceptance": tabletop,
            "appAcceptance": app,
            "layout": metrics,
            "dragPanWorks": before != after,
            "doubleClickChildEntryWorks": double_click_child,
            "overlayOpens": menu_open,
            "overlayCentered": menu_centered,
            "closedOverlayInterceptsInput": closed_intercepts,
            "overlayButtonResponds": button_responds,
            "canvas": canvas,
            "consoleErrors": base.collect_console_errors(cdp),
            "screenshot": screenshot,
        }
    finally:
        cdp.close()


def run_mobile(port: int, app_url: str) -> dict:
    cdp = base.new_tab(port, app_url)
    try:
        base.configure_viewport(cdp, 390, 844, True)
        cdp.wait_for("Boolean(window.shaelvienApp && window.shaelvienApp.getState)", timeout=60)
        tabletop = tabletop_acceptance(cdp)
        metrics = layout_metrics(cdp)
        evaluate(cdp, "window.shaelvienApp.showMapForVerification('map-world'); window.shaelvienApp.getState().role = 'gm'; window.shaelvienApp.getState().scene = 'MAP_EDIT'; window.shaelvienApp.getState().editor.activeTool = 'select';", timeout=5)
        point = workspace_point(cdp, "map-world", "{ x: 7, y: 4 }")
        before_pan = evaluate(cdp, "JSON.stringify(window.shaelvienApp.getState().editor.viewportByMap['map-world'])", timeout=5)
        dispatch_pointer(cdp, "pointerdown", point, pointer_type="touch", pointer_id=11, button=0, buttons=1)
        dispatch_pointer(cdp, "pointermove", {"x": point["x"] + 82, "y": point["y"] + 38}, pointer_type="touch", pointer_id=11, button=0, buttons=1)
        dispatch_pointer(cdp, "pointerup", {"x": point["x"] + 82, "y": point["y"] + 38}, pointer_type="touch", pointer_id=11, button=0, buttons=0)
        after_pan = evaluate(cdp, "JSON.stringify(window.shaelvienApp.getState().editor.viewportByMap['map-world'])", timeout=5)

        before_pinch = evaluate(cdp, "JSON.stringify(window.shaelvienApp.getState().editor.viewportByMap['map-world'])", timeout=5)
        dispatch_pointer(cdp, "pointerdown", {"x": point["x"] - 42, "y": point["y"] - 20}, pointer_type="touch", pointer_id=21, button=0, buttons=1)
        dispatch_pointer(cdp, "pointerdown", {"x": point["x"] + 42, "y": point["y"] + 20}, pointer_type="touch", pointer_id=22, button=0, buttons=1)
        dispatch_pointer(cdp, "pointermove", {"x": point["x"] - 62, "y": point["y"] + 50}, pointer_type="touch", pointer_id=21, button=0, buttons=1)
        dispatch_pointer(cdp, "pointermove", {"x": point["x"] + 62, "y": point["y"] - 50}, pointer_type="touch", pointer_id=22, button=0, buttons=1)
        dispatch_pointer(cdp, "pointerup", {"x": point["x"] - 62, "y": point["y"] + 50}, pointer_type="touch", pointer_id=21, button=0, buttons=0)
        dispatch_pointer(cdp, "pointerup", {"x": point["x"] + 62, "y": point["y"] - 50}, pointer_type="touch", pointer_id=22, button=0, buttons=0)
        after_pinch = evaluate(cdp, "JSON.stringify(window.shaelvienApp.getState().editor.viewportByMap['map-world'])", timeout=5)
        release_clean = evaluate(cdp, "window.shaelvienApp.getState().input.pointerActive === false", timeout=5)

        evaluate(cdp, "window.shaelvienApp.showMapForVerification('map-world'); window.shaelvienApp.getState().role = 'gm'; window.shaelvienApp.getState().scene = 'MAP_EDIT'; window.shaelvienApp.getState().editor.activeTool = 'select';", timeout=5)
        city_point = workspace_point(cdp, "map-world", "{ x: 7, y: 4 }")
        click_point(cdp, city_point, pointer_type="touch")
        time.sleep(0.08)
        click_point(cdp, city_point, pointer_type="touch")
        double_tap_child = evaluate(cdp, "window.shaelvienApp.getState().currentMapId === 'map-city'", timeout=5)

        evaluate(cdp, "window.shaelvienApp.showMapForVerification('map-world'); window.shaelvienApp.getState().role = 'gm'; window.shaelvienApp.getState().scene = 'MAP_VIEW'; window.shaelvienApp.getState().editor.activeTool = 'select';", timeout=5)
        city_point = workspace_point(cdp, "map-world", "{ x: 7, y: 4 }")
        dispatch_pointer(cdp, "pointerdown", city_point, pointer_type="touch", pointer_id=31, button=0, buttons=1)
        time.sleep(0.72)
        long_press_menu = evaluate(cdp, "!document.getElementById('tabletopOverlay').hidden", timeout=5)
        menu_centered = overlay_centered(cdp)
        dispatch_pointer(cdp, "pointerup", city_point, pointer_type="touch", pointer_id=31, button=0, buttons=0)
        evaluate(cdp, "document.getElementById('closeTabletopOverlayButton').click()", timeout=5)
        overlay_closed = evaluate(cdp, "document.getElementById('tabletopOverlay').hidden", timeout=5)
        text_selection = evaluate(cdp, "String(window.getSelection ? window.getSelection() : '').length", timeout=5)
        canvas = base.verify_canvas(cdp)
        return {
            "tabletopAcceptance": tabletop,
            "layout": metrics,
            "swipePans": before_pan != after_pan,
            "pinchChangesViewport": before_pinch != after_pinch,
            "releaseClearsGestureState": release_clean,
            "doubleTapChildEntryWorks": double_tap_child,
            "longPressMenuWorks": long_press_menu,
            "longPressMenuCentered": menu_centered,
            "overlayCloses": overlay_closed,
            "browserTextSelectionLength": text_selection,
            "canvas": canvas,
            "consoleErrors": base.collect_console_errors(cdp),
            "screenshot": base.save_screenshot(cdp, "mobile_tabletop_390x844.png"),
        }
    finally:
        cdp.close()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9227)
    parser.add_argument("--app-url", default="http://127.0.0.1:8780/")
    args = parser.parse_args()

    proc = base.ensure_chrome(args.port)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "schemaVersion": "shaelvien.digital_tabletop.browser_verify.v1",
        "appUrl": args.app_url,
        "desktop": run_desktop(args.port, args.app_url),
        "mobile": run_mobile(args.port, args.app_url),
    }
    final_hash = report["desktop"]["appAcceptance"].get("result", {}).get("finalStateHash")
    integrity_hash = report["desktop"]["appAcceptance"].get("result", {}).get("integrityHash")
    report["pass"] = (
        report["desktop"]["tabletopAcceptance"].get("ok") is True
        and report["mobile"]["tabletopAcceptance"].get("ok") is True
        and report["desktop"]["appAcceptance"].get("ok") is True
        and final_hash == "c7a4ac67"
        and integrity_hash is not None
        and report["desktop"]["layout"]["noPageScroll"] is True
        and report["desktop"]["layout"]["noHorizontalOverflow"] is True
        and report["mobile"]["layout"]["noPageScroll"] is True
        and report["mobile"]["layout"]["noHorizontalOverflow"] is True
        and report["desktop"]["dragPanWorks"] is True
        and report["desktop"]["doubleClickChildEntryWorks"] is True
        and report["desktop"]["overlayOpens"] is True
        and report["desktop"]["overlayCentered"] is True
        and report["desktop"]["closedOverlayInterceptsInput"] is False
        and report["desktop"]["overlayButtonResponds"] is True
        and report["mobile"]["swipePans"] is True
        and report["mobile"]["pinchChangesViewport"] is True
        and report["mobile"]["releaseClearsGestureState"] is True
        and report["mobile"]["doubleTapChildEntryWorks"] is True
        and report["mobile"]["longPressMenuWorks"] is True
        and report["mobile"]["longPressMenuCentered"] is True
        and report["mobile"]["overlayCloses"] is True
        and report["mobile"]["browserTextSelectionLength"] == 0
        and report["desktop"]["canvas"]["nonTransparent"] > 100
        and report["mobile"]["canvas"]["nonTransparent"] > 100
        and not report["desktop"]["consoleErrors"]
        and not report["mobile"]["consoleErrors"]
    )
    report["replayHashes"] = {"finalStateHash": final_hash, "integrityHash": integrity_hash}
    report_path = REPORT_DIR / "browser_tabletop_verification.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(report_path), "pass": report["pass"], "replayHashes": report["replayHashes"]}, indent=2))
    if proc is not None:
        proc.terminate()
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
