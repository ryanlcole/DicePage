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

const DEPTH_FACTORS = Object.freeze([0.28, 0.60, 1.0]);
const SPECTRAL_MAX_PIXELS = 640 * 360;
const SPECTRAL_FRAME_INTERVAL_MS = 1000 / 30;
const SPECTRAL_FAST_MIN = 185;
const SPECTRAL_FAST_MAX = 315;
const SPECTRAL_MID_MIN = 65;
const SPECTRAL_MID_MAX = 185;
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

function updateReadout(state) {
  setText(
    state.labelNode,
    state.mode === 'spectral' ? 'Spectral · Tier 1 + Tier 2 + Tier 3' : STEP_SEQUENCE[state.currentStep].label
  );
  setText(state.playStateNode, state.playing ? 'Playing' : 'Paused');
  setText(state.motionNode, state.motionEnabled ? 'Tilt Ready' : 'Pointer');
  setText(state.zoomNode, `${Math.round(state.cameraScale * 100)}%`);
  if (state.mode === 'spectral') {
    setText(state.modeNoteNode, 'T1 FAST · VIOLET/BLUE  ·  T2 MID · GREEN/YELLOW  ·  T3 SLOW · ORANGE/RED');
  } else {
    setText(state.modeNoteNode, '1 → 2 → 3 → 1+2 → 1+3 → 2+3 → 1+2+3 → repeat');
  }
}

function renderStep(state) {
  const active = state.mode === 'spectral'
    ? new Set([0, 1, 2])
    : new Set(STEP_SEQUENCE[state.currentStep].tiers);
  state.layers.forEach((layer, index) => {
    const visible = active.has(index);
    layer.style.opacity = visible ? '1' : '0';
    layer.dataset.active = visible ? 'true' : 'false';
    layer.setAttribute('aria-hidden', visible ? 'false' : 'true');
  });
  updateReadout(state);
}

function advance(state, delta) {
  const total = STEP_SEQUENCE.length;
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
  // middle tier as the structural reference instead of inventing a frequency.
  if (spectral.saturation < 0.10) return 1;

  if (spectral.hue >= SPECTRAL_FAST_MIN && spectral.hue < SPECTRAL_FAST_MAX) {
    return 0; // Short wavelength / fastest in this experiment.
  }
  if (spectral.hue >= SPECTRAL_MID_MIN && spectral.hue < SPECTRAL_MID_MAX) {
    return 1;
  }
  return 2; // Long wavelength / slowest in this experiment.
}

function setVideoStatus(state, value) {
  setText(state.videoStatusNode, value);
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
    display: 'block',
    maxWidth: '106%',
    maxHeight: '106%',
    width: 'auto',
    height: 'auto',
    pointerEvents: 'none'
  });
  wrapper.appendChild(canvas);
  wrapper._spectralCanvas = canvas;
  wrapper._spectralContext = canvas.getContext('2d', { alpha: true });
  return wrapper;
}

