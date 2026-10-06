const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const geometryPath = path.join(root, 'wwwroot', 'prototype', 'region-geometry-tools.js');
const hostPath = path.join(root, 'wwwroot', 'region-definer-host.js');
const contractPath = path.join(root, 'REGION_DEFINER_CONTRACT.md');
const uiPath = path.join(root, 'Components', 'UniversalInterface.razor');

const geometry = fs.readFileSync(geometryPath, 'utf8');
const host = fs.readFileSync(hostPath, 'utf8');
const contract = fs.readFileSync(contractPath, 'utf8');
const ui = fs.readFileSync(uiPath, 'utf8');

test('Region Definer geometry helper is valid classic JavaScript', () => {
  assert.doesNotThrow(() => new Function(geometry));
});

test('Region Definer v2 keeps crop, border, angle, tiers, and grid authority distinct', () => {
  assert.match(geometry, /phase:NEW_FLOW\?'focus':'existing'/);
  assert.match(geometry, /borderTool:'line'/);
  assert.match(geometry, /\['line','LINE'\],\['pencil','PENCIL'\],\['magic','MAGIC SELECT'\]/);
  assert.match(geometry, /fitFocus\(60\)/);
  assert.match(geometry, /viewAngle:60/);
  assert.match(geometry, /visibleTierIndices/);
  assert.match(geometry, /Geography definition is gridless/);
});

test('Region Definer host loads geometry v2 and preserves one-map persistence', () => {
  assert.match(host, /region-geometry-tools\.js\?v=20261006-region-border-1/);
  assert.match(host, /CreateRegionGeometryFromPrototypeAsync/);
  assert.match(host, /GetRegionGeometryCatalogForPrototype/);
});

test('Region Definer contract says crop is view scope and 60 degree region view', () => {
  assert.match(contract, /Crop is view\/edit scope, never a duplicated map\./);
  assert.match(contract, /Region presentation after border confirmation is 60°\./);
  assert.match(contract, /Geography authoring is gridless to the user/);
  assert.match(contract, /Cursor selection and touch selection are equivalent semantic inputs\./);
});

test('Region entry is intercepted before the generic legacy hex selector', () => {
  const regionEntry = ui.indexOf('if(string.Equals(VisibleSpatialKind,"REGION",StringComparison.OrdinalIgnoreCase))');
  const legacyHexEntry = ui.indexOf('"beginSpatialSelection"');
  assert.ok(regionEntry >= 0, 'Region geometry entry guard must exist');
  assert.ok(legacyHexEntry >= 0, 'Legacy selector remains available for non-Region scopes');
  assert.ok(regionEntry < legacyHexEntry, 'Region must be routed before the legacy selector');
  assert.match(ui, /_spatialDefinitionActive=false;[\s\S]*?_regionDefinerOpen=true;/);
});

test('Region flow rejects legacy hex save and browser prompt', () => {
  assert.match(ui, /Legacy hex Region selection is retired/);
  assert.doesNotMatch(ui, /\"prompt\",\"Name this region\"/);
  assert.match(ui, /_builderChainIndex=1;_requestedBuilderChainIndex=1;_assetScope=\"REGION\";_stage=Stage.SpatialSelect/);
  assert.doesNotMatch(ui, /Continuing into Local inside the same recursive viewer/);
});

test('Region host waits for loaded iframe before geometry injection', () => {
  assert.match(host, /const initial=await waitForPrototype\(frame\);/);
  assert.match(host, /if\(!initial\)return null;/);
  assert.match(host, /const loaded=await ensureRegionGeometryTools\(frame\);/);
});

test('Region tier analog movement cannot save the Region', () => {
  assert.match(geometry, /if\(state\.phase==='tiers'\)\{[\s\S]*?state\.tierCursor=wrap\(state\.tierCursor\+direction,[\s\S]*?return true;/);
  assert.match(geometry, /if\(state\.phase==='tiers'\)\{[\s\S]*?state\.visibleTiers\.has\(tier\)[\s\S]*?applyVisibleTiers\(\)/);
  const stepStart = geometry.indexOf('function controllerStep(axis,direction)');
  const nextFunction = geometry.indexOf('function ', stepStart + 9);
  const stepBody = geometry.slice(stepStart, nextFunction > stepStart ? nextFunction : undefined);
  assert.doesNotMatch(stepBody, /saveRegion|SAVE REGION|primaryAction/);
});
