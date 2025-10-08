// ============================================================
// HEX PIXEL ENGINE  (stand-alone JS module)
// ============================================================

const canvas = document.getElementById("screen");
const ctx = canvas.getContext("2d", { willReadFrequently: false });

// --- screen buffer -------------------------------------------------
let W, H, image, pix32;
function allocScreen() {
  W = innerWidth;
  H = innerHeight;
  canvas.width = W;
  canvas.height = H;
  image = ctx.createImageData(W, H);
  pix32 = new Uint32Array(image.data.buffer);
}
addEventListener("resize", () => {
  allocScreen();
  rebuildHexWorld();
});
allocScreen();

// --- hex topology --------------------------------------------------
const HEX_SIZE = 12;
const HEX_W = Math.sqrt(3) * HEX_SIZE;
const HEX_H = 2 * HEX_SIZE * 0.75;
let hexes = [],
  hexIndex = new Map();
let SW = 0,
  SH = 0,
  spEnergyA,
  spEnergyB,
  spElem,
  spOwner;

function keyQR(q, r) {
  return q + "," + r;
}

function rebuildHexWorld() {
  hexes = [];
  hexIndex.clear();
  const cols = Math.ceil(W / HEX_W) + 4;
  const rows = Math.ceil(H / HEX_H) + 4;
  const cx = W / 2,
    cy = H / 2;

  for (let r = -rows / 2; r < rows / 2; r++) {
    for (let q = -cols / 2; q < cols / 2; q++) {
      const x = cx + HEX_W * (q + r / 2);
      const y = cy + HEX_H * r;
      const hue = Math.random() * 360;
      const elem = 1 + ((Math.random() * 5) | 0);
      const phase = Math.random() * Math.PI * 2;
      const idx = hexes.push({ q, r, x, y, hue, elem, phase }) - 1;
      hexIndex.set(keyQR(q, r), idx);
    }
  }
  buildSpaxelOwnerMap();
}

// --- spaxel grid ---------------------------------------------------
function buildSpaxels() {
  const scale = 2;
  SW = Math.max(Math.floor(W / scale), 16);
  SH = Math.max(Math.floor(H / scale), 16);
  spEnergyA = new Float32Array(SW * SH);
  spEnergyB = new Float32Array(SW * SH);
  spElem = new Uint8Array(SW * SH);
  spOwner = new Int32Array(SW * SH);
}

function buildSpaxelOwnerMap() {
  buildSpaxels();
  const cx = W / 2,
    cy = H / 2;
  for (let y = 0; y < SH; y++) {
    for (let x = 0; x < SW; x++) {
      const sx = (x + 0.5) * (W / SW);
      const sy = (y + 0.5) * (H / SH);
      const q = (sx - cx) / HEX_W - (sy - cy) / (2 * HEX_H);
      const r = (sy - cy) / HEX_H;
      const aq = Math.round(q),
        ar = Math.round(r);
      const idx = hexIndex.get(keyQR(aq, ar));
      const i = y * SW + x;
      spOwner[i] = idx === undefined ? -1 : idx;
      if (idx !== undefined) {
        spElem[i] = hexes[idx].elem;
        spEnergyA[i] = Math.random() * 0.05;
      } else {
        spElem[i] = 0;
        spEnergyA[i] = 0;
      }
    }
  }
}
rebuildHexWorld();

// --- element rules -------------------------------------------------
function ruleWater(e, v) {
  return v + 0.002 - 0.0005 * e;
}
function ruleFire(e, v) {
  return v - 0.003 + (Math.random() - 0.5) * 0.003;
}
function ruleCrystal(e, v) {
  return v + (v > 0.35 ? 0.002 : 0.005) - 0.0008 * (v > 0.8);
}
function ruleFlora(e, v) {
  const r = 0.015,
    K = 0.9;
  return v + r * v * (K - v);
}
function ruleSand(e, v) {
  return v + 0.0008 - 0.0015 * v;
}
const ruleFn = [
  (e, v) => v,
  ruleWater,
  ruleFire,
  ruleCrystal,
  ruleFlora,
  ruleSand,
];

function idxClamp(x, y) {
  if (x < 0) x = 0;
  if (x >= SW) x = SW - 1;
  if (y < 0) y = 0;
  if (y >= SH) y = SH - 1;
  return y * SW + x;
}

