// Shaelvien fail-closed DOM perception surface.
//
// This module lets trusted perception envelopes alter a small presentation allowlist by
// stable semantic identity. It intentionally does NOT accept CSS selectors, DOM paths,
// arbitrary attributes, HTML, URLs, classes, styles, event handlers, or source code.
// Runtime-local operation ids are migration representations, not canonical Rune/Glyph ids.
(() => {
  "use strict";

  const runtime = window.Shaelvien;
  if (!runtime?.registerPerceptionOperation || runtime.DomPerception) return;

  const VERSION = "dom-perception/1";
  const MAX_TEXT = 65536;
  const OPERATIONS = Object.freeze({
    text: "runtime.perception.dom.text",
    hidden: "runtime.perception.dom.hidden",
    disabled: "runtime.perception.dom.disabled"
  });
  const IDENTITY_ATTRS = Object.freeze({
    chid: "chid",
    shaep: "shaep",
    semantic: "semanticId"
  });

  const isRecord = value => value !== null && typeof value === "object" && !Array.isArray(value);
  const exactBoolean = value => typeof value === "boolean";
  const cleanIdentity = value => typeof value === "string" && value.trim() ? value.trim() : null;

  function declaredIdentities(element) {
    const values = [];
    const chid = cleanIdentity(element?.dataset?.chid);
    const shaep = cleanIdentity(element?.dataset?.shaep);
    const semantic = cleanIdentity(element?.dataset?.semanticId);
    if (chid) values.push({ type: "chid", id: chid });
    if (shaep) values.push({ type: "shaep", id: shaep });
    if (semantic) values.push({ type: "semantic", id: semantic });
    return values;
  }

  function resolveUniqueTarget(envelope) {
    const identity = envelope?.target?.identity;
    const type = cleanIdentity(identity?.type);
    const id = cleanIdentity(identity?.id);
    const datasetKey = IDENTITY_ATTRS[type];
    if (!datasetKey || !id) throw new TypeError("DOM perception requires one supported semantic target identity.");

    const candidates = document.querySelectorAll("[data-chid],[data-shaep],[data-semantic-id]");
    const matches = [];
    for (const element of candidates) {
      const identities = declaredIdentities(element);
      if (identities.length !== 1) continue;
      if (identities[0].type === type && identities[0].id === id) matches.push(element);
      if (matches.length > 1) break;
    }
    if (matches.length !== 1) {
      throw new Error(matches.length === 0
        ? "Semantic DOM target was not found."
        : "Semantic DOM target is ambiguous; refusing perception mutation.");
    }
    return matches[0];
  }

  function requireOperands(envelope) {
    if (!isRecord(envelope?.operands)) throw new TypeError("DOM perception operands must be an object.");
    return envelope.operands;
  }

  function emitFeedback(operationId, envelope, operands) {
    const feedback = runtime.createEnvelope({
      kind: "feedback",
      operation: runtime.operation("runtime-feedback", operationId),
      target: envelope.target,
      operands: Object.freeze(operands),
      meta: Object.freeze({ version: VERSION, perceptionOnly: true })
    });
    window.dispatchEvent(new CustomEvent("shaelvien:feedback", { detail: feedback }));
    return feedback;
  }

  runtime.registerPerceptionOperation(OPERATIONS.text, envelope => {
    const operands = requireOperands(envelope);
    if (typeof operands.text !== "string") throw new TypeError("DOM text perception requires a string text operand.");
    if (operands.text.length > MAX_TEXT) throw new RangeError("DOM text perception exceeds the bounded text limit.");
    const element = resolveUniqueTarget(envelope);
    element.textContent = operands.text;
    emitFeedback("dom.text.applied", envelope, { length: operands.text.length });
    return element;
  });

  runtime.registerPerceptionOperation(OPERATIONS.hidden, envelope => {
    const operands = requireOperands(envelope);
    if (!exactBoolean(operands.hidden)) throw new TypeError("DOM hidden perception requires a boolean hidden operand.");
    const element = resolveUniqueTarget(envelope);
    element.hidden = operands.hidden;
    emitFeedback("dom.hidden.applied", envelope, { hidden: operands.hidden });
    return element;
  });

  runtime.registerPerceptionOperation(OPERATIONS.disabled, envelope => {
    const operands = requireOperands(envelope);
    if (!exactBoolean(operands.disabled)) throw new TypeError("DOM disabled perception requires a boolean disabled operand.");
    const element = resolveUniqueTarget(envelope);
    if (!("disabled" in element)) throw new TypeError("Semantic DOM target does not support the disabled state.");
    element.disabled = operands.disabled;
    emitFeedback("dom.disabled.applied", envelope, { disabled: operands.disabled });
    return element;
  });

  runtime.DomPerception = Object.freeze({
    version: VERSION,
    canonical: false,
    perceptionOnly: true,
    operations: OPERATIONS,
    maxTextLength: MAX_TEXT
  });
})();
