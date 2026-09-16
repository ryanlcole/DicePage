// World Builder Rune Test browser boundary.
// The world/rule layer decides what a rune means. This module only decodes
// fixed-width numeric packets into browser-facing presentation instructions.

const STRIDE = 4;

const OP = Object.freeze({
  VIEW: 1,
  FOOTPRINT: 2,
  Z_LOCK: 3,
  LAYER: 4,
  TIER: 5,
  LAYER_PANEL: 6,
  TIER_PANEL: 7,
  LIBRARY: 8,
  ASSET_STAGE: 9,
  SAVE: 10,
  LOAD_LOCAL: 11,
  LOAD_PRIVATE: 12,
  PUBLISH: 13,
  BENCHMARK_MARK: 14
});

const OP_NAMES = Object.freeze({
  [OP.VIEW]: "VIEW",
  [OP.FOOTPRINT]: "FOOTPRINT",
  [OP.Z_LOCK]: "Z_LOCK",
  [OP.LAYER]: "LAYER",
  [OP.TIER]: "TIER",
  [OP.LAYER_PANEL]: "LAYER_PANEL",
  [OP.TIER_PANEL]: "TIER_PANEL",
  [OP.LIBRARY]: "LIBRARY",
  [OP.ASSET_STAGE]: "ASSET_STAGE",
  [OP.SAVE]: "SAVE",
  [OP.LOAD_LOCAL]: "LOAD_LOCAL",
  [OP.LOAD_PRIVATE]: "LOAD_PRIVATE",
  [OP.PUBLISH]: "PUBLISH",
  [OP.BENCHMARK_MARK]: "BENCHMARK"
});

const encoder = new TextEncoder();
const encodedBytes = value => encoder.encode(JSON.stringify(value)).byteLength;

function decodePacket(root, packet, writeDom) {
  const started = performance.now();
  const trace = [];
  let decoded = 0;

  for (let i = 0; i + 3 < packet.length; i += STRIDE) {
    const op = packet[i] | 0;
    const a = packet[i + 1] | 0;
    const b = packet[i + 2] | 0;
    const c = packet[i + 3] | 0;
    const name = OP_NAMES[op] || `OP_${op}`;
    decoded++;

    // Presentation only. World legality/authority has already been decided
    // by the rune engine before the packet reaches this browser boundary.
    if (writeDom && root) {
      switch (op) {
        case OP.VIEW:
          root.dataset.runeGrid = a ? "on" : "off";
          break;
        case OP.FOOTPRINT:
          root.dataset.runeFootprint = String(a);
          break;
        case OP.Z_LOCK:
          root.dataset.runeZLock = a ? "locked" : "unlocked";
          break;
        case OP.LAYER:
          root.dataset.runeLayer = String(b);
          root.dataset.runeSceneZ = String(c);
          break;
        case OP.TIER:
          root.dataset.runeTier = String(b);
          break;
        case OP.LAYER_PANEL:
          root.dataset.runeLayerPanel = a ? "open" : "closed";
          break;
        case OP.TIER_PANEL:
          root.dataset.runeTierPanel = a ? "open" : "closed";
          break;
        case OP.LIBRARY:
          root.dataset.runeLibrary = a ? "open" : "closed";
          break;
        case OP.ASSET_STAGE:
          root.dataset.runeAssetSlot = String(a);
          break;
        case OP.PUBLISH:
          root.dataset.runePublish = a ? "on" : "off";
          break;
      }
    }

    if (trace.length < 8) trace.push(`${name}(${a},${b},${c})`);
  }

  const elapsed = performance.now() - started;
  const packedLogicalBytes = packet.length * 4;
  const interopJsonBytes = encodedBytes(packet);
  const verbose = [];
  for (let i = 0; i + 3 < packet.length; i += STRIDE) {
    verbose.push({ op: OP_NAMES[packet[i] | 0] || `OP_${packet[i] | 0}`, a: packet[i + 1] | 0, b: packet[i + 2] | 0, c: packet[i + 3] | 0 });
  }
  const verboseJsonBytes = encodedBytes(verbose);

  if (writeDom && root) {
    root.dataset.runeLast = trace.length ? trace[trace.length - 1] : "—";
    const traceNode = root.querySelector("[data-rune-trace]");
    if (traceNode) traceNode.textContent = trace.join(" · ") || "No runes decoded yet";
  }

  return [decoded, elapsed, packedLogicalBytes, interopJsonBytes, verboseJsonBytes];
}

function benchmarkDecode(packet, runeCount) {
  let checksum = 0;
  const values = packet.length;
  for (let rune = 0; rune < runeCount; rune++) {
    const i = (rune * STRIDE) % values;
    const op = packet[i] | 0;
    const a = packet[i + 1] | 0;
    const b = packet[i + 2] | 0;
    const c = packet[i + 3] | 0;
    switch (op) {
      case OP.VIEW:
      case OP.Z_LOCK:
      case OP.LAYER_PANEL:
      case OP.TIER_PANEL:
      case OP.LIBRARY:
      case OP.PUBLISH:
        checksum ^= (a & 1);
        break;
      case OP.LAYER:
      case OP.TIER:
        checksum = (checksum + a + b + c) | 0;
        break;
      default:
        checksum = (checksum + op + a) | 0;
        break;
    }
  }
  return checksum;
}

export function attach(root) {
  let disposed = false;

  return {
    dispatch(packet) {
      if (disposed) return [0, 0, 0, 0, 0];
      return decodePacket(root, Array.isArray(packet) ? packet : [], true);
    },

    benchmark(iterations = 10000, runesPerBatch = 32) {
      const count = Math.max(1, Math.min(250000, iterations | 0));
      const batchSize = Math.max(1, Math.min(512, runesPerBatch | 0));
      const packet = new Array(batchSize * STRIDE);
      for (let r = 0; r < batchSize; r++) {
        const i = r * STRIDE;
        packet[i] = (r % 13) + 1;
        packet[i + 1] = r & 31;
        packet[i + 2] = (r * 2) & 63;
        packet[i + 3] = (r * 3) & 127;
      }

      const started = performance.now();
      const checksum = benchmarkDecode(packet, count);
      const elapsed = performance.now() - started;
      const logicalBytes = count * STRIDE * 4;
      const packedJsonBytesPerBatch = encodedBytes(packet);
      const verbose = [];
      for (let r = 0; r < batchSize; r++) {
        const i = r * STRIDE;
        verbose.push({ op: OP_NAMES[packet[i]] || `OP_${packet[i]}`, a: packet[i + 1], b: packet[i + 2], c: packet[i + 3] });
      }
      const verboseJsonBytesPerBatch = encodedBytes(verbose);
      return [count, elapsed, logicalBytes, packedJsonBytesPerBatch, verboseJsonBytesPerBatch, checksum];
    },

    dispose() {
      disposed = true;
    }
  };
}

export { OP, STRIDE };
