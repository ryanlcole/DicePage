const STATES = new WeakMap();

const STEP_SEQUENCE = Object.freeze([
  Object.freeze({ label: 'Tier 1', tiers: [0] }),
  Object.freeze({ label: 'Tier 2', tiers: [1] }),
  Object.freeze({ label: 'Tier 3', tiers: [2] }),
  Object.freeze({ label: 'Tier 1 + Tier 2', tiers: [0, 1] }),
  Object.freeze({ label: 'Tier 1 + Tier 3', tiers: [0, 2] }),
  Object.freeze({ label: 'Tier 2 + Tier 3', tiers: [1, 2] }),
  Object.freeze({ label: 'Tier 1 + Tier 2 + Tier 3', tiers: [0, 1, 2] })
]);

const SPECTRAL_STEP_SEQUENCE = Object.freeze([
  Object.freeze({ label: 'T1 Violet · Fastest', tiers: [0] }),
  Object.freeze({ label: 'T2 Blue', tiers: [1] }),
  Object.freeze({ label: 'T3 Cyan', tiers: [2] }),
  Object.freeze({ label: 'T4 Green · Structure', tiers: [3] }),
  Object.freeze({ label: 'T5 Yellow', tiers: [4] }),
  Object.freeze({ label: 'T6 Orange', tiers: [5] }),
  Object.freeze({ label: 'T7 Red · Slowest', tiers: [6] }),
  Object.freeze({ label: 'All 7 Spectral Layers', tiers: [0, 1, 2, 3, 4, 5, 6] })
]);

const SCENE_STEP_SEQUENCE = Object.freeze([
  Object.freeze({ label: 'Sprite Scene', tiers: [0, 1, 2, 3] })
]);

const ENDEMAR_DEPTH_FACTORS = Object.freeze([0.28, 0.60, 1.0]);
const SCENE_DEFAULT_DEPTHS = Object.freeze([0.22, 0.48, 0.76, 1.0]);
const SPECTRAL_DEPTH_FACTORS = Object.freeze([1.00, 0.88, 0.76, 0.64, 0.52, 0.40, 0.30]);
const SPECTRAL_OVERSCAN = Object.freeze([1.24, 1.20, 1.16, 1.13, 1.10, 1.07, 1.04]);
const SPECTRAL_MAX_PIXELS = 512 * 288;
const SPECTRAL_FRAME_INTERVAL_MS = 1000 / 30;
const SPRITE_EXPORT_MAX_PIXELS = 256 * 144;
const SPRITE_EXPORT_COLUMNS = 6;
const SPRITE_EXPORT_ROWS = 6;
const SPRITE_EXPORT_FRAMES_PER_PAGE = SPRITE_EXPORT_COLUMNS * SPRITE_EXPORT_ROWS;
const SPRITE_DEFAULT_FPS = 8;
const MIN_CAMERA_SCALE = 1;
const MAX_CAMERA_SCALE = 256;
const ZOOM_STEP = 1.22;
const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

function stateFor(root) {
  const state = STATES.get(root);
  if (!state) throw new Error('Perceiver has not been attached.');
  return state;
}

function setText(node, value) {
  if (node && node.textContent !== value) node.textContent = value;
}

function sequenceFor(state) {
  if (state.mode === 'spectral' || state.mode === 'sprite') return SPECTRAL_STEP_SEQUENCE;
  if (state.mode === 'scene') return SCENE_STEP_SEQUENCE;
  return STEP_SEQUENCE;
}

function updateLayerButtons(state) {
  const spectral = state.mode === 'spectral' || state.mode === 'sprite';
  if (state.layerStrip) state.layerStrip.hidden = !spectral;
  state.layerButtons.forEach(button => {
    const value = button.dataset.perceiverLayer || '';
    const targetStep = value === 'all' ? SPECTRAL_STEP_SEQUENCE.length - 1 : Math.max(0, Number(value) - 1);
    const active = spectral && targetStep === state.currentStep;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', active ? 'true' : 'false');
  });
}

function updateReadout(state) {
  const sequence = sequenceFor(state);
  const step = sequence[state.currentStep] || sequence[sequence.length - 1];
  const label = state.mode === 'spectral'
    ? `Video → Sprites · ${step.label}`
    : state.mode === 'sprite'
      ? `Sprite Movie · ${step.label}`
      : state.mode === 'scene'
        ? `Scene · ${state.sceneTitle || 'Legacy scene'}`
        : step.label;
  setText(state.labelNode, label);
  setText(state.playStateNode, state.playing ? 'Playing' : 'Paused');
  setText(state.motionNode, state.motionEnabled ? 'Tilt Ready' : 'Pointer');
  setText(state.zoomNode, `${Math.round(state.cameraScale * 100)}%`);
  if (state.mode === 'spectral') {
    setText(state.modeNoteNode, 'video frames → 7 parallax tiers → standard WebP sprite sheets · source cadence retained');
  } else if (state.mode === 'sprite') {
    setText(state.modeNoteNode, 'standard PNG/WebP sprite sheets · filename metadata when available · reactive parallax');
  } else if (state.mode === 'scene') {
    setText(state.modeNoteNode, 'background → environment FX → actors → foreground · sprite sheets + reactive parallax');
  } else {
    setText(state.modeNoteNode, '1 → 2 → 3 → 1+2 → 1+3 → 2+3 → 1+2+3 → repeat');
  }
  updateLayerButtons(state);
}

function renderStep(state) {
  const sequence = sequenceFor(state);
  const step = sequence[state.currentStep] || sequence[sequence.length - 1];
  const active = new Set(step.tiers);
  state.layers.forEach((layer, index) => {
    const visible = active.has(index);
    const editOpacity = state.mode === 'sprite' ? spriteEdit(state, index).opacity : 1;
    layer.style.opacity = visible ? String(editOpacity) : '0';
    layer.dataset.active = visible ? 'true' : 'false';
    layer.setAttribute('aria-hidden', visible ? 'false' : 'true');
  });
  updateReadout(state);
}

function advance(state, delta) {
  const sequence = sequenceFor(state);
  const total = sequence.length;
  state.currentStep = (state.currentStep + delta + total) % total;
  state.lastAdvance = performance.now();
  renderStep(state);
}

function screenAdjusted(beta, gamma) {
  const angle = screen.orientation?.angle ?? window.orientation ?? 0;
  if (angle === 90) return { beta: -gamma, gamma: beta };
  if (angle === -90 || angle === 270) return { beta: gamma, gamma: -beta };
  if (Math.abs(angle) === 180) return { beta: -beta, gamma: -gamma };
  return { beta, gamma };
}

function applyPointerTarget(state, clientX, clientY) {
  const rect = state.canvas.getBoundingClientRect();
  if (rect.width < 1 || rect.height < 1) return;
  const nx = ((clientX - rect.left) / rect.width - 0.5) * 2;
  const ny = ((clientY - rect.top) / rect.height - 0.5) * 2;
  state.pointerX = clamp(nx, -1, 1);
  state.pointerY = clamp(ny, -1, 1);
  const motionIsLive = state.motionEnabled && (performance.now() - state.lastMotionAt) < 650;
  if (state.dragging || !motionIsLive) {
    state.targetX = state.pointerX;
    state.targetY = state.pointerY;
  }
}

function applyCamera(state) {
  state.camera.style.transform =
    `translate3d(${state.cameraX.toFixed(2)}px,${state.cameraY.toFixed(2)}px,0) scale(${state.cameraScale.toFixed(5)})`;
  updateReadout(state);
}

function fitCameraState(state) {
  state.cameraScale = 1;
  state.cameraX = 0;
  state.cameraY = 0;
  applyCamera(state);
}

function zoomAt(state, clientX, clientY, factor) {
  const rect = state.canvas.getBoundingClientRect();
  if (rect.width < 1 || rect.height < 1) return;

  const sx = clientX - rect.left;
  const sy = clientY - rect.top;
  const oldScale = state.cameraScale;
  const nextScale = clamp(oldScale * factor, MIN_CAMERA_SCALE, MAX_CAMERA_SCALE);
  if (Math.abs(nextScale - oldScale) < 0.00001) return;

  const worldX = (sx - state.cameraX) / oldScale;
  const worldY = (sy - state.cameraY) / oldScale;
  state.cameraScale = nextScale;
  state.cameraX = sx - worldX * nextScale;
  state.cameraY = sy - worldY * nextScale;
  applyCamera(state);
}

function zoomCenter(state, factor) {
  const rect = state.canvas.getBoundingClientRect();
  zoomAt(state, rect.left + rect.width / 2, rect.top + rect.height / 2, factor);
}

function makeLayer(src, index) {
  const image = document.createElement('img');
  image.className = 'perceiver-layer';
  image.src = src;
  image.alt = '';
  image.draggable = false;
  image.dataset.tier = String(index + 1);
  Object.assign(image.style, {
    position: 'absolute',
    inset: '-3%',
    width: '106%',
    height: '106%',
    objectFit: 'contain',
    objectPosition: 'center',
    opacity: '0',
    visibility: 'visible',
    transition: 'opacity 260ms ease',
    willChange: 'transform, opacity',
    pointerEvents: 'none',
    userSelect: 'none',
    WebkitUserDrag: 'none'
  });
  return image;
}

function addMotionListener(state) {
  if (state.motionListenerAttached) return;
  state.motionListenerAttached = true;
  window.addEventListener('deviceorientation', state.onDeviceOrientation, true);
}

function removeMotionListener(state) {
  if (!state.motionListenerAttached) return;
  state.motionListenerAttached = false;
  window.removeEventListener('deviceorientation', state.onDeviceOrientation, true);
}

async function enableMotion(state) {
  let status = 'unknown';

  try {
    if (window.ristMotionPermission?.request) {
      status = await window.ristMotionPermission.request();
    } else {
      const Orientation = window.DeviceOrientationEvent;
      if (!Orientation) status = 'unsupported';
      else if (typeof Orientation.requestPermission === 'function') {
        status = await Orientation.requestPermission();
      } else {
        status = 'granted';
      }
    }
  } catch {
    status = 'denied';
  }

  state.motionEnabled = status === 'granted';
  state.baselineBeta = null;
  state.baselineGamma = null;

  if (state.motionEnabled) addMotionListener(state);
  else removeMotionListener(state);

  updateReadout(state);
  return state.motionEnabled;
}


function rgbHue(r, g, b) {
  const rn = r / 255;
  const gn = g / 255;
  const bn = b / 255;
  const max = Math.max(rn, gn, bn);
  const min = Math.min(rn, gn, bn);
  const delta = max - min;
  const saturation = max <= 0 ? 0 : delta / max;

  if (delta <= 0.00001) return { hue: 0, saturation, value: max };

  let hue;
  if (max === rn) hue = 60 * (((gn - bn) / delta) % 6);
  else if (max === gn) hue = 60 * (((bn - rn) / delta) + 2);
  else hue = 60 * (((rn - gn) / delta) + 4);
  if (hue < 0) hue += 360;
  return { hue, saturation, value: max };
}

