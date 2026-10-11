const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

const root=path.resolve(__dirname,'..');
const adapter=fs.readFileSync(path.join(root,'wwwroot/desktop-controller-adapter.js'),'utf8');
const viewerInput=fs.readFileSync(path.join(root,'wwwroot/prototype/viewer-input.js'),'utf8');
const appIndex=fs.readFileSync(path.join(root,'wwwroot/index.html'),'utf8');

test('desktop controller adapter is loaded after universal input',()=>{
  assert.match(appIndex,/universal-interface-input\.js[\s\S]*desktop-controller-adapter\.js/);
});

test('desktop uses D-pad presentation unless connected gamepad has analog axes',()=>{
  assert.match(adapter,/function hasAnalogStick\(\)[\s\S]*axes\.length>=2/);
  assert.match(adapter,/analogCapable\?'analog':'dpad'/);
  assert.match(adapter,/classList\.toggle\('hardware-dpad',desktop&&!analogCapable\)/);
});

test('desktop gamepad stays semantic and does not own cursor',()=>{
  assert.match(adapter,/mouse owns cursor behavior/i);
  assert.match(adapter,/if\(desktop&&pads\(\)\.length\)node\.classList\.add\('paging-mode'\)/);
  assert.match(adapter,/\.rist-desktop-input \.viewer-reticle\{display:none!important\}/);
});

test('zoom bar exists only for desktop laptop fine pointer presentation',()=>{
  assert.match(viewerInput,/installDesktopZoomBar/);
  assert.match(viewerInput,/\(hover: hover\) and \(pointer: fine\)/);
  assert.match(viewerInput,/if\(!shouldShow\)\{bar\?\.remove\(\);bar=null;range=null;return;\}/);
  assert.match(viewerInput,/id='desktopZoomBar'/);
  assert.match(viewerInput,/type="range"/);
  assert.match(viewerInput,/zoom\(next>previous\?1\.08:1\/1\.08\)/);
});
