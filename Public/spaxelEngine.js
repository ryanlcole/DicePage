// ============================================================
// Shaelvien DiceMall – Spaxel Engine v4.1 (Hex Terrain Growth)
// ============================================================

// === Canvas Setup ===
const canvas = document.getElementById("screen");
const ctx = canvas.getContext("2d", { willReadFrequently: false });
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

// === Hex Geometry ===
const HEX_SIZE = 12;
const HEX_W = Math.sqrt(3) * HEX_SIZE;
const HEX_H = 2 * HEX_SIZE * 0.75;
let hexes = [];
let hexIndex = new Map();

function keyQR(q, r) {
  return q + "," + r;
}

// === Terrain Definitions ===
const terrains = {
  ocean:   { hue:[190,230], sat:[0.6,1.0], val:[0.4,0.9], life:5 },
  mountain:{ hue:[0,40],   sat:[0.1,0.4], val:[0.4,0.7],  life:5 },
  volcano: { hue:[0,25],   sat:[0.9,1.0], val:[0.5,1.0],  life:5 },
  tundra:  { hue:[180,200],sat:[0.0,0.2], val:[0.8,1.0],  life:5 },
  desert:  { hue:[30,55],  sat:[0.6,1.0], val:[0.8,1.0],  life:5 },
};

// === Build Hex World ===
function rebuildHexWorld() {
  hexes = [];
  hexIndex.clear();
  const cols = Math.ceil(W / HEX_W) + 4;
  const rows = Math.ceil(H / HEX_H) + 4;
  const cx = W / 2, cy = H / 2;
  for (let r = -rows / 2; r < rows / 2; r++) {
    for (let q = -cols / 2; q < cols / 2; q++) {
      const x = cx + HEX_W * (q + r / 2);
      const y = cy + HEX_H * r;
      const hue = Math.random() * 360;
      const terrain = "none";
      const idx = hexes.push({ q, r, x, y, hue, terrain, birth: 0, grow: 0 }) - 1;
      hexIndex.set(keyQR(q, r), idx);
    }
  }
}
rebuildHexWorld();

// === Color + Utility ===
function HSVtoRGB(h, s, v) {
  let r, g, b;
  const i = Math.floor(h * 6);
  const f = h * 6 - i;
  const p = v * (1 - s);
  const q = v * (1 - f * s);
  const t = v * (1 - (1 - f) * s);
  switch (i % 6) {
    case 0: (r = v), (g = t), (b = p); break;
    case 1: (r = q), (g = v), (b = p); break;
    case 2: (r = p), (g = v), (b = t); break;
    case 3: (r = p), (g = q), (b = v); break;
    case 4: (r = t), (g = p), (b = v); break;
    default: (r = v), (g = p), (b = q);
  }
  return { r: (r * 255) | 0, g: (g * 255) | 0, b: (b * 255) | 0 };
}

function putPixel(x, y, r, g, b) {
  if (x < 0 || y < 0 || x >= W || y >= H) return;
  pix32[y * W + x] = (255 << 24) | (b << 16) | (g << 8) | r;
}

// === Terrain Growth ===
function startTerrainGrowth(hex, terrain) {
  if (!terrains[terrain]) return;
  const t = terrains[terrain];
  hex.terrain = terrain;
  hex.birth = performance.now();
  hex.grow = t.life * 1000;
  hex.seedHue = t.hue[0] + Math.random() * (t.hue[1] - t.hue[0]);
  hex.seedSat = t.sat[0] + Math.random() * (t.sat[1] - t.sat[0]);
  hex.seedVal = t.val[0] + Math.random() * (t.val[1] - t.val[0]);
  hex.noiseSeed = Math.random() * 1000;
}

// === User Interaction ===
canvas.addEventListener("click", (e) => {
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  const q = (mx - W / 2) / HEX_W - (my - H / 2) / (2 * HEX_H);
  const r = (my - H / 2) / HEX_H;
  const aq = Math.round(q);
  const ar = Math.round(r);
  const idx = hexIndex.get(keyQR(aq, ar));
  if (idx === undefined) return;
  const h = hexes[idx];
  const terrainName = prompt("Enter terrain type (ocean, mountain, volcano, tundra, desert):", "ocean");
  if (!terrainName) return;
  startTerrainGrowth(h, terrainName.toLowerCase());
});

// === Render Loop ===
function render() {
  pix32.fill(0xff000000);
  const time = performance.now();
  for (const h of hexes) {
    if (h.terrain !== "none") {
      const t = terrains[h.terrain];
      if (!t) continue;
      const age = (time - h.birth) / h.grow;
      const phase = Math.min(1, age);
      const flicker = Math.sin(time * 0.005 + h.noiseSeed) * 0.05;
      const col = HSVtoRGB(
        (h.seedHue + Math.sin(time * 0.001 + h.noiseSeed) * 5) / 360,
        h.seedSat,
        Math.min(1, h.seedVal * (0.3 + 0.7 * phase + flicker))
      );
      const R = HEX_SIZE * phase;
      const step = Math.PI / 18;
      for (let a = 0; a < Math.PI * 2; a += step) {
        const xx = (h.x + R * Math.cos(a)) | 0;
        const yy = (h.y + R * Math.sin(a)) | 0;
        putPixel(xx, yy, col.r, col.g, col.b);
      }
    } else {
      // draw faint grid
      const col = HSVtoRGB((h.hue % 360) / 360, 0.4, 0.1);
      const R = HEX_SIZE - 1;
      const step = Math.PI / 18;
      for (let a = 0; a < Math.PI * 2; a += step) {
        const xx = (h.x + R * Math.cos(a)) | 0;
        const yy = (h.y + R * Math.sin(a)) | 0;
        putPixel(xx, yy, col.r, col.g, col.b);
      }
    }
  }
  ctx.putImageData(image, 0, 0);
  requestAnimationFrame(render);
}
requestAnimationFrame(render);
