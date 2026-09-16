// Shaelvien semantic compatibility bridge for the existing Worldbuilder viewer.
//
// This is a migration boundary, not a new source of world truth.
// - Server/trusted runtime remains authoritative.
// - Camera and transient placement previews are perception state only.
// - Grid visibility and camera-navigation lock remain registered perception operations but are not adaptively queued.
// - Runtime-local operation ids below are NOT canonical Rune/Glyph ids or frozen wire opcodes.
// - Existing viewer/placement implementations remain authoritative while callers migrate to semantic envelopes.
// - No arbitrary selectors, source execution, hidden world data, or generic property mutation.
(() => {
  "use strict";

  const runtime = window.Shaelvien;
  if (!runtime?.registerPerceptionOperation || !runtime?.createEnvelope || !runtime?.operation) return;
  if (runtime.WorldbuilderPerception) return;

  const BRIDGE_VERSION = "worldbuilder-perception-bridge/3";
  const CAMERA_STREAM = "worldbuilder.camera";
  const PLACEMENT_PREVIEW_STREAM = "worldbuilder.placement-preview";
  const MAX_PREVIEW_SESSION_ID = 96;
  const OPERATIONS = Object.freeze({
    camera: "runtime.perception.worldbuilder.camera",
    grid: "runtime.perception.worldbuilder.grid",
    cameraNavigationLock: "runtime.perception.worldbuilder.camera-navigation-lock",
    placementPreviewPointer: "runtime.perception.worldbuilder.placement-preview.pointer"
  });

  let cameraSequence = 0;
  let placementPreviewSequence = 0;
  const isRecord = value => value !== null && typeof value === "object" && !Array.isArray(value);
  const finite = value => typeof value === "number" && Number.isFinite(value);
  const exactBoolean = value => typeof value === "boolean";
  const cleanString = value => typeof value === "string" && value.trim() ? value.trim() : null;

  function authority() {
    const value = window.ristViewerAuthority;
    if (!value || typeof value.get !== "function") {
      throw new Error("Worldbuilder viewer authority is unavailable.");
    }
    return value;
  }

  function currentSnapshot() {
    const value = authority().get();
    return Object.freeze({
      x: Number(value?.x) || 0,
      y: Number(value?.y) || 0,
      zoom: Number(value?.zoom) || 1,
      visibleCells: Number(value?.visibleCells) || null,
      grid: value?.grid === true,
      locked: value?.locked === true,
      mode: value?.mode === "auto" ? "auto" : "manual"
    });
  }

  function requireOperands(envelope) {
    if (!isRecord(envelope?.operands)) throw new TypeError("Worldbuilder perception operands must be an object.");
    return envelope.operands;
  }

  function requirePreviewSession(value) {
    const sessionId = cleanString(value);
    if (!sessionId || sessionId.length > MAX_PREVIEW_SESSION_ID) {
      throw new TypeError("Worldbuilder placement preview requires a bounded session id.");
    }
    return sessionId;
  }

  runtime.registerPerceptionOperation(OPERATIONS.camera, envelope => {
    const operands = requireOperands(envelope);
    const viewer = authority();
    let snapshot = currentSnapshot();

    if (Object.prototype.hasOwnProperty.call(operands, "mode") && operands.mode !== "auto" && operands.mode !== "manual") {
      throw new TypeError("Worldbuilder camera mode must be 'auto' or 'manual'.");
    }
    for (const key of ["x", "y", "zoom"]) {
      if (Object.prototype.hasOwnProperty.call(operands, key) && !finite(operands[key])) {
        throw new TypeError(`Worldbuilder camera ${key} must be a finite number.`);
      }
    }

    const mode = operands.mode ?? snapshot.mode;
    if (mode === "auto" && !Object.prototype.hasOwnProperty.call(operands, "zoom")) {
      snapshot = viewer.resetAutoZoom({ source: "semantic-perception" });
    } else if (Object.prototype.hasOwnProperty.call(operands, "zoom") || Object.prototype.hasOwnProperty.call(operands, "mode")) {
      snapshot = viewer.setZoom(operands.zoom ?? snapshot.zoom, { mode, source: "semantic-perception" });
    }

    if (Object.prototype.hasOwnProperty.call(operands, "x") || Object.prototype.hasOwnProperty.call(operands, "y")) {
      snapshot = viewer.setPosition(
        operands.x ?? snapshot.x,
        operands.y ?? snapshot.y,
        true,
        "semantic-perception"
      );
    }

    return snapshot;
  });

  runtime.registerPerceptionOperation(OPERATIONS.grid, envelope => {
    const operands = requireOperands(envelope);
    if (!exactBoolean(operands.enabled)) throw new TypeError("Worldbuilder grid enabled must be boolean.");
    return authority().setGrid(operands.enabled, { source: "semantic-perception" });
  });

  runtime.registerPerceptionOperation(OPERATIONS.cameraNavigationLock, envelope => {
    const operands = requireOperands(envelope);
    if (!exactBoolean(operands.enabled)) throw new TypeError("Worldbuilder camera-navigation lock enabled must be boolean.");
    return authority().setLocked(operands.enabled, { source: "semantic-perception" });
  });

  runtime.registerPerceptionOperation(OPERATIONS.placementPreviewPointer, envelope => {
    const operands = requireOperands(envelope);
    const sessionId = requirePreviewSession(operands.sessionId);
    if (!finite(operands.x) || !finite(operands.y)) {
      throw new TypeError("Worldbuilder placement preview pointer coordinates must be finite numbers.");
    }
    const presenter = window.ristPlacementPreviewPresentation;
    if (!presenter || typeof presenter.applyQuickSlot !== "function") {
      throw new Error("Worldbuilder placement preview presenter is unavailable.");
    }
    // Presenter is visual-only. It must reject an inactive session rather than reviving a cleared drag.
    return presenter.applyQuickSlot(Object.freeze({ sessionId, x: operands.x, y: operands.y }));
  });

  function cameraEnvelope(operands, { source = "worldbuilder-adaptive-camera" } = {}) {
    if (!isRecord(operands)) throw new TypeError("Worldbuilder camera operands must be an object.");
    return runtime.createEnvelope({
      kind: "perception",
      operation: runtime.operation("runtime-perception", OPERATIONS.camera),
      target: Object.freeze({
        authoritative: false,
        identity: null,
        representation: Object.freeze({ kind: "worldbuilder-viewer" })
      }),
      operands: Object.freeze({ ...operands }),
      meta: Object.freeze({
        source,
        bridgeVersion: BRIDGE_VERSION,
        perceptionOnly: true,
        adaptive: true
      })
    });
  }

  function placementPreviewEnvelope(sessionId, x, y, { source = "worldbuilder-adaptive-placement-preview" } = {}) {
    const safeSessionId = requirePreviewSession(sessionId);
    if (!finite(x) || !finite(y)) throw new TypeError("Worldbuilder placement preview pointer coordinates must be finite numbers.");
    return runtime.createEnvelope({
      kind: "perception",
      operation: runtime.operation("runtime-perception", OPERATIONS.placementPreviewPointer),
      target: Object.freeze({
        authoritative: false,
        identity: null,
        representation: Object.freeze({ kind: "worldbuilder-placement-preview" })
      }),
      operands: Object.freeze({ sessionId: safeSessionId, x, y }),
      meta: Object.freeze({
        source,
        bridgeVersion: BRIDGE_VERSION,
        perceptionOnly: true,
        transient: true,
        adaptive: true
      })
    });
  }

  function enqueueCamera(operands, { source = "worldbuilder-adaptive-camera", supersedable = true } = {}) {
    if (!runtime.AdaptivePerception?.enqueue) {
      throw new Error("Adaptive perception runtime is unavailable.");
    }
    if (cameraSequence >= Number.MAX_SAFE_INTEGER) {
      throw new RangeError("Worldbuilder camera presentation sequence exhausted.");
    }
    const sequence = ++cameraSequence;
    const envelope = cameraEnvelope(operands, { source });
    return runtime.AdaptivePerception.enqueue(envelope, {
      streamId: CAMERA_STREAM,
      sequence,
      supersedable: supersedable === true
    });
  }

  function enqueuePlacementPreview(sessionId, x, y, { source = "worldbuilder-adaptive-placement-preview" } = {}) {
    if (!runtime.AdaptivePerception?.enqueue) {
      throw new Error("Adaptive perception runtime is unavailable.");
    }
    if (placementPreviewSequence >= Number.MAX_SAFE_INTEGER) {
      throw new RangeError("Worldbuilder placement preview presentation sequence exhausted.");
    }
    const sequence = ++placementPreviewSequence;
    const envelope = placementPreviewEnvelope(sessionId, x, y, { source });
    return runtime.AdaptivePerception.enqueue(envelope, {
      streamId: PLACEMENT_PREVIEW_STREAM,
      sequence,
      supersedable: true
    });
  }

  function emitViewerFeedback(detail) {
    if (!isRecord(detail)) return null;
    const operands = Object.freeze({
      x: finite(detail.x) ? detail.x : 0,
      y: finite(detail.y) ? detail.y : 0,
      zoom: finite(detail.zoom) ? detail.zoom : 1,
      visibleCells: finite(detail.visibleCells) ? detail.visibleCells : null,
      grid: detail.grid === true,
      locked: detail.locked === true,
      mode: detail.mode === "auto" ? "auto" : "manual"
    });
    const envelope = runtime.createEnvelope({
      kind: "feedback",
      operation: runtime.operation("runtime-feedback", "worldbuilder.viewer.state"),
      target: Object.freeze({
        authoritative: false,
        identity: null,
        representation: Object.freeze({ kind: "worldbuilder-viewer" })
      }),
      operands,
      meta: Object.freeze({
        source: typeof detail.source === "string" ? detail.source : "viewer-state",
        bridgeVersion: BRIDGE_VERSION,
        perceptionOnly: true
      })
    });
    window.dispatchEvent(new CustomEvent("shaelvien:feedback", { detail: envelope }));
    return envelope;
  }

  window.addEventListener("rist:viewer-state", event => emitViewerFeedback(event.detail));

  runtime.WorldbuilderPerception = Object.freeze({
    version: BRIDGE_VERSION,
    canonical: false,
    perceptionOnly: true,
    cameraStream: CAMERA_STREAM,
    placementPreviewStream: PLACEMENT_PREVIEW_STREAM,
    operations: OPERATIONS,
    cameraEnvelope,
    placementPreviewEnvelope,
    enqueueCamera,
    enqueuePlacementPreview,
    snapshot: () => currentSnapshot()
  });
})();
