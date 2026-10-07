const FACE_LAYOUT = [
  [0, 0], // front
  [1, 0], // right
  [2, 0], // back
  [0, 1], // left
  [1, 1], // top
  [2, 1]  // bottom
];

function imageFromUrl(url) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("Image could not be decoded."));
    image.src = url;
  });
}

function parseHex(value) {
  const raw = String(value || "#ffffff").replace("#", "").trim();
  const hex = raw.length === 3 ? raw.split("").map(x => x + x).join("") : raw.padEnd(6, "f").slice(0, 6);
  return [parseInt(hex.slice(0, 2), 16), parseInt(hex.slice(2, 4), 16), parseInt(hex.slice(4, 6), 16)];
}

function colorDistanceSq(data, index, key) {
  const r = data[index] - key[0];
  const g = data[index + 1] - key[1];
  const b = data[index + 2] - key[2];
  return r * r + g * g + b * b;
}

export async function processFace(dataUrl, keyHex, tolerancePercent, targetSize = 512) {
  const image = await imageFromUrl(dataUrl);
  const maxWorkSide = 1600;
  const scale = Math.min(1, maxWorkSide / Math.max(image.naturalWidth || image.width, image.naturalHeight || image.height));
  const width = Math.max(1, Math.round((image.naturalWidth || image.width) * scale));
  const height = Math.max(1, Math.round((image.naturalHeight || image.height) * scale));

  const work = document.createElement("canvas");
  work.width = width;
  work.height = height;
  const ctx = work.getContext("2d", { willReadFrequently: true });
  ctx.drawImage(image, 0, 0, width, height);
  const pixels = ctx.getImageData(0, 0, width, height);
  const data = pixels.data;
  const key = parseHex(keyHex);
  const maxDistance = 441.67295593 * Math.max(0, Math.min(100, Number(tolerancePercent) || 0)) / 100;
  const thresholdSq = maxDistance * maxDistance;
  const count = width * height;
  const visited = new Uint8Array(count);
  const queue = new Int32Array(count);
  let head = 0;
  let tail = 0;

  const matches = pixel => {
    const offset = pixel * 4;
    return data[offset + 3] === 0 || colorDistanceSq(data, offset, key) <= thresholdSq;
  };
  const enqueue = pixel => {
    if (pixel < 0 || pixel >= count || visited[pixel] || !matches(pixel)) return;
    visited[pixel] = 1;
    queue[tail++] = pixel;
  };

  for (let x = 0; x < width; x++) {
    enqueue(x);
    enqueue((height - 1) * width + x);
  }
  for (let y = 1; y < height - 1; y++) {
    enqueue(y * width);
    enqueue(y * width + width - 1);
  }

  while (head < tail) {
    const pixel = queue[head++];
    const x = pixel % width;
    const y = Math.floor(pixel / width);
    data[pixel * 4 + 3] = 0;
    if (x > 0) enqueue(pixel - 1);
    if (x + 1 < width) enqueue(pixel + 1);
    if (y > 0) enqueue(pixel - width);
    if (y + 1 < height) enqueue(pixel + width);
  }
  ctx.putImageData(pixels, 0, 0);

  let minX = width, minY = height, maxX = -1, maxY = -1;
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      if (data[(y * width + x) * 4 + 3] < 8) continue;
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (y < minY) minY = y;
      if (y > maxY) maxY = y;
    }
  }
  if (maxX < minX || maxY < minY) throw new Error("The selected outside color removed the entire image. Choose a different color or lower the tolerance.");

  const subjectWidth = maxX - minX + 1;
  const subjectHeight = maxY - minY + 1;
  const target = document.createElement("canvas");
  target.width = targetSize;
  target.height = targetSize;
  const out = target.getContext("2d");
  out.clearRect(0, 0, targetSize, targetSize);
  const padding = Math.max(8, Math.round(targetSize * 0.06));
  const available = targetSize - padding * 2;
  const fit = Math.min(available / subjectWidth, available / subjectHeight);
  const drawWidth = subjectWidth * fit;
  const drawHeight = subjectHeight * fit;
  const dx = (targetSize - drawWidth) / 2;
  const dy = (targetSize - drawHeight) / 2;
  out.imageSmoothingEnabled = true;
  out.imageSmoothingQuality = "high";
  out.drawImage(work, minX, minY, subjectWidth, subjectHeight, dx, dy, drawWidth, drawHeight);
  return target.toDataURL("image/png");
}

