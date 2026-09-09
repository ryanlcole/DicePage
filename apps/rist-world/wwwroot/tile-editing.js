let bridge = null;
let down = null;
let observer = null;

function tileCells() {
  return [...document.querySelectorAll('.world-stage > .tile-cell')];
}

function editableIndexFromTarget(target) {
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

    const smaller = document.createElement('button');
    smaller.type = 'button';
    smaller.className = 'rist-app-slider-button tile-size-down';
    smaller.textContent = 'Size −';
    smaller.addEventListener('click', e => {
      e.preventDefault();
      e.stopPropagation();
      bridge.invokeMethodAsync('ResizeSelectedTile', false);
    });

    const larger = document.createElement('button');
    larger.type = 'button';
    larger.className = 'rist-app-slider-button tile-size-up';
    larger.textContent = 'Size +';
    larger.addEventListener('click', e => {
      e.preventDefault();
      e.stopPropagation();
      bridge.invokeMethodAsync('ResizeSelectedTile', true);
    });

    const lock = document.createElement('button');
    lock.type = 'button';
    lock.className = 'rist-app-slider-button tile-lock-commit';
    lock.textContent = 'Lock Tile';
    lock.disabled = true;
    lock.addEventListener('click', e => {
      e.preventDefault();
      e.stopPropagation();
      if (!lock.disabled) bridge.invokeMethodAsync('CommitTileLock');
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
  const index = editableIndexFromTarget(event.target);
  if (index !== start.index) return;
  if (Math.abs(event.clientX - start.x) + Math.abs(event.clientY - start.y) > 7) return;
  bridge?.invokeMethodAsync('SelectTileFromMap', index);
}

export function register(dotnet) {
  bridge = dotnet;
  document.addEventListener('pointerdown', pointerDown, true);
  document.addEventListener('pointerup', pointerUp, true);
  ensureBottomControls();
  observer = new MutationObserver(ensureBottomControls);
  observer.observe(document.body, { childList: true, subtree: true });
}

export function updateBottomState(hasTile, lockArmed) {
  ensureBottomControls();
  const group = document.querySelector('#rist-app-home-slider .rist-tile-edit-bottom');
  if (!group) return;
  group.hidden = !hasTile;
  group.querySelectorAll('.tile-size-down,.tile-size-up').forEach(button => button.disabled = !hasTile);
  const lock = group.querySelector('.tile-lock-commit');
  if (lock) {
    lock.disabled = !hasTile || !lockArmed;
    lock.classList.toggle('armed', !!lockArmed);
  }
}

export function positionOverlay(element, index) {
  if (!element) return null;
  const tile = tileCells()[index];
  const stage = document.querySelector('.world-stage');
  if (!tile || !stage) {
    element.style.display = 'none';
    return null;
  }

  const rect = tile.getBoundingClientRect();
  const stageRect = stage.getBoundingClientRect();
  element.style.display = '';
  element.style.setProperty('--tile-left', `${rect.left}px`);
  element.style.setProperty('--tile-top', `${rect.top}px`);
  element.style.setProperty('--tile-width', `${rect.width}px`);
  element.style.setProperty('--tile-height', `${rect.height}px`);

  return {
    pixelX: stageRect.width > 0 ? 1 / stageRect.width : 0,
    pixelY: stageRect.height > 0 ? 1 / stageRect.height : 0
  };
}

export function dispose() {
  document.removeEventListener('pointerdown', pointerDown, true);
  document.removeEventListener('pointerup', pointerUp, true);
  observer?.disconnect();
  observer = null;
  bridge = null;
  down = null;
  document.querySelector('#rist-app-home-slider .rist-tile-edit-bottom')?.remove();
}