function spectralTierForPixel(r, g, b) {
  const spectral = rgbHue(r, g, b);

  // Neutral pixels have no visible-spectrum wavelength. Keep them in the
  // center structural layer instead of inventing a frequency.
  if (spectral.saturation < 0.10) return 3;

  const hue = spectral.hue;
  if (hue >= 315 || hue < 20) return 6; // Red · longest / slowest.
  if (hue < 45) return 5;               // Orange.
  if (hue < 80) return 4;               // Yellow.
  if (hue < 165) return 3;              // Green / structural center.
  if (hue < 205) return 2;              // Cyan.
  if (hue < 255) return 1;              // Blue.
  return 0;                              // Violet · shortest / fastest.
}

function setVideoStatus(state, value) {
  setText(state.videoStatusNode, value);
}

function fullscreenElement() {
  return document.fullscreenElement || document.webkitFullscreenElement || null;
}

function updateFullscreenButton(state) {
  const nativeActive = fullscreenElement() === state.root;
  const pseudoActive = state.root.classList.contains('perceiver-pseudo-fullscreen');
  setText(state.fullscreenButton, nativeActive || pseudoActive ? 'EXIT FULL SCREEN' : 'FULL SCREEN');
}

function exitPseudoFullscreen(state) {
  if (!state.root.classList.contains('perceiver-pseudo-fullscreen')) return;
  state.root.classList.remove('perceiver-pseudo-fullscreen');
  document.documentElement.style.overflow = state.previousDocumentOverflow || '';
  document.body.style.overflow = state.previousBodyOverflow || '';
  window.scrollTo(0, state.fullscreenScrollY || 0);
  updateFullscreenButton(state);
  fitCameraState(state);
}

async function toggleFullscreen(state) {
  const nativeActive = fullscreenElement() === state.root;
  const pseudoActive = state.root.classList.contains('perceiver-pseudo-fullscreen');

  if (nativeActive) {
    const exit = document.exitFullscreen || document.webkitExitFullscreen;
    if (exit) {
      try { await exit.call(document); } catch {}
    }
    updateFullscreenButton(state);
    return;
  }

  if (pseudoActive) {
    exitPseudoFullscreen(state);
    return;
  }

  const request = state.root.requestFullscreen || state.root.webkitRequestFullscreen;
  if (request) {
    try {
      await request.call(state.root);
      updateFullscreenButton(state);
      requestAnimationFrame(() => fitCameraState(state));
      return;
    } catch {}
  }

  state.fullscreenScrollY = window.scrollY || 0;
  state.previousDocumentOverflow = document.documentElement.style.overflow;
  state.previousBodyOverflow = document.body.style.overflow;
  document.documentElement.style.overflow = 'hidden';
  document.body.style.overflow = 'hidden';
  state.root.classList.add('perceiver-pseudo-fullscreen');
  updateFullscreenButton(state);
  requestAnimationFrame(() => fitCameraState(state));
}

function stopSpectralObjectUrl(state) {
  if (state.videoObjectUrl) {
    URL.revokeObjectURL(state.videoObjectUrl);
    state.videoObjectUrl = '';
  }
}

function spectralProcessingSize(video) {
  const sourceWidth = Math.max(1, video.videoWidth || 1);
  const sourceHeight = Math.max(1, video.videoHeight || 1);
  const sourcePixels = sourceWidth * sourceHeight;
  const scale = sourcePixels > SPECTRAL_MAX_PIXELS
    ? Math.sqrt(SPECTRAL_MAX_PIXELS / sourcePixels)
    : 1;
  return {
    width: Math.max(2, Math.round(sourceWidth * scale)),
    height: Math.max(2, Math.round(sourceHeight * scale))
  };
}

function makeSpectralLayer(index) {
  const wrapper = document.createElement('div');
  wrapper.className = 'perceiver-spectral-layer';
  wrapper.dataset.tier = String(index + 1);
  wrapper.setAttribute('aria-hidden', 'false');
  Object.assign(wrapper.style, {
    position: 'absolute',
    inset: '0',
    display: 'grid',
    placeItems: 'center',
    opacity: '1',
    visibility: 'visible',
    willChange: 'transform, opacity',
    pointerEvents: 'none'
  });

  const canvas = document.createElement('canvas');
  canvas.className = 'perceiver-spectral-canvas';
  Object.assign(canvas.style, {
    position: 'absolute',
    inset: '0',
    display: 'block',
    width: '100%',
    height: '100%',
    objectFit: 'contain',
    objectPosition: '50% 50%',
    margin: 'auto',
    pointerEvents: 'none'
  });
  wrapper.appendChild(canvas);
  wrapper._spectralCanvas = canvas;
  wrapper._spectralContext = canvas.getContext('2d', { alpha: true });
  return wrapper;
}


function sceneWrapper(className) {
  const wrapper = document.createElement('div');
  wrapper.className = className;
  wrapper.setAttribute('aria-hidden', 'false');
  Object.assign(wrapper.style, {
    position: 'absolute',
    inset: '0',
    overflow: 'hidden',
    opacity: '1',
    visibility: 'visible',
    willChange: 'transform, opacity',
    pointerEvents: 'none'
  });
  return wrapper;
}

function sceneImageLayer(src, className) {
  const wrapper = sceneWrapper(className);
  const image = document.createElement('img');
  image.alt = '';
  image.draggable = false;
  image.src = String(src || '');
  Object.assign(image.style, {
    position: 'absolute',
    inset: '0',
    width: '100%',
    height: '100%',
    objectFit: 'cover',
    objectPosition: '50% 50%',
    pointerEvents: 'none',
    userSelect: 'none',
    WebkitUserDrag: 'none'
  });
  wrapper.appendChild(image);
  return wrapper;
}

function waitForImage(image) {
  return new Promise((resolve, reject) => {
    if (image.complete && image.naturalWidth > 0) {
      resolve(image);
      return;
    }
    image.addEventListener('load', () => resolve(image), { once: true });
    image.addEventListener('error', () => reject(new Error('Sprite image failed to load.')), { once: true });
  });
}

function normalizeSpriteSpec(spec = {}) {
  return {
    columns: Math.max(1, Math.floor(Number(spec.columns) || 1)),
    rows: Math.max(1, Math.floor(Number(spec.rows) || 1)),
    frameCount: Math.max(1, Math.floor(Number(spec.frameCount) || 1)),
    frameMs: Math.max(40, Number(spec.frameMs) || 160),
    phase: Math.max(0, Math.floor(Number(spec.phase) || 0))
  };
}

async function createSpriteRecord(spec, canvas, stretch = false) {
  const image = new Image();
  image.decoding = 'async';
  image.src = String(spec?.src || '');
  await waitForImage(image);
  const normalized = normalizeSpriteSpec(spec);
  const frameWidth = Math.max(1, Math.floor(image.naturalWidth / normalized.columns));
  const frameHeight = Math.max(1, Math.floor(image.naturalHeight / normalized.rows));
  canvas.width = stretch ? 960 : frameWidth;
  canvas.height = stretch ? 540 : frameHeight;
  const context = canvas.getContext('2d', { alpha: true });
  return { image, canvas, context, frameWidth, frameHeight, stretch, ...normalized };
}

function drawSceneSprite(record, clockMs) {
  if (!record?.context || !record?.image) return;
  const frame = (Math.floor(clockMs / record.frameMs) + record.phase) % record.frameCount;
  const column = frame % record.columns;
  const row = Math.floor(frame / record.columns) % record.rows;
  const sx = column * record.frameWidth;
  const sy = row * record.frameHeight;
  record.context.clearRect(0, 0, record.canvas.width, record.canvas.height);
  const motionFrame = record.motionOnly && record.motionFrames?.[frame];
  if (motionFrame) {
    record.context.drawImage(motionFrame, 0, 0, record.canvas.width, record.canvas.height);
    return;
  }
  record.context.drawImage(
    record.image,
    sx,
    sy,
    record.frameWidth,
    record.frameHeight,
    0,
    0,
    record.canvas.width,
    record.canvas.height
  );
}

async function buildMotionOnlyFrames(record) {
  if (!record?.image || record.frameCount < 2) return [];
  if (record.motionFrames?.length === record.frameCount) return record.motionFrames;
  const images = [], canvases = [];
  for (let frame = 0; frame < record.frameCount; frame += 1) {
    const column = frame % record.columns;
    const row = Math.floor(frame / record.columns) % record.rows;
    const canvas = document.createElement('canvas');
    canvas.width = record.frameWidth;
    canvas.height = record.frameHeight;
    const ctx = canvas.getContext('2d', { alpha: true, willReadFrequently: true });
    ctx.drawImage(record.image, column * record.frameWidth, row * record.frameHeight,
      record.frameWidth, record.frameHeight, 0, 0, record.frameWidth, record.frameHeight);
    canvases.push({ canvas, ctx });
    images.push(ctx.getImageData(0, 0, record.frameWidth, record.frameHeight));
  }
  const pixels = images[0].data.length;
  for (let i = 0; i < pixels; i += 4) {
    let minR = 255, minG = 255, minB = 255, maxR = 0, maxG = 0, maxB = 0;
    for (const image of images) {
      const d = image.data;
      minR = Math.min(minR, d[i]); maxR = Math.max(maxR, d[i]);
      minG = Math.min(minG, d[i + 1]); maxG = Math.max(maxG, d[i + 1]);
      minB = Math.min(minB, d[i + 2]); maxB = Math.max(maxB, d[i + 2]);
    }
    const delta = Math.max(maxR - minR, maxG - minG, maxB - minB);
    const alphaScale = clamp((delta - 18) / 54, 0, 1);
    for (const image of images) image.data[i + 3] = Math.round(image.data[i + 3] * alphaScale);
  }
  canvases.forEach((entry, index) => entry.ctx.putImageData(images[index], 0, 0));
  record.motionFrames = canvases.map(entry => entry.canvas);
  return record.motionFrames;
}

function clearSceneLayers(state) {
  state.sceneLayers.forEach(layer => layer.remove());
  state.sceneLayers = [];
  state.sceneSprites = [];
  state.sceneDepths = [...SCENE_DEFAULT_DEPTHS];
  state.sceneTitle = '';
  state.sceneClockMs = 0;
  state.sceneLastAt = performance.now();
}