function stepSpaxels() {
  for (let y = 0; y < SH; y++) {
    for (let x = 0; x < SW; x++) {
      const i = y * SW + x;
      const v = spEnergyA[i];
      const n = spEnergyA[idxClamp(x - 1, y)];
      const s = spEnergyA[idxClamp(x + 1, y)];
      const e = spEnergyA[idxClamp(x, y - 1)];
      const w = spEnergyA[idxClamp(x, y + 1)];
      let out = v + (n + s + e + w - 4 * v) * 0.22;
      const el = spElem[i] || 0;
      out = ruleFn[el](el, out);
      spEnergyB[i] = out < 0 ? 0 : out > 1 ? 1 : out;
    }
  }
  const tmp = spEnergyA;
  spEnergyA = spEnergyB;
  spEnergyB = tmp;
}

// --- interaction ---------------------------------------------------
canvas.addEventListener("click", (e) => {
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left,
    my = e.clientY - rect.top;
  const q = (mx - W / 2) / HEX_W - (my - H / 2) / (2 * HEX_H);
  const r = (my - H / 2) / HEX_H;
  const aq = Math.round(q),
    ar = Math.round(r);
  const idx = hexIndex.get(keyQR(aq, ar));
  if (idx === undefined) return;
  const h = hexes[idx];
  h.elem = (h.elem % 5) + 1;
  h.hue = (h.hue + 36) % 360;

  const radX = Math.ceil((HEX_W * 0.8) / (W / SW));
  const radY = Math.ceil((HEX_H * 0.8) / (H / SH));
  const cx = Math.floor(h.x / (W / SW)),
    cy = Math.floor(h.y / (H / SH));
  for (let y = cy - radY; y <= cy + radY; y++) {
    for (let x = cx - radX; x <= cx + radX; x++) {
      if (x < 0 || y < 0 || x >= SW || y >= SH) continue;
      const i = y * SW + x;
      if (spOwner[i] === idx) {
        spElem[i] = h.elem;
        spEnergyA[i] = Math.min(1, spEnergyA[i] + 0.1);
      }
    }
  }
});

// --- color helpers -------------------------------------------------
function HSVtoRGB(h, s, v) {
  let r, g, b;
  const i = Math.floor(h * 6),
    f = h * 6 - i,
    p = v * (1 - s),
    q = v * (1 - f * s),
    t = v * (1 - (1 - f) * s);
  switch (i % 6) {
    case 0:
      r = v;
      g = t;
      b = p;
      break;
    case 1:
      r = q;
      g = v;
      b = p;
      break;
    case 2:
      r = p;
      g = v;
      b = t;
      break;
    case 3:
      r = p;
      g = q;
      b = v;
      break;
    case 4:
      r = t;
      g = p;
      b = v;
      break;
    default:
      r = v;
      g = p;
      b = q;
  }
  return { r: (r * 255) | 0, g: (g * 255) | 0, b: (b * 255) | 0 };
}

function putPixel(x, y, r, g, b) {
  if (x < 0 || y < 0 || x >= W || y >= H) return;
  pix32[y * W + x] = (255 << 24) | (b << 16) | (g << 8) | r;
}

// --- rendering -----------------------------------------------------
function render(t) {
  pix32.fill(0xff000000);
  const sx = W / SW,
    sy = H / SH;
  for (let y = 0; y < SH; y++) {
    const y0 = (y * sy) | 0,
      y1 = ((y + 1) * sy) | 0;
    for (let x = 0; x < SW; x++) {
      const i = y * SW + x,
        v = spEnergyA[i],
        owner = spOwner[i];
      if (owner < 0) continue;
      const hex = hexes[owner];
      const base = HSVtoRGB((hex.hue % 360) / 360, 0.85, 0.55 + 0.45 * v);
      for (let yy = y0; yy < y1; yy++) {
        let row = yy * W;
        for (let xx = (x * sx) | 0; xx < ((x + 1) * sx) | 0; xx++) {
          pix32[row + xx] =
            (255 << 24) | (base.b << 16) | (base.g << 8) | base.r;
        }
      }
    }
  }
  for (const h of hexes) {
    const col = HSVtoRGB((h.hue % 360) / 360, 0.5, 1.0);
    const R = HEX_SIZE - 1,
      step = Math.PI / 18;
    for (let a = 0; a < Math.PI * 2; a += step) {
      const xx = (h.x + R * Math.cos(a)) | 0;
      const yy = (h.y + R * Math.sin(a)) | 0;
      putPixel(xx, yy, col.r, col.g, col.b);
    }
  }
  ctx.putImageData(image, 0, 0);
}

// --- main loop -----------------------------------------------------
let last = performance.now(),
  acc = 0,
  target = 1000 / 120;
function loop(now) {
  const dt = now - last;
  last = now;
  acc += dt;
  while (acc >= target) {
    stepSpaxels();
    acc -= target;
  }
  render(now * 0.001);
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);
