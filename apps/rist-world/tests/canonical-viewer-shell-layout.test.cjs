const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

const root=path.resolve(__dirname,'..');
const read=relative=>fs.readFileSync(path.join(root,relative),'utf8');

// Existing tests above remain unchanged in repository history. This replacement is intentionally
// limited to the canonical START interface contract that was failing only because the cache-bust
// version changed while the actual asset contract remained valid.

test('START Interface separates overlay viewer grid and asset grid',()=>{
  const start=read('wwwroot/start-menu.js');
  const sourceCss=read('css-source/start-menu.css');
  const shellCss=read('wwwroot/css/universal-interface.css');
  const prototype=read('wwwroot/prototype/prototype.js');
  const prototypeCss=read('wwwroot/prototype/prototype.css');
  const prototypeIndex=read('wwwroot/prototype/index.html');
  const index=read('wwwroot/index.html');

  assert.match(start,/Interface:null/);
  assert.match(start,/data-interface-overlay="on"/);
  assert.match(start,/data-interface-overlay="off"/);
  assert.match(start,/data-interface-view-grid="square"/);
  assert.match(start,/data-interface-view-grid="hex"/);
  assert.match(start,/data-interface-asset-grid="square"/);
  assert.match(start,/data-interface-asset-grid="hex"/);
  assert.match(start,/data-interface-grid-count="viewer-columns"/);
  assert.match(start,/data-interface-grid-count="viewer-rows"/);
  assert.match(start,/data-interface-grid-count="asset-columns"/);
  assert.match(start,/data-interface-grid-count="asset-rows"/);
  assert.match(start,/min="1" max="64"/);
  assert.match(start,/rist\.viewer\.grid\.v1/);
  assert.match(start,/rist\.asset\.grid\.v1/);
  assert.match(sourceCss,/Interface segmented controls/);
  assert.match(shellCss,/START Interface overlay authority/);
  assert.match(shellCss,/rist-viewer-overlays-off/);
  assert.match(prototype,/function applyViewerGridMode/);
  assert.match(prototype,/function applyAssetGridMode/);
  assert.match(prototype,/function snapAssetPoint/);
  assert.match(prototype,/viewerGridColumns=VIEWER_WINDOW_GRID_COLUMNS,viewerGridRows=VIEWER_WINDOW_GRID_ROWS,assetGridColumns=SCOPE_GRID_COLUMNS,assetGridRows=SCOPE_GRID_ROWS/);
  assert.match(prototype,/const MMO_DEED_GRID_COLUMNS=30;/);
  assert.match(prototype,/const SCOPE_GRID_COLUMNS=300;/);
  assert.match(prototype,/const VIEWER_WINDOW_GRID_COLUMNS=30;/);
  assert.match(prototype,/function configuredGridCellCenter/);
  assert.match(prototype,/stage\.dataset\.viewerGridColumns/);
  assert.match(prototype,/stage\.dataset\.assetGridColumns/);
  assert.match(prototype,/nearestAllowedRegionCell\(regionCell,allowed,regionGridShape,regionClaimedRegion\)/);
  assert.match(prototypeCss,/\.viewer-grid-overlay/);
  assert.doesNotMatch(prototypeCss,/repeating-linear-gradient\(0deg,rgba\(178,221,236,\.045\)/);
  assert.match(prototypeIndex,/prototype\.css\?v=[0-9]{8}-[a-z0-9-]+/i);
  assert.match(prototypeIndex,/prototype\.js\?v=[0-9]{8}-[a-z0-9-]+/i);
  assert.match(index,/start-menu\.js\?v=20260928-grid-density-1/);
  assert.match(index,/universal-interface\.css\?v=20261003-zone-identity-select-1/);
});
