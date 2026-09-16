// Shaelvien perception planner.
//
// EXPERIMENTAL / NONCANONICAL MIGRATION RUNTIME
// The planner selects among representation candidates that trusted code has already declared
// authorized and presentation-equivalent for the current viewer. It does not grant authority,
// reveal hidden truth, execute renderers, fetch code, transmit capability data, or mutate world state.
(() => {
  "use strict";

  const runtime = window.Shaelvien;
  if (!runtime?.runtimeVersion || !runtime?.ClientPerception || runtime.PerceptionPlanner) return;

  const VERSION = "perception-planner/1";
  const MAX_CANDIDATES = 16;
  const MAX_ID_LENGTH = 128;
  const MODES = new Set(runtime.ClientPerception.modes || []);
  const isRecord = value => value !== null && typeof value === "object" && !Array.isArray(value);
  const clean = value => typeof value === "string" && value.trim() ? value.trim() : null;

  function boundedId(value, label) {
    const result = clean(value);
    if (!result || result.length > MAX_ID_LENGTH) throw new TypeError(`${label} must be a bounded non-empty string.`);
    return result;
  }

  function normalizeCandidate(candidate, index) {
    if (!isRecord(candidate)) throw new TypeError(`Perception candidate ${index} must be an object.`);
    const representationId = boundedId(candidate.representationId, `Perception candidate ${index} representationId`);
    const mode = clean(candidate.mode);
    if (!mode || !MODES.has(mode)) throw new TypeError(`Perception candidate ${index} has an unsupported mode.`);
    const priority = Number.isInteger(candidate.priority) && candidate.priority >= 0 && candidate.priority <= 1000
      ? candidate.priority
      : index;

    return Object.freeze({
      representationId,
      mode,
      priority,
      accessibility: Object.freeze({
        reducedMotionSafe: candidate.accessibility?.reducedMotionSafe === true,
        forcedColorsSafe: candidate.accessibility?.forcedColorsSafe === true,
        increasedContrastSafe: candidate.accessibility?.increasedContrastSafe === true
      })
    });
  }

  function accessibilityCompatible(candidate, accessibility) {
    if (accessibility.reducedMotion && !candidate.accessibility.reducedMotionSafe) return false;
    if (accessibility.forcedColors && !candidate.accessibility.forcedColorsSafe) return false;
    if (accessibility.increasedContrast && !candidate.accessibility.increasedContrastSafe) return false;
    return true;
  }

  function plan(offer) {
    if (!isRecord(offer)) throw new TypeError("Perception plan offer must be an object.");
    if (offer.authorizedEquivalent !== true) {
      throw new TypeError("Perception planning requires trusted code to explicitly mark all offered representations authorized and presentation-equivalent.");
    }
    const offerId = boundedId(offer.offerId, "Perception offerId");
    if (!Array.isArray(offer.candidates) || offer.candidates.length < 1 || offer.candidates.length > MAX_CANDIDATES) {
      throw new RangeError(`Perception planning requires 1-${MAX_CANDIDATES} candidates.`);
    }

    const profile = runtime.ClientPerception.profile();
    const candidates = offer.candidates.map(normalizeCandidate);
    candidates.sort((a, b) => a.priority - b.priority);

    const compatible = candidates.filter(candidate =>
      profile.supportedModes[candidate.mode] === true && accessibilityCompatible(candidate, profile.accessibility)
    );

    if (!compatible.length) {
      return Object.freeze({
        ok: false,
        version: VERSION,
        offerId,
        selected: null,
        fallbacks: Object.freeze([]),
        reason: "no-compatible-authorized-representation",
        authority: "none",
        executes: false,
        localOnly: true
      });
    }

    const describe = candidate => Object.freeze({
      representationId: candidate.representationId,
      mode: candidate.mode
    });

    return Object.freeze({
      ok: true,
      version: VERSION,
      offerId,
      selected: describe(compatible[0]),
      fallbacks: Object.freeze(compatible.slice(1).map(describe)),
      reason: null,
      authority: "none",
      executes: false,
      localOnly: true
    });
  }

  runtime.PerceptionPlanner = Object.freeze({
    version: VERSION,
    canonical: false,
    maxCandidates: MAX_CANDIDATES,
    plan
  });
})();