export async function buildAtlas(faceDataUrls, faceSize = 512) {
  if (!Array.isArray(faceDataUrls) || faceDataUrls.length !== 6) throw new Error("Rock Candy d6 requires exactly six cleaned views.");
  const atlas = document.createElement("canvas");
  atlas.width = faceSize * 3;
  atlas.height = faceSize * 2;
  const ctx = atlas.getContext("2d");
  ctx.clearRect(0, 0, atlas.width, atlas.height);
  for (let i = 0; i < 6; i++) {
    const image = await imageFromUrl(faceDataUrls[i]);
    const [column, row] = FACE_LAYOUT[i];
    ctx.drawImage(image, column * faceSize, row * faceSize, faceSize, faceSize);
  }
  return atlas.toDataURL("image/png");
}

function isRockCandySource(src) {
  if (!src) return false;
  let value = String(src).toLowerCase();
  try { value = decodeURIComponent(value); } catch { }
  return value.includes("/rock-candy/") || value.includes("rock-candy%2f") || value.includes("rock-candy");
}

const BOARD_FACES = [
  ["front", "0%", "0%"],
  ["right", "50%", "0%"],
  ["back", "100%", "0%"],
  ["left", "0%", "100%"],
  ["top", "50%", "100%"],
  ["bottom", "100%", "100%"]
];

function decorateTile(tile) {
  const crop = tile.querySelector(":scope > .tile-image-crop");
  const image = crop?.querySelector("img");
  if (!image || !isRockCandySource(image.src)) return;
  if (tile.dataset.rockCandySource === image.src && tile.querySelector(":scope > .rock-candy-render")) return;

  tile.querySelector(":scope > .rock-candy-render")?.remove();
  tile.dataset.rockCandySource = image.src;
  tile.classList.add("rock-candy-tile");
  const viewport = document.createElement("span");
  viewport.className = "rock-candy-render";
  viewport.setAttribute("aria-hidden", "true");
  const cube = document.createElement("span");
  cube.className = "rock-candy-cube";
  for (const [name, x, y] of BOARD_FACES) {
    const face = document.createElement("span");
    face.className = `rock-candy-board-face rc-board-${name}`;
    face.style.backgroundImage = `url("${image.src.replaceAll('"', '%22')}")`;
    face.style.backgroundSize = "300% 200%";
    face.style.backgroundPosition = `${x} ${y}`;
    cube.appendChild(face);
  }
  viewport.appendChild(cube);
  tile.appendChild(viewport);
}

function decorateBoard(root = document) {
  root.querySelectorAll?.(".world-stage .tile-cell").forEach(decorateTile);
}

function installBoardObserver() {
  if (window.__ristRockCandyObserver) return;
  const observer = new MutationObserver(records => {
    for (const record of records) {
      if (record.type === "attributes" && record.target instanceof HTMLImageElement) {
        const tile = record.target.closest(".world-stage .tile-cell");
        if (tile) decorateTile(tile);
      }
      for (const node of record.addedNodes) {
        if (!(node instanceof Element)) continue;
        if (node.matches(".world-stage .tile-cell")) decorateTile(node);
        decorateBoard(node);
      }
    }
  });
  observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ["src"] });
  window.__ristRockCandyObserver = observer;
  decorateBoard();
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", installBoardObserver, { once: true });
else installBoardObserver();
