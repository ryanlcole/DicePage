const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const prototypeRoot = path.join(root, 'wwwroot', 'prototype');

function text(file) {
  return fs.readFileSync(file, 'utf8');
}

test('legacy Region selector cannot restore hex/crop geography', () => {
  const legacy = text(path.join(prototypeRoot, 'region-selection-tools.js'));
  assert.match(legacy, /Retired compatibility shim/);
  assert.match(legacy, /bounded volume over the same World/);
  assert.doesNotMatch(legacy, /shadowShape\s*=\s*['"]hex['"]/);
  assert.doesNotMatch(legacy, /maskImageNode\s*=/);
});

test('Region controller exposes semantic bounded-volume modes instead of grid shape', () => {
  const host = text(path.join(root, 'wwwroot', 'region-definer-host.js'));
  assert.match(host, /case "xy":return "BOUNDS"/);
  assert.match(host, /case "z":return "Z"/);
  assert.match(host, /case "save":return "60°"/);
  assert.match(host, /case "existing":return "REGION"/);
  assert.match(host, /gridShape:controllerModeLabel\(phase\)/);
  assert.doesNotMatch(host, /regionControllerToggleGrid/);
});

test('canonical Region tool defines X Y then Z and stores cells as derived compatibility metadata', () => {
  const tool = text(path.join(prototypeRoot, 'region-volume-tools.js'));
  assert.match(tool, /phase:NEW_FLOW\?'xy':'existing'/);
  assert.match(tool, /function derivedCells\(\)/);
  assert.match(tool, /volumeModel:'BOUNDED_WORLD_VOLUME'/);
  assert.match(tool, /canonicalMinX:b\.minX/);
  assert.match(tool, /canonicalMaxY:b\.maxY/);
  assert.match(tool, /minTierIndex:state\.minTierIndex/);
  assert.match(tool, /maxTierIndex:state\.maxTierIndex/);
  assert.match(tool, /viewAngle:60/);
});
