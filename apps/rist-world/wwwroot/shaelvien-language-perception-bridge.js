// Shaelvien semantic bridge for sitewide language presentation.
// Language, direction and typography are perception state; this module does not mutate world truth.
// Runtime-local ids are migration representations and are not canonical Rune/Glyph ids.
(() => {
  "use strict";

  const runtime = window.Shaelvien;
  const languageRuntime = window.RistUiLanguage;
  if (!runtime?.registerPerceptionOperation || !languageRuntime?.setLanguage || runtime.LanguagePerception) return;

  const VERSION = "language-perception-bridge/1";
  const OPERATION = "runtime.perception.ui.language";
  const MAX_LANGUAGE_TOKEN = 96;

  function clean(value) {
    return typeof value === "string" && value.trim() ? value.trim() : null;
  }

  function resolveLanguage(value) {
    const token = clean(value);
    if (!token || token.length > MAX_LANGUAGE_TOKEN) throw new TypeError("Language perception requires a bounded language token.");
    const lower = token.toLocaleLowerCase();
    const matches = new Set();
    for (const option of languageRuntime.languageOptions()) {
      for (const candidate of [option.value, option.label, option.locale, option.code]) {
        if (typeof candidate === "string" && candidate.toLocaleLowerCase() === lower) matches.add(option.value);
      }
    }
    if (matches.size !== 1) {
      throw new Error(matches.size === 0
        ? "Requested language is not registered."
        : "Requested language token is ambiguous; use the language name or locale.");
    }
    return [...matches][0];
  }

  runtime.registerPerceptionOperation(OPERATION, async envelope => {
    if (!envelope?.operands || typeof envelope.operands !== "object" || Array.isArray(envelope.operands)) {
      throw new TypeError("Language perception operands must be an object.");
    }
    const language = resolveLanguage(envelope.operands.language);
    await languageRuntime.setLanguage(language);
    return languageRuntime.state();
  });

  document.addEventListener("rist:ui-language-changed", event => {
    const detail = event.detail;
    if (!detail || typeof detail !== "object") return;
    const envelope = runtime.createEnvelope({
      kind: "feedback",
      operation: runtime.operation("runtime-feedback", "ui.language.state"),
      target: Object.freeze({
        authoritative: false,
        identity: null,
        representation: Object.freeze({ kind: "ui-language" })
      }),
      operands: Object.freeze({
        name: clean(detail.name),
        code: clean(detail.code),
        locale: clean(detail.locale),
        dir: detail.dir === "rtl" ? "rtl" : "ltr",
        label: clean(detail.label)
      }),
      meta: Object.freeze({ version: VERSION, perceptionOnly: true })
    });
    window.dispatchEvent(new CustomEvent("shaelvien:feedback", { detail: envelope }));
  });

  runtime.LanguagePerception = Object.freeze({
    version: VERSION,
    canonical: false,
    perceptionOnly: true,
    operation: OPERATION,
    state: () => languageRuntime.state()
  });
})();
