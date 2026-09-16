// Shaelvien adaptive perception scheduler.
//
// EXPERIMENTAL / NONCANONICAL MIGRATION RUNTIME
// This scheduler optimizes presentation work only. It is not a source of truth, authority,
// permissions, Rune/Glyph identity, or transport semantics.
//
// FOUNDATIONAL RULES
// - Only already-authorized `perception` envelopes may enter this scheduler.
// - Intent/input/action envelopes are rejected and can never be coalesced here.
// - Supersession may discard obsolete presentation work, never authoritative actions.
// - Sequence numbers describe one presentation stream only; they are not world revisions.
// - Representation mode selection occurs only among modes explicitly offered by trusted code.
// - Existing `runtime.receive()` behavior remains unchanged during migration.
(() => {
  "use strict";

  const runtime = window.Shaelvien;
  if (!runtime?.runtimeVersion || !runtime?.validateEnvelope || !runtime?.applyPerception || runtime.AdaptivePerception) return;

  const VERSION = "adaptive-perception/1";
  const MAX_STREAMS = 128;
  const MAX_PENDING_PER_STREAM = 32;
  const MAX_STREAM_ID_LENGTH = 128;
  const streams = new Map();

  const clean = value => typeof value === "string" && value.trim() ? value.trim() : null;
  const safeSequence = value => Number.isSafeInteger(value) && value >= 0;

  function requireStreamId(value) {
    const id = clean(value);
    if (!id || id.length > MAX_STREAM_ID_LENGTH) {
      throw new TypeError("Adaptive perception requires a bounded stream id.");
    }
    return id;
  }

  function requirePerceptionEnvelope(envelope) {
    const validation = runtime.validateEnvelope(envelope);
    if (!validation.ok) throw new TypeError(`Rejected adaptive perception envelope: ${validation.reason}`);
    if (envelope.kind !== "perception") {
      throw new TypeError("Adaptive perception accepts presentation envelopes only; input/intent/action work may not be scheduled here.");
    }
    if (envelope.operation?.type !== "runtime-perception") {
      throw new TypeError("Adaptive perception accepts registered runtime-perception operations only.");
    }
    return envelope;
  }

  function createStream(id) {
    if (streams.size >= MAX_STREAMS) throw new RangeError(`Adaptive perception stream budget exceeded (${MAX_STREAMS}).`);
    const stream = {
      id,
      lastAcceptedSequence: -1,
      lastAppliedSequence: -1,
      pending: [],
      scheduled: false,
      draining: false,
      applied: 0,
      superseded: 0,
      stale: 0,
      rejected: 0
    };
    streams.set(id, stream);
    return stream;
  }

  function getStream(id, create = true) {
    const key = requireStreamId(id);
    return streams.get(key) || (create ? createStream(key) : null);
  }

  function scheduleDrain(stream) {
    if (stream.scheduled || stream.draining) return;
    stream.scheduled = true;
    const run = () => {
      stream.scheduled = false;
      void drain(stream).catch(error => {
        runtime.diagnostic?.("error", "adaptive-perception-drain-failed", error instanceof Error ? error.message : String(error));
      });
    };
    if (typeof requestAnimationFrame === "function") requestAnimationFrame(run);
    else setTimeout(run, 0);
  }

  async function drain(stream) {
    if (stream.draining) return;
    stream.draining = true;
    try {
      while (stream.pending.length) {
        const item = stream.pending.shift();
        if (item.sequence <= stream.lastAppliedSequence) {
          stream.stale++;
          item.resolve(Object.freeze({ ok: false, status: "stale", streamId: stream.id, sequence: item.sequence }));
          continue;
        }
        try {
          const result = await runtime.applyPerception(item.envelope);
          stream.lastAppliedSequence = item.sequence;
          stream.applied++;
          item.resolve(Object.freeze({
            ok: true,
            status: "applied",
            streamId: stream.id,
            sequence: item.sequence,
            result
          }));
        } catch (error) {
          stream.rejected++;
          item.reject(error);
        }
      }
    } finally {
      stream.draining = false;
      if (stream.pending.length) scheduleDrain(stream);
    }
  }

  function supersedePending(stream, incoming) {
    if (!incoming.supersedable || stream.pending.length === 0) return;

    // Replace only supersedable presentation entries after the most recent ordered barrier.
    // Non-supersedable perception remains ordered and cannot be jumped by a later frame.
    let barrier = -1;
    for (let i = stream.pending.length - 1; i >= 0; i--) {
      if (!stream.pending[i].supersedable) {
        barrier = i;
        break;
      }
    }

    for (let i = stream.pending.length - 1; i > barrier; i--) {
      const previous = stream.pending[i];
      if (!previous.supersedable) continue;
      stream.pending.splice(i, 1);
      stream.superseded++;
      previous.resolve(Object.freeze({
        ok: false,
        status: "superseded",
        streamId: stream.id,
        sequence: previous.sequence,
        supersededBy: incoming.sequence
      }));
    }
  }

  function enqueue(envelope, options = {}) {
    requirePerceptionEnvelope(envelope);
    const stream = getStream(options.streamId);
    const sequence = options.sequence;
    if (!safeSequence(sequence)) throw new TypeError("Adaptive perception sequence must be a non-negative safe integer.");
    const supersedable = options.supersedable === true;

    if (sequence <= stream.lastAcceptedSequence) {
      stream.stale++;
      return Promise.resolve(Object.freeze({
        ok: false,
        status: "stale",
        streamId: stream.id,
        sequence,
        lastAcceptedSequence: stream.lastAcceptedSequence
      }));
    }

    return new Promise((resolve, reject) => {
      const item = { envelope, sequence, supersedable, resolve, reject };
      supersedePending(stream, item);
      if (stream.pending.length >= MAX_PENDING_PER_STREAM) {
        stream.rejected++;
        reject(new RangeError(`Adaptive perception pending budget exceeded for stream ${stream.id}.`));
        return;
      }
      stream.lastAcceptedSequence = sequence;
      stream.pending.push(item);
      scheduleDrain(stream);
    });
  }

  function negotiate(offer) {
    if (!offer || typeof offer !== "object" || Array.isArray(offer)) {
      throw new TypeError("Adaptive perception offer must be an object.");
    }
    if (offer.authorizedEquivalent !== true) {
      throw new TypeError("Adaptive perception offer must explicitly state that offered representations were authorized as equivalent by trusted code.");
    }
    if (!runtime.ClientPerception?.negotiate) throw new Error("Client perception negotiation runtime is unavailable.");
    return runtime.ClientPerception.negotiate({ offeredModes: offer.offeredModes });
  }

  function snapshot(streamId = null) {
    if (streamId !== null) {
      const stream = getStream(streamId, false);
      return stream ? streamSnapshot(stream) : null;
    }
    return Object.freeze([...streams.values()].map(streamSnapshot));
  }

  function streamSnapshot(stream) {
    return Object.freeze({
      streamId: stream.id,
      lastAcceptedSequence: stream.lastAcceptedSequence,
      lastAppliedSequence: stream.lastAppliedSequence,
      pending: stream.pending.length,
      applied: stream.applied,
      superseded: stream.superseded,
      stale: stream.stale,
      rejected: stream.rejected
    });
  }

  function release(streamId) {
    const stream = getStream(streamId, false);
    if (!stream) return false;
    if (stream.pending.length || stream.draining) return false;
    return streams.delete(stream.id);
  }

  runtime.AdaptivePerception = Object.freeze({
    version: VERSION,
    canonical: false,
    perceptionOnly: true,
    maxStreams: MAX_STREAMS,
    maxPendingPerStream: MAX_PENDING_PER_STREAM,
    enqueue,
    negotiate,
    snapshot,
    release
  });
})();
