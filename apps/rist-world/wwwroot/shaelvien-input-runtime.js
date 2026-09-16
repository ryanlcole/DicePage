// Shaelvien browser input feedback boundary.
// Existing handlers remain authoritative for legacy behavior during migration. This observer
// never cancels browser events. Only explicit data-rune/data-glyph declarations become semantic
// intents; every other interaction is representation-only feedback.
(() => {
  "use strict";

  const runtime = window.Shaelvien;
  if (!runtime?.runtimeVersion || runtime.Input) return;

  let enabled = true;

  function pointFromEvent(event) {
    if (Number.isFinite(event.clientX) && Number.isFinite(event.clientY)) {
      return { x: event.clientX, y: event.clientY };
    }
    return null;
  }

  function sensitiveTarget(target) {
    return target instanceof HTMLInputElement && (target.type === "password" || target.type === "file");
  }

  function inputDescriptor(event) {
    const pointer = "pointerType" in event ? event.pointerType || "pointer" : null;
    const withholdKeyboard = sensitiveTarget(event.target);
    return Object.freeze({
      modality: pointer || (event instanceof KeyboardEvent ? "keyboard" : "browser"),
      eventType: event.type,
      trustedBrowserEvent: event.isTrusted === true,
      key: event instanceof KeyboardEvent && !withholdKeyboard ? event.key : null,
      code: event instanceof KeyboardEvent && !withholdKeyboard ? event.code : null,
      sensitiveInputWithheld: withholdKeyboard,
      button: "button" in event && Number.isFinite(event.button) ? event.button : null,
      buttons: "buttons" in event && Number.isFinite(event.buttons) ? event.buttons : null,
      altKey: Boolean(event.altKey),
      ctrlKey: Boolean(event.ctrlKey),
      metaKey: Boolean(event.metaKey),
      shiftKey: Boolean(event.shiftKey)
    });
  }

  function valueFeedback(event) {
    const target = event.target;
    if (!(target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement || target instanceof HTMLSelectElement)) {
      return null;
    }

    // Password/file values are deliberately never copied into semantic feedback.
    if (sensitiveTarget(target)) {
      return Object.freeze({ valueKind: target.type, valueWithheld: true });
    }

    if (target instanceof HTMLInputElement && (target.type === "checkbox" || target.type === "radio")) {
      return Object.freeze({ valueKind: target.type, checked: target.checked });
    }

    return Object.freeze({
      valueKind: target.tagName.toLowerCase(),
      value: target.value
    });
  }

  function observe(event) {
    if (!enabled) return;

    const point = pointFromEvent(event);
    const visualTarget = point ? document.elementFromPoint(point.x, point.y) || event.target : event.target;
    const target = runtime.resolveTarget(visualTarget, point);
    const input = inputDescriptor(event);
    const operands = (event.type === "input" || event.type === "change") ? valueFeedback(event) : null;

    const feedback = runtime.emitInput({
      target,
      eventKind: `browser.${event.type}`,
      operands,
      input,
      meta: Object.freeze({ authority: "none", representationFeedback: true })
    });

    // A declared Rune/Glyph is an intent request, never proof of authority. Trusted server-side
    // code must authenticate, validate schema/context and apply Recursive Authority before truth changes.
    if (target.declaration) {
      runtime.emitDeclaredIntent({
        target,
        declaration: target.declaration,
        operands,
        input,
        meta: Object.freeze({
          authority: "request-only",
          feedbackCreatedAt: feedback.createdAt
        })
      });
    }
  }

  const eventTypes = ["click", "change", "input", "keydown"];
  for (const type of eventTypes) window.addEventListener(type, observe, { capture: true, passive: true });

  runtime.Input = Object.freeze({
    enable() { enabled = true; },
    disable() { enabled = false; },
    get enabled() { return enabled; },
    observedEvents: Object.freeze([...eventTypes])
  });
})();
