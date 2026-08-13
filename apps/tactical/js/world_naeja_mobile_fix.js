import { NAEJA_WORLD_MAP } from './naeja_world_asset.js';

function tabletopState() {
  return window.shaelvienApp?.getState?.()?.tabletop || null;
}

function hardCloseOverlay() {
  const tabletop = tabletopState();
  if (tabletop?.overlay) {
    tabletop.overlay.open = false;
    tabletop.overlay.detailCardId = null;
    tabletop.overlay.detailDeckId = null;
  }
  const overlay = document.getElementById('tabletopOverlay');
  const backdrop = document.getElementById('tabletopOverlayBackdrop');
  if (overlay) overlay.hidden = true;
  if (backdrop) backdrop.hidden = true;
  document.body.classList.remove('tabletop-overlay-open');
  const world = document.getElementById('naejaWorldSurface');
  const state = window.shaelvienApp?.getState?.();
  if (world && state?.currentMapId === 'map-world') world.hidden = false;
}

function ensureEmbeddedMap() {
  const image = document.querySelector('#naejaWorldSurface .naeja-map-image');
  if (!image) return false;
  const cleanSource = String(NAEJA_WORLD_MAP || '').replace(/\s+/g, '');
  if (cleanSource.startsWith('data:image/')) {
    if (image.src !== cleanSource) image.src = cleanSource;
    image.addEventListener('load', () => {
      image.dataset.naejaLoaded = 'true';
      const status = document.getElementById('naejaWorldStatus');
      if (status && !status.textContent.includes('Atlas registry failed')) status.textContent = 'WORLD • Naeja map loaded • Atlas tiles ready • Party coin is draggable';
    }, { once: true });
    image.addEventListener('error', () => {
      image.dataset.naejaLoaded = 'false';
      const status = document.getElementById('naejaWorldStatus');
      if (status) status.textContent = 'WORLD • Naeja image failed to decode';
    }, { once: true });
  }
  return true;
}

function interceptClose(event) {
  const target = event.target instanceof Element ? event.target : null;
  if (!target) return;
  const close = target.closest('#closeTabletopOverlayButton,[data-tabletop-action="close-menu"]');
  const backdrop = target.closest('#tabletopOverlayBackdrop');
  if (!close && !backdrop) return;
  event.preventDefault();
  event.stopPropagation();
  event.stopImmediatePropagation?.();
  hardCloseOverlay();
}

document.addEventListener('pointerup', interceptClose, true);
document.addEventListener('click', interceptClose, true);

let attempts = 0;
const timer = window.setInterval(() => {
  attempts += 1;
  hardCloseOverlay();
  if (ensureEmbeddedMap()) {
    window.clearInterval(timer);
    return;
  }
  if (attempts > 200) window.clearInterval(timer);
}, 50);
