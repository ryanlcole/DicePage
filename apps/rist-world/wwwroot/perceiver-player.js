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
  setText(state.labelNode, STEP_SEQUENCE[state.currentStep].label);
  setText(state.playStateNode, state.playing ? 'Playing' : 'Paused');
  setText(state.motionNode, state.motionEnabled ? 'Tilt Ready' : 'Pointer');
}

function renderStep(state) {
  const active = new Set(STEP_SEQUENCE[state.currentStep].tiers);
  state.layers.forEach((image, index) => {
    const visible = active.has(index);
    image.style.opacity = visible ? '1' : '0';
    image.dataset.active = visible ? 'true' : 'false';
    image.setAttribute('aria-hidden', visible ? 'false' : 'true');
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

function animate(state, now) {
  if (state.destroyed) return;

  const duration = state.stepDurationMs / state.speed;
  if (state.playing && now - state.lastAdvance >= duration) advance(state, 1);

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
    layers: [],
    currentStep: 0,
    playing: !window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    speed: 1,
    stepDurationMs: Math.max(400, Number(config.stepDurationMs) || 2000),
    lastAdvance: performance.now(),
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
    activePointerId: null,
    labelNode: root.querySelector('[data-perceiver-label]'),
    playStateNode: root.querySelector('[data-perceiver-play-state]'),
    motionNode: root.querySelector('[data-perceiver-motion-state]'),
    motionButton: root.querySelector('[data-perceiver-motion-button]'),
    onPointerMove: null,
    onPointerDown: null,
    onPointerUp: null,
    onPointerLeave: null,
    onDeviceOrientation: null,
    onMotionClick: null,
    onOrientationChange: null
  };

  state.layers = urls.map((src, index) => {
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
    stack.appendChild(image);
    return image;
  });

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
    if (event.pointerType === 'mouse' || state.dragging) {
      applyPointerTarget(state, event.clientX, event.clientY);
    }
  };

  state.onPointerDown = event => {
    state.dragging = true;
    state.activePointerId = event.pointerId;
    try { canvas.setPointerCapture(event.pointerId); } catch {}
    applyPointerTarget(state, event.clientX, event.clientY);
  };

  state.onPointerUp = event => {
    if (state.activePointerId !== null && event.pointerId !== state.activePointerId) return;
    state.dragging = false;
    state.activePointerId = null;
    try { canvas.releasePointerCapture(event.pointerId); } catch {}
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
  state.onOrientationChange = () => {
    state.baselineBeta = null;
    state.baselineGamma = null;
    state.targetX = state.motionEnabled ? 0 : state.pointerX;
    state.targetY = state.motionEnabled ? 0 : state.pointerY;
  };

  canvas.addEventListener('pointermove', state.onPointerMove, { passive: true });
  canvas.addEventListener('pointerdown', state.onPointerDown, { passive: true });
  canvas.addEventListener('pointerup', state.onPointerUp, { passive: true });
  canvas.addEventListener('pointercancel', state.onPointerUp, { passive: true });
  canvas.addEventListener('pointerleave', state.onPointerLeave, { passive: true });
  state.motionButton?.addEventListener('click', state.onMotionClick);
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
  renderStep(state);
  state.raf = requestAnimationFrame(frame => animate(state, frame));
}

export function play(root) {
  const state = stateFor(root);
  state.playing = true;
  state.lastAdvance = performance.now();
  updateReadout(state);
}

export function pause(root) {
  const state = stateFor(root);
  state.playing = false;
  updateReadout(state);
}

export function restart(root) {
  const state = stateFor(root);
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

export function setSpeed(root, speed) {
  const state = stateFor(root);
  const value = Number(speed);
  state.speed = Number.isFinite(value) && value > 0 ? clamp(value, 0.25, 4) : 1;
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
  state.canvas.removeEventListener('pointerleave', state.onPointerLeave);
  state.motionButton?.removeEventListener('click', state.onMotionClick);
  window.removeEventListener('orientationchange', state.onOrientationChange);
  screen.orientation?.removeEventListener?.('change', state.onOrientationChange);
  removeMotionListener(state);

  STATES.delete(root);
}
