const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const prototypeRoot=path.join(root,'wwwroot','prototype');
const text=file=>fs.readFileSync(file,'utf8');

test('legacy Region selector cannot restore hex/crop geography',()=>{
  const legacy=text(path.join(prototypeRoot,'region-selection-tools.js'));
  assert.match(legacy,/Retired compatibility shim/);
  assert.match(legacy,/bounded volume over the same World/);
  assert.doesNotMatch(legacy,/shadowShape\s*=\s*['"]hex['"]/);
});

test('Region controller exposes semantic bounded-volume modes instead of grid geography',()=>{
  const host=text(path.join(root,'wwwroot','region-definer-host.js'));
  assert.match(host,/case "xy":return "BOUNDS"/);
  assert.match(host,/case "z":return "Z"/);
  assert.match(host,/case "existing":return "REGION"/);
  assert.match(host,/gridShape:controllerModeLabel\(phase\)/);
  assert.doesNotMatch(host,/regionControllerToggleGrid/);
});

test('canonical Region tool defines X Y then Z and persists canonical bounds',()=>{
  const tool=text(path.join(prototypeRoot,'region-volume-tools.js'));
  assert.match(tool,/phase:NEW_FLOW\?'xy':'existing'/);
  assert.match(tool,/function cells\(\)/);
  assert.match(tool,/function boundary\(\)/);
  assert.match(tool,/canonicalMinX:b\.minX/);
  assert.match(tool,/canonicalMaxY:b\.maxY/);
  assert.match(tool,/minTierIndex:s\.minTier/);
  assert.match(tool,/maxTierIndex:s\.maxTier/);
  assert.match(tool,/type:'create-region',version:2/);
});
