function closeToWorld(event) {
  if (event) {
    event.preventDefault?.();
    event.stopPropagation?.();
    event.stopImmediatePropagation?.();
  }

  const app = window.shaelvienApp;
  const state = app?.getState?.();
  if (state?.tabletop?.overlay) {
    state.tabletop.overlay.open = false;
    state.tabletop.overlay.detailCardId = null;
    state.tabletop.overlay.detailDeckId = null;
  }
  if (state) {
    state.currentMapId = 'map-world';
    state.lastValidMapId = 'map-world';
    state.scene = 'MAP_VIEW';
    state.selectedTileId = null;
    state.selectedAtlasInstanceId = null;
    state.selection = null;
    if (state.editor && window.innerWidth < 900) {
      state.editor.inspectorOpen = false;
      state.editor.inspectorSheetState = 'collapsed';
    }
  }

  const overlay = document.getElementById('tabletopOverlay');
  const backdrop = document.getElementById('tabletopOverlayBackdrop');
  const world = document.getElementById('naejaWorldSurface');
  if (overlay) overlay.hidden = true;
  if (backdrop) backdrop.hidden = true;
  if (world) world.hidden = false;
  document.body.classList.remove('tabletop-overlay-open');
}

function bindMobileEscape() {
  const closeButton = document.getElementById('closeTabletopOverlayButton');
  const backdrop = document.getElementById('tabletopOverlayBackdrop');
  if (closeButton && !closeButton.dataset.naejaCloseBound) {
    closeButton.dataset.naejaCloseBound = '1';
    closeButton.addEventListener('pointerup', closeToWorld, true);
    closeButton.addEventListener('click', closeToWorld, true);
    closeButton.addEventListener('touchend', closeToWorld, { capture: true, passive: false });
  }
  if (backdrop && !backdrop.dataset.naejaCloseBound) {
    backdrop.dataset.naejaCloseBound = '1';
    backdrop.addEventListener('pointerup', closeToWorld, true);
    backdrop.addEventListener('click', closeToWorld, true);
  }
}

if (!window.__naejaMobileEscapeBound) {
  window.__naejaMobileEscapeBound = true;
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !document.getElementById('tabletopOverlay')?.hidden) closeToWorld(event);
  }, true);
  document.addEventListener('DOMContentLoaded', bindMobileEscape, { once: true });
  const observer = new MutationObserver(bindMobileEscape);
  observer.observe(document.documentElement, { childList: true, subtree: true });
  window.setTimeout(bindMobileEscape, 0);
  window.setTimeout(bindMobileEscape, 250);
}

export { closeToWorld };