async function loadRistMovie(state, file) {
  if (!file) return;
  if (Number(file.size || 0) > 20 * 1024 * 1024) {
    setVideoStatus(state, 'RISTMOVIE TOO LARGE · 20 MB MAX');
    return;
  }

  let movie;
  try {
    movie = JSON.parse(await file.text());
  } catch {
    setVideoStatus(state, 'RISTMOVIE INVALID JSON');
    return;
  }

  if (movie?.format !== 'ristmovie' || Number(movie?.version) !== 1 || !movie?.layers) {
    setVideoStatus(state, 'RISTMOVIE FORMAT NOT SUPPORTED');
    return;
  }

  if (state.video) {
    state.video.pause();
    state.video.removeAttribute('src');
    state.video.load();
  }
  stopVideoFramePump(state);
  stopSpectralObjectUrl(state);
  clearSceneLayers(state);
  clearSpritePlayback(state);

  const layers = movie.layers || {};
  const backgroundSpec = layers.background || {};
  const effectsSpec = layers.effects || {};
  const actorsSpec = layers.actors || {};
  const foregroundSpec = layers.foreground || {};

  const background = sceneImageLayer(backgroundSpec.src, 'perceiver-scene-background');
  const effects = sceneWrapper('perceiver-scene-effects');
  const actors = sceneWrapper('perceiver-scene-actors');
  const foreground = sceneImageLayer(foregroundSpec.src, 'perceiver-scene-foreground');

  state.camera.append(background, effects, actors, foreground);
  state.sceneLayers = [background, effects, actors, foreground];
  state.sceneDepths = [
    Number(backgroundSpec.depth) || SCENE_DEFAULT_DEPTHS[0],
    Number(effectsSpec.depth) || SCENE_DEFAULT_DEPTHS[1],
    Number(actorsSpec.depth) || SCENE_DEFAULT_DEPTHS[2],
    Number(foregroundSpec.depth) || SCENE_DEFAULT_DEPTHS[3]
  ];

  const spritePromises = [];
  if (effectsSpec.src) {
    const canvas = document.createElement('canvas');
    Object.assign(canvas.style, {
      position: 'absolute',
      inset: '0',
      width: '100%',
      height: '100%',
      opacity: String(clamp(Number(effectsSpec.opacity) || 1, 0, 1)),
      pointerEvents: 'none'
    });
    effects.appendChild(canvas);
    spritePromises.push(
      createSpriteRecord(effectsSpec, canvas, true).then(record => state.sceneSprites.push(record))
    );
  }

  const actorItems = Array.isArray(actorsSpec.items) ? actorsSpec.items.slice(0, 12) : [];
  actorItems.forEach(item => {
    if (!item?.src) return;
    const canvas = document.createElement('canvas');
    Object.assign(canvas.style, {
      position: 'absolute',
      left: `${clamp(Number(item.x) || 0, -0.5, 1.5) * 100}%`,
      top: `${clamp(Number(item.y) || 0, -0.5, 1.5) * 100}%`,
      width: `${clamp(Number(item.w) || 0.35, 0.05, 1.5) * 100}%`,
      height: `${clamp(Number(item.h) || 0.35, 0.05, 1.5) * 100}%`,
      objectFit: 'contain',
      pointerEvents: 'none'
    });
    actors.appendChild(canvas);
    spritePromises.push(
      createSpriteRecord(item, canvas, false).then(record => state.sceneSprites.push(record))
    );
  });

  state.endemarLayers.forEach(layer => { layer.style.display = 'none'; });
  state.spectralLayers.forEach(layer => { layer.style.display = 'none'; });
  state.sceneLayers.forEach(layer => { layer.style.display = ''; });
  state.layers = state.sceneLayers;
  state.mode = 'scene';
  state.currentStep = 0;
  state.sceneTitle = String(movie.title || file.name || 'RISTMOVIE');
  state.sceneClockMs = 0;
  state.sceneLastAt = performance.now();
  state.playing = !state.reducedMotion;
  fitCameraState(state);
  renderStep(state);
  setVideoStatus(state, `${state.sceneTitle} · LOADING SPRITES · LOCAL`);

  try {
    await Promise.all(spritePromises);
    state.sceneSprites.forEach(record => drawSceneSprite(record, 0));
    setVideoStatus(state, `${state.sceneTitle} · ${actorItems.length} ACTORS · LOCAL`);
  } catch {
    setVideoStatus(state, `${state.sceneTitle} · SPRITE LOAD ERROR`);
  }
  updateReadout(state);
}

function renderSceneFrame(state, now = performance.now()) {
  if (state.mode !== 'scene') return;
  if (state.playing) {
    const delta = Math.max(0, now - state.sceneLastAt);
    state.sceneClockMs += delta * state.speed;
  }
  state.sceneLastAt = now;
  state.sceneSprites.forEach(record => drawSceneSprite(record, state.sceneClockMs));
}



function safeSpriteBaseName(value) {
  const raw = String(value || 'perceiver').replace(/\.[^.]+$/, '');
  const clean = raw.replace(/[^a-z0-9_-]+/gi, '_').replace(/^_+|_+$/g, '');
  return clean || 'perceiver';
}

function median(values) {
  const list = values.filter(Number.isFinite).filter(value => value > 0).sort((a, b) => a - b);
  if (!list.length) return 0;
  const mid = Math.floor(list.length / 2);
  return list.length % 2 ? list[mid] : (list[mid - 1] + list[mid]) / 2;
}

function parseSpriteFilename(name) {
  const value = String(name || '');
  const normal = value.match(/__fc(\d+)__fps([\d.]+)__c(\d+)__r(\d+)/i);
  if (normal) {
    return {
      kind: 'sheet',
      frameCount: Math.max(1, Number(normal[1]) || 1),
      fps: Math.max(0.1, Number(normal[2]) || SPRITE_DEFAULT_FPS),
      columns: Math.max(1, Number(normal[3]) || 1),
      rows: Math.max(1, Number(normal[4]) || 1)
    };
  }

  const exported = value.match(/__tier(\d+)__fps([\d.]+)__fw(\d+)__fh(\d+)__c(\d+)__r(\d+)__fc(\d+)__page(\d+)/i);
  if (exported) {
    return {
      kind: 'parallax-page',
      tier: clamp(Number(exported[1]) || 1, 1, 7),
      fps: Math.max(0.1, Number(exported[2]) || 30),
      frameWidth: Math.max(1, Number(exported[3]) || 1),
      frameHeight: Math.max(1, Number(exported[4]) || 1),
      columns: Math.max(1, Number(exported[5]) || 1),
      rows: Math.max(1, Number(exported[6]) || 1),
      frameCount: Math.max(1, Number(exported[7]) || 1),
      page: Math.max(1, Number(exported[8]) || 1)
    };
  }
  return null;
}

function inferSpriteMeta(fileName, image) {
  const parsed = parseSpriteFilename(fileName);
  if (parsed) return parsed;

  const name = String(fileName || '').toLowerCase();
  if (name.includes('dragon_water')) {
    return { kind: 'sheet', frameCount: 8, fps: 1000 / 170, columns: 4, rows: 2 };
  }
  if (name.includes('dragon_celestial')) {
    return { kind: 'sheet', frameCount: 8, fps: 1000 / 190, columns: 4, rows: 2 };
  }
  if (name.includes('dragon_night')) {
    return { kind: 'sheet', frameCount: 8, fps: 1000 / 175, columns: 4, rows: 2 };
  }
  if (name.includes('effects')) {
    return { kind: 'sheet', frameCount: 8, fps: 1000 / 180, columns: 4, rows: 2 };
  }

  const ratio = image.naturalWidth / Math.max(1, image.naturalHeight);
  const animatedHint = /(sprite|dragon|effect|aurora|cloud|water|fire|smoke|wave)/i.test(name);
  if (animatedHint && ratio > 1.75 && ratio < 2.25) {
    return { kind: 'sheet', frameCount: 8, fps: SPRITE_DEFAULT_FPS, columns: 4, rows: 2 };
  }
  return { kind: 'sheet', frameCount: 1, fps: 1, columns: 1, rows: 1 };
}

function knownSpriteLayout(fileName) {
  const name = String(fileName || '').toLowerCase();
  if (name.includes('background')) return { depth: 0.22, x: 0, y: 0, w: 1, h: 1, opacity: 1 };
  if (name.includes('effects')) return { depth: 0.48, x: 0, y: 0, w: 1, h: 1, opacity: 0.44 };
  if (name.includes('dragon_water')) return { depth: 0.76, x: 0.02, y: 0.18, w: 0.46, h: 0.63, opacity: 1 };
  if (name.includes('dragon_celestial')) return { depth: 0.78, x: 0.29, y: 0.02, w: 0.42, h: 0.58, opacity: 1 };
  if (name.includes('dragon_night')) return { depth: 0.80, x: 0.55, y: 0.23, w: 0.44, h: 0.62, opacity: 1 };
  if (name.includes('foreground')) return { depth: 1.0, x: 0, y: 0, w: 1, h: 1, opacity: 1 };
  return null;
}

function spriteRoleWeight(fileName) {
  const name = String(fileName || '').toLowerCase();
  if (name.includes('background')) return 0;
  if (/(effect|aurora|cloud|water|light|weather)/.test(name)) return 1;
  if (/(dragon|actor|character|creature|npc)/.test(name)) return 2;
  if (name.includes('foreground')) return 3;
  return 2;
}

function clearSpritePlayback(state) {
  state.spriteLayers.forEach(layer => layer.remove());
  state.spriteLayers = [];
  state.spriteRecords = [];
  state.spriteParallax = null;
  state.spriteDepths = [...SPECTRAL_DEPTH_FACTORS];
  state.spriteEdits = [];
  state.selectedSpriteIndex = 0;
  state.spriteClockMs = 0;
  state.spriteLastAt = performance.now();
  state.spriteObjectUrls.forEach(url => URL.revokeObjectURL(url));
  state.spriteObjectUrls = [];
}

function spriteEdit(state, index) {
  while (state.spriteEdits.length <= index) state.spriteEdits.push({ scale: 1, x: 0, y: 0, opacity: 1 });
  return state.spriteEdits[index];
}

function spriteRecordForIndex(state, index) {
  return state.spriteRecords.find(record => Number(record.layerIndex) === Number(index)) || null;
}

function selectedSpriteFps(state) {
  if (state.spriteParallax) return clamp(Number(state.spriteParallax.fps) || 30, 1, 60);
  const record = spriteRecordForIndex(state, state.selectedSpriteIndex);
  return record ? clamp(1000 / Math.max(1, Number(record.frameMs) || 1000 / SPRITE_DEFAULT_FPS), 1, 60) : 60;
}

function setSelectedSpriteFps(state, fps) {
  fps = clamp(Number(fps) || 1, 1, 60);
  if (state.spriteParallax) state.spriteParallax.fps = fps;
  else {
    const record = spriteRecordForIndex(state, state.selectedSpriteIndex);
    if (record) record.frameMs = 1000 / fps;
  }
}

