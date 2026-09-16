// Shaelvien client perception negotiation boundary.
//
// This module reports only coarse presentation capabilities. It deliberately does NOT expose
// user-agent strings, exact screen geometry, hardware concurrency, device memory, GPU identity,
// network measurements, or other high-entropy fingerprint material.
//
// FOUNDATIONAL RULES
// - Capability is not authority.
// - Representation is not truth.
// - The trusted side decides what information may be revealed before offering representations.
// - The browser may choose only among explicitly offered, presentation-equivalent modes.
// - Negotiation never executes source code and never changes world truth.
(() => {
  "use strict";

  const runtime = window.Shaelvien;
  if (!runtime?.runtimeVersion || !runtime?.createEnvelope || runtime.ClientPerception) return;

  const VERSION = "client-perception/1";
  const MODES = Object.freeze(["semantic", "local-render", "pixel-delta", "encoded-media"]);
  const isRecord = value => value !== null && typeof value === "object" && !Array.isArray(value);

  function supportsCanvas2d() {
    try {
      const canvas = document.createElement("canvas");
      return Boolean(canvas.getContext("2d"));
    } catch {
      return false;
    }
  }

  function supportsWebgl2() {
    try {
      const canvas = document.createElement("canvas");
      return Boolean(canvas.getContext("webgl2"));
    } catch {
      return false;
    }
  }

  function mediaPreference(query) {
    try {
      return window.matchMedia?.(query)?.matches === true;
    } catch {
      return false;
    }
  }

  function profile() {
    const capabilities = Object.freeze({
      semanticControl: true,
      wasm: typeof WebAssembly === "object",
      canvas2d: supportsCanvas2d(),
      offscreenCanvas: typeof OffscreenCanvas === "function",
      webgl2: supportsWebgl2(),
      webgpu: Boolean(navigator.gpu),
      webcodecsVideo: typeof VideoDecoder === "function" && typeof VideoFrame === "function",
      webcodecsAudio: typeof AudioDecoder === "function" && typeof AudioData === "function",
      webAudio: typeof AudioContext === "function" || typeof window.webkitAudioContext === "function",
      audioWorklet: typeof AudioWorkletNode === "function",
      websocket: typeof WebSocket === "function",
      webtransport: typeof WebTransport === "function",
      webrtc: typeof RTCPeerConnection === "function"
    });

    const accessibility = Object.freeze({
      reducedMotion: mediaPreference("(prefers-reduced-motion: reduce)"),
      forcedColors: mediaPreference("(forced-colors: active)"),
      increasedContrast: mediaPreference("(prefers-contrast: more)")
    });

    const supportedModes = Object.freeze({
      semantic: true,
      "local-render": capabilities.wasm || capabilities.canvas2d || capabilities.webgl2 || capabilities.webgpu,
      "pixel-delta": capabilities.canvas2d,
      "encoded-media": capabilities.webcodecsVideo || capabilities.webcodecsAudio || capabilities.webrtc
    });

    return Object.freeze({
      version: VERSION,
      fingerprintMinimized: true,
      capabilities,
      accessibility,
      supportedModes
    });
  }

  function normalizeMode(value) {
    return typeof value === "string" && MODES.includes(value) ? value : null;
  }

  function negotiate(request = {}) {
    if (!isRecord(request)) throw new TypeError("Perception negotiation request must be an object.");
    const offered = Array.isArray(request.offeredModes) ? request.offeredModes.map(normalizeMode).filter(Boolean) : [];
    if (!offered.length) throw new TypeError("Perception negotiation requires at least one recognized offered mode.");

    // The trusted producer must offer only representations that are already authorized and
    // semantically equivalent for this viewer. This function checks client support only.
    const current = profile();
    const selected = offered.find(mode => current.supportedModes[mode] === true) || null;
    if (!selected) {
      return Object.freeze({ ok: false, selected: null, reason: "no-supported-offered-mode", profile: current });
    }
    return Object.freeze({ ok: true, selected, reason: null, profile: current });
  }

  function feedbackEnvelope() {
    const current = profile();
    return runtime.createEnvelope({
      kind: "feedback",
      operation: runtime.operation("runtime-feedback", "client.perception.capabilities"),
      target: Object.freeze({
        authoritative: false,
        identity: null,
        representation: Object.freeze({ kind: "client-runtime" })
      }),
      operands: current,
      meta: Object.freeze({
        localOnly: true,
        authority: "none",
        truthMutation: false,
        fingerprintMinimized: true
      })
    });
  }

  function announce() {
    const envelope = feedbackEnvelope();
    // Local event only. It is intentionally not sent through the semantic transport automatically;
    // trusted application code must make an explicit policy decision before transmitting it.
    window.dispatchEvent(new CustomEvent("shaelvien:feedback", { detail: envelope }));
    return envelope;
  }

  runtime.ClientPerception = Object.freeze({
    version: VERSION,
    modes: MODES,
    profile,
    negotiate,
    feedbackEnvelope,
    announce
  });

  announce();
})();
