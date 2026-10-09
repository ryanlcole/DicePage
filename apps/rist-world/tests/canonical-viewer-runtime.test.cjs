// Runtime contract tests for the embedded viewer. The universal controller is the
// canonical RIST interaction surface. Keyboard/pointer adapters may remain for
// accessibility or legacy compatibility, but they must not define the active UI.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.join(__dirname,'../wwwroot/prototype');
const appRoot=path.join(__dirname,'..');
const prototype=fs.readFileSync(path.join(root,'prototype.js'),'utf8');
const region=fs.readFileSync(path.join(root,'region-volume-tools.js'),'utf8');
const semantic=fs.readFileSync(path.join(appRoot,'UniversalSemanticControls.cs'),'utf8');
const host=fs.readFileSync(path.join(appRoot,'wwwroot/region-definer-host.js'),'utf8');

test('canonical viewer scripts parse',()=>{
  assert.doesNotThrow(()=>new Function(prototype));
  assert.doesNotThrow(()=>new Function(region));
  assert.doesNotThrow(()=>new Function(host.replace(/^export /gm,'')));
});

test('universal controller owns canonical navigation and actions',()=>{
  assert.match(semantic,/touch\.analog-x[^\n]*Action\.NavigateX/);
  assert.match(semantic,/touch\.analog-y[^\n]*Action\.NavigateY/);
  assert.match(semantic,/touch\.left-display[^\n]*Action\.Secondary/);
  assert.match(semantic,/touch\.right-display[^\n]*Action\.Primary/);
  assert.match(semantic,/touch\.analog-press[^\n]*Action\.Select/);
});

test('Region controller exposes semantic state without HEX or SQUARE geography',()=>{
  assert.match(host,/Grid shape is internal compatibility metadata/);
  assert.match(host,/case "xy":return "BOUNDS"/);
  assert.match(host,/controllerPrimary/);
  assert.match(host,/controllerStep/);
  assert.match(host,/controllerSelect/);
  assert.match(region,/getRegionControllerState/);
  assert.match(region,/regionControllerPrimary/);
});

test('view-only and claim-only modes fail closed for authoritative edits',()=>{
  assert.match(prototype,/const READ_ONLY=ACCESS_MODE==='view'/);
  assert.match(prototype,/const CLAIM_ONLY=ACCESS_MODE==='claim'/);
  assert.match(prototype,/persistentSave\.disabled=true/);
  assert.match(prototype,/imageUploadToggle\.disabled=true/);
});

test('Region resume restores the same World after iOS visibility changes',()=>{
  assert.match(region,/document\.addEventListener\('visibilitychange',resume\)/);
  assert.match(region,/window\.addEventListener\('pageshow',resume\)/);
  assert.match(region,/window\.addEventListener\('focus',resume\)/);
  assert.match(region,/world\.style\.visibility='visible'/);
  assert.match(region,/showAllParallax/);
});
