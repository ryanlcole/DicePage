const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const host=fs.readFileSync(path.join(root,'wwwroot','region-definer-host.js'),'utf8');
const tool=fs.readFileSync(path.join(root,'wwwroot','prototype','region-volume-tools.js'),'utf8');
const index=fs.readFileSync(path.join(root,'wwwroot','prototype','index.html'),'utf8');
const ui=fs.readFileSync(path.join(root,'Components','UniversalInterface.razor'),'utf8');

test('marker-first Region controller is valid classic JavaScript',()=>{
  assert.doesNotThrow(()=>new Function(tool));
});

test('new Region entry suppresses the retired tier preview before first paint',()=>{
  assert.match(index,/region-marker-preboot/);
  assert.match(index,/regionFlow/);
  assert.doesNotMatch(index,/region-selection-tools\.js/);
  assert.match(index,/region-volume-tools\.js\?v=20261009-force-region-marker-5/);
});

test('Region host loads bounded volume controller and preserves geometry persistence',()=>{
  assert.match(host,/region-volume-tools\.js/);
  assert.match(host,/CreateRegionGeometryFromPrototypeAsync/);
  assert.match(host,/GetRegionGeometryCatalogForPrototype/);
  assert.match(host,/const loaded=await ensureRegionTools\(frame\);/);
});

test('Region marker keeps one canonical World and defines X Y before Z',()=>{
  assert.match(tool,/phase:NEW_FLOW\?'xy':'existing'/);
  assert.match(tool,/canonicalMinX:b\.minX/);
  assert.match(tool,/canonicalMaxX:b\.maxX/);
  assert.match(tool,/canonicalMinY:b\.minY/);
  assert.match(tool,/canonicalMaxY:b\.maxY/);
  assert.match(tool,/minTierIndex:s\.minTier/);
  assert.match(tool,/maxTierIndex:s\.maxTier/);
  assert.match(tool,/showAllParallax/);
});

test('Region entry is intercepted before the generic legacy selector',()=>{
  const regionEntry=ui.indexOf('if(string.Equals(VisibleSpatialKind,"REGION",StringComparison.OrdinalIgnoreCase))');
  const legacyEntry=ui.indexOf('"beginSpatialSelection"');
  assert.ok(regionEntry>=0);
  assert.ok(legacyEntry>=0);
  assert.ok(regionEntry<legacyEntry);
  assert.match(ui,/_spatialDefinitionActive=false;[\s\S]*?_regionDefinerOpen=true;/);
});

test('Region flow rejects legacy hex save and browser prompt',()=>{
  assert.match(ui,/Legacy hex Region selection is retired/);
  assert.doesNotMatch(ui,/\"prompt\",\"Name this region\"/);
  assert.match(host,/Grid shape is internal compatibility metadata/);
  assert.match(host,/gridShape:controllerModeLabel\(phase\)/);
});