function spriteLayerName(state, index) {
  const record = spriteRecordForIndex(state, index);
  return record?.name || `Sprite ${index + 1}`;
}

function refreshSpriteEditor(state) {
  const editor = state.spriteEditor;
  if (!editor) return;
  const active = state.mode === 'sprite' && state.spriteLayers.length > 0;
  editor.hidden = !active;
  if (!active) return;

  const select = state.spriteSelect;
  if (select) {
    const previous = String(state.selectedSpriteIndex);
    select.innerHTML = '';
    state.spriteLayers.forEach((layer, index) => {
      if (layer.style.display === 'none' && !spriteRecordForIndex(state, index)) return;
      const option = document.createElement('option');
      option.value = String(index);
      option.textContent = spriteLayerName(state, index);
      select.appendChild(option);
    });
    if ([...select.options].some(option => option.value === previous)) select.value = previous;
    else if (select.options.length) {
      select.selectedIndex = 0;
      state.selectedSpriteIndex = Number(select.value) || 0;
    }
  }

  const edit = spriteEdit(state, state.selectedSpriteIndex);
  if (state.spriteSizeInput) state.spriteSizeInput.value = edit.scale.toFixed(2);
  if (state.spriteSizeRange) state.spriteSizeRange.value = String(edit.scale);
  if (state.spriteXInput) state.spriteXInput.value = (edit.x * 100).toFixed(1);
  if (state.spriteYInput) state.spriteYInput.value = (edit.y * 100).toFixed(1);
  if (state.spriteOpacityInput) state.spriteOpacityInput.value = String(Math.round(edit.opacity * 100));
  if (state.spriteFpsInput) state.spriteFpsInput.value = String(Math.round(selectedSpriteFps(state)));
  const record = spriteRecordForIndex(state, state.selectedSpriteIndex);
  if (state.spriteMotionOnlyButton) {
    state.spriteMotionOnlyButton.disabled = !record || record.frameCount < 2;
    state.spriteMotionOnlyButton.setAttribute('aria-pressed', record?.motionOnly ? 'true' : 'false');
  }
}

function applySpriteEditInputs(state) {
  const edit = spriteEdit(state, state.selectedSpriteIndex);
  edit.scale = clamp(Number(state.spriteSizeInput?.value ?? state.spriteSizeRange?.value) || edit.scale, 0.05, 8);
  edit.x = clamp((Number(state.spriteXInput?.value) || 0) / 100, -1, 1);
  edit.y = clamp((Number(state.spriteYInput?.value) || 0) / 100, -1, 1);
  edit.opacity = clamp((Number(state.spriteOpacityInput?.value) || 0) / 100, 0, 1);
  setSelectedSpriteFps(state, state.spriteFpsInput?.value);
  if (state.spriteSizeRange) state.spriteSizeRange.value = String(edit.scale);
  if (state.spriteSizeInput) state.spriteSizeInput.value = edit.scale.toFixed(2);
  renderStep(state);
}

function resetSelectedSpriteEdit(state) {
  state.spriteEdits[state.selectedSpriteIndex] = { scale: 1, x: 0, y: 0, opacity: 1 };
  setSelectedSpriteFps(state, state.spriteParallax ? state.spriteParallax.fps : SPRITE_DEFAULT_FPS);
  const record = spriteRecordForIndex(state, state.selectedSpriteIndex);
  if (record) record.motionOnly = false;
  refreshSpriteEditor(state);
  renderStep(state);
}

function makeSpritePlaybackLayer(index) {
  const wrapper = sceneWrapper('perceiver-sprite-layer');
  wrapper.dataset.tier = String(index + 1);
  const canvas = document.createElement('canvas');
  canvas.width = 2;
  canvas.height = 2;
  Object.assign(canvas.style, {
    position: 'absolute',
    inset: '0',
    width: '100%',
    height: '100%',
    pointerEvents: 'none'
  });
  wrapper.appendChild(canvas);
  wrapper._spriteCanvas = canvas;
  wrapper._spriteContext = canvas.getContext('2d', { alpha: true });
  return wrapper;
}

function findParallaxPage(tierPages, globalFrame) {
  let offset = 0;
  for (const page of tierPages) {
    if (globalFrame < offset + page.frameCount) {
      return { page, localFrame: globalFrame - offset };
    }
    offset += page.frameCount;
  }
  return tierPages.length
    ? { page: tierPages[tierPages.length - 1], localFrame: Math.max(0, tierPages[tierPages.length - 1].frameCount - 1) }
    : null;
}

function drawParallaxSpriteFrame(state, clockMs) {
  const movie = state.spriteParallax;
  if (!movie || !movie.frameCount || !movie.fps) return;
  const globalFrame = Math.floor((clockMs / 1000) * movie.fps) % movie.frameCount;

  state.spriteLayers.forEach((layer, tierIndex) => {
    const pages = movie.tiers[tierIndex] || [];
    const located = findParallaxPage(pages, globalFrame);
    const ctx = layer._spriteContext;
    const canvas = layer._spriteCanvas;
    if (!located || !ctx) return;

    const page = located.page;
    const localFrame = located.localFrame;
    const column = localFrame % page.columns;
    const row = Math.floor(localFrame / page.columns);
    const sx = column * page.frameWidth;
    const sy = row * page.frameHeight;

    if (canvas.width !== page.frameWidth || canvas.height !== page.frameHeight) {
      canvas.width = page.frameWidth;
      canvas.height = page.frameHeight;
    }
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(
      page.image,
      sx, sy, page.frameWidth, page.frameHeight,
      0, 0, canvas.width, canvas.height
    );
  });
}

async function loadSpriteFiles(state, fileList) {
  const files = [...(fileList || [])].filter(file => String(file.type || '').startsWith('image/'));
  if (!files.length) {
    setVideoStatus(state, 'CHOOSE PNG / WEBP SPRITES');
    return;
  }

  if (state.video) state.video.pause();
  stopVideoFramePump(state);
  stopSpectralObjectUrl(state);
  clearSpritePlayback(state);
  clearSceneLayers(state);

  const decoded = [];
  for (const file of files.slice(0, 64)) {
    const url = URL.createObjectURL(file);
    state.spriteObjectUrls.push(url);
    const image = new Image();
    image.decoding = 'async';
    image.src = url;
    try {
      await waitForImage(image);
      decoded.push({ file, image, meta: inferSpriteMeta(file.name, image) });
    } catch {}
  }

  decoded.sort((a, b) => spriteRoleWeight(a.file.name) - spriteRoleWeight(b.file.name));

  const parallaxFiles = decoded.filter(item => item.meta && item.meta.kind === 'parallax-page');
  if (parallaxFiles.length) {
    const tiers = Array.from({ length: 7 }, () => []);
    let fps = 0;

    parallaxFiles
      .sort((a, b) => (a.meta.page - b.meta.page) || (a.meta.tier - b.meta.tier))
      .forEach(item => {
        const meta = item.meta;
        fps = fps || meta.fps;
        tiers[meta.tier - 1].push({
          image: item.image,
          page: meta.page,
          frameCount: meta.frameCount,
          frameWidth: meta.frameWidth,
          frameHeight: meta.frameHeight,
          columns: meta.columns,
          rows: meta.rows
        });
      });

    const populated = tiers.filter(pages => pages.length);
    if (!populated.length) {
      setVideoStatus(state, 'NO PARALLAX SPRITE PAGES');
      return;
    }
    const frameCount = populated[0].reduce((sum, page) => sum + page.frameCount, 0);

    state.spriteLayers = tiers.map((pages, index) => {
      const layer = makeSpritePlaybackLayer(index);
      if (!pages.length) layer.style.display = 'none';
      state.camera.appendChild(layer);
      return layer;
    });
    state.spriteParallax = { tiers, fps: fps || 30, frameCount };
    state.spriteDepths = [...SPECTRAL_DEPTH_FACTORS];
  } else {
    state.spriteLayers = decoded.slice(0, 7).map((item, index) => {
      const layer = makeSpritePlaybackLayer(index);
      state.camera.appendChild(layer);
      return layer;
    });
    state.spriteDepths = state.spriteLayers.map((_, index) => {
      const layout = knownSpriteLayout(decoded[index]?.file?.name);
      if (layout) return layout.depth;
      if (state.spriteLayers.length <= 1) return 0.72;
      return 0.25 + (index / (state.spriteLayers.length - 1)) * 0.75;
    });

    for (let index = 0; index < state.spriteLayers.length; index += 1) {
      const item = decoded[index];
      const meta = item.meta;
      const canvas = state.spriteLayers[index]._spriteCanvas;
      const layout = knownSpriteLayout(item.file.name);
      if (layout) {
        Object.assign(canvas.style, {
          left: (layout.x * 100) + '%',
          top: (layout.y * 100) + '%',
          width: (layout.w * 100) + '%',
          height: (layout.h * 100) + '%',
          opacity: String(layout.opacity)
        });
      }
      const columns = Math.max(1, meta.columns || 1);
      const rows = Math.max(1, meta.rows || 1);
      const frameCount = Math.max(1, Math.min(meta.frameCount || 1, columns * rows));
      canvas.width = Math.max(1, Math.floor(item.image.naturalWidth / columns));
      canvas.height = Math.max(1, Math.floor(item.image.naturalHeight / rows));
      state.spriteRecords.push({
        name: item.file.name || `Sprite ${index + 1}`,
        layerIndex: index,
        image: item.image,
        canvas,
        context: canvas.getContext('2d', { alpha: true }),
        frameWidth: canvas.width,
        frameHeight: canvas.height,
        stretch: false,
        columns,
        rows,
        frameCount,
        frameMs: 1000 / Math.max(0.1, meta.fps || SPRITE_DEFAULT_FPS),
        phase: item.file.name.toLowerCase().includes('dragon_celestial')
          ? 2
          : item.file.name.toLowerCase().includes('dragon_night')
            ? 4
            : 0
      });
    }
  }

  state.endemarLayers.forEach(layer => { layer.style.display = 'none'; });
  state.spectralLayers.forEach(layer => { layer.style.display = 'none'; });
  state.spriteLayers.forEach(layer => { if (layer.style.display !== 'none') layer.style.display = ''; });
  state.spriteEdits = state.spriteLayers.map(() => ({ scale: 1, x: 0, y: 0, opacity: 1 }));
  state.selectedSpriteIndex = Math.max(0, state.spriteLayers.findIndex(layer => layer.style.display !== 'none'));
  state.layers = state.spriteLayers;
  state.mode = 'sprite';
  state.currentStep = SPECTRAL_STEP_SEQUENCE.length - 1;
  state.spriteClockMs = 0;
  state.spriteLastAt = performance.now();
  state.playing = !state.reducedMotion;
  fitCameraState(state);
  renderSpriteFrame(state, performance.now());
  renderStep(state);
  setVideoStatus(
    state,
    state.spriteParallax
      ? 'SPRITE MOVIE · ' + state.spriteParallax.frameCount + ' FRAMES · ' + state.spriteParallax.fps.toFixed(2) + ' FPS'
      : state.spriteLayers.length + ' SPRITE LAYERS · LOCAL'
  );
  updateReadout(state);
  refreshSpriteEditor(state);
}

