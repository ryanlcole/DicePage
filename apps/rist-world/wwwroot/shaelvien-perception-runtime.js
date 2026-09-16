// Shaelvien authorized perception surfaces.
// Pixels are presentation, never persistent identity or authority.
(() => {
  "use strict";

  const runtime = window.Shaelvien;
  if (!runtime?.runtimeVersion || runtime.Perception) return;

  const MAX_DIMENSION = 8192;
  const MAX_RGBA_BYTES = 64 * 1024 * 1024;
  const surfaces = new Map();

  const stringId = value => typeof value === "string" && value.trim() ? value.trim() : null;

  function validateDimensions(width, height) {
    if (!Number.isInteger(width) || !Number.isInteger(height) || width <= 0 || height <= 0) {
      throw new RangeError("Perception dimensions must be positive integers.");
    }
    if (width > MAX_DIMENSION || height > MAX_DIMENSION) {
      throw new RangeError(`Perception surface exceeds ${MAX_DIMENSION}px dimension budget.`);
    }
    const bytes = width * height * 4;
    if (!Number.isSafeInteger(bytes) || bytes > MAX_RGBA_BYTES) {
      throw new RangeError(`RGBA payload exceeds ${MAX_RGBA_BYTES} byte budget.`);
    }
    return bytes;
  }

  function resolveCanvas(canvasOrSelector) {
    const canvas = typeof canvasOrSelector === "string"
      ? document.querySelector(canvasOrSelector)
      : canvasOrSelector;
    if (!(canvas instanceof HTMLCanvasElement)) throw new TypeError("Perception surface must be an HTMLCanvasElement.");
    return canvas;
  }

  function registerSurface(id, canvasOrSelector, options = {}) {
    const key = stringId(id);
    if (!key) throw new TypeError("Perception surface id is required.");
    if (surfaces.has(key)) throw new Error(`Perception surface already registered: ${key}`);

    const canvas = resolveCanvas(canvasOrSelector);
    const context = canvas.getContext("2d", { alpha: options.alpha !== false });
    if (!context) throw new Error("2D canvas context is unavailable.");

    const record = Object.freeze({
      id: key,
      canvas,
      context,
      identity: options.identity || null,
      representationOnly: true
    });
    surfaces.set(key, record);
    canvas.dataset.shaelvienPerceptionSurface = key;
    return () => {
      surfaces.delete(key);
      if (canvas.dataset.shaelvienPerceptionSurface === key) delete canvas.dataset.shaelvienPerceptionSurface;
    };
  }

  function getSurface(id) {
    const key = stringId(id);
    const surface = key ? surfaces.get(key) : null;
    if (!surface) throw new Error(`Unknown perception surface: ${String(id)}`);
    return surface;
  }

  function rgbaBytes(value) {
    if (value instanceof Uint8ClampedArray) return value;
    if (value instanceof Uint8Array) return new Uint8ClampedArray(value.buffer, value.byteOffset, value.byteLength);
    if (value instanceof ArrayBuffer) return new Uint8ClampedArray(value);
    if (ArrayBuffer.isView(value)) return new Uint8ClampedArray(value.buffer, value.byteOffset, value.byteLength);
    if (Array.isArray(value)) return Uint8ClampedArray.from(value);
    throw new TypeError("RGBA payload must be bytes or an array of channel values.");
  }

  function putRgbaFrame(surfaceId, width, height, rgba) {
    const expectedBytes = validateDimensions(width, height);
    const bytes = rgbaBytes(rgba);
    if (bytes.byteLength !== expectedBytes) {
      throw new RangeError(`RGBA frame length ${bytes.byteLength} does not match ${expectedBytes}.`);
    }
    const surface = getSurface(surfaceId);
    if (surface.canvas.width !== width) surface.canvas.width = width;
    if (surface.canvas.height !== height) surface.canvas.height = height;
    surface.context.putImageData(new ImageData(bytes, width, height), 0, 0);
    return Object.freeze({ surfaceId, width, height, bytes: expectedBytes });
  }

  function putRgbaRect(surfaceId, x, y, width, height, rgba) {
    const expectedBytes = validateDimensions(width, height);
    if (![x, y].every(Number.isInteger)) throw new RangeError("Perception rectangle origin must be integer pixels.");
    const bytes = rgbaBytes(rgba);
    if (bytes.byteLength !== expectedBytes) {
      throw new RangeError(`RGBA rectangle length ${bytes.byteLength} does not match ${expectedBytes}.`);
    }
    const surface = getSurface(surfaceId);
    if (x < 0 || y < 0 || x + width > surface.canvas.width || y + height > surface.canvas.height) {
      throw new RangeError("Perception rectangle is outside its registered canvas.");
    }
    surface.context.putImageData(new ImageData(bytes, width, height), x, y);
    return Object.freeze({ surfaceId, x, y, width, height, bytes: expectedBytes });
  }

  function envelopePayload(envelope) {
    if (!envelope?.operands || typeof envelope.operands !== "object") {
      throw new TypeError("Perception envelope requires operands.");
    }
    return envelope.operands;
  }

  runtime.registerPerceptionOperation("runtime.perception.pixel.rgba.frame", envelope => {
    const p = envelopePayload(envelope);
    return putRgbaFrame(p.surfaceId, p.width, p.height, p.rgba);
  });

  runtime.registerPerceptionOperation("runtime.perception.pixel.rgba.rect", envelope => {
    const p = envelopePayload(envelope);
    return putRgbaRect(p.surfaceId, p.x, p.y, p.width, p.height, p.rgba);
  });

  runtime.Perception = Object.freeze({
    maxDimension: MAX_DIMENSION,
    maxRgbaBytes: MAX_RGBA_BYTES,
    registerSurface,
    getSurface,
    putRgbaFrame,
    putRgbaRect
  });
})();
