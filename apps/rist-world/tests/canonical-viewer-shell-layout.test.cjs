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
  assert.match(
    razor,
    /case "select":[\s\S]{0,260}?if\(_stage==Stage\.BrowsePlace&&CursorMode\)await ActivateBrowseCursorTargetAsync\(\);[\s\S]{0,120}?else await PressLeft\(\);/
  );
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
  assert.match(index,/experiments-universal-suite\.css\?v=20260928-experiment-boot-1/);
  assert.match(index,/experiments-universal-input\.js\?v=20260928-cursor-assets-1/);
});


test('START opens the existing settings menu without duplicating settings',()=>{
  const razor=read('Components/ExperimentsWorkspace.razor');
  const css=read('wwwroot/css/experiments-universal-suite.css');
  const index=read('wwwroot/index.html');

  assert.match(razor,/class="analog-start-button"[\s\S]{0,220}?@onclick="HandleStartButtonAsync"[\s\S]{0,220}?>START<\/button>/);
  assert.match(razor,/HandleStartButtonAsync\(\)[\s\S]*?await OpenStartMenuAsync\(\)/);
  assert.match(razor,/await JS\.InvokeVoidAsync\("RistStartMenu\.open","experiment"\)/);
  assert.doesNotMatch(razor,/<h2>Video<\/h2>|<h2>Picture<\/h2>|<h2>Sound<\/h2>|<h2>Effects<\/h2>/);
  assert.match(css,/body\.rist-start-open \.rist-start-overlay\{[\s\S]*?z-index:2147483600!important/);
  assert.match(index,/start-menu\.js/);
});

test('Browse cursor and analog press target the thumbnail beneath the reticle',()=>{
  const razor=read('Components/ExperimentsWorkspace.razor');
  const input=read('wwwroot/experiments-universal-input.js');
  const index=read('wwwroot/index.html');

  assert.match(razor,/bool _browseCursorActive;/);
  assert.match(razor,/bool CursorAvailable=>!IsPathDrivenStage&&LeftDisplayOptionCount<=1&&RightDisplayOptionCount<=1;/);
  assert.match(razor,/bool CursorMode=>CursorAvailable[\s\S]{0,120}?!_analogButtonMode/);
  assert.match(razor,/case Stage\.BrowsePlace:[\s\S]{0,360}?_browseCursorActive=true;[\s\S]{0,120}?_analogButtonMode=false;/);
  assert.match(razor,/if\(_stage==Stage\.BrowsePlace&&CursorMode\)await ActivateBrowseCursorTargetAsync\(\)/);
  assert.match(input,/function activateCursorTarget\(\)/);
  assert.match(input,/document\.elementFromPoint/);
  assert.match(input,/\.asset-source-explorer \.linked-asset/);
  assert.match(input,/target\.click\(\)/);
  assert.match(input,/event\.target instanceof Element && event\.target\.closest\("\.analog-start-button,\.analog-mode-button"\)/);
  assert.match(index,/experiments-universal-suite\.css\?v=20260928-experiment-boot-1/);
  assert.match(index,/experiments-universal-input\.js\?v=20260928-cursor-assets-1/);
});


test('analog top button switches CURSOR and BUTTONS without changing START',()=>{
  const razor=read('Components/ExperimentsWorkspace.razor');
  const input=read('wwwroot/experiments-universal-input.js');
  const css=read('wwwroot/css/experiments-universal-suite.css');

  assert.match(razor,/class="analog-mode-button"[\s\S]{0,360}?@onclick="ToggleAnalogMode"[\s\S]{0,420}?@AnalogModeLabel<\/button>/);
  assert.match(razor,/string AnalogModeLabel=>CursorMode\?"CURSOR":"BUTTONS"/);
  assert.match(razor,/void ToggleAnalogMode\(\)[\s\S]*?_analogButtonMode=true;[\s\S]*?_analogButtonMode=false;/);
  assert.match(razor,/case Stage\.BrowsePlace:[\s\S]*?_analogButtonMode=false;[\s\S]*?Cursor active/);
  assert.match(razor,/class="analog-start-button"[\s\S]*?@onclick="HandleStartButtonAsync"/);
  assert.match(input,/\.analog-start-button,\.analog-mode-button/);
  assert.match(css,/Analog mode toggle authority/);
});


test('viewer cursor uses existing Shaelvien cursor assets on touch and pointer devices',()=>{
  const razor=read('Components/ExperimentsWorkspace.razor');
  const input=read('wwwroot/experiments-universal-input.js');
  const cursors=read('wwwroot/cursors-haptics.js');
  const css=read('wwwroot/css/experiments-universal-suite.css');
  const index=read('wwwroot/index.html');

  assert.match(razor,/class="viewer-reticle" data-cursor-role="pointer"/);
  assert.match(cursors,/--rist-cursor-image-\$\{name\}/);
  assert.match(cursors,/shaelvien-cursor-assets-ready/);
  assert.match(cursors,/if\(finePointer\)document\.documentElement\.classList\.add\('shaelvien-cursors-ready'\)/);
  assert.match(input,/function cursorTarget\(reticle = currentReticle\(\)\)/);
  assert.match(input,/target\.classList\.contains\("selected"\) \? "selectAlt2"/);
  assert.match(input,/reticle\.dataset\.cursorRole = role/);
  assert.match(css,/Shaelvien cursor asset authority/);
  assert.match(css,/--rist-cursor-image-pointer/);
  assert.match(css,/--rist-cursor-image-selectAlt2/);
  assert.match(index,/cursors-haptics\.js\?v=20260928-visible-cursor-assets-1/);
  assert.match(index,/experiments-universal-input\.js\?v=20260928-cursor-assets-1/);
  assert.match(index,/experiments-universal-suite\.css\?v=20260928-experiment-boot-1/);
});


test('analog center tap selects the asset currently under the cursor',()=>{
  const razor=read('Components/ExperimentsWorkspace.razor');
  const input=read('wwwroot/experiments-universal-input.js');

  assert.match(input,/const ANALOG_SELECT_RADIUS = 0\.46;/);
  assert.match(input,/const ANALOG_SELECT_MOVE_PX = 10;/);
  assert.match(input,/selectCandidate =[\s\S]{0,100}?Math\.hypot\(pointerAnalogX, pointerAnalogY\) <= ANALOG_SELECT_RADIUS/);
  assert.match(input,/if \(shouldSelect\) invoke\("select"\)/);
  assert.match(input,/function cursorTarget\(reticle = currentReticle\(\)\)/);
  assert.match(input,/document\.elementFromPoint/);
  assert.match(input,/\.asset-source-explorer \.linked-asset/);
  assert.match(input,/target\.click\(\)/);
  assert.match(razor,/case "select":[\s\S]{0,260}?Stage\.BrowsePlace&&CursorMode[\s\S]{0,120}?ActivateBrowseCursorTargetAsync/);
});


test('asset activation is select once and place on the second activation',()=>{
  const razor=read('Components/ExperimentsWorkspace.razor');
  assert.match(razor,/void SelectGameAsset\(string key\)=>ActivateAssetFromBrowser\(key\)/);
  assert.match(razor,/void SelectMyAsset\(string key\)=>ActivateAssetFromBrowser\(key\)/);
  assert.match(razor,/if\(string\.Equals\(_selectedAssetKey,key,StringComparison\.Ordinal\)\)[\s\S]*?BeginSelectedAssetPlacement\(\)/);
  assert.match(razor,/void BeginSelectedAssetPlacement\(\)[\s\S]*?_stage=Stage\.Scale/);
  assert.match(razor,/Stage\.BrowsePlace=>string\.IsNullOrWhiteSpace\(_selectedAssetKey\)\?"BROWSE":SelectedAssetName/);
  assert.doesNotMatch(razor,/Stage\.BrowsePlace=>"SELECT"/);
  assert.match(razor,/ONCE SELECTS · AGAIN PLACES/);
});

test('Experiment Start menu keeps controller visible and reuses Save Load and exit hooks',()=>{
  const razor=read('Components/ExperimentsWorkspace.razor');
  const host=read('wwwroot/worldbuilder-source-host.js');
  const start=read('wwwroot/start-menu.js');
  const css=read('wwwroot/css/experiments-universal-suite.css');
  const index=read('wwwroot/index.html');

  assert.match(razor,/data-experiment-start-save/);
  assert.match(razor,/data-experiment-start-load/);
  assert.match(razor,/data-experiment-start-exit/);
  assert.match(razor,/RistStartMenu\.open","experiment"/);
  assert.match(razor,/SaveExperimentFromStartAsync\(\)[\s\S]*?\.InvokeVoidAsync\("save",_worldBuilderFrame\)/);
  assert.match(razor,/LoadExperimentFromStartAsync\(\)[\s\S]*?\.InvokeVoidAsync\("reload",_worldBuilderFrame,source\)/);
  assert.match(host,/export async function save\(frame\)/);
  assert.match(host,/export function reload\(frame,worldSource\)/);
  assert.match(start,/data-start-action="save"/);
  assert.match(start,/data-start-action="load"/);
  assert.match(start,/Exit Experiment/);
  assert.match(start,/rist-start-experiment-controller/);
  assert.match(css,/bottom:var\(--rist-start-controller-reserve,220px\)!important/);
  assert.match(index,/start-menu\.js\?v=20260928-experiment-save-load-1/);
});

test('mobile expanded context is contained and avoids iOS form zoom',()=>{
  const css=read('wwwroot/css/experiments-universal-suite.css');
  assert.match(css,/\.asset-context-pip\.expanded\{[\s\S]*?left:8px!important;[\s\S]*?right:8px!important;[\s\S]*?width:auto!important/);
  assert.match(css,/\.asset-context-fields input,[\s\S]*?\.asset-context-fields textarea\{[\s\S]*?font-size:16px!important/);
  assert.match(css,/resize:none!important/);
});


test('Experiments open on the start artwork and START reveals environment choices',()=>{
  const razor=read('Components/ExperimentsWorkspace.razor');
  const css=read('wwwroot/css/experiments-universal-suite.css');

  assert.match(razor,/@if\(_stage==Stage\.Environment\)[\s\S]{0,500}?experiment-start-screen/);
  assert.match(razor,/shaelvien-dragon-creation-startup-screen\.png/);
  assert.match(razor,/_experimentStartRevealed\?"CHOOSE ENVIRONMENT":"PRESS START"/);
  assert.match(razor,/experiment-dragon-head shaelvien-head[\s\S]{0,120}?is-faded/);
  assert.match(razor,/experiment-dragon-head rist-head[\s\S]{0,120}?is-faded/);
  assert.match(razor,/@onclick="HandleStartButtonAsync"/);
  assert.match(razor,/HandleStartButtonAsync\(\)[\s\S]{0,360}?_experimentStartRevealed=true;[\s\S]{0,240}?Choose Shaelvien, RIST, or Legacy/);
  assert.match(razor,/case Stage\.Environment:[\s\S]{0,260}?if\(!_experimentStartRevealed\)/);
  assert.match(css,/Experiment boot screen authority/);
  assert.match(css,/experiment-dragon-head/);
});
