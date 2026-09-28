const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

const root=path.resolve(__dirname,'..');
const read=relative=>fs.readFileSync(path.join(root,relative),'utf8');

test('Browser Back authority is not a visible or grid-flow control',()=>{
  const razor=read('Components/ExperimentsWorkspace.razor');
  const css=read('wwwroot/css/experiments-universal-suite.css');

  assert.match(
    razor,
    /class="experiments-browser-back"[\s\S]{0,220}?data-browser-back="experiments"[\s\S]{0,220}?hidden/
  );
  assert.match(
    css,
    /\.experiments-browser-back\s*\{[\s\S]*?display:none!important;[\s\S]*?\}/
  );
});

test('Browser Back authority remains connected to the experiments shell',()=>{
  const bridge=read('wwwroot/browser-back-authority.js');
  assert.match(bridge,/\.experiments-shell \[data-browser-back="experiments"\]/);
  assert.match(bridge,/target\.click\(\)/);
});


test('landscape mode prioritizes viewer visibility with a compact control deck',()=>{
  const css=read('wwwroot/css/experiments-universal-suite.css');
  assert.match(css,/Compact landscape visibility authority/);
  assert.match(css,/@media \(orientation:landscape\) and \(max-height:620px\)/);
  assert.match(css,/grid-template-rows:minmax\(0,1fr\) clamp\(92px,26dvh,112px\)!important/);
  assert.match(css,/grid-template-columns:minmax\(0,1fr\) clamp\(76px,14vw,96px\) minmax\(0,1fr\)!important/);
  assert.match(css,/\.single-analog-deck \.analog-pad\{[\s\S]*?width:min\(100%,76px\)!important/);
  assert.match(css,/\.single-analog-deck button\.control-display-button>span\{[\s\S]*?display:none!important/);
});


test('universal analog stick press acts as the primary Select control',()=>{
  const razor=read('Components/ExperimentsWorkspace.razor');
  const input=read('wwwroot/experiments-universal-input.js');

  assert.match(razor,/data-analog-select="true"/);
  assert.match(razor,/case "select": await PressLeft\(\); break;/);
  assert.match(input,/const ANALOG_SELECT_RADIUS = 0\.46;/);
  assert.match(input,/const ANALOG_SELECT_MOVE_PX = 10;/);
  assert.match(input,/if \(shouldSelect\) invoke\("select"\);/);
  assert.match(input,/edgeButton\(gamepad, 10, "select"\);/);
  assert.match(input,/event\.key !== "Enter" && event\.key !== " "/);
});

test('portrait builder keeps source content in the vertical center and corner PIPs translucent',()=>{
  const css=read('wwwroot/css/experiments-universal-suite.css');
  const index=read('wwwroot/index.html');

  assert.match(css,/Analog Select \+ four-corner pip safe-center authority/);
  assert.match(
    css,
    /\.depth-pip,[\s\S]*?\.asset-context-pip\.minimized\{[\s\S]*?opacity:\.76!important;/
  );
  assert.match(
    css,
    /@media\(max-width:700px\) and \(orientation:portrait\)\{[\s\S]*?\.experiments-worldbuilder-viewer \.asset-source-explorer\{[\s\S]*?top:144px!important;[\s\S]*?bottom:82px!important;/
  );
  assert.match(css,/grid-template-columns:repeat\(auto-fit,minmax\(82px,1fr\)\)!important;/);
  assert.match(
    css,
    /@media\(max-width:430px\) and \(orientation:portrait\)\{[\s\S]*?grid-template-columns:repeat\(3,minmax\(0,1fr\)\)!important;/
  );
  assert.match(index,/experiments-universal-suite\.css\?v=20260928-browse-cursor-start-1/);
  assert.match(index,/experiments-universal-input\.js\?v=20260928-browse-cursor-start-1/);
});


test('START opens the existing settings menu without duplicating settings',()=>{
  const razor=read('Components/ExperimentsWorkspace.razor');
  const css=read('wwwroot/css/experiments-universal-suite.css');
  const index=read('wwwroot/index.html');

  assert.match(razor,/class="analog-start-button"[\s\S]{0,180}?@onclick="OpenStartMenuAsync"[\s\S]{0,180}?>START<\/button>/);
  assert.match(razor,/await JS\.InvokeVoidAsync\("RistStartMenu\.open"\)/);
  assert.doesNotMatch(razor,/<h2>Video<\/h2>|<h2>Picture<\/h2>|<h2>Sound<\/h2>|<h2>Effects<\/h2>/);
  assert.match(css,/body\.rist-start-open \.rist-start-overlay\{[\s\S]*?z-index:2147483600!important/);
  assert.match(index,/start-menu\.js/);
});

test('Browse SELECT arms cursor and analog press targets the thumbnail beneath the reticle',()=>{
  const razor=read('Components/ExperimentsWorkspace.razor');
  const input=read('wwwroot/experiments-universal-input.js');
  const index=read('wwwroot/index.html');

  assert.match(razor,/bool _browseCursorActive;/);
  assert.match(razor,/_stage!=Stage\.BrowsePlace\|\|_browseCursorActive/);
  assert.match(razor,/case Stage\.BrowsePlace:[\s\S]*?if\(!_browseCursorActive\)[\s\S]*?_browseCursorActive=true;/);
  assert.match(razor,/if\(_stage==Stage\.BrowsePlace&&_browseCursorActive\)await ActivateBrowseCursorTargetAsync\(\)/);
  assert.match(input,/function activateCursorTarget\(\)/);
  assert.match(input,/document\.elementFromPoint/);
  assert.match(input,/\.asset-source-explorer \.linked-asset/);
  assert.match(input,/target\.click\(\)/);
  assert.match(input,/event\.target instanceof Element && event\.target\.closest\("\.analog-start-button"\)/);
  assert.match(index,/experiments-universal-suite\.css\?v=20260928-browse-cursor-start-1/);
  assert.match(index,/experiments-universal-input\.js\?v=20260928-browse-cursor-start-1/);
});
