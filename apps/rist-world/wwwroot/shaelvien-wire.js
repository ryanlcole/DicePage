// Shaelvien semantic control-plane wire adapter.
// JSON/UTF-8 is deliberately the first versioned wire representation. It keeps semantics
// inspectable while Rune/Glyph identities and compact binary opcodes remain unfrozen.
// Large pixel/audio/video payloads belong on media/binary channels referenced by envelopes,
// not embedded into this control envelope.
(() => {
  "use strict";

  const runtime = window.Shaelvien;
  if (!runtime?.runtimeVersion || runtime.Wire) return;

  const MAX_CONTROL_BYTES = 1024 * 1024;
  const encoder = new TextEncoder();
  const decoder = new TextDecoder("utf-8", { fatal: true });

  function asBytes(value) {
    if (value instanceof Uint8Array) return value;
    if (value instanceof ArrayBuffer) return new Uint8Array(value);
    if (ArrayBuffer.isView(value)) return new Uint8Array(value.buffer, value.byteOffset, value.byteLength);
    throw new TypeError("Wire payload must be ArrayBuffer or ArrayBufferView.");
  }

  function encode(envelope) {
    const validation = runtime.validateEnvelope(envelope);
    if (!validation.ok) throw new TypeError(`Cannot encode semantic envelope: ${validation.reason}`);
    const bytes = encoder.encode(JSON.stringify(envelope));
    if (bytes.byteLength > MAX_CONTROL_BYTES) {
      throw new RangeError(`Semantic control envelope exceeds ${MAX_CONTROL_BYTES} byte budget.`);
    }
    return bytes;
  }

  function decode(value) {
    const bytes = asBytes(value);
    if (bytes.byteLength > MAX_CONTROL_BYTES) {
      throw new RangeError(`Semantic control envelope exceeds ${MAX_CONTROL_BYTES} byte budget.`);
    }
    const envelope = JSON.parse(decoder.decode(bytes));
    const validation = runtime.validateEnvelope(envelope);
    if (!validation.ok) throw new TypeError(`Rejected semantic envelope: ${validation.reason}`);
    return envelope;
  }

  runtime.Wire = Object.freeze({
    version: "utf8-json/1",
    maxControlBytes: MAX_CONTROL_BYTES,
    encode,
    decode
  });
})();