function renderSpriteFrame(state, now = performance.now()) {
  if (state.mode !== 'sprite') return;
  if (state.playing) {
    const delta = Math.max(0, now - state.spriteLastAt);
    state.spriteClockMs += delta * state.speed;
  }
  state.spriteLastAt = now;

  if (state.spriteParallax) drawParallaxSpriteFrame(state, state.spriteClockMs);
  else state.spriteRecords.forEach(record => drawSceneSprite(record, state.spriteClockMs));
}

function spriteExportSize(state) {
  const width = Math.max(1, state.spectralWidth || 1);
  const height = Math.max(1, state.spectralHeight || 1);
  const pixels = width * height;
  const scale = pixels > SPRITE_EXPORT_MAX_PIXELS
    ? Math.sqrt(SPRITE_EXPORT_MAX_PIXELS / pixels)
    : 1;
  return {
    width: Math.max(2, Math.round(width * scale)),
    height: Math.max(2, Math.round(height * scale))
  };
}

function newCaptureCanvases(capture) {
  capture.canvases = Array.from({ length: 7 }, () => {
    const canvas = document.createElement('canvas');
    canvas.width = capture.frameWidth * capture.columns;
    canvas.height = capture.frameHeight * capture.rows;
    return canvas;
  });
  capture.contexts = capture.canvases.map(canvas => canvas.getContext('2d', { alpha: true }));
  capture.pageFrameCount = 0;
}

function beginVideoSpriteCapture(state, file) {
  const size = spriteExportSize(state);
  state.spriteCapture = {
    baseName: safeSpriteBaseName(file && file.name ? file.name : 'perceiver_video'),
    frameWidth: size.width,
    frameHeight: size.height,
    columns: SPRITE_EXPORT_COLUMNS,
    rows: SPRITE_EXPORT_ROWS,
    pageFrameCount: 0,
    pageIndex: 1,
    totalFrames: 0,
    firstMediaTime: null,
    lastMediaTime: null,
    lastCapturedMediaTime: null,
    frameDeltas: [],
    pages: [],
    pending: [],
    complete: false,
    canvases: [],
    contexts: []
  };
  state.spriteExportPages = [];
  state.spriteExportMeta = null;
  newCaptureCanvases(state.spriteCapture);
}

function canvasBlob(canvas) {
  return new Promise(resolve => {
    canvas.toBlob(blob => resolve(blob), 'image/webp', 0.90);
  });
}

function finalizeCapturePage(state) {
  const capture = state.spriteCapture;
  if (!capture || capture.pageFrameCount <= 0) return Promise.resolve(null);

  const canvases = capture.canvases;
  const pageFrameCount = capture.pageFrameCount;
  const pageIndex = capture.pageIndex++;
  newCaptureCanvases(capture);

  const pending = Promise.all(canvases.map(canvas => canvasBlob(canvas))).then(blobs => {
    const page = { pageIndex, frameCount: pageFrameCount, blobs };
    capture.pages.push(page);
    return page;
  });
  capture.pending.push(pending);
  return pending;
}

function captureParallaxFrame(state, mediaTime) {
  const capture = state.spriteCapture;
  if (!capture || capture.complete || state.mode !== 'spectral') return;
  const t = Number(mediaTime);
  if (!Number.isFinite(t)) return;
  if (capture.lastCapturedMediaTime != null && Math.abs(t - capture.lastCapturedMediaTime) < 0.00001) return;

  if (capture.firstMediaTime == null) capture.firstMediaTime = t;
  if (capture.lastMediaTime != null) {
    const delta = t - capture.lastMediaTime;
    if (delta > 0.001 && delta < 1) capture.frameDeltas.push(delta);
  }
  capture.lastMediaTime = t;
  capture.lastCapturedMediaTime = t;

  const local = capture.pageFrameCount;
  const column = local % capture.columns;
  const row = Math.floor(local / capture.columns);
  const dx = column * capture.frameWidth;
  const dy = row * capture.frameHeight;

  state.spectralLayers.forEach((layer, tier) => {
    capture.contexts[tier].drawImage(
      layer._spectralCanvas,
      0, 0, state.spectralWidth, state.spectralHeight,
      dx, dy, capture.frameWidth, capture.frameHeight
    );
  });

  capture.pageFrameCount += 1;
  capture.totalFrames += 1;
  if (capture.pageFrameCount >= SPRITE_EXPORT_FRAMES_PER_PAGE) {
    void finalizeCapturePage(state);
  }
}

function captureFps(capture) {
  const frameDelta = median(capture && capture.frameDeltas ? capture.frameDeltas : []);
  if (frameDelta > 0) return clamp(1 / frameDelta, 1, 120);
  if (capture && capture.firstMediaTime != null && capture.lastMediaTime != null && capture.totalFrames > 1) {
    const duration = capture.lastMediaTime - capture.firstMediaTime;
    if (duration > 0) return clamp((capture.totalFrames - 1) / duration, 1, 120);
  }
  return 30;
}

async function finishVideoSpriteCapture(state) {
  const capture = state.spriteCapture;
  if (!capture || capture.complete) return capture;
  await finalizeCapturePage(state);
  await Promise.all(capture.pending);
  capture.pages.sort((a, b) => a.pageIndex - b.pageIndex);
  capture.complete = true;
  const fps = captureFps(capture);
  state.spriteExportPages = capture.pages;
  state.spriteExportMeta = {
    baseName: capture.baseName,
    fps,
    frameWidth: capture.frameWidth,
    frameHeight: capture.frameHeight,
    columns: capture.columns,
    rows: capture.rows,
    frameCount: capture.totalFrames
  };
  return capture;
}

function downloadSpriteBlob(blob, fileName) {
  if (!blob) return;
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = fileName;
  anchor.style.display = 'none';
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}

async function saveSpriteExports(state) {
  if (!state.spriteCapture && !state.spriteExportPages.length) {
    setVideoStatus(state, 'UPLOAD A VIDEO FIRST');
    return;
  }
  if (state.video && !state.video.paused && state.mode === 'spectral') state.video.pause();
  await finishVideoSpriteCapture(state);

  const meta = state.spriteExportMeta;
  const pages = state.spriteExportPages;
  if (!meta || !pages.length) {
    setVideoStatus(state, 'NO SPRITE FRAMES CAPTURED');
    return;
  }

  const fpsText = meta.fps.toFixed(3).replace(/0+$/, '').replace(/\.$/, '');
  for (const page of pages) {
    for (let tier = 0; tier < 7; tier += 1) {
      const name =
        meta.baseName + '__tier' + (tier + 1) + '__fps' + fpsText +
        '__fw' + meta.frameWidth + '__fh' + meta.frameHeight +
        '__c' + meta.columns + '__r' + meta.rows +
        '__fc' + page.frameCount + '__page' + String(page.pageIndex).padStart(3, '0') + '.webp';
      downloadSpriteBlob(page.blobs[tier], name);
    }
  }
  setVideoStatus(
    state,
    'SAVED ' + meta.frameCount + ' FRAMES · ' + meta.fps.toFixed(2) + ' FPS · ' + (pages.length * 7) + ' WEBP SPRITES'
  );
}

function stopVideoFramePump(state) {
  if (state.videoFrameCallbackId && state.video && state.video.cancelVideoFrameCallback) {
    try { state.video.cancelVideoFrameCallback(state.videoFrameCallbackId); } catch {}
  }
  state.videoFrameCallbackId = 0;
  state.videoFramePumpSupported = false;
}

function startVideoFramePump(state) {
  stopVideoFramePump(state);
  if (!state.video || !state.video.requestVideoFrameCallback) return;
  state.videoFramePumpSupported = true;

  const loop = (now, metadata) => {
    if (state.destroyed) return;
    if (state.mode === 'spectral' && state.video && !state.video.paused && !state.video.ended) {
      renderSpectralFrame(state, now, true);
      captureParallaxFrame(state, metadata && Number.isFinite(metadata.mediaTime) ? metadata.mediaTime : state.video.currentTime);
    }
    state.videoFrameCallbackId = state.video.requestVideoFrameCallback(loop);
  };
  state.videoFrameCallbackId = state.video.requestVideoFrameCallback(loop);
}

function resetEndemarLayers(state) {
  state.mode = 'endemar';
  stopVideoFramePump(state);
  if (state.video) {
    state.video.pause();
    state.video.removeAttribute('src');
    state.video.load();
  }
  stopSpectralObjectUrl(state);
  state.currentStep = 0;
  state.playing = !state.reducedMotion;
  state.lastAdvance = performance.now();

  state.spectralLayers.forEach(layer => { layer.style.display = 'none'; });
  state.sceneLayers.forEach(layer => { layer.style.display = 'none'; });
  state.spriteLayers.forEach(layer => { layer.style.display = 'none'; });
  state.endemarLayers.forEach(layer => { layer.style.display = ''; });
  state.layers = state.endemarLayers;

  setVideoStatus(state, 'ENDEMAR PROOF');
  fitCameraState(state);
  renderStep(state);
}

function initializeSpectralCanvases(state) {
  const size = spectralProcessingSize(state.video);
  state.sourceCanvas.width = size.width;
  state.sourceCanvas.height = size.height;

  state.spectralBuffers = state.spectralLayers.map(layer => {
    const canvas = layer._spectralCanvas;
    canvas.width = size.width;
    canvas.height = size.height;
    canvas.style.aspectRatio = `${size.width} / ${size.height}`;
    const context = layer._spectralContext;
    context.clearRect(0, 0, size.width, size.height);
    return context.createImageData(size.width, size.height);
  });

  state.spectralWidth = size.width;
  state.spectralHeight = size.height;
  state.spectralLastVideoTime = -1;
  state.lastSpectralFrameAt = 0;
}

