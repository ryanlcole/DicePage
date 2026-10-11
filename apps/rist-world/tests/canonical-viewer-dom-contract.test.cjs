'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const root = path.resolve(__dirname, '..');
const index = fs.readFileSync(path.join(root, 'wwwroot', 'prototype', 'index.html'), 'utf8');
const runtime = fs.readFileSync(path.join(root, 'wwwroot', 'prototype', 'prototype.js'), 'utf8');

const requiredIds = [
  'stage', 'world', 'surfacePlane', 'highlandsPlane', 'mountainPlane', 'loading',
  'persistentSave', 'home', 'imageUploadToggle', 'tierToggle', 'tierGlyph',
  'keyboardToggle', 'settingsToggle', 'zoomOut', 'zoomIn', 'fit', 'tierMenu',
  'viewerSettingsPanel', 'viewerSettingsClose', 'settingsFit', 'settingsResetTilt',
  'viewAngleSelect', 'settingsUpscale', 'settingsUpscaleLabel', 'settingsStartMenu',
  'imageUploadPanel', 'imageUploadClose', 'imagePlacementRole', 'imagePlacementHint',
  'imagePositionGrid', 'imageDropzone', 'imageBrowse', 'imageFile', 'imageX', 'imageY',
  'imageTier', 'imageLayer', 'imageTransparency', 'spriteUploadPanel',
  'spriteUploadClose', 'spriteDropzone', 'spriteBrowse', 'spriteFile', 'spriteColumns',
  'spriteRows', 'spriteFps', 'spriteFrameCount', 'viewerKeyboard', 'keyboardTabs',
  'keyboardKeys', 'keyboardClose', 'live'
];

test('prototype HTML preserves the DOM contract required by prototype.js', () => {
  for (const id of requiredIds) {
    assert.match(index, new RegExp(`id=["']${id}["']`), `missing required viewer DOM id: ${id}`);
  }
});

test('canonical Endemar plane nodes exist before prototype runtime starts', () => {
  assert.match(runtime, /\$\('surfacePlane'\)/, 'runtime must consume surfacePlane');
  assert.match(runtime, /\$\('highlandsPlane'\)/, 'runtime must consume highlandsPlane');
  assert.match(runtime, /\$\('mountainPlane'\)/, 'runtime must consume mountainPlane');
  assert.ok(index.indexOf('id="surfacePlane"') < index.indexOf('prototype.js'), 'surfacePlane must exist before runtime execution');
  assert.ok(index.indexOf('id="highlandsPlane"') < index.indexOf('prototype.js'), 'highlandsPlane must exist before runtime execution');
  assert.ok(index.indexOf('id="mountainPlane"') < index.indexOf('prototype.js'), 'mountainPlane must exist before runtime execution');
});