function resetEndemarLayers(state) {
  if (state.video) state.video.pause();
  state.mode = 'endemar';
  state.currentStep = 0;
  state.playing = !state.reducedMotion;
  state.lastAdvance = performance.now();

  state.spectralLayers.forEach(layer => { layer.style.display = 'none'; });
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
    canvas.style.aspectRatio = \`\${size.width} / \${size.height}\`;
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

  stopSpectralObjectUrl(state);
  state.videoObjectUrl = URL.createObjectURL(file);
  state.video.pause();
  state.video.src = state.videoObjectUrl;
  state.video.load();

  state.mode = 'spectral';
  state.playing = false;
  state.endemarLayers.forEach(layer => { layer.style.display = 'none'; });
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
  setVideoStatus(
    state,
    \`\${file.name || 'PHONE VIDEO'} · \${state.spectralWidth}×\${state.spectralHeight} · LOCAL\`
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
    setVideoStatus(state, \`\${file.name || 'PHONE VIDEO'} · CONVERTING LIVE · LOCAL\`);
  } catch {
    state.playing = false;
    setVideoStatus(state, \`\${file.name || 'PHONE VIDEO'} · READY · TAP PLAY\`);
  }
  updateReadout(state);
}

function animate(state, now) {
  if (state.destroyed) return;

  if (state.mode === 'spectral') {
    renderSpectralFrame(state, now);
  } else {
    const duration = state.stepDurationMs / state.speed;
    if (state.playing && now - state.lastAdvance >= duration) advance(state, 1);
  }

  state.currentX += (state.targetX - state.currentX) * 0.13;
  state.currentY += (state.targetY - state.currentY) * 0.13;

  const idleX = state.reducedMotion ? 0 : Math.sin(now * 0.00052) * 0.08;
  const idleY = state.reducedMotion ? 0 : Math.cos(now * 0.00039) * 0.06;

  state.layers.forEach((image, index) => {
    const depth = DEPTH_FACTORS[index] ?? 1;
    const x = (state.currentX + idleX) * 26 * depth;
    const y = (state.currentY + idleY) * 19 * depth;
    const scale = 1.005 + depth * 0.018;
    image.style.transform = `translate3d(${x.toFixed(2)}px,${y.toFixed(2)}px,0) scale(${scale.toFixed(4)})`;
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
    uploadButton: root.querySelector('[data-perceiver-upload-button]'),
    endemarButton: root.querySelector('[data-perceiver-endemar-button]'),
    videoInput: root.querySelector('[data-perceiver-video-input]'),
    videoStatusNode: root.querySelector('[data-perceiver-video-status]'),
    modeNoteNode: root.querySelector('[data-perceiver-mode-note]'),
    mode: 'endemar',
    endemarLayers: [],
    spectralLayers: [],
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
    onUploadClick: null,
    onVideoChange: null,
    onEndemarClick: null,
    onVideoPlay: null,
    onVideoPause: null,
    onVideoSeeked: null,
    onVideoEnded: null,
    onOrientationChange: null
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

  state.spectralLayers = [0, 1, 2].map(index => {
    const layer = makeSpectralLayer(index);
    layer.style.display = 'none';
    camera.appendChild(layer);
    return layer;
  });

  state.video = document.createElement('video');
  state.video.playsInline = true;
  state.video.preload = 'metadata';
  state.video.controls = false;
  state.video.style.display = 'none';
  state.video.setAttribute('playsinline', '');
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
  state.onUploadClick = () => state.videoInput?.click();
  state.onVideoChange = event => {
    const file = event.target?.files?.[0];
    if (file) void loadSpectralVideo(state, file);
    if (event.target) event.target.value = '';
  };
  state.onEndemarClick = () => resetEndemarLayers(state);
  state.onVideoPlay = () => {
    if (state.mode !== 'spectral') return;
    state.playing = true;
    setVideoStatus(state, 'SPECTRAL VIDEO · CONVERTING LIVE · LOCAL');
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
    setVideoStatus(state, 'SPECTRAL VIDEO · ENDED');
    updateReadout(state);
  };
  state.onOrientationChange = () => {
    state.baselineBeta = null;
    state.baselineGamma = null;
    state.targetX = state.motionEnabled ? 0 : state.pointerX;
    state.targetY = state.motionEnabled ? 0 : state.pointerY;
  };

  canvas.addEventListener('pointermove', state.onPointerMove, { passive: false });
  canvas.addEventListener('pointerdown', state.onPointerDown, { passive: false });
  canvas.addEventListener('pointerup', state.onPointerUp, { passive: false });
  canvas.addEventListener('pointercancel', state.onPointerUp, { passive: false });
  canvas.addEventListener('lostpointercapture', state.onPointerUp, { passive: false });
  canvas.addEventListener('pointerleave', state.onPointerLeave, { passive: true });
  canvas.addEventListener('wheel', state.onWheel, { passive: false });
  canvas.addEventListener('keydown', state.onKeyDown);
  state.motionButton?.addEventListener('click', state.onMotionClick);
  state.uploadButton?.addEventListener('click', state.onUploadClick);
  state.endemarButton?.addEventListener('click', state.onEndemarClick);
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
  fitCameraState(state);
  renderStep(state);
  state.raf = requestAnimationFrame(frame => animate(state, frame));
}

export function play(root) {
  const state = stateFor(root);
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
  if (state.mode === 'spectral' && state.video) {
    state.video.pause();
    return;
  }
  state.playing = false;
  updateReadout(state);
}

export function restart(root) {
  const state = stateFor(root);
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
  const state = stateFor(root);
  if (state.mode === 'spectral' && state.video) {
    state.video.currentTime = Math.max(0, state.video.currentTime - 5);
    return;
  }
  advance(state, -1);
}

export function next(root) {
  const state = stateFor(root);
  if (state.mode === 'spectral' && state.video) {
    const duration = Number.isFinite(state.video.duration) ? state.video.duration : state.video.currentTime + 5;
    state.video.currentTime = Math.min(duration, state.video.currentTime + 5);
    return;
  }
  advance(state, 1);
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
  state.uploadButton?.removeEventListener('click', state.onUploadClick);
  state.endemarButton?.removeEventListener('click', state.onEndemarClick);
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
  window.removeEventListener('orientationchange', state.onOrientationChange);
  screen.orientation?.removeEventListener?.('change', state.onOrientationChange);
  removeMotionListener(state);

  STATES.delete(root);
}
