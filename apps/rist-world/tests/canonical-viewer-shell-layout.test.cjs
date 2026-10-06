const fs=require('fs');
const path=require('path');
const test=require('node:test');
const assert=require('node:assert/strict');

const root=path.resolve(__dirname,'..');
const read=(relative)=>fs.readFileSync(path.join(root,relative),'utf8');
const razor=read('Components/UniversalInterface.razor');
const css=read('wwwroot/css/universal-interface.css');

test('landscape mode prioritizes viewer visibility with a compact control deck',()=>{
  assert.match(css,/@media \(orientation:landscape\) and \(max-height:640px\)/);
  assert.match(css,/\.universal-interface\{[\s\S]*?grid-template-rows:minmax\(0,1fr\) clamp\(112px,24vh,154px\)!important/);
  assert.match(css,/\.universal-controller\.single-analog-deck\{[\s\S]*?grid-template-columns:minmax\(0,1fr\) clamp\(76px,14vw,96px\) minmax\(0,1fr\)!important/);
  assert.match(css,/\.single-analog-deck \.analog-pad\{[\s\S]*?width:min\(100%,76px\)!important/);
  assert.match(css,/\.single-analog-deck button\.control-display-button>span\{[\s\S]*?display:none!important/);
});


test('universal analog stick press acts as the semantic Select control',()=>{
  const razor=read('Components/UniversalInterface.razor');
  const semantic=read('Components/UniversalInterface.SemanticControls.cs');
  const input=read('wwwroot/universal-interface-input.js');

  assert.match(razor,/data-analog-select="true"/);
  assert.match(razor,/data-semantic-action="@UniversalSemanticControls\.Action\.Select"/);
  assert.match(razor,/ReceiveSemanticHardwareInputAsync\(control,direction\)/);
  assert.match(semantic,/case UniversalSemanticControls\.Action\.Select:[\s\S]{0,120}?await SelectSemanticAsync\(\)/);
  const selectStart=semantic.indexOf('async Task SelectSemanticAsync()');
  const dispatchStart=semantic.indexOf('async Task DispatchSemanticActionAsync',selectStart);
  assert.ok(selectStart>=0&&dispatchStart>selectStart,'SelectSemanticAsync must remain a bounded semantic dispatcher');
  const selectBody=semantic.slice(selectStart,dispatchStart);
  assert.match(selectBody,/Stage\.BrowsePlace[\s\S]*?ActivateBrowseCursorTargetAsync\(\)/);
  assert.match(selectBody,/Stage\.SpatialSelect[\s\S]*?_regionDefinerOpen[\s\S]*?SelectRegionDefinerAsync\(\)/);
  assert.match(input,/const ANALOG_SELECT_RADIUS = 0\.46;/);
  assert.match(input,/const ANALOG_SELECT_MOVE_PX = 10;/);
  assert.match(input,/if \(shouldSelect\) invoke\("select"\);/);
  assert.match(input,/edgeButton\(gamepad, 10, "select"\);/);
  assert.match(input,/event\.key !== "Enter" && event\.key !== " "/);
});

test('portrait builder keeps source content in the vertical center and corner PIPs translucent',()=>{
  assert.match(css,/@media \(orientation:portrait\)/);
  assert.match(css,/\.universal-viewer-main\{[\s\S]*?align-items:center/);
  assert.match(css,/\.viewer-pip\{[\s\S]*?opacity:/);
});

test('START opens the existing settings menu without duplicating settings',()=>{
  assert.match(razor,/HandleStartButtonAsync/);
  assert.match(razor,/StartMenuOpen/);
  assert.doesNotMatch(razor,/START SETTINGS[\s\S]*START SETTINGS/);
});

test('Browse cursor and analog press target the thumbnail beneath the reticle',()=>{
  assert.match(razor,/ActivateBrowseCursorTargetAsync/);
  assert.match(razor,/BrowsePlace/);
  assert.match(razor,/cursor/i);
});
