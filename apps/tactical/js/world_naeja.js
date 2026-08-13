import { NAEJA_WORLD_MAP, NAEJA_WORLD_META } from './naeja_world_asset.js';

const WORLD_UI_KEY = 'rist.world.naeja.ui.v1';
const WORLD_OBJECTS_KEY = 'rist.world.naeja.objects.v1';
const DEFAULT_PARTY = { x: 0.52, y: 0.55 };
let atlasAssets = [];
let selectedAssetId = null;
let surface = null;
let stage = null;
let party = null;
let tileLayer = null;
let tilePalette = null;
let statusNode = null;

function loadJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function saveJson(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function closeLegacyOverlay() {
  const app = window.shaelvienApp;
  const state = app?.getState?.();
  if (state?.tabletop?.overlay) state.tabletop.overlay.open = false;
  const overlay = document.getElementById('tabletopOverlay');
  const backdrop = document.getElementById('tabletopOverlayBackdrop');
  if (overlay) overlay.hidden = true;
  if (backdrop) backdrop.hidden = true;
  document.body.classList.remove('tabletop-overlay-open');
}

function establishWorldState() {
  const app = window.shaelvienApp;
  const state = app?.getState?.();
  if (!state?.maps?.['map-world']) return false;
  state.currentMapId = 'map-world';
  state.lastValidMapId = 'map-world';
  state.scene = 'MAP_VIEW';
  state.selectedTileId = null;
  state.selectedAtlasInstanceId = null;
  state.selection = null;
  if (window.innerWidth < 900 && state.editor) {
    state.editor.inspectorOpen = false;
    state.editor.inspectorSheetState = 'collapsed';
  }
  closeLegacyOverlay();
  document.getElementById('mapViewButton')?.click();
  return true;
}

function injectStyles() {
  if (document.getElementById('naejaWorldStyles')) return;
  const style = document.createElement('style');
  style.id = 'naejaWorldStyles';
  style.textContent = `
    #naejaWorldSurface { position:absolute; inset:0; z-index:16; display:flex; flex-direction:column; background:#080b0e; color:#f3ead4; touch-action:none; overflow:hidden; }
    #naejaWorldSurface[hidden] { display:none !important; }
    .naeja-world-head { min-height:46px; display:flex; align-items:center; gap:8px; padding:7px 10px; background:linear-gradient(180deg,rgba(15,18,20,.98),rgba(9,11,13,.94)); border-bottom:1px solid rgba(217,182,93,.35); }
    .naeja-world-title { min-width:0; flex:1; }
    .naeja-world-title strong { display:block; font-size:15px; letter-spacing:.04em; }
    .naeja-world-title span { display:block; font-size:11px; color:#b9af96; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .naeja-world-btn { min-height:34px; border:1px solid rgba(217,182,93,.45); border-radius:7px; background:#211d16; color:#f3ead4; padding:6px 10px; font-weight:700; }
    .naeja-world-btn.is-active { background:#d9b65d; color:#17130d; }
    .naeja-world-body { flex:1; min-height:0; display:grid; place-items:center; position:relative; padding:8px; overflow:hidden; }
    .naeja-map-stage { position:relative; width:min(100%, calc((100dvh - 150px) * 1.77634)); max-height:100%; aspect-ratio:961/541; border:1px solid rgba(217,182,93,.42); box-shadow:0 12px 40px rgba(0,0,0,.45); background:#0b1015; overflow:hidden; touch-action:none; user-select:none; }
    .naeja-map-stage > .naeja-map-image { position:absolute; inset:0; width:100%; height:100%; object-fit:fill; pointer-events:none; user-select:none; -webkit-user-drag:none; }
    .naeja-tile-layer { position:absolute; inset:0; pointer-events:none; }
    .naeja-atlas-instance { position:absolute; transform:translate(-50%,-50%); pointer-events:auto; touch-action:none; filter:drop-shadow(0 3px 3px rgba(0,0,0,.45)); }
    .naeja-atlas-instance.is-selected { outline:2px solid #8fd3ff; outline-offset:2px; }
    .naeja-party-coin { position:absolute; width:42px; height:42px; transform:translate(-50%,-50%); border-radius:50%; border:3px solid #e4c363; background:radial-gradient(circle at 36% 31%,#fff3ae 0 8%,#b77825 10% 32%,#5a3217 68%,#23150d 100%); box-shadow:0 3px 10px rgba(0,0,0,.75), inset 0 0 0 2px rgba(255,238,172,.25); display:grid; place-items:center; color:#fff2b5; font:bold 12px/1 system-ui; z-index:7; touch-action:none; cursor:grab; }
    .naeja-party-coin::after { content:'PARTY'; text-shadow:0 1px 2px #000; font-size:8px; letter-spacing:.04em; }
    .naeja-world-status { position:absolute; left:14px; bottom:12px; z-index:9; max-width:min(75%,520px); padding:6px 9px; border-radius:6px; background:rgba(5,8,10,.78); border:1px solid rgba(217,182,93,.28); color:#e8dfca; font-size:11px; pointer-events:none; }
    .naeja-tile-palette { position:absolute; left:8px; right:8px; bottom:8px; z-index:20; max-height:42%; overflow:auto; display:grid; grid-template-columns:repeat(auto-fill,minmax(96px,1fr)); gap:6px; padding:8px; background:rgba(10,13,16,.96); border:1px solid rgba(217,182,93,.42); border-radius:8px; box-shadow:0 10px 28px rgba(0,0,0,.5); touch-action:pan-y; }
    .naeja-tile-palette[hidden] { display:none !important; }
    .naeja-asset-card { min-height:86px; border:1px solid #3b4650; border-radius:6px; padding:5px; background:#151d25; color:#eee5d0; display:grid; grid-template-rows:52px auto; gap:4px; text-align:left; }
    .naeja-asset-card img { width:100%; height:52px; object-fit:contain; background:#0d1217; }
    .naeja-asset-card span { font-size:10px; line-height:1.15; overflow:hidden; }
    .naeja-asset-card.is-selected { border-color:#e4c363; box-shadow:0 0 0 1px #e4c363 inset; }
    .naeja-world-mode-button { margin-left:4px; }
    @media (max-width:700px) {
      .naeja-world-head { min-height:42px; padding:5px 7px; }
      .naeja-world-title strong { font-size:13px; }
      .naeja-world-title span { font-size:10px; }
      .naeja-world-btn { min-height:32px; padding:5px 8px; font-size:12px; }
      .naeja-world-body { padding:4px; }
      .naeja-map-stage { width:100%; max-height:100%; }
      .naeja-party-coin { width:38px; height:38px; }
      .naeja-world-status { left:8px; bottom:7px; font-size:10px; max-width:86%; }
    }
  `;
  document.head.appendChild(style);
}

function clamp01(value) { return Math.max(0, Math.min(1, value)); }

function normalizedPoint(event) {
  const rect = stage.getBoundingClientRect();
  return {
    x: clamp01((event.clientX - rect.left) / rect.width),
    y: clamp01((event.clientY - rect.top) / rect.height)
  };
}

function setPartyPosition(pos, persist = true) {
  party.style.left = `${clamp01(pos.x) * 100}%`;
  party.style.top = `${clamp01(pos.y) * 100}%`;
  if (persist) {
    const ui = loadJson(WORLD_UI_KEY, {});
    ui.party = { x: clamp01(pos.x), y: clamp01(pos.y) };
    saveJson(WORLD_UI_KEY, ui);
  }
  if (statusNode) statusNode.textContent = `WORLD • Party ${(pos.x * 100).toFixed(1)}%, ${(pos.y * 100).toFixed(1)}% • Atlas tiles ready`;
}

function bindPartyDrag() {
  let dragging = false;
  party.addEventListener('pointerdown', (event) => {
    event.preventDefault();
    event.stopPropagation();
    dragging = true;
    party.setPointerCapture?.(event.pointerId);
    party.style.cursor = 'grabbing';
  });
  party.addEventListener('pointermove', (event) => {
    if (!dragging) return;
    event.preventDefault();
    setPartyPosition(normalizedPoint(event), false);
  });
  const finish = (event) => {
    if (!dragging) return;
    dragging = false;
    party.style.cursor = 'grab';
    setPartyPosition(normalizedPoint(event), true);
  };
  party.addEventListener('pointerup', finish);
  party.addEventListener('pointercancel', () => { dragging = false; party.style.cursor = 'grab'; });
}

function worldObjectState() {
  const saved = loadJson(WORLD_OBJECTS_KEY, { instances: [] });
  if (!Array.isArray(saved.instances)) saved.instances = [];
  return saved;
}

function renderPlacedTiles() {
  if (!tileLayer) return;
  const saved = worldObjectState();
  tileLayer.innerHTML = '';
  saved.instances.forEach((instance) => {
    const asset = atlasAssets.find((row) => row.assetId === instance.assetId);
    if (!asset) return;
    const img = document.createElement('img');
    img.src = asset.derivedPath;
    img.alt = asset.name || '';
    img.className = 'naeja-atlas-instance';
    img.dataset.instanceId = instance.instanceId;
    img.style.left = `${clamp01(instance.x) * 100}%`;
    img.style.top = `${clamp01(instance.y) * 100}%`;
    img.style.width = `${Math.max(5, Math.min(24, instance.widthPct || 12))}%`;
    img.draggable = false;
    bindAtlasDrag(img, instance);
    tileLayer.appendChild(img);
  });
}

function bindAtlasDrag(node, instance) {
  let dragging = false;
  node.addEventListener('pointerdown', (event) => {
    event.preventDefault();
    event.stopPropagation();
    dragging = true;
    node.classList.add('is-selected');
    node.setPointerCapture?.(event.pointerId);
  });
  node.addEventListener('pointermove', (event) => {
    if (!dragging) return;
    const p = normalizedPoint(event);
    instance.x = p.x; instance.y = p.y;
    node.style.left = `${p.x * 100}%`;
    node.style.top = `${p.y * 100}%`;
  });
  node.addEventListener('pointerup', () => {
    if (!dragging) return;
    dragging = false;
    node.classList.remove('is-selected');
    const saved = worldObjectState();
    const target = saved.instances.find((item) => item.instanceId === instance.instanceId);
    if (target) { target.x = instance.x; target.y = instance.y; }
    saveJson(WORLD_OBJECTS_KEY, saved);
  });
}

function placeSelectedAsset(event) {
  if (!selectedAssetId) return false;
  const asset = atlasAssets.find((row) => row.assetId === selectedAssetId);
  if (!asset) return false;
  const p = normalizedPoint(event);
  const saved = worldObjectState();
  saved.instances.push({
    instanceId: `world-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    assetId: asset.assetId,
    x: p.x,
    y: p.y,
    widthPct: asset.layer === 'terrain' ? 18 : 10
  });
  saveJson(WORLD_OBJECTS_KEY, saved);
  selectedAssetId = null;
  renderPlacedTiles();
  renderPalette();
  statusNode.textContent = `Placed ${asset.name}. Drag it to adjust position.`;
  return true;
}

function renderPalette() {
  if (!tilePalette) return;
  tilePalette.innerHTML = '';
  const worldAssets = atlasAssets.filter((asset) => (asset.tags || []).includes('world_map') || asset.layer === 'terrain' || asset.layer === 'natural_landmark');
  worldAssets.forEach((asset) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `naeja-asset-card${selectedAssetId === asset.assetId ? ' is-selected' : ''}`;
    button.innerHTML = `<img src="${asset.thumbnailPath}" alt=""><span>${asset.name}</span>`;
    button.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      selectedAssetId = selectedAssetId === asset.assetId ? null : asset.assetId;
      renderPalette();
      statusNode.textContent = selectedAssetId ? `Tap Naeja to place ${asset.name}.` : 'Atlas placement cancelled.';
    });
    tilePalette.appendChild(button);
  });
}

async function loadAtlas() {
  try {
    const response = await fetch('data/atlas/atlas_asset_registry.json', { cache: 'no-store' });
    const registry = await response.json();
    atlasAssets = (registry.assets || []).filter((asset) => asset.enabled !== false && asset.derivedPath && asset.thumbnailPath);
    renderPalette();
    renderPlacedTiles();
    statusNode.textContent = `WORLD • ${atlasAssets.length} registered Atlas tiles ready • Party coin is draggable`;
  } catch (error) {
    statusNode.textContent = `WORLD • Naeja ready • Atlas registry failed: ${error.message}`;
  }
}

function resetWorld() {
  saveJson(WORLD_UI_KEY, { party: DEFAULT_PARTY });
  saveJson(WORLD_OBJECTS_KEY, { instances: [] });
  setPartyPosition(DEFAULT_PARTY, false);
  selectedAssetId = null;
  renderPalette();
  renderPlacedTiles();
  statusNode.textContent = 'WORLD reset • Naeja map preserved • Atlas placements cleared';
}

function createSurface() {
  const viewport = document.getElementById('mapViewport');
  if (!viewport || document.getElementById('naejaWorldSurface')) return;
  injectStyles();
  surface = document.createElement('section');
  surface.id = 'naejaWorldSurface';
  surface.setAttribute('aria-label', 'World of Naeja world map');
  surface.innerHTML = `
    <header class="naeja-world-head">
      <div class="naeja-world-title"><strong>WORLD OF NAEJA</strong><span>RIST • WORLD layer • Google Drive map + Atlas registry</span></div>
      <button class="naeja-world-btn" id="naejaTilesButton" type="button">Tiles</button>
      <button class="naeja-world-btn" id="naejaResetButton" type="button">Reset</button>
      <button class="naeja-world-btn" id="naejaTacticalButton" type="button">Tabletop</button>
    </header>
    <div class="naeja-world-body">
      <div class="naeja-map-stage" id="naejaMapStage">
        <img class="naeja-map-image" src="${NAEJA_WORLD_MAP}" alt="World of Naeja map">
        <div class="naeja-tile-layer" id="naejaTileLayer"></div>
        <button class="naeja-party-coin" id="naejaPartyCoin" type="button" aria-label="Party coin. Drag to move."></button>
      </div>
      <div class="naeja-world-status" id="naejaWorldStatus">WORLD • Loading Atlas tiles…</div>
      <div class="naeja-tile-palette" id="naejaTilePalette" hidden></div>
    </div>`;
  viewport.appendChild(surface);
  stage = surface.querySelector('#naejaMapStage');
  party = surface.querySelector('#naejaPartyCoin');
  tileLayer = surface.querySelector('#naejaTileLayer');
  tilePalette = surface.querySelector('#naejaTilePalette');
  statusNode = surface.querySelector('#naejaWorldStatus');
  const savedUi = loadJson(WORLD_UI_KEY, { party: DEFAULT_PARTY });
  setPartyPosition(savedUi.party || DEFAULT_PARTY, false);
  bindPartyDrag();
  stage.addEventListener('pointerup', (event) => {
    if (event.target.closest('.naeja-party-coin,.naeja-atlas-instance')) return;
    if (placeSelectedAsset(event)) return;
  });
  surface.querySelector('#naejaTilesButton').addEventListener('click', (event) => {
    event.preventDefault(); event.stopPropagation();
    tilePalette.hidden = !tilePalette.hidden;
    event.currentTarget.classList.toggle('is-active', !tilePalette.hidden);
  });
  surface.querySelector('#naejaResetButton').addEventListener('click', (event) => { event.preventDefault(); event.stopPropagation(); resetWorld(); });
  surface.querySelector('#naejaTacticalButton').addEventListener('click', (event) => {
    event.preventDefault(); event.stopPropagation();
    surface.hidden = true;
    closeLegacyOverlay();
  });
  const toolbar = document.querySelector('.toolbar-group-mode');
  if (toolbar && !document.getElementById('naejaWorldModeButton')) {
    const button = document.createElement('button');
    button.className = 'toolbar-button naeja-world-mode-button';
    button.id = 'naejaWorldModeButton';
    button.type = 'button';
    button.textContent = 'WORLD';
    button.addEventListener('click', () => { closeLegacyOverlay(); surface.hidden = false; establishWorldState(); });
    toolbar.prepend(button);
  }
  loadAtlas();
}

function bootWorld() {
  let attempts = 0;
  const timer = window.setInterval(() => {
    attempts += 1;
    if (window.shaelvienApp?.getState?.() && document.getElementById('mapViewport')) {
      window.clearInterval(timer);
      establishWorldState();
      createSurface();
      closeLegacyOverlay();
      document.title = 'ReLiCGameMaster • World of Naeja';
      const brand = document.querySelector('.brand-copy strong');
      if (brand) brand.textContent = 'ReLiCGameMaster • RIST';
    } else if (attempts > 120) {
      window.clearInterval(timer);
      console.error('Naeja WORLD surface could not attach to tabletop runtime.');
    }
  }, 50);
}

bootWorld();
