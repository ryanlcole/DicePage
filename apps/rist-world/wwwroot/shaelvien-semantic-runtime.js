// Shaelvien browser semantic membrane.
//
// FOUNDATIONAL RULES
// - Server/trusted runtime owns truth and authority.
// - Browser owns authorized perception and user feedback.
// - CHID/SHAEP are identity; pixels, DOM nodes, text, paths and layout are representation.
// - This file does not invent canonical Rune/Glyph identifiers. It transports identifiers
//   explicitly declared by trusted application code or markup and provides a runtime-local
//   namespace for presentation handlers.
// - No eval/dynamic source execution. Only registered presentation handlers can execute.
(() => {
  "use strict";

  if (window.Shaelvien?.runtimeVersion) return;

  const RUNTIME_VERSION = "0.1.0";
  const ENVELOPE_SCHEMA = "shaelvien.semantic-envelope/1";
  const KINDS = new Set(["input", "intent", "perception", "feedback"]);
  const perceptionHandlers = new Map();
  let transport = null;

  const isRecord = value => value !== null && typeof value === "object" && !Array.isArray(value);
  const cleanString = value => typeof value === "string" && value.trim() ? value.trim() : null;

  function diagnostic(level, code, detail = null) {
    const payload = Object.freeze({
      level,
      code,
      detail,
      runtimeVersion: RUNTIME_VERSION,
      at: new Date().toISOString()
    });
    window.dispatchEvent(new CustomEvent("shaelvien:diagnostic", { detail: payload }));
    return payload;
  }

  function semanticBindingFromElement(element) {
    if (!(element instanceof Element)) return null;
    const bound = element.closest("[data-chid],[data-shaep],[data-semantic-id],[data-rune],[data-glyph]");
    if (!bound) return null;

    const chid = cleanString(bound.dataset.chid);
    const shaep = cleanString(bound.dataset.shaep);
    const semanticId = cleanString(bound.dataset.semanticId);
    const rune = cleanString(bound.dataset.rune);
    const glyph = cleanString(bound.dataset.glyph);

    const identity = chid
      ? { type: "chid", id: chid }
      : shaep
        ? { type: "shaep", id: shaep }
        : semanticId
          ? { type: "semantic", id: semanticId }
          : null;

    return Object.freeze({
      element: bound,
      identity,
      declaration: glyph
        ? Object.freeze({ type: "glyph", id: glyph })
        : rune
          ? Object.freeze({ type: "rune", id: rune })
          : null
    });
  }

  function representationDescriptor(element, point = null) {
    const node = element instanceof Element ? element : null;
    return Object.freeze({
      authoritative: false,
      kind: "browser-representation",
      tag: node?.tagName?.toLowerCase() || null,
      role: cleanString(node?.getAttribute?.("role")),
      domId: cleanString(node?.id),
      point: point && Number.isFinite(point.x) && Number.isFinite(point.y)
        ? Object.freeze({ x: Math.round(point.x), y: Math.round(point.y) })
        : null
    });
  }

  function resolveTarget(node, point = null) {
    const element = node instanceof Element ? node : node?.parentElement || null;
    const binding = semanticBindingFromElement(element);
    return Object.freeze({
      authoritative: false,
      identity: binding?.identity || null,
      declaration: binding?.declaration || null,
      representation: representationDescriptor(binding?.element || element, point)
    });
  }

  function operation(type, id) {
    const normalizedType = cleanString(type);
    const normalizedId = cleanString(id);
    if (!normalizedType || !normalizedId) throw new TypeError("Semantic operation requires non-empty type and id.");
    return Object.freeze({ type: normalizedType, id: normalizedId });
  }

  function createEnvelope({ kind, operation: op = null, target = null, operands = null, input = null, meta = null } = {}) {
    if (!KINDS.has(kind)) throw new TypeError(`Unsupported semantic envelope kind: ${String(kind)}`);
    if (op !== null && (!isRecord(op) || !cleanString(op.type) || !cleanString(op.id))) {
      throw new TypeError("Envelope operation must contain string type and id.");
    }
    return Object.freeze({
      schema: ENVELOPE_SCHEMA,
      runtimeVersion: RUNTIME_VERSION,
      kind,
      operation: op,
      target,
      operands,
      input,
      meta,
      createdAt: new Date().toISOString()
    });
  }

  function validateEnvelope(envelope) {
    if (!isRecord(envelope)) return { ok: false, reason: "envelope-not-object" };
    if (envelope.schema !== ENVELOPE_SCHEMA) return { ok: false, reason: "schema-mismatch" };
    if (!KINDS.has(envelope.kind)) return { ok: false, reason: "unknown-kind" };
    if (envelope.operation !== null && envelope.operation !== undefined) {
      if (!isRecord(envelope.operation) || !cleanString(envelope.operation.type) || !cleanString(envelope.operation.id)) {
        return { ok: false, reason: "invalid-operation" };
      }
    }
    return { ok: true, reason: null };
  }

  function dispatchEvent(name, envelope) {
    window.dispatchEvent(new CustomEvent(name, { detail: envelope }));
    return envelope;
  }

  function emitInput({ target, eventKind, operands = null, input = null, meta = null }) {
    const envelope = createEnvelope({
      kind: "input",
      operation: operation("runtime-input", eventKind),
      target,
      operands,
      input,
      meta
    });
    return dispatchEvent("shaelvien:input", envelope);
  }

  function emitDeclaredIntent({ target, declaration, operands = null, input = null, meta = null }) {
    if (!declaration?.type || !declaration?.id) return null;
    const envelope = createEnvelope({
      kind: "intent",
      operation: operation(declaration.type, declaration.id),
      target,
      operands,
      input,
      meta
    });
    dispatchEvent("shaelvien:intent", envelope);
    if (transport?.send) {
      Promise.resolve(transport.send(envelope)).catch(error => {
        diagnostic("error", "transport-send-failed", error instanceof Error ? error.message : String(error));
      });
    }
    return envelope;
  }

  function registerPerceptionOperation(id, handler) {
    const key = cleanString(id);
    if (!key) throw new TypeError("Presentation operation id is required.");
    if (typeof handler !== "function") throw new TypeError("Presentation operation handler must be a function.");
    if (perceptionHandlers.has(key)) throw new Error(`Presentation operation already registered: ${key}`);
    perceptionHandlers.set(key, handler);
    return () => perceptionHandlers.delete(key);
  }

  async function applyPerception(envelope) {
    const validation = validateEnvelope(envelope);
    if (!validation.ok) throw new TypeError(`Rejected semantic envelope: ${validation.reason}`);
    if (envelope.kind !== "perception") throw new TypeError("Only perception envelopes can execute in the browser presentation registry.");
    if (envelope.operation?.type !== "runtime-perception") {
      throw new TypeError("Browser presentation registry accepts runtime-perception operations only.");
    }
    const handler = perceptionHandlers.get(envelope.operation.id);
    if (!handler) throw new Error(`Unregistered presentation operation: ${envelope.operation.id}`);
    return await handler(envelope);
  }

  function setTransport(nextTransport) {
    if (nextTransport !== null && (!isRecord(nextTransport) || typeof nextTransport.send !== "function")) {
      throw new TypeError("Transport must be null or an object with send(envelope).");
    }
    transport = nextTransport;
  }

  async function receive(value) {
    let envelope = value;
    if ((value instanceof ArrayBuffer || ArrayBuffer.isView(value)) && window.Shaelvien?.Wire?.decode) {
      envelope = window.Shaelvien.Wire.decode(value);
    }
    const validation = validateEnvelope(envelope);
    if (!validation.ok) throw new TypeError(`Rejected semantic envelope: ${validation.reason}`);
    if (envelope.kind === "perception") return applyPerception(envelope);
    return dispatchEvent("shaelvien:received", envelope);
  }

  const api = {
    runtimeVersion: RUNTIME_VERSION,
    envelopeSchema: ENVELOPE_SCHEMA,
    operation,
    createEnvelope,
    validateEnvelope,
    resolveTarget,
    semanticBindingFromElement,
    emitInput,
    emitDeclaredIntent,
    registerPerceptionOperation,
    applyPerception,
    setTransport,
    receive,
    diagnostic,
    Wire: null,
    Perception: null,
    Input: null
  };

  window.Shaelvien = api;
  window.dispatchEvent(new CustomEvent("shaelvien:runtime-ready", {
    detail: Object.freeze({ runtimeVersion: RUNTIME_VERSION, envelopeSchema: ENVELOPE_SCHEMA })
  }));
})();
