// RIST Experiments universal beginner-input adapter.
// One physical analog represents page-up/page-down/page-left/page-right snapping.
// The left display is a vertical swipe selector; the right display is horizontal.
// When neither display has multiple choices, the analog is available to the viewer cursor.
(() => {
  "use strict";

  if (window.ristExperimentsUniversalInput) return;

  let dotnet = null;
  let frame = 0;
  let previousButtons = [];
  let analog = null;
  let pad = null;
  let knob = null;
  let pointerId = null;
  let pointerX = 0;
  let pointerY = 0;
  let pointerAnalogX = 0;
  let pointerAnalogY = 0;
  let cursorX = 0;
  let cursorY = 0;
  let lastCursorFrame = 0;
  let lastCursorSync = 0;
  let cleanupAnalog = null;
  let cleanupLeftSlider = null;
  let cleanupRightSlider = null;

  const ANALOG_DEAD_ZONE = 0.34;
  const GAMEPAD_DEAD_ZONE = 0.55;
  const CURSOR_POINTER_DEAD_ZONE = 0.08;
  const CURSOR_GAMEPAD_DEAD_ZONE = 0.14;
  const CURSOR_MAX_SPEED = 86;
  const CURSOR_SYNC_MS = 120;
  const axisState = { x: 0, y: 0 };

  function activeGamepad() {
    const pads = navigator.getGamepads?.() || [];
    for (const candidate of pads) if (candidate?.connected) return candidate;
    return null;
  }

  function buttonPressed(gamepad, index) {
    return Boolean(gamepad?.buttons?.[index]?.pressed);
  }

  function invoke(control, direction = 0) {
    if (!dotnet) return;
    dotnet.invokeMethodAsync("ReceiveUniversalInput", control, direction).catch(() => {});
  }

  function edgeButton(gamepad, index, control) {
    const down = buttonPressed(gamepad, index);
    if (down && !previousButtons[index]) invoke(control);
    previousButtons[index] = down;
  }

  function direction(value, deadZone) {
    if (value > deadZone) return 1;
    if (value < -deadZone) return -1;
    return 0;
  }

  function radialResponse(x, y, deadZone) {
    const magnitude = Math.hypot(x, y);
    if (magnitude <= deadZone) return { x: 0, y: 0 };

    const capped = Math.min(1, magnitude);
    const scaled = (capped - deadZone) / (1 - deadZone);
    const curved = Math.pow(Math.max(0, scaled), 1.35);
    const factor = curved / Math.max(magnitude, 0.0001);

    return {
      x: x * factor,
      y: y * factor
    };
  }

  function gamepadAnalogVector(gamepad) {
    if (!gamepad) return { x: 0, y: 0 };

    let x = Number(gamepad.axes?.[0] ?? 0);
    let y = -Number(gamepad.axes?.[1] ?? 0);

    if (buttonPressed(gamepad, 14)) x = -1;
    else if (buttonPressed(gamepad, 15)) x = 1;

    if (buttonPressed(gamepad, 12)) y = 1;
    else if (buttonPressed(gamepad, 13)) y = -1;

    return { x, y };
  }

  function currentReticle() {
    return analog?.closest?.(".experiments-shell")?.querySelector?.(".viewer-reticle") || null;
  }

  function renderCursor() {
    const reticle = currentReticle();
    if (!reticle) return;
    reticle.style.left = `${50 + cursorX * 0.45}%`;
    reticle.style.top = `${50 - cursorY * 0.45}%`;
  }

  function syncCursor(force = false) {
    if (!dotnet) return;
    const now = performance.now();
    if (!force && now - lastCursorSync < CURSOR_SYNC_MS) return;
    lastCursorSync = now;
    dotnet.invokeMethodAsync("ReceiveCursorPosition", cursorX, cursorY).catch(() => {});
  }

  function updateSmoothCursor(rawX, rawY, now, deadZone) {
    if (!lastCursorFrame) lastCursorFrame = now;
    const dt = Math.min(0.05, Math.max(0, (now - lastCursorFrame) / 1000));
    lastCursorFrame = now;

    const response = radialResponse(rawX, rawY, deadZone);
    cursorX = Math.max(-100, Math.min(100, cursorX + response.x * CURSOR_MAX_SPEED * dt));
    cursorY = Math.max(-100, Math.min(100, cursorY + response.y * CURSOR_MAX_SPEED * dt));

    renderCursor();
    syncCursor(false);
  }

  function isPagingMode() {
    return Boolean(analog?.classList?.contains("paging-mode"));
  }

  function constrainedVector(x, y, deadZone) {
    if (isPagingMode()) {
      if (Math.abs(x) >= Math.abs(y)) y = 0;
      else x = 0;
    }
    return {
      x: direction(x, deadZone),
      y: direction(y, deadZone)
    };
  }

  function gamepadVector(gamepad) {
    if (!gamepad) return { x: 0, y: 0 };

    let x = Number(gamepad.axes?.[0] ?? 0);
    let y = -Number(gamepad.axes?.[1] ?? 0);

    if (buttonPressed(gamepad, 14)) x = -1;
    else if (buttonPressed(gamepad, 15)) x = 1;

    if (buttonPressed(gamepad, 12)) y = 1;
    else if (buttonPressed(gamepad, 13)) y = -1;

    return constrainedVector(x, y, GAMEPAD_DEAD_ZONE);
  }

  // Snapping controller: emit once when an axis enters a direction.
  // Re-centering arms that axis for another page snap.
  function processAxis(name, dir) {
    if (!dir) {
      axisState[name] = 0;
      return;
    }
    if (axisState[name] === dir) return;
    axisState[name] = dir;
    invoke(name, dir);
  }

  function resetAxisState() {
    axisState.x = 0;
    axisState.y = 0;
  }

  function setKnob(nx, ny) {
    if (!pad || !knob) return;
    const rect = pad.getBoundingClientRect();
    const radius = Math.max(0, Math.min(rect.width, rect.height) * 0.27);
    knob.style.transform =
      `translate(calc(-50% + ${nx * radius}px), calc(-50% + ${-ny * radius}px))`;
  }

  function updateAnalogPointer(event) {
    if (!pad) return;
    const rect = pad.getBoundingClientRect();
    if (rect.width < 2 || rect.height < 2) return;

    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const maxRadius = Math.max(1, Math.min(rect.width, rect.height) * 0.42);

    let nx = (event.clientX - cx) / maxRadius;
    let ny = -(event.clientY - cy) / maxRadius;
    const length = Math.hypot(nx, ny);
    if (length > 1) {
      nx /= length;
      ny /= length;
    }

    pointerAnalogX = nx;
    pointerAnalogY = ny;

    const semantic = constrainedVector(nx, ny, ANALOG_DEAD_ZONE);
    pointerX = semantic.x;
    pointerY = semantic.y;

    if (isPagingMode()) {
      const magnitude = Math.max(Math.abs(nx), Math.abs(ny));
      nx = semantic.x === 0 ? 0 : Math.sign(semantic.x) * magnitude;
      ny = semantic.y === 0 ? 0 : Math.sign(semantic.y) * magnitude;
    }

    setKnob(nx, ny);
  }

  function bindAnalog(element) {
    cleanupAnalog?.();
    analog = element || null;
    pad = analog?.querySelector?.(".analog-pad") || null;
    knob = analog?.querySelector?.(".analog-knob") || null;
    if (!analog || !pad || !knob) {
      cleanupAnalog = null;
      return;
    }

    const onPointerDown = event => {
      if (event.button !== undefined && event.button !== 0) return;
      pointerId = event.pointerId;
      pointerX = 0;
      pointerY = 0;
      pointerAnalogX = 0;
      pointerAnalogY = 0;
      resetAxisState();
      analog.setPointerCapture?.(pointerId);
      updateAnalogPointer(event);
      event.preventDefault();
    };

    const onPointerMove = event => {
      if (pointerId !== event.pointerId) return;
      updateAnalogPointer(event);
      event.preventDefault();
    };

    const finishPointer = event => {
      if (pointerId !== event.pointerId) return;
      pointerId = null;
      pointerX = 0;
      pointerY = 0;
      pointerAnalogX = 0;
      pointerAnalogY = 0;
      lastCursorFrame = 0;
      resetAxisState();
      setKnob(0, 0);
      syncCursor(true);
      event.preventDefault();
    };

    analog.addEventListener("pointerdown", onPointerDown, { passive: false });
    analog.addEventListener("pointermove", onPointerMove, { passive: false });
    analog.addEventListener("pointerup", finishPointer, { passive: false });
    analog.addEventListener("pointercancel", finishPointer, { passive: false });
    analog.addEventListener("lostpointercapture", finishPointer, { passive: false });

    cleanupAnalog = () => {
      analog?.removeEventListener("pointerdown", onPointerDown);
      analog?.removeEventListener("pointermove", onPointerMove);
      analog?.removeEventListener("pointerup", finishPointer);
      analog?.removeEventListener("pointercancel", finishPointer);
      analog?.removeEventListener("lostpointercapture", finishPointer);
      pointerId = null;
      pointerX = 0;
      pointerY = 0;
      pointerAnalogX = 0;
      pointerAnalogY = 0;
      lastCursorFrame = 0;
      setKnob(0, 0);
    };

    setKnob(0, 0);
  }

  function bindDisplaySlider(element, axis, control) {
    if (!element) return () => {};

    let activePointer = null;
    let startX = 0;
    let startY = 0;
    let lastX = 0;
    let lastY = 0;
    let dragged = false;
    let suppressClickUntil = 0;

    const visualLimit = 42;
    const dragStart = 7;
    const snapThreshold = 24;

    const setVisual = (dx, dy, dragging) => {
      const x = Math.max(-visualLimit, Math.min(visualLimit, dx));
      const y = Math.max(-visualLimit, Math.min(visualLimit, dy));
      element.style.setProperty("--display-slide-x", `${x}px`);
      element.style.setProperty("--display-slide-y", `${y}px`);
      element.classList.toggle("is-dragging", Boolean(dragging));
    };

    const resetVisual = () => {
      element.classList.remove("is-dragging");
      element.classList.add("is-snapping");
      setVisual(0, 0, false);
      window.setTimeout(() => element.classList.remove("is-snapping"), 180);
    };

    const onPointerDown = event => {
      if (!element.classList.contains("is-scrollable")) return;
      if (event.button !== undefined && event.button !== 0) return;
      activePointer = event.pointerId;
      startX = lastX = event.clientX;
      startY = lastY = event.clientY;
      dragged = false;
      element.setPointerCapture?.(activePointer);
    };

    const onPointerMove = event => {
      if (activePointer !== event.pointerId) return;
      lastX = event.clientX;
      lastY = event.clientY;
      const dx = lastX - startX;
      const dy = lastY - startY;
      const primary = axis === "x" ? dx : dy;

      if (!dragged && Math.abs(primary) >= dragStart) dragged = true;
      if (!dragged) return;

      if (axis === "x") setVisual(dx, 0, true);
      else setVisual(0, dy, true);
      event.preventDefault();
    };

    const finish = event => {
      if (activePointer !== event.pointerId) return;
      lastX = event.clientX;
      lastY = event.clientY;
      const dx = lastX - startX;
      const dy = lastY - startY;
      const primary = axis === "x" ? dx : dy;
      const didSnap = dragged && Math.abs(primary) >= snapThreshold;

      activePointer = null;

      if (didSnap) {
        // Physical direction matches semantic direction:
        // up/right = +1, down/left = -1.
        const dir = axis === "x"
          ? (primary > 0 ? 1 : -1)
          : (primary < 0 ? 1 : -1);
        suppressClickUntil = performance.now() + 350;
        invoke(control, dir);
        event.preventDefault();
      }

      resetVisual();
    };

    const cancel = event => {
      if (activePointer !== event.pointerId) return;
      activePointer = null;
      resetVisual();
    };

    const onClickCapture = event => {
      if (performance.now() < suppressClickUntil) {
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation?.();
      }
    };

    element.addEventListener("pointerdown", onPointerDown, { passive: true });
    element.addEventListener("pointermove", onPointerMove, { passive: false });
    element.addEventListener("pointerup", finish, { passive: false });
    element.addEventListener("pointercancel", cancel, { passive: true });
    element.addEventListener("lostpointercapture", cancel, { passive: true });
    element.addEventListener("click", onClickCapture, true);

    return () => {
      element.removeEventListener("pointerdown", onPointerDown);
      element.removeEventListener("pointermove", onPointerMove);
      element.removeEventListener("pointerup", finish);
      element.removeEventListener("pointercancel", cancel);
      element.removeEventListener("lostpointercapture", cancel);
      element.removeEventListener("click", onClickCapture, true);
      element.classList.remove("is-dragging", "is-snapping");
      element.style.removeProperty("--display-slide-x");
      element.style.removeProperty("--display-slide-y");
    };
  }

  function poll(now) {
    const gamepad = activeGamepad();
    edgeButton(gamepad, 0, "left");
    edgeButton(gamepad, 1, "right");

    if (isPagingMode()) {
      lastCursorFrame = 0;
      const vector = pointerId !== null
        ? { x: pointerX, y: pointerY }
        : gamepadVector(gamepad);

      processAxis("x", vector.x);
      processAxis("y", vector.y);
    } else {
      resetAxisState();

      const raw = pointerId !== null
        ? { x: pointerAnalogX, y: pointerAnalogY, deadZone: CURSOR_POINTER_DEAD_ZONE }
        : { ...gamepadAnalogVector(gamepad), deadZone: CURSOR_GAMEPAD_DEAD_ZONE };

      updateSmoothCursor(raw.x, raw.y, now, raw.deadZone);
    }

    frame = requestAnimationFrame(poll);
  }

  window.ristExperimentsUniversalInput = Object.freeze({
    start(dotnetReference, analogElement, leftSliderElement, rightSliderElement) {
      dotnet = dotnetReference;
      previousButtons = [];
      resetAxisState();
      cursorX = 0;
      cursorY = 0;
      lastCursorFrame = 0;
      lastCursorSync = 0;
      bindAnalog(analogElement);
      renderCursor();
      cleanupLeftSlider?.();
      cleanupRightSlider?.();
      cleanupLeftSlider = bindDisplaySlider(leftSliderElement, "y", "y");
      cleanupRightSlider = bindDisplaySlider(rightSliderElement, "x", "x");
      if (!frame) frame = requestAnimationFrame(poll);
    },
    stop() {
      dotnet = null;
      previousButtons = [];
      resetAxisState();
      cleanupAnalog?.();
      cleanupAnalog = null;
      cleanupLeftSlider?.();
      cleanupLeftSlider = null;
      cleanupRightSlider?.();
      cleanupRightSlider = null;
      analog = null;
      pad = null;
      knob = null;
      cursorX = 0;
      cursorY = 0;
      lastCursorFrame = 0;
      lastCursorSync = 0;
      if (frame) cancelAnimationFrame(frame);
      frame = 0;
    }
  });
})();