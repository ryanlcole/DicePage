const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const geometryPath = path.join(root, 'wwwroot', 'prototype', 'region-geometry-tools.js');
const hostPath = path.join(root, 'wwwroot', 'region-definer-host.js');
const contractPath = path.join(root, 'REGION_DEFINER_CONTRACT.md');

const geometry = fs.readFileSync(geometryPath, 'utf8');
const host = fs.readFileSync(hostPath, 'utf8');
const contract = fs.readFileSync(contractPath, 'utf8');

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
