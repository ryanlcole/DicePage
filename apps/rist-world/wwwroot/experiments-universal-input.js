// RIST Experiments universal beginner-input adapter.
// One physical analog represents the X and Y semantic axes.
// The two display surfaces remain the Left and Right semantic buttons.
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
  let cleanupPointer = null;

  const DEAD_ZONE = 0.34;
  const GAMEPAD_DEAD_ZONE = 0.55;
  const INITIAL_REPEAT_MS = 330;
  const REPEAT_MS = 115;
  const axisState = {
    x: { dir: 0, next: 0 },
    y: { dir: 0, next: 0 }
  };

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

  function gamepadVector(gamepad) {
    if (!gamepad) return { x: 0, y: 0 };

    let x = Number(gamepad.axes?.[0] ?? 0);
    let y = -Number(gamepad.axes?.[1] ?? 0);

    if (buttonPressed(gamepad, 14)) x = -1;
    else if (buttonPressed(gamepad, 15)) x = 1;

    if (buttonPressed(gamepad, 12)) y = 1;
    else if (buttonPressed(gamepad, 13)) y = -1;

    return {
      x: direction(x, GAMEPAD_DEAD_ZONE),
      y: direction(y, GAMEPAD_DEAD_ZONE)
    };
  }

  function processAxis(name, dir, now) {
    const state = axisState[name];
    if (!dir) {
      state.dir = 0;
      state.next = 0;
      return;
    }

    if (dir !== state.dir) {
      state.dir = dir;
      state.next = now + INITIAL_REPEAT_MS;
      invoke(name, dir);
      return;
    }

    if (now >= state.next) {
      state.next = now + REPEAT_MS;
      invoke(name, dir);
    }
  }

  function resetAxisState() {
    axisState.x.dir = 0;
    axisState.x.next = 0;
    axisState.y.dir = 0;
    axisState.y.next = 0;
  }

  function setKnob(nx, ny) {
    if (!pad || !knob) return;
    const rect = pad.getBoundingClientRect();
    const radius = Math.max(0, Math.min(rect.width, rect.height) * 0.27);
    knob.style.transform = `translate(calc(-50% + ${nx * radius}px), calc(-50% + ${-ny * radius}px))`;
  }

  function updatePointer(event) {
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

    pointerX = direction(nx, DEAD_ZONE);
    pointerY = direction(ny, DEAD_ZONE);
    setKnob(nx, ny);
  }

  function bindAnalog(element) {
    cleanupPointer?.();
    analog = element || null;
    pad = analog?.querySelector?.(".analog-pad") || null;
    knob = analog?.querySelector?.(".analog-knob") || null;
    if (!analog || !pad || !knob) {
      cleanupPointer = null;
      return;
    }

    const onPointerDown = event => {
      if (event.button !== undefined && event.button !== 0) return;
      pointerId = event.pointerId;
      pointerX = 0;
      pointerY = 0;
      resetAxisState();
      analog.setPointerCapture?.(pointerId);
      updatePointer(event);
      event.preventDefault();
    };

    const onPointerMove = event => {
      if (pointerId !== event.pointerId) return;
      updatePointer(event);
      event.preventDefault();
    };

    const finishPointer = event => {
      if (pointerId !== event.pointerId) return;
      pointerId = null;
      pointerX = 0;
      pointerY = 0;
      resetAxisState();
      setKnob(0, 0);
      event.preventDefault();
    };

    analog.addEventListener("pointerdown", onPointerDown, { passive: false });
    analog.addEventListener("pointermove", onPointerMove, { passive: false });
    analog.addEventListener("pointerup", finishPointer, { passive: false });
    analog.addEventListener("pointercancel", finishPointer, { passive: false });
    analog.addEventListener("lostpointercapture", finishPointer, { passive: false });

    cleanupPointer = () => {
      analog?.removeEventListener("pointerdown", onPointerDown);
      analog?.removeEventListener("pointermove", onPointerMove);
      analog?.removeEventListener("pointerup", finishPointer);
      analog?.removeEventListener("pointercancel", finishPointer);
      analog?.removeEventListener("lostpointercapture", finishPointer);
      pointerId = null;
      pointerX = 0;
      pointerY = 0;
      setKnob(0, 0);
    };

    setKnob(0, 0);
  }

  function poll(now) {
    const gamepad = activeGamepad();
    edgeButton(gamepad, 0, "left");
    edgeButton(gamepad, 1, "right");

    const vector = pointerId !== null
      ? { x: pointerX, y: pointerY }
      : gamepadVector(gamepad);

    processAxis("x", vector.x, now);
    processAxis("y", vector.y, now);

    frame = requestAnimationFrame(poll);
  }

  window.ristExperimentsUniversalInput = Object.freeze({
    start(dotnetReference, analogElement) {
      dotnet = dotnetReference;
      previousButtons = [];
      resetAxisState();
      bindAnalog(analogElement);
      if (!frame) frame = requestAnimationFrame(poll);
    },
    stop() {
      dotnet = null;
      previousButtons = [];
      resetAxisState();
      cleanupPointer?.();
      cleanupPointer = null;
      analog = null;
      pad = null;
      knob = null;
      if (frame) cancelAnimationFrame(frame);
      frame = 0;
    }
  });
})();