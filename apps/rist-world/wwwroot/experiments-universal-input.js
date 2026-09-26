// RIST Experiments universal beginner-input adapter.
// Hardware is representation only: gamepad signals resolve to the same X/Y/Left/Right
// semantic controls used by keyboard, touch and pointer in ExperimentsWorkspace.
(() => {
  "use strict";

  if (window.ristExperimentsUniversalInput) return;

  let dotnet = null;
  let frame = 0;
  let previousButtons = [];
  let heldDirection = "";
  let nextRepeatAt = 0;

  const DEAD_ZONE = 0.55;
  const INITIAL_REPEAT_MS = 330;
  const REPEAT_MS = 115;

  function activeGamepad() {
    const pads = navigator.getGamepads?.() || [];
    for (const pad of pads) if (pad?.connected) return pad;
    return null;
  }

  function buttonPressed(pad, index) {
    return Boolean(pad?.buttons?.[index]?.pressed);
  }

  function invoke(control, direction = 0) {
    if (!dotnet) return;
    dotnet.invokeMethodAsync("ReceiveUniversalInput", control, direction).catch(() => {});
  }

  function edgeButton(pad, index, control) {
    const down = buttonPressed(pad, index);
    if (down && !previousButtons[index]) invoke(control);
    previousButtons[index] = down;
  }

  function directionFor(pad) {
    if (!pad) return "";

    if (buttonPressed(pad, 12)) return "y+";
    if (buttonPressed(pad, 13)) return "y-";
    if (buttonPressed(pad, 14)) return "x-";
    if (buttonPressed(pad, 15)) return "x+";

    const x = Number(pad.axes?.[0] ?? 0);
    const y = Number(pad.axes?.[1] ?? 0);
    if (Math.abs(y) >= Math.abs(x) && Math.abs(y) > DEAD_ZONE) return y < 0 ? "y+" : "y-";
    if (Math.abs(x) > DEAD_ZONE) return x < 0 ? "x-" : "x+";
    return "";
  }

  function emitDirection(direction) {
    if (direction === "y+") invoke("y", 1);
    else if (direction === "y-") invoke("y", -1);
    else if (direction === "x-") invoke("x", -1);
    else if (direction === "x+") invoke("x", 1);
  }

  function poll(now) {
    const pad = activeGamepad();
    edgeButton(pad, 0, "left");
    edgeButton(pad, 1, "right");

    const direction = directionFor(pad);
    if (!direction) {
      heldDirection = "";
      nextRepeatAt = 0;
    } else if (direction !== heldDirection) {
      heldDirection = direction;
      emitDirection(direction);
      nextRepeatAt = now + INITIAL_REPEAT_MS;
    } else if (now >= nextRepeatAt) {
      emitDirection(direction);
      nextRepeatAt = now + REPEAT_MS;
    }

    frame = requestAnimationFrame(poll);
  }

  window.ristExperimentsUniversalInput = Object.freeze({
    start(dotnetReference) {
      dotnet = dotnetReference;
      previousButtons = [];
      heldDirection = "";
      nextRepeatAt = 0;
      if (!frame) frame = requestAnimationFrame(poll);
    },
    stop() {
      dotnet = null;
      previousButtons = [];
      heldDirection = "";
      nextRepeatAt = 0;
      if (frame) cancelAnimationFrame(frame);
      frame = 0;
    }
  });
})();