function renderSpectralFrame(state, now = performance.now(), force = false) {
  if (state.mode !== 'spectral' || !state.video || state.video.readyState < 2) return;
  if (!force && now - state.lastSpectralFrameAt < SPECTRAL_FRAME_INTERVAL_MS) return;
  if (!force && Math.abs(state.video.currentTime - state.spectralLastVideoTime) < 0.0001) return;

  const width = state.spectralWidth;
  const height = state.spectralHeight;
  if (!width || !height) return;

  state.sourceContext.drawImage(state.video, 0, 0, width, height);
  let source;
  try {
    source = state.sourceContext.getImageData(0, 0, width, height);
  } catch {
    setVideoStatus(state, 'VIDEO FRAME BLOCKED');
    return;
  }

  const tierData = state.spectralBuffers.map(buffer => buffer.data);
  tierData.forEach(data => data.fill(0));
  const input = source.data;

  for (let i = 0; i < input.length; i += 4) {
    const alpha = input[i + 3];
    if (alpha === 0) continue;

    const tier = spectralTierForPixel(input[i], input[i + 1], input[i + 2]);
    const output = tierData[tier];
    output[i] = input[i];
    output[i + 1] = input[i + 1];
    output[i + 2] = input[i + 2];
    output[i + 3] = alpha;
  }

  state.spectralLayers.forEach((layer, index) => {
    layer._spectralContext.putImageData(state.spectralBuffers[index], 0, 0);
  });

  state.lastSpectralFrameAt = now;
  state.spectralLastVideoTime = state.video.currentTime;
}

async function loadSpectralVideo(state, file) {
  if (!file || !String(file.type || '').startsWith('video/')) {
    setVideoStatus(state, 'CHOOSE A VIDEO');
    return;
  }

  stopVideoFramePump(state);
  clearSpritePlayback(state);
  stopSpectralObjectUrl(state);
  state.videoObjectUrl = URL.createObjectURL(file);
  state.video.pause();
  state.video.src = state.videoObjectUrl;
  state.video.load();

  state.mode = 'spectral';
  state.currentStep = SPECTRAL_STEP_SEQUENCE.length - 1;
  state.playing = false;
  state.endemarLayers.forEach(layer => { layer.style.display = 'none'; });
  state.sceneLayers.forEach(layer => { layer.style.display = 'none'; });
  state.spectralLayers.forEach(layer => { layer.style.display = ''; });
  state.layers = state.spectralLayers;
  setVideoStatus(state, 'LOADING · LOCAL ONLY');
  fitCameraState(state);
  renderStep(state);

  await new Promise(resolve => {
    if (state.video.readyState >= 1) {
      resolve();
      return;
    }
    state.video.addEventListener('loadedmetadata', resolve, { once: true });
  });

  initializeSpectralCanvases(state);
  beginVideoSpriteCapture(state, file);
  startVideoFramePump(state);
  setVideoStatus(
    state,
    `${file.name || 'PHONE VIDEO'} · ${state.spectralWidth}×${state.spectralHeight} · LOCAL`
  );

  await new Promise(resolve => {
    if (state.video.readyState >= 2) {
      resolve();
      return;
    }
    state.video.addEventListener('loadeddata', resolve, { once: true });
  });

  renderSpectralFrame(state, performance.now(), true);

  try {
    await state.video.play();
    state.playing = true;
    setVideoStatus(state, `${file.name || 'PHONE VIDEO'} · CAPTURING PARALLAX SPRITES · LOCAL`);
  } catch {
    state.playing = false;
    setVideoStatus(state, `${file.name || 'PHONE VIDEO'} · READY · TAP PLAY`);
  }
  updateReadout(state);
}

function animate(state, now) {
  if (state.destroyed) return;

  if (state.mode === 'spectral') {
    renderSpectralFrame(state, now);
    if (!state.videoFramePumpSupported && state.video && !state.video.paused) {
      captureParallaxFrame(state, state.video.currentTime);
    }
  } else if (state.mode === 'sprite') {
    renderSpriteFrame(state, now);
  } else if (state.mode === 'scene') {
    renderSceneFrame(state, now);
  } else {
    const duration = state.stepDurationMs / state.speed;
    if (state.playing && now - state.lastAdvance >= duration) advance(state, 1);
  }

  state.currentX += (state.targetX - state.currentX) * 0.13;
  state.currentY += (state.targetY - state.currentY) * 0.13;

  const idleX = state.reducedMotion ? 0 : Math.sin(now * 0.00052) * 0.08;
  const idleY = state.reducedMotion ? 0 : Math.cos(now * 0.00039) * 0.06;

  const depths = state.mode === 'spectral'
    ? SPECTRAL_DEPTH_FACTORS
    : state.mode === 'sprite'
      ? state.spriteDepths
      : state.mode === 'scene'
        ? state.sceneDepths
        : ENDEMAR_DEPTH_FACTORS;
  state.layers.forEach((layer, index) => {
    const depth = depths[index] ?? depths[depths.length - 1] ?? 1;
    const xStrength = state.mode === 'spectral' || state.mode === 'sprite' ? 32 : state.mode === 'scene' ? 30 : 26;
    const yStrength = state.mode === 'spectral' || state.mode === 'sprite' ? 24 : state.mode === 'scene' ? 22 : 19;
    const edit = state.mode === 'sprite' ? spriteEdit(state, index) : { scale: 1, x: 0, y: 0 };
    const x = (state.currentX + idleX) * xStrength * depth + edit.x * state.canvas.clientWidth;
    const y = (state.currentY + idleY) * yStrength * depth + edit.y * state.canvas.clientHeight;
    const baseScale = state.mode === 'spectral' || state.mode === 'sprite'
      ? (SPECTRAL_OVERSCAN[index] ?? 1.04)
      : state.mode === 'scene'
        ? 1.008 + depth * 0.026
        : 1.005 + depth * 0.018;
    const scale = baseScale * edit.scale;
    layer.style.transform = `translate3d(${x.toFixed(2)}px,${y.toFixed(2)}px,0) scale(${scale.toFixed(4)})`;
  });

  state.raf = requestAnimationFrame(frame => animate(state, frame));
}

