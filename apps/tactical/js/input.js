const KEY_DIRECTIONS = Object.freeze({
  ArrowUp: "up",
  w: "up",
  W: "up",
  ArrowDown: "down",
  s: "down",
  S: "down",
  ArrowLeft: "left",
  a: "left",
  A: "left",
  ArrowRight: "right",
  d: "right",
  D: "right"
});

export function bindInput(canvas, handlers) {
  canvas.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    try {
      canvas.setPointerCapture?.(event.pointerId);
    } catch (error) {
      // Synthetic verification events may not have a capturable pointer ID.
    }
    handlers.onPointerState?.(true);
    handlers.onPointerDown?.(eventToCanvasPoint(canvas, event), event);
  });
  canvas.addEventListener("pointermove", (event) => {
    handlers.onPointerMove?.(eventToCanvasPoint(canvas, event), event);
  });
  const release = (event) => {
    handlers.onPointerState?.(false);
    handlers.onPointerRelease?.(eventToCanvasPoint(canvas, event), event);
  };
  canvas.addEventListener("pointerup", release);
  canvas.addEventListener("pointercancel", release);
  canvas.addEventListener("lostpointercapture", release);
  canvas.addEventListener("wheel", (event) => {
    event.preventDefault();
    handlers.onWheel?.(eventToCanvasPoint(canvas, event), event);
  }, { passive: false });
  canvas.addEventListener("contextmenu", (event) => {
    handlers.onContextMenu?.(eventToCanvasPoint(canvas, event), event);
  });
  window.addEventListener("keydown", (event) => {
    if (["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement?.tagName)) return;
    const shortcutHandled = handlers.onShortcut?.(event);
    if (shortcutHandled) {
      event.preventDefault();
      return;
    }
    const direction = KEY_DIRECTIONS[event.key];
    if (!direction) return;
    event.preventDefault();
    handlers.onDirection?.(direction, event);
  });
}

export function directionVector(direction) {
  if (direction === "up") return { dx: 0, dy: -1 };
  if (direction === "down") return { dx: 0, dy: 1 };
  if (direction === "left") return { dx: -1, dy: 0 };
  if (direction === "right") return { dx: 1, dy: 0 };
  return { dx: 0, dy: 0 };
}

function eventToCanvasPoint(canvas, event) {
  const rect = canvas.getBoundingClientRect();
  return {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top,
    clientX: event.clientX,
    clientY: event.clientY,
    width: rect.width,
    height: rect.height
  };
}
