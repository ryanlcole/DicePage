const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

const root=path.resolve(__dirname,'..');
const index=fs.readFileSync(path.join(root,'wwwroot/prototype/index.html'),'utf8');
const handoff=fs.readFileSync(path.join(root,'wwwroot/prototype/spatial-title-handoff.js'),'utf8');
const lock=fs.readFileSync(path.join(root,'wwwroot/prototype/spatial-selector-lock.js'),'utf8');

test('spatial helper scripts parse and load after canonical viewer',()=>{
  assert.doesNotThrow(()=>new Function(handoff));
  assert.doesNotThrow(()=>new Function(lock));
  const prototype=index.indexOf('prototype.js?v=20261004-continuous-space-2');
  const title=index.indexOf('spatial-title-handoff.js?v=20261004-spatial-title-1');
  const cameraLock=index.indexOf('spatial-selector-lock.js?v=20261004-map-selector-lock-1');
  assert.ok(prototype>=0);
  assert.ok(title>prototype);
  assert.ok(cameraLock>title);
});

test('spatial hex selector is map-space and preserves visible layer truth',()=>{
  assert.match(handoff,/world\.querySelectorAll\('\[data-tier\]\[data-layer\]'\)/);
  assert.match(handoff,/world\.appendChild\(overlay\)/);
  assert.match(handoff,/overlay\.dataset\.coordinateSpace='world-map'/);
  assert.match(handoff,/mapSelectionAnchor=freezeSelectionSnapshot\(initial\)/);
  assert.match(handoff,/getSpatialSelection:anchoredSnapshot/);
  assert.match(handoff,/visibleTierIndices:\[\.\.\.anchor\.visibleTierIndices\]/);
  assert.match(handoff,/visibleLayerOffsets:\[\.\.\.anchor\.visibleLayerOffsets\]/);
});

test('camera cannot redefine a live map selection',()=>{
  assert.match(handoff,/const ids=\['zoomIn','zoomOut','fit','settingsFit','tierToggle'\]/);
  assert.match(handoff,/addEventListener\('wheel',blockCameraMutationWhileSelecting/);
  assert.match(lock,/pointerType==='touch'/);
  assert.match(lock,/addEventListener\('touchmove',blockTouchCameraMove/);
  assert.match(lock,/\['\+','=','-','_','f','t'\]/);
});

test('spatial naming uses Labels editor and Enter, never native naming prompt',()=>{
  assert.match(handoff,/if\(String\(message\|\|''\)==='Name this space'\)return beginSpatialTitle\(defaultValue\)/);
  assert.doesNotMatch(handoff,/return nativePrompt\('Name this space'/);
  assert.match(handoff,/const center=selectionCenter\(snapshot\)/);
  assert.match(handoff,/Name this area · Enter to save/);
  assert.match(handoff,/if\(event\.key==='Enter'\)/);
  assert.match(handoff,/input\.dispatchEvent\(new KeyboardEvent\('keydown',\{key:'Enter'/);
  assert.match(handoff,/Title selected; adjust font and position/);
});
