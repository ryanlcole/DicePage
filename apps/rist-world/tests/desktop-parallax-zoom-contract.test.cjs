const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

const root=path.resolve(__dirname,'..');
const proto=fs.readFileSync(path.join(root,'wwwroot/prototype/prototype.js'),'utf8');
const index=fs.readFileSync(path.join(root,'wwwroot/prototype/index.html'),'utf8');

test('desktop All Parallax follows mouse without changing touch behavior',()=>{
  assert.match(proto,/function desktopMouseParallaxActive\(\)[\s\S]*?viewerTier==='all'[\s\S]*?DESKTOP_FINE_POINTER\.matches[\s\S]*?!REDUCED_MOTION\.matches/);
  assert.match(proto,/function updateDesktopMouseParallax\(event\)[\s\S]*?event\.pointerType!==\'mouse\'[\s\S]*?tiltTargetX=nx\*18;[\s\S]*?tiltTargetY=ny\*14;/);
  assert.match(proto,/stage\.addEventListener\('pointermove',[\s\S]*?updateDesktopMouseParallax\(e\)/);
  assert.match(proto,/stage\.addEventListener\('pointerleave',[\s\S]*?resetDesktopMouseParallax\(\)/);
});

test('desktop zoom remains pointer-centered and discoverable',()=>{
  assert.match(proto,/stage\.addEventListener\('wheel'[\s\S]*?zoomAt\(e\.clientX,e\.clientY/);
  assert.match(index,/mouse wheel or trackpad zooms toward the pointer/i);
  assert.match(index,/id="zoomOut"[\s\S]*?id="zoomIn"/);
});
