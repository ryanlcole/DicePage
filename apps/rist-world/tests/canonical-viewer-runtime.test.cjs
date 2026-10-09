// Runtime contract tests for the embedded viewer. Universal controls live in the
// parent shell; this file must not require retired duplicate viewer buttons.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.join(__dirname,'../wwwroot/prototype');
const prototype=fs.readFileSync(path.join(root,'prototype.js'),'utf8');
const input=fs.readFileSync(path.join(root,'viewer-input.js'),'utf8');
const region=fs.readFileSync(path.join(root,'region-volume-tools.js'),'utf8');

test('canonical viewer scripts parse',()=>{
  assert.doesNotThrow(()=>new Function(prototype));
  assert.doesNotThrow(()=>new Function(input));
  assert.doesNotThrow(()=>new Function(region));
});

test('viewer retains pointer, wheel, keyboard and resize camera paths',()=>{
  assert.match(prototype,/addEventListener\('pointerdown'/);
  assert.match(prototype,/addEventListener\('pointermove'/);
  assert.match(prototype,/addEventListener\('wheel'/);
  assert.match(prototype,/addEventListener\('keydown'/);
  assert.match(prototype,/ResizeObserver/);
  assert.match(prototype,/function zoomCenter/);
  assert.match(prototype,/function applyTransform/);
});

test('viewer separates text input from map navigation',()=>{
  // Keyboard camera navigation is owned by viewer-input.js. It is intentionally
  // fail-closed: only the focused stage may consume navigation keys, so native
  // inputs, selects, textareas and buttons retain their own keyboard behavior.
  assert.match(input,/event\.target!==stage/);
  assert.match(input,/doc\.activeElement!==stage/);
  assert.match(input,/event\.ctrlKey\|\|event\.metaKey\|\|event\.altKey/);
  assert.match(prototype,/button,input,select,textarea,a\[href\],\[contenteditable\]/);
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
