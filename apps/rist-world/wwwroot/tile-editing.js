let bridge = null;
let down = null;
let observer = null;
let zStyle = null;

function tileCells() {
  return [...document.querySelectorAll('.world-stage > .tile-cell')];
}

function zNavigationUnlocked() {
  const control = document.querySelector('.map-lock-button');
  return !!control && (control.getAttribute('aria-pressed') === 'true' || control.classList.contains('active'));
}

function ensureZNavigationStyle() {
  if (zStyle) return;
  zStyle = document.createElement('style');
  zStyle.id = 'rist-z-navigation-authority';
  zStyle.textContent = `
    html.rist-z-unlocked .map-shell > .map {
      touch-action: none !important;
      cursor: grab !important;
      user-select: none !important;
      -webkit-user-select: none !important;
    }
    html.rist-z-unlocked .map-shell > .map:active { cursor: grabbing !important; }
    html.rist-z-unlocked .world-stage > .tile-cell,
    html.rist-z-unlocked .world-stage > .piece {
      pointer-events: none !important;
    }
    html.rist-z-unlocked .tile-edit-overlay,
    html.rist-z-unlocked #rist-app-home-slider .rist-tile-edit-bottom {
      display: none !important;
    }
  `;
  document.head.appendChild(zStyle);
}

function syncZNavigationMode() {
  ensureZNavigationStyle();
  const unlocked = zNavigationUnlocked();
  document.documentElement.classList.toggle('rist-z-unlocked', unlocked);
  const map = document.querySelector('.release-map-region .map-shell > .map, .map-shell > .map');
  if (map) map.setAttribute('data-z-unlocked', unlocked ? 'true' : 'false');
  if (unlocked) down = null;
}

function editableIndexFromTarget(target) {
  if (zNavigationUnlocked()) return -1;
  const tile = target?.closest?.('.world-stage > .tile-cell.unlocked');
  if (!tile || target?.closest?.('.tile-edit-overlay, .rist-tile-edit-bottom')) return -1;
  return tileCells().indexOf(tile);
}

function ensureBottomControls() {
  const slider = document.querySelector('#rist-app-home-slider');
  if (!slider || !bridge) return;

  let group = slider.querySelector('.rist-tile-edit-bottom');
  if (!group) {
    group = document.createElement('span');
    group.className = 'rist-tile-edit-bottom';
    group.setAttribute('role', 'group');
    group.setAttribute('aria-label', 'Selected tile controls');
    group.style.display = 'none';

    const smaller = document.createElement('button');
    smaller.type = 'button';
    smaller.className = 'rist-app-slider-button tile-size-down';
    smaller.textContent = 'Size −';
    smaller.setAttribute('aria-label', 'Make selected tile smaller');
    smaller.addEventListener('click', e => {
      e.preventDefault();
      e.stopPropagation();
      bridge?.invokeMethodAsync('ResizeSelectedTile', false);
    });

    const larger = document.createElement('button');
    larger.type = 'button';
    larger.className = 'rist-app-slider-button tile-size-up';
    larger.textContent = 'Size +';
    larger.setAttribute('aria-label', 'Make selected tile larger');
    larger.addEventListener('click', e => {
      e.preventDefault();
      e.stopPropagation();
      bridge?.invokeMethodAsync('ResizeSelectedTile', true);
    });

    const lock = document.createElement('button');
    lock.type = 'button';
    lock.className = 'rist-app-slider-button tile-lock-commit';
    lock.textContent = 'Lock Tile';
    lock.disabled = true;
    lock.setAttribute('aria-label', 'Lock selected tile and autosave');
    lock.addEventListener('click', e => {
      e.preventDefault();
      e.stopPropagation();
      if (!lock.disabled) bridge?.invokeMethodAsync('CommitTileLock');
    });

    group.append(smaller, larger, lock);
    slider.append(group);
  }
}

function pointerDown(event) {
  const index = editableIndexFromTarget(event.target);
  if (index < 0) return;
  down = { index, x: event.clientX, y: event.clientY, pointerId: event.pointerId };
}

function pointerUp(event) {
  if (!down || down.pointerId !== event.pointerId) return;
  const start = down;
  down = null;
  if (Math.abs(event.clientX - start.x) + Math.abs(event.clientY - start.y) > 7) return;

  const visibleTarget = document.elementFromPoint(event.clientX, event.clientY);
  const index = editableIndexFromTarget(visibleTarget);
  if (index !== start.index) return;
  bridge?.invokeMethodAsync('SelectTileFromMap', index);
}

function resync() {
  ensureBottomControls();
  syncZNavigationMode();
}

export function register(dotnet) {
  bridge = dotnet;
  document.addEventListener('pointerdown', pointerDown, true);
  document.addEventListener('pointerup', pointerUp, true);
  document.addEventListener('click', event => {
    if (event.target?.closest?.('.map-lock-button')) setTimeout(syncZNavigationMode, 0);
  }, true);
  resync();
  observer = new MutationObserver(resync);
  observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['aria-pressed', 'class'] });
}

export function updateBottomState(hasTile, lockArmed) {
  ensureBottomControls();
  const group = document.querySelector('#rist-app-home-slider .rist-tile-edit-bottom');
  if (!group) return;
  const navigates = zNavigationUnlocked();
  group.style.display = hasTile && !navigates ? 'contents' : 'none';
  group.querySelectorAll('.tile-size-down,.tile-size-up').forEach(button => button.disabled = !hasTile || navigates);
  const lock = group.querySelector('.tile-lock-commit');
  if (lock) {
    lock.disabled = !hasTile || !lockArmed || navigates;
    lock.classList.toggle('armed', !!lockArmed && !navigates);
    lock.setAttribute('aria-pressed', lockArmed && !navigates ? 'true' : 'false');
  }
}

export function syncRotations(rotations) {
  const values = Array.isArray(rotations) ? rotations : [];
  tileCells().forEach((tile, index) => {
    const crop = tile.querySelector(':scope > .tile-image-crop');
    if (!crop) return;
    const quarterTurns = Number(values[index] || 0);
    crop.style.transformOrigin = '50% 50%';
    crop.style.transform = `rotate(${quarterTurns * 90}deg)`;
  });
}

export function positionOverlay(element, index) {
  if (!element) return [0, 0];
  if (zNavigationUnlocked()) {
    element.style.display = 'none';
    return [0, 0];
  }
  const tile = tileCells()[index];
  const stage = document.querySelector('.world-stage');
  if (!tile || !stage) {
    element.style.display = 'none';
    return [0, 0];
  }

  const rect = tile.getBoundingClientRect();
  const stageRect = stage.getBoundingClientRect();
  element.style.display = '';
  element.style.setProperty('--tile-left', `${rect.left}px`);
  element.style.setProperty('--tile-top', `${rect.top}px`);
  element.style.setProperty('--tile-width', `${rect.width}px`);
  element.style.setProperty('--tile-height', `${rect.height}px`);

  return [
    stageRect.width > 0 ? 1 / stageRect.width : 0,
    stageRect.height > 0 ? 1 / stageRect.height : 0
  ];
}

export function dispose() {
  document.removeEventListener('pointerdown', pointerDown, true);
  document.removeEventListener('pointerup', pointerUp, true);
  observer?.disconnect();
  observer = null;
  bridge = null;
  down = null;
  document.documentElement.classList.remove('rist-z-unlocked');
  zStyle?.remove();
  zStyle = null;
  document.querySelector('#rist-app-home-slider .rist-tile-edit-bottom')?.remove();
}
