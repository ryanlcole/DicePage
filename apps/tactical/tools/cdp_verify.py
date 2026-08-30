"""Headless Chrome verification for the Shaelvien tactical tabletop.

This uses only the Python standard library for the Chrome DevTools Protocol so
the browser-executed acceptance path remains available when Node is absent.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import random
import socket
import struct
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(r"C:\Shaelvien")
APP_ROOT = ROOT / "dev_studio_alpha"
REPORT_DIR = ROOT / "verify_reports" / "shaelvien_tactical_web_0"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")


class WebSocket:
    def __init__(self, url: str):
        parsed = urllib.parse.urlparse(url)
        self.host = parsed.hostname or "127.0.0.1"
        self.port = parsed.port or 80
        self.path = parsed.path + (("?" + parsed.query) if parsed.query else "")
        self.sock = socket.create_connection((self.host, self.port), timeout=10)
        self._handshake()

    def _handshake(self) -> None:
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(request.encode("ascii"))
        response = self.sock.recv(4096)
        if b" 101 " not in response.split(b"\r\n", 1)[0]:
            raise RuntimeError("WebSocket upgrade failed")

    def send_json(self, payload: dict) -> None:
        self._send_frame(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

    def recv_json(self) -> dict:
        while True:
            opcode, payload = self._recv_frame()
            if opcode == 1:
                return json.loads(payload.decode("utf-8"))
            if opcode == 8:
                raise RuntimeError("WebSocket closed")
            if opcode == 9:
                self._send_frame(payload, opcode=10)

    def close(self) -> None:
        try:
            self._send_frame(b"", opcode=8)
        finally:
            self.sock.close()

    def _send_frame(self, payload: bytes, opcode: int = 1) -> None:
        header = bytearray([0x80 | opcode])
        length = len(payload)
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))
        mask = random.randbytes(4)
        header.extend(mask)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self.sock.sendall(header + masked)

    def _recv_frame(self) -> tuple[int, bytes]:
        first = self._read_exact(2)
        opcode = first[0] & 0x0F
        masked = bool(first[1] & 0x80)
        length = first[1] & 0x7F
        if length == 126:
            length = struct.unpack("!H", self._read_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._read_exact(8))[0]
        mask = self._read_exact(4) if masked else b""
        payload = self._read_exact(length)
        if masked:
            payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        return opcode, payload

    def _read_exact(self, length: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < length:
            chunk = self.sock.recv(length - len(chunks))
            if not chunk:
                raise RuntimeError("Socket closed while reading")
            chunks.extend(chunk)
        return bytes(chunks)


class CDP:
    def __init__(self, websocket_url: str):
        self.ws = WebSocket(websocket_url)
        self.next_id = 1
        self.events: list[dict] = []

    def command(self, method: str, params: dict | None = None, timeout: float = 10) -> dict:
        message_id = self.next_id
        self.next_id += 1
        self.ws.send_json({"id": message_id, "method": method, "params": params or {}})
        deadline = time.time() + timeout
        while time.time() < deadline:
            message = self.ws.recv_json()
            if message.get("id") == message_id:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message.get("result", {})
            self.events.append(message)
        raise TimeoutError(method)

    def close(self) -> None:
        self.ws.close()

    def evaluate(self, expression: str, timeout: float = 10):
        result = self.command(
            "Runtime.evaluate",
            {"expression": expression, "awaitPromise": True, "returnByValue": True},
            timeout=timeout,
        )
        if "exceptionDetails" in result:
            raise RuntimeError(result["exceptionDetails"].get("text", "Runtime exception"))
        return result.get("result", {}).get("value")

    def wait_for(self, expression: str, timeout: float = 15, interval: float = 0.2):
        deadline = time.time() + timeout
        last_value = None
        while time.time() < deadline:
            last_value = self.evaluate(expression, timeout=timeout)
            if last_value:
                return last_value
            time.sleep(interval)
        raise TimeoutError(f"Timed out waiting for {expression}; last={last_value!r}")


def http_json(url: str, method: str = "GET") -> dict:
    request = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def ensure_chrome(port: int) -> subprocess.Popen | None:
    try:
        http_json(f"http://127.0.0.1:{port}/json/version")
        return None
    except Exception:
        pass
    profile = Path(r"C:\Temp") / f"shaelvien_tactical_cdp_profile_{port}"
    profile.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        [
            str(CHROME),
            "--headless=new",
            "--disable-gpu",
            "--disable-extensions",
            "--no-first-run",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile}",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.time() + 12
    while time.time() < deadline:
        try:
            http_json(f"http://127.0.0.1:{port}/json/version")
            return proc
        except Exception:
            time.sleep(0.25)
    raise RuntimeError("Chrome CDP did not become available")


def new_tab(port: int, url: str) -> CDP:
    encoded = urllib.parse.quote(url, safe=":/?=&")
    try:
        target = http_json(f"http://127.0.0.1:{port}/json/new?{encoded}", method="PUT")
    except Exception:
        target = http_json(f"http://127.0.0.1:{port}/json/new?{encoded}")
    cdp = CDP(target["webSocketDebuggerUrl"])
    cdp.command("Page.enable")
    cdp.command("Runtime.enable")
    cdp.command("Log.enable")
    return cdp


def configure_viewport(cdp: CDP, width: int, height: int, mobile: bool) -> None:
    cdp.command(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": width,
            "height": height,
            "deviceScaleFactor": 3 if mobile else 1,
            "mobile": mobile,
            "screenWidth": width,
            "screenHeight": height,
        },
    )


def collect_console_errors(cdp: CDP) -> list[str]:
    errors = []
    for event in cdp.events:
        method = event.get("method")
        params = event.get("params", {})
        if method == "Runtime.exceptionThrown":
            errors.append(params.get("exceptionDetails", {}).get("text", "exception"))
        if method == "Log.entryAdded" and params.get("entry", {}).get("level") == "error":
            errors.append(params.get("entry", {}).get("text", "log error"))
    return errors


def save_screenshot(cdp: CDP, name: str) -> str:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    data = cdp.command("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False}, timeout=15)["data"]
    path = REPORT_DIR / name
    path.write_bytes(base64.b64decode(data))
    return str(path)


def verify_canvas(cdp: CDP) -> dict:
    return cdp.evaluate(
        """
        (() => {
          const canvas = document.getElementById('gameCanvas');
          const ctx = canvas.getContext('2d');
          const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
          let nonTransparent = 0;
          const colors = new Set();
          for (let i = 0; i < data.length; i += 16) {
            if (data[i + 3] > 0) nonTransparent += 1;
            colors.add(`${data[i]},${data[i+1]},${data[i+2]},${data[i+3]}`);
            if (colors.size > 32 && nonTransparent > 100) break;
          }
          return { width: canvas.width, height: canvas.height, nonTransparent, colorSamples: colors.size };
        })()
        """
    )


def run_desktop_acceptance(port: int, app_url: str) -> dict:
    cdp = new_tab(port, app_url + "?acceptance=1")
    try:
        configure_viewport(cdp, 1365, 900, False)
        cdp.wait_for("document.body.dataset.acceptance === 'complete' || document.body.dataset.acceptance === 'failed'", timeout=30)
        acceptance = cdp.evaluate("JSON.parse(document.getElementById('acceptanceResult').textContent)", timeout=5)
        overflow = cdp.evaluate("document.documentElement.scrollWidth <= window.innerWidth", timeout=5)
        canvas = verify_canvas(cdp)
        screenshot = save_screenshot(cdp, "desktop_acceptance.png")
        cdp.command("Page.navigate", {"url": app_url})
        cdp.wait_for("Boolean(window.shaelvienApp && window.shaelvienApp.getState)", timeout=15)
        refresh_state = cdp.evaluate(
            "(() => { const s = window.shaelvienApp.getState(); return {scene:s.scene,currentMapId:s.currentMapId,valid:Boolean(s.maps[s.currentMapId]),replays:s.replays.length}; })()",
            timeout=5,
        )
        return {
            "acceptance": acceptance,
            "noHorizontalOverflow": overflow,
            "canvas": canvas,
            "screenshot": screenshot,
            "refreshState": refresh_state,
            "consoleErrors": collect_console_errors(cdp),
        }
    finally:
        cdp.close()


def run_mobile_checks(port: int, app_url: str) -> dict:
    cdp = new_tab(port, app_url)
    try:
        configure_viewport(cdp, 390, 844, True)
        cdp.wait_for("Boolean(window.shaelvienApp && window.shaelvienApp.getState)", timeout=15)
        overflow = cdp.evaluate("document.documentElement.scrollWidth <= window.innerWidth", timeout=5)
        canvas = verify_canvas(cdp)
        rect = cdp.evaluate(
            "(() => { const r = document.getElementById('gameCanvas').getBoundingClientRect(); return {x:r.x,y:r.y,width:r.width,height:r.height}; })()",
            timeout=5,
        )
        x = int(rect["x"] + rect["width"] / 2)
        y = int(rect["y"] + rect["height"] / 2)
        cdp.command("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y, "radiusX": 4, "radiusY": 4, "force": 1}]})
        cdp.command("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        touch_released = cdp.evaluate("window.shaelvienApp.getState().input.pointerActive === false", timeout=5)
        screenshot = save_screenshot(cdp, "mobile_390x844.png")
        return {
            "noHorizontalOverflow": overflow,
            "touchReleaseStopsInput": touch_released,
            "canvas": canvas,
            "screenshot": screenshot,
            "consoleErrors": collect_console_errors(cdp),
        }
    finally:
        cdp.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9223)
    parser.add_argument("--app-url", default="http://127.0.0.1:8780/")
    args = parser.parse_args()

    proc = ensure_chrome(args.port)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "schemaVersion": "shaelvien.tactical.browser_verify.v1",
        "appUrl": args.app_url,
        "desktop": run_desktop_acceptance(args.port, args.app_url),
        "mobile": run_mobile_checks(args.port, args.app_url),
    }
    report["pass"] = (
        report["desktop"]["acceptance"].get("ok") is True
        and report["desktop"]["noHorizontalOverflow"] is True
        and report["mobile"]["noHorizontalOverflow"] is True
        and report["mobile"]["touchReleaseStopsInput"] is True
        and not report["desktop"]["consoleErrors"]
        and not report["mobile"]["consoleErrors"]
    )
    report_path = REPORT_DIR / "browser_verification.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(report_path), "pass": report["pass"]}, indent=2))
    if proc is not None:
        proc.terminate()
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