export function attach(root, config = {}) {
  if (!root) throw new Error('Perceiver root was not supplied.');
  if (STATES.has(root)) detach(root);

  const canvas = root.querySelector('.perceiver-canvas');
  if (!canvas) throw new Error('Perceiver canvas was not found.');

  canvas.replaceChildren();

  const stack = document.createElement('div');
  stack.className = 'perceiver-layer-stack';
  Object.assign(stack.style, {
    position: 'absolute',
    inset: '0',
    overflow: 'hidden',
    background: 'radial-gradient(circle at 50% 45%,rgba(44,91,117,.12),transparent 48%)'
  });
  canvas.appendChild(stack);

  const camera = document.createElement('div');
  camera.className = 'perceiver-camera';
  Object.assign(camera.style, {
    position: 'absolute',
    inset: '0',
    transformOrigin: '0 0',
    willChange: 'transform'
  });
  stack.appendChild(camera);

  const urls = Array.isArray(config.tierImages)
    ? config.tierImages.map(value => String(value || '').trim()).slice(0, 3)
    : [];
  const fallbackUrls = Array.isArray(config.fallbackTierImages)
    ? config.fallbackTierImages.map(value => String(value || '').trim()).slice(0, 3)
    : [];
  while (urls.length < 3) urls.push('');
  while (fallbackUrls.length < 3) fallbackUrls.push('');

  const state = {
    root,
    canvas,
    stack,
    camera,
    layers: [],
    currentStep: 0,
    playing: !window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    speed: 1,
    stepDurationMs: Math.max(400, Number(config.stepDurationMs) || 2000),
    lastAdvance: performance.now(),
    cameraScale: 1,
    cameraX: 0,
    cameraY: 0,
    pointers: new Map(),
    panStart: null,
    pinchStart: null,
    pointerX: 0,
    pointerY: 0,
    targetX: 0,
    targetY: 0,
    currentX: 0,
    currentY: 0,
    baselineBeta: null,
    baselineGamma: null,
    motionEnabled: false,
    motionListenerAttached: false,
    lastMotionAt: 0,
    destroyed: false,
    raf: 0,
    dragging: false,
    labelNode: root.querySelector('[data-perceiver-label]'),
    playStateNode: root.querySelector('[data-perceiver-play-state]'),
    motionNode: root.querySelector('[data-perceiver-motion-state]'),
    zoomNode: root.querySelector('[data-perceiver-zoom]'),
    motionButton: root.querySelector('[data-perceiver-motion-button]'),
    fullscreenButton: root.querySelector('[data-perceiver-fullscreen-button]'),
    uploadButton: root.querySelector('[data-perceiver-upload-button]'),
    spriteButton: root.querySelector('[data-perceiver-sprite-button]'),
    saveSpritesButton: root.querySelector('[data-perceiver-save-sprites-button]'),
    endemarButton: root.querySelector('[data-perceiver-endemar-button]'),
    spriteInput: root.querySelector('[data-perceiver-sprite-input]'),
    spriteEditor: root.querySelector('[data-perceiver-sprite-editor]'),
    spriteSelect: root.querySelector('[data-perceiver-sprite-select]'),
    spriteSizeInput: root.querySelector('[data-perceiver-sprite-size]'),
    spriteSizeRange: root.querySelector('[data-perceiver-sprite-size-range]'),
    spriteXInput: root.querySelector('[data-perceiver-sprite-x]'),
    spriteYInput: root.querySelector('[data-perceiver-sprite-y]'),
    spriteOpacityInput: root.querySelector('[data-perceiver-sprite-opacity]'),
    spriteFpsInput: root.querySelector('[data-perceiver-sprite-fps]'),
    spriteMotionOnlyButton: root.querySelector('[data-perceiver-sprite-motion-only]'),
    spriteResetButton: root.querySelector('[data-perceiver-sprite-reset]'),
    videoInput: root.querySelector('[data-perceiver-video-input]'),
    videoStatusNode: root.querySelector('[data-perceiver-video-status]'),
    modeNoteNode: root.querySelector('[data-perceiver-mode-note]'),
    layerStrip: root.querySelector('[data-perceiver-layer-strip]'),
    layerButtons: [...root.querySelectorAll('[data-perceiver-layer]')],
    mode: 'endemar',
    endemarLayers: [],
    spectralLayers: [],
    sceneLayers: [],
    sceneSprites: [],
    sceneDepths: [...SCENE_DEFAULT_DEPTHS],
    sceneTitle: '',
    sceneClockMs: 0,
    sceneLastAt: performance.now(),
    spriteLayers: [],
    spriteRecords: [],
    spriteParallax: null,
    spriteEdits: [],
    selectedSpriteIndex: 0,
    spriteDepths: [...SPECTRAL_DEPTH_FACTORS],
    spriteClockMs: 0,
    spriteLastAt: performance.now(),
    spriteObjectUrls: [],
    spriteCapture: null,
    spriteExportPages: [],
    spriteExportMeta: null,
    videoFrameCallbackId: 0,
    videoFramePumpSupported: false,
    spectralBuffers: [],
    spectralWidth: 0,
    spectralHeight: 0,
    spectralLastVideoTime: -1,
    lastSpectralFrameAt: 0,
    videoObjectUrl: '',
    video: null,
    sourceCanvas: null,
    sourceContext: null,
    onPointerMove: null,
    onPointerDown: null,
    onPointerUp: null,
    onPointerLeave: null,
    onWheel: null,
    onKeyDown: null,
    onDeviceOrientation: null,
    onMotionClick: null,
    onFullscreenClick: null,
    onFullscreenChange: null,
    onUploadClick: null,
    onSpriteClick: null,
    onSaveSpritesClick: null,
    onVideoChange: null,
    onSpriteChange: null,
    onSpriteEditorChange: null,
    onSpriteSizeRange: null,
    onSpriteMotionOnly: null,
    onSpriteReset: null,
    onEndemarClick: null,
    onLayerClick: null,
    onVideoPlay: null,
    onVideoPause: null,
    onVideoSeeked: null,
    onVideoEnded: null,
    onOrientationChange: null,
    fullscreenScrollY: 0,
    previousDocumentOverflow: '',
    previousBodyOverflow: ''
  };

  state.endemarLayers = urls.map((src, index) => {
    const image = makeLayer(src, index);
    image.dataset.primarySrc = src;
    image.dataset.fallbackSrc = fallbackUrls[index] || '';
    image.addEventListener('error', () => {
      const fallback = image.dataset.fallbackSrc || '';
      const usingFallback = image.dataset.fallbackActive === 'true';
      if (!usingFallback && fallback && fallback !== image.src) {
        image.dataset.fallbackActive = 'true';
        image.dataset.loadState = 'fallback';
        image.src = fallback;
        return;
      }
      image.dataset.loadState = 'error';
      root.dataset.perceiverLoadError = String(index + 1);
    });
    image.addEventListener('load', () => {
      image.dataset.loadState = image.dataset.fallbackActive === 'true' ? 'fallback-ready' : 'ready';
    });
    camera.appendChild(image);
    return image;
  });

  state.layers = state.endemarLayers;

  state.spectralLayers = [0, 1, 2, 3, 4, 5, 6].map(index => {
    const layer = makeSpectralLayer(index);
    layer.style.display = 'none';
    camera.appendChild(layer);
    return layer;
  });

  state.video = document.createElement('video');
  state.video.playsInline = true;
  state.video.preload = 'metadata';
  state.video.controls = false;
  state.video.setAttribute('playsinline', '');
  Object.assign(state.video.style, {
    position: 'absolute',
    left: '0',
    top: '0',
    width: '1px',
    height: '1px',
    opacity: '0',
    pointerEvents: 'none'
  });
  canvas.appendChild(state.video);

  state.sourceCanvas = document.createElement('canvas');
  state.sourceContext = state.sourceCanvas.getContext('2d', { willReadFrequently: true, alpha: true });

  const vignette = document.createElement('div');
  vignette.setAttribute('aria-hidden', 'true');
  Object.assign(vignette.style, {
    position: 'absolute',
    inset: '0',
    pointerEvents: 'none',
    zIndex: '5',
    background: 'linear-gradient(180deg,rgba(0,0,0,.12),transparent 18%,transparent 80%,rgba(0,0,0,.20))'
  });
  canvas.appendChild(vignette);

  state.onPointerMove = event => {
    if (state.pointers.has(event.pointerId)) {
      if (event.cancelable) event.preventDefault();
      state.pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });

      if (state.pointers.size === 1 && state.panStart) {
        state.cameraX = state.panStart.x + (event.clientX - state.panStart.pointerX);
        state.cameraY = state.panStart.y + (event.clientY - state.panStart.pointerY);
        applyCamera(state);
        return;
      }

      if (state.pointers.size === 2 && state.pinchStart) {
        const [a, b] = [...state.pointers.values()];
        const rect = canvas.getBoundingClientRect();
        const cx = (a.x + b.x) / 2 - rect.left;
        const cy = (a.y + b.y) / 2 - rect.top;
        const distance = Math.hypot(a.x - b.x, a.y - b.y) || 1;
        const nextScale = clamp(
          state.pinchStart.scale * (distance / state.pinchStart.distance),
          MIN_CAMERA_SCALE,
          MAX_CAMERA_SCALE
        );
        state.cameraScale = nextScale;
        state.cameraX = cx - state.pinchStart.worldX * nextScale;
        state.cameraY = cy - state.pinchStart.worldY * nextScale;
        applyCamera(state);
        return;
      }
    }

    if (event.pointerType === 'mouse') {
      applyPointerTarget(state, event.clientX, event.clientY);
    }
  };

  state.onPointerDown = event => {
    if (event.pointerType === 'mouse' && event.button !== 0) return;
    if (event.cancelable) event.preventDefault();
    canvas.focus({ preventScroll: true });
    try { canvas.setPointerCapture(event.pointerId); } catch {}

    state.pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
    state.dragging = true;

    if (state.pointers.size === 1) {
      state.panStart = {
        pointerX: event.clientX,
        pointerY: event.clientY,
        x: state.cameraX,
        y: state.cameraY
      };
      state.pinchStart = null;
    } else if (state.pointers.size === 2) {
      const [a, b] = [...state.pointers.values()];
      const rect = canvas.getBoundingClientRect();
      const cx = (a.x + b.x) / 2 - rect.left;
      const cy = (a.y + b.y) / 2 - rect.top;
      const distance = Math.hypot(a.x - b.x, a.y - b.y) || 1;
      state.pinchStart = {
        distance,
        scale: state.cameraScale,
        worldX: (cx - state.cameraX) / state.cameraScale,
        worldY: (cy - state.cameraY) / state.cameraScale
      };
      state.panStart = null;
    }
  };

  state.onPointerUp = event => {
    if (!state.pointers.has(event.pointerId)) return;
    state.pointers.delete(event.pointerId);
    try {
      if (canvas.hasPointerCapture?.(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
    } catch {}

    if (state.pointers.size === 0) {
      state.dragging = false;
      state.panStart = null;
      state.pinchStart = null;
    } else if (state.pointers.size === 1) {
      const remaining = [...state.pointers.values()][0];
      state.dragging = true;
      state.panStart = {
        pointerX: remaining.x,
        pointerY: remaining.y,
        x: state.cameraX,
        y: state.cameraY
      };
      state.pinchStart = null;
    }
  };

  state.onPointerLeave = () => {
    if (state.dragging) return;
    const motionIsLive = state.motionEnabled && (performance.now() - state.lastMotionAt) < 650;
    if (motionIsLive) return;
    state.pointerX = 0;
    state.pointerY = 0;
    state.targetX = 0;
    state.targetY = 0;
  };

  state.onWheel = event => {
    if (!event.deltaY) return;
    event.preventDefault();
    const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? canvas.clientHeight : 1;
    const delta = clamp(event.deltaY * unit, -240, 240);
    zoomAt(state, event.clientX, event.clientY, Math.exp(-delta * 0.0015));
  };

  state.onKeyDown = event => {
    if (event.key === '+' || event.key === '=') {
      event.preventDefault();
      zoomCenter(state, ZOOM_STEP);
    } else if (event.key === '-' || event.key === '_') {
      event.preventDefault();
      zoomCenter(state, 1 / ZOOM_STEP);
    } else if (event.key === '0' || event.key.toLowerCase() === 'f') {
      event.preventDefault();
      fitCameraState(state);
    } else if (event.key === 'ArrowLeft') {
      event.preventDefault();
      state.cameraX += 40;
      applyCamera(state);
    } else if (event.key === 'ArrowRight') {
      event.preventDefault();
      state.cameraX -= 40;
      applyCamera(state);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      state.cameraY += 40;
      applyCamera(state);
    } else if (event.key === 'ArrowDown') {
      event.preventDefault();
      state.cameraY -= 40;
      applyCamera(state);
    }
  };

  state.onDeviceOrientation = event => {
    if (!state.motionEnabled || event.beta == null || event.gamma == null) return;
    const adjusted = screenAdjusted(Number(event.beta), Number(event.gamma));
    state.lastMotionAt = performance.now();

    if (state.baselineBeta == null || state.baselineGamma == null) {
      state.baselineBeta = adjusted.beta;
      state.baselineGamma = adjusted.gamma;
    }

    const beta = clamp(adjusted.beta - state.baselineBeta, -24, 24);
    const gamma = clamp(adjusted.gamma - state.baselineGamma, -24, 24);
    state.targetX = clamp(gamma / 20, -1, 1);
    state.targetY = clamp(beta / 20, -1, 1);
  };

  state.onMotionClick = () => { void enableMotion(state); };
  state.onFullscreenClick = () => { void toggleFullscreen(state); };
  state.onFullscreenChange = () => {
    updateFullscreenButton(state);
    requestAnimationFrame(() => fitCameraState(state));
  };
  state.onUploadClick = () => state.videoInput?.click();
  state.onSpriteClick = () => state.spriteInput?.click();
  state.onSaveSpritesClick = () => { void saveSpriteExports(state); };
  state.onVideoChange = event => {
    const file = event.target?.files?.[0];
    if (file) void loadSpectralVideo(state, file);
    if (event.target) event.target.value = '';
  };
  state.onSpriteChange = event => {
    const files = event.target?.files;
    if (files?.length) void loadSpriteFiles(state, files);
    if (event.target) event.target.value = '';
  };
  state.onSpriteEditorChange = event => {
    if (event.currentTarget === state.spriteSelect) {
      state.selectedSpriteIndex = clamp(Number(state.spriteSelect.value) || 0, 0, Math.max(0, state.spriteLayers.length - 1));
      refreshSpriteEditor(state);
      return;
    }
    applySpriteEditInputs(state);
  };
  state.onSpriteSizeRange = () => {
    const edit = spriteEdit(state, state.selectedSpriteIndex);
    edit.scale = clamp(Number(state.spriteSizeRange?.value) || 1, 0.05, 8);
    if (state.spriteSizeInput) state.spriteSizeInput.value = edit.scale.toFixed(2);
  };
  state.onSpriteMotionOnly = () => {
    const record = spriteRecordForIndex(state, state.selectedSpriteIndex);
    if (!record || record.frameCount < 2) return;
    void buildMotionOnlyFrames(record).then(() => {
      record.motionOnly = !record.motionOnly;
      refreshSpriteEditor(state);
      renderSpriteFrame(state, performance.now());
    });
  };
  state.onSpriteReset = () => resetSelectedSpriteEdit(state);
    state.onEndemarClick = () => resetEndemarLayers(state);
  state.onLayerClick = event => {
    if (state.mode !== 'spectral' && state.mode !== 'sprite') return;
    const value = event.currentTarget?.dataset?.perceiverLayer || '';
    state.currentStep = value === 'all'
      ? SPECTRAL_STEP_SEQUENCE.length - 1
      : clamp(Number(value) - 1, 0, 6);
    renderStep(state);
  };
  state.onVideoPlay = () => {
    if (state.mode !== 'spectral') return;
    state.playing = true;
    setVideoStatus(state, 'VIDEO → PARALLAX SPRITES · CAPTURING · LOCAL');
    updateReadout(state);
  };
  state.onVideoPause = () => {
    if (state.mode !== 'spectral') return;
    state.playing = false;
    setVideoStatus(state, state.video.ended ? 'SPECTRAL VIDEO · ENDED' : 'SPECTRAL VIDEO · PAUSED');
    updateReadout(state);
  };
  state.onVideoSeeked = () => renderSpectralFrame(state, performance.now(), true);
  state.onVideoEnded = () => {
    if (state.mode !== 'spectral') return;
    state.playing = false;
    void finishVideoSpriteCapture(state).then(() => {
      const meta = state.spriteExportMeta;
      setVideoStatus(state, meta
        ? 'SPRITES READY · ' + meta.frameCount + ' FRAMES · ' + meta.fps.toFixed(2) + ' FPS · TAP SAVE SPRITES'
        : 'VIDEO ENDED · NO SPRITES');
      updateReadout(state);
    });
  };
  state.onOrientationChange = () => {
    state.baselineBeta = null;
    state.baselineGamma = null;
    state.targetX = state.motionEnabled ? 0 : state.pointerX;
    state.targetY = state.motionEnabled ? 0 : state.pointerY;
  };

  canvas.addEventListener('contextmenu', event => { event.preventDefault(); event.stopPropagation(); });
  canvas.addEventListener('dragstart', event => { event.preventDefault(); event.stopPropagation(); });
  canvas.addEventListener('pointermove', state.onPointerMove, { passive: false });
  canvas.addEventListener('pointerdown', state.onPointerDown, { passive: false });
  canvas.addEventListener('pointerup', state.onPointerUp, { passive: false });
  canvas.addEventListener('pointercancel', state.onPointerUp, { passive: false });
  canvas.addEventListener('lostpointercapture', state.onPointerUp, { passive: false });
  canvas.addEventListener('pointerleave', state.onPointerLeave, { passive: true });
  canvas.addEventListener('wheel', state.onWheel, { passive: false });
  canvas.addEventListener('keydown', state.onKeyDown);
  state.motionButton?.addEventListener('click', state.onMotionClick);
  state.fullscreenButton?.addEventListener('click', state.onFullscreenClick);
  document.addEventListener('fullscreenchange', state.onFullscreenChange);
  document.addEventListener('webkitfullscreenchange', state.onFullscreenChange);
  state.uploadButton?.addEventListener('click', state.onUploadClick);
  state.spriteButton?.addEventListener('click', state.onSpriteClick);
  state.saveSpritesButton?.addEventListener('click', state.onSaveSpritesClick);
  state.endemarButton?.addEventListener('click', state.onEndemarClick);
  state.spriteInput?.addEventListener('change', state.onSpriteChange);
  state.spriteSelect?.addEventListener('change', state.onSpriteEditorChange);
  state.spriteSizeInput?.addEventListener('change', state.onSpriteEditorChange);
  state.spriteSizeRange?.addEventListener('input', state.onSpriteSizeRange);
  state.spriteSizeRange?.addEventListener('change', state.onSpriteEditorChange);
  state.spriteXInput?.addEventListener('change', state.onSpriteEditorChange);
  state.spriteYInput?.addEventListener('change', state.onSpriteEditorChange);
  state.spriteOpacityInput?.addEventListener('change', state.onSpriteEditorChange);
  state.spriteFpsInput?.addEventListener('change', state.onSpriteEditorChange);
  state.spriteMotionOnlyButton?.addEventListener('click', state.onSpriteMotionOnly);
  state.spriteResetButton?.addEventListener('click', state.onSpriteReset);
  state.layerButtons.forEach(button => button.addEventListener('click', state.onLayerClick));
  state.videoInput?.addEventListener('change', state.onVideoChange);
  state.video.addEventListener('play', state.onVideoPlay);
  state.video.addEventListener('pause', state.onVideoPause);
  state.video.addEventListener('seeked', state.onVideoSeeked);
  state.video.addEventListener('ended', state.onVideoEnded);
  window.addEventListener('orientationchange', state.onOrientationChange, { passive: true });
  screen.orientation?.addEventListener?.('change', state.onOrientationChange);

  const existingMotionState = window.ristMotionPermission?.state?.();
  if (existingMotionState === 'granted') {
    state.motionEnabled = true;
    addMotionListener(state);
  } else if ('DeviceOrientationEvent' in window &&
             typeof window.DeviceOrientationEvent?.requestPermission !== 'function') {
    state.motionEnabled = true;
    addMotionListener(state);
  }

  STATES.set(root, state);
  updateFullscreenButton(state);
  fitCameraState(state);
  renderStep(state);
  state.raf = requestAnimationFrame(frame => animate(state, frame));
}

export function play(root) {
  const state = stateFor(root);
  if (state.mode === 'scene' || state.mode === 'sprite') {
    state.playing = true;
    if (state.mode === 'scene') state.sceneLastAt = performance.now();
    else state.spriteLastAt = performance.now();
    updateReadout(state);
    return;
  }
  if (state.mode === 'spectral' && state.video) {
    void state.video.play().catch(() => {
      state.playing = false;
      setVideoStatus(state, 'SPECTRAL VIDEO · TAP PLAY AGAIN');
      updateReadout(state);
    });
    return;
  }
  state.playing = true;
  state.lastAdvance = performance.now();
  updateReadout(state);
}

export function pause(root) {
  const state = stateFor(root);
  if (state.mode === 'scene' || state.mode === 'sprite') {
    state.playing = false;
    updateReadout(state);
    return;
  }
  if (state.mode === 'spectral' && state.video) {
    state.video.pause();
    return;
  }
  state.playing = false;
  updateReadout(state);
}

export function restart(root) {
  const state = stateFor(root);
  if (state.mode === 'scene') {
    state.sceneClockMs = 0;
    state.sceneLastAt = performance.now();
    state.sceneSprites.forEach(record => drawSceneSprite(record, 0));
    updateReadout(state);
    return;
  }
  if (state.mode === 'sprite') {
    state.spriteClockMs = 0;
    state.spriteLastAt = performance.now();
    renderSpriteFrame(state, performance.now());
    updateReadout(state);
    return;
  }
  if (state.mode === 'spectral' && state.video) {
    state.video.currentTime = 0;
    renderSpectralFrame(state, performance.now(), true);
    if (state.playing) void state.video.play().catch(() => {});
    return;
  }
  state.currentStep = 0;
  state.lastAdvance = performance.now();
  renderStep(state);
}

export function previous(root) {
  advance(stateFor(root), -1);
}

export function next(root) {
  advance(stateFor(root), 1);
}

export function zoomIn(root) {
  zoomCenter(stateFor(root), ZOOM_STEP);
}

export function zoomOut(root) {
  zoomCenter(stateFor(root), 1 / ZOOM_STEP);
}

export function fit(root) {
  fitCameraState(stateFor(root));
}

export function setSpeed(root, speed) {
  const state = stateFor(root);
  const value = Number(speed);
  state.speed = Number.isFinite(value) && value > 0 ? clamp(value, 0.25, 4) : 1;
  if (state.video) state.video.playbackRate = state.speed;
  state.lastAdvance = performance.now();
}

export async function requestMotion(root) {
  return await enableMotion(stateFor(root));
}

export function detach(root) {
  const state = STATES.get(root);
  if (!state) return;

  state.destroyed = true;
  cancelAnimationFrame(state.raf);

  state.canvas.removeEventListener('pointermove', state.onPointerMove);
  state.canvas.removeEventListener('pointerdown', state.onPointerDown);
  state.canvas.removeEventListener('pointerup', state.onPointerUp);
  state.canvas.removeEventListener('pointercancel', state.onPointerUp);
  state.canvas.removeEventListener('lostpointercapture', state.onPointerUp);
  state.canvas.removeEventListener('pointerleave', state.onPointerLeave);
  state.canvas.removeEventListener('wheel', state.onWheel);
  state.canvas.removeEventListener('keydown', state.onKeyDown);
  state.motionButton?.removeEventListener('click', state.onMotionClick);
  state.fullscreenButton?.removeEventListener('click', state.onFullscreenClick);
  document.removeEventListener('fullscreenchange', state.onFullscreenChange);
  document.removeEventListener('webkitfullscreenchange', state.onFullscreenChange);
  exitPseudoFullscreen(state);
  state.uploadButton?.removeEventListener('click', state.onUploadClick);
  state.spriteButton?.removeEventListener('click', state.onSpriteClick);
  state.saveSpritesButton?.removeEventListener('click', state.onSaveSpritesClick);
  state.endemarButton?.removeEventListener('click', state.onEndemarClick);
  state.spriteInput?.removeEventListener('change', state.onSpriteChange);
  state.spriteSelect?.removeEventListener('change', state.onSpriteEditorChange);
  state.spriteSizeInput?.removeEventListener('change', state.onSpriteEditorChange);
  state.spriteSizeRange?.removeEventListener('input', state.onSpriteSizeRange);
  state.spriteSizeRange?.removeEventListener('change', state.onSpriteEditorChange);
  state.spriteXInput?.removeEventListener('change', state.onSpriteEditorChange);
  state.spriteYInput?.removeEventListener('change', state.onSpriteEditorChange);
  state.spriteOpacityInput?.removeEventListener('change', state.onSpriteEditorChange);
  state.spriteFpsInput?.removeEventListener('change', state.onSpriteEditorChange);
  state.spriteMotionOnlyButton?.removeEventListener('click', state.onSpriteMotionOnly);
  state.spriteResetButton?.removeEventListener('click', state.onSpriteReset);
  state.layerButtons.forEach(button => button.removeEventListener('click', state.onLayerClick));
  state.videoInput?.removeEventListener('change', state.onVideoChange);
  state.video?.removeEventListener('play', state.onVideoPlay);
  state.video?.removeEventListener('pause', state.onVideoPause);
  state.video?.removeEventListener('seeked', state.onVideoSeeked);
  state.video?.removeEventListener('ended', state.onVideoEnded);
  if (state.video) {
    state.video.pause();
    state.video.removeAttribute('src');
    state.video.load();
  }
  stopSpectralObjectUrl(state);
  clearSceneLayers(state);
  window.removeEventListener('orientationchange', state.onOrientationChange);
  screen.orientation?.removeEventListener?.('change', state.onOrientationChange);
  removeMotionListener(state);

  STATES.delete(root);
}
