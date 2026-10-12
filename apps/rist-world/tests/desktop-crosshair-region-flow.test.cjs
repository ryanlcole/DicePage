const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

const root=path.resolve(__dirname,'..');
const index=fs.readFileSync(path.join(root,'wwwroot/prototype/index.html'),'utf8');
const js=fs.readFileSync(path.join(root,'wwwroot/prototype/crosshair-zoom.js'),'utf8');
const css=fs.readFileSync(path.join(root,'wwwroot/prototype/crosshair-zoom.css'),'utf8');

test('desktop crosshair zoom is isolated from canonical viewer implementation',()=>{
  assert.match(index,/crosshair-zoom\.css\?v=20261011-crosshair-zoom-1/);
  assert.match(index,/prototype\.js\?v=20261011-crosshair-zoom-1[\s\S]*crosshair-zoom\.js\?v=20261011-crosshair-zoom-1/);
  assert.match(js,/desktop-crosshair-camera/);
  assert.match(js,/function applyFrameZoom\(\)/);
  assert.match(js,/Camera changed; spatial identity did not/);
  assert.doesNotMatch(js,/setExternalDepth\(/);
});

test('crosshair supports move, resize and outer gutter zoom-out',()=>{
  assert.match(js,/beginFramePointer\(event,'move'\)/);
  assert.match(js,/beginFramePointer\(event,'resize'\)/);
  assert.match(js,/function zoomOutOne\(\)/);
  assert.match(js,/data-zoom-out/);
  assert.match(css,/desktop-crosshair-handle[\s\S]*nwse-resize/);
  assert.match(css,/desktop-crosshair-gutter-strip/);
});

test('SELECT creates color candidate and entering explicitly advances spatial scope',()=>{
  assert.match(js,/function drawCandidate\(\)/);
  assert.match(css,/desktop-spatial-dimmer[\s\S]*grayscale\(1\)/);
  assert.match(js,/desktop-spatial-color-window/);
  assert.match(js,/function enterCandidate\(\)[\s\S]*postExplicitScope\(target\)/);
  assert.match(js,/setTopSelectLabel\('DESELECT'\)/);
  assert.match(js,/function deselectEntered\(\)[\s\S]*postExplicitScope\(priorScope\)[\s\S]*setTopSelectLabel\('SELECT'\)/);
});

test('recursive scope order remains WORLD REGION LOCAL INSTANCE',()=>{
  assert.match(js,/\['WORLD','REGION','LOCAL','INSTANCE'\]/);
  assert.match(js,/scopeAngle=\{WORLD:0,REGION:15,LOCAL:30,INSTANCE:45\}/);
  assert.match(js,/scopePrefix=\{WORLD:'Z',REGION:'R',LOCAL:'L',INSTANCE:'I'\}/);
});
