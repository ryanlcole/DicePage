const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

const root=path.resolve(__dirname,'..');
const read=relative=>fs.readFileSync(path.join(root,relative),'utf8');

test('Browser Back authority is not a visible or grid-flow control',()=>{
  const razor=read('Components/UniversalInterface.razor');
  const css=read('wwwroot/css/universal-interface.css');

  assert.match(
    razor,
    /class="universal-browser-back"[\s\S]{0,220}?data-browser-back="universal"[\s\S]{0,220}?hidden/
  );
  assert.match(
    css,
    /\.universal-browser-back\s*\{[\s\S]*?display:none!important;[\s\S]*?\}/
  );
});

test('Browser Back authority remains connected to the universal shell',()=>{
  const bridge=read('wwwroot/browser-back-authority.js');
  assert.match(bridge,/\.universal-shell \[data-browser-back="universal"\]/);
  assert.match(bridge,/target\.click\(\)/);
});


test('landscape mode prioritizes viewer visibility with a compact control deck',()=>{
  const css=read('wwwroot/css/universal-interface.css');
  assert.match(css,/Compact landscape visibility authority/);
  assert.match(css,/@media \(orientation:landscape\) and \(max-height:620px\)/);
  assert.match(css,/grid-template-rows:minmax\(0,1fr\) clamp\(92px,26dvh,112px\)!important/);
  assert.match(css,/grid-template-columns:minmax\(0,1fr\) clamp\(76px,14vw,96px\) minmax\(0,1fr\)!important/);
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
  assert.match(semantic,/SelectSemanticAsync\(\)[\s\S]{0,360}?Stage\.BrowsePlace[\s\S]{0,160}?ActivateBrowseCursorTargetAsync\(\)/);
  assert.match(input,/const ANALOG_SELECT_RADIUS = 0\.46;/);
  assert.match(input,/const ANALOG_SELECT_MOVE_PX = 10;/);
  assert.match(input,/if \(shouldSelect\) invoke\("select"\);/);
  assert.match(input,/edgeButton\(gamepad, 10, "select"\);/);
  assert.match(input,/event\.key !== "Enter" && event\.key !== " "/);
});

test('portrait builder keeps source content in the vertical center and corner PIPs translucent',()=>{
  const css=read('wwwroot/css/universal-interface.css');
  const index=read('wwwroot/index.html');

  assert.match(css,/Analog Select \+ four-corner pip safe-center authority/);
  assert.match(
    css,
    /\.depth-pip,[\s\S]*?\.asset-context-pip\.minimized\{[\s\S]*?opacity:\.76!important;/
  );
  assert.match(
    css,
    /@media\(max-width:700px\) and \(orientation:portrait\)\{[\s\S]*?\.universal-worldbuilder-viewer \.asset-source-explorer\{[\s\S]*?top:144px!important;[\s\S]*?bottom:82px!important;/
  );
  assert.match(css,/grid-template-columns:repeat\(auto-fit,minmax\(82px,1fr\)\)!important;/);
  assert.match(
    css,
    /@media\(max-width:430px\) and \(orientation:portrait\)\{[\s\S]*?grid-template-columns:repeat\(3,minmax\(0,1fr\)\)!important;/
  );
  assert.match(index,/universal-interface\.css\?v=20260930-semantic-controls-2/);
  assert.match(index,/universal-interface-input\.js\?v=20260930-semantic-controls-2/);
});


test('START opens the existing settings menu without duplicating settings',()=>{
  const razor=read('Components/UniversalInterface.razor');
  const css=read('wwwroot/css/universal-interface.css');
  const index=read('wwwroot/index.html');

  assert.match(razor,/class="analog-start-button"[\s\S]{0,220}?@onclick="HandleStartButtonAsync"[\s\S]{0,220}?>START<\/button>/);
  assert.match(razor,/HandleStartButtonAsync\(\)[\s\S]*?await OpenStartMenuAsync\(\)/);
  assert.match(razor,/await JS\.InvokeVoidAsync\("RistStartMenu\.open","universal"\)/);
  assert.doesNotMatch(razor,/<h2>Video<\/h2>|<h2>Picture<\/h2>|<h2>Sound<\/h2>|<h2>Effects<\/h2>/);
  assert.match(css,/body\.rist-start-open \.rist-start-overlay\{[\s\S]*?z-index:2147483600!important/);
  assert.match(index,/start-menu\.js/);
});

test('Browse cursor and analog press target the thumbnail beneath the reticle',()=>{
  const razor=read('Components/UniversalInterface.razor');
  const semantic=read('Components/UniversalInterface.SemanticControls.cs');
  const input=read('wwwroot/universal-interface-input.js');
  const index=read('wwwroot/index.html');

  assert.match(razor,/bool _browseCursorActive;/);
  assert.match(razor,/bool CursorAvailable=>!IsGameMasterMenuStage&&_stage!=Stage\.MmoMap&&(?:_stage!=Stage\.[A-Za-z]+&&)*_stage!=Stage\.SpatialSelect&&!IsPathDrivenStage&&LeftDisplayOptionCount<=1&&RightDisplayOptionCount<=1;/);
  assert.match(razor,/bool CursorMode=>_stage==Stage\.MmoMap[\s\S]{0,100}?MmoAnalogCursorMode[\s\S]{0,160}?CursorAvailable[\s\S]{0,120}?!_analogButtonMode/);
  assert.match(razor,/case Stage\.BrowsePlace:[\s\S]{0,360}?_browseCursorActive=true;[\s\S]{0,120}?_analogButtonMode=false;/);
  assert.match(semantic,/SelectSemanticAsync\(\)[\s\S]{0,260}?Stage\.BrowsePlace[\s\S]{0,120}?Stage\.MmoMap[\s\S]{0,120}?CursorMode[\s\S]{0,120}?ActivateBrowseCursorTargetAsync\(\)/);
  assert.match(input,/function activateCursorTarget\(\)/);
  assert.match(input,/document\.elementFromPoint/);
  assert.match(input,/\.asset-source-explorer \.linked-asset/);
  assert.match(input,/target\.click\(\)/);
  assert.match(input,/event\.target instanceof Element && event\.target\.closest\("\.analog-start-button,\.analog-mode-button"\)/);
  assert.match(index,/universal-interface\.css\?v=20260930-semantic-controls-2/);
  assert.match(index,/universal-interface-input\.js\?v=20260930-semantic-controls-2/);
});


test('authenticated launch enters the universal controller instead of the old environment cards',()=>{
  const auth=read('Components/AuthenticatedWorld.razor');
  assert.match(auth,/BeginAuthenticatedLaunchAsync\(\)[\s\S]{0,420}?_launchStarted=true;[\s\S]{0,140}?_universalInterfaceOpen=true;[\s\S]{0,180}?LoadLaunchWorldsAsync\(\)/);
  assert.match(auth,/else if\(_universalInterfaceOpen\)[\s\S]{0,180}?<UniversalInterface/);
});

test('LEGACY opens the GM archive importer and continues into RIST',()=>{
  const razor=read('Components/UniversalInterface.razor');
  assert.match(razor,/<LegacyWorldGate[\s\S]{0,260}?Open="@_legacyGateOpen"[\s\S]{0,260}?OnContinue="ContinueLegacyIntoRistAsync"/);
  assert.match(razor,/Legacy: import or load a preserved GM archive\. Completing Legacy continues into RIST\./);
  assert.match(razor,/ContinueLegacyIntoRistAsync\(\)[\s\S]{0,420}?_selectedEnvironment="RIST"[\s\S]{0,260}?_stage=Stage\.Role/);
  assert.doesNotMatch(razor,/Opening Legacy interface…[\s\S]{0,180}?OnExit\.InvokeAsync/);
});

test('analog top button exposes BUTTONS ZONES and CURSOR on the MMO deed map without changing START',()=>{
  const razor=read('Components/UniversalInterface.razor');
  const mmo=read('Components/UniversalInterface.MmoMap.cs');
  const input=read('wwwroot/universal-interface-input.js');
  const css=read('wwwroot/css/universal-interface.css');

  assert.match(razor,/class="analog-mode-button"[\s\S]{0,360}?@onclick="ToggleAnalogMode"[\s\S]{0,420}?@AnalogModeLabel<\/button>/);
  assert.match(mmo,/MmoAnalogModes = \["BUTTONS", "ZONES", "CURSOR"\]/);
  assert.match(razor,/string AnalogModeLabel=>[\s\S]{0,240}?_stage==Stage\.MmoMap[\s\S]{0,80}?MmoAnalogMode/);
  assert.match(razor,/async Task ToggleAnalogMode\(\)[\s\S]{0,520}?_stage==Stage\.MmoMap[\s\S]{0,120}?CycleMmoAnalogMode\(\)/);
  assert.match(razor,/void StepY\(int direction\)[\s\S]{0,900}?MmoAnalogButtonsMode[\s\S]{0,120}?CycleMmoLeftOption\(direction\)/);
  assert.match(razor,/void StepX\(int direction\)[\s\S]{0,900}?MmoAnalogButtonsMode[\s\S]{0,120}?CycleMmoRightOption\(direction\)/);
  assert.match(razor,/case Stage\.BrowsePlace:[\s\S]*?_analogButtonMode=false;[\s\S]*?Cursor active/);
  assert.match(razor,/class="analog-start-button"[\s\S]*?@onclick="HandleStartButtonAsync"/);
  assert.match(input,/\.asset-source-explorer \.linked-asset, \.mmo-deed-cell/);
  assert.match(input,/\.analog-start-button,\.analog-mode-button/);
  assert.match(css,/Analog mode toggle authority/);
});


test('viewer cursor uses existing Shaelvien cursor assets on touch and pointer devices',()=>{
  const razor=read('Components/UniversalInterface.razor');
  const input=read('wwwroot/universal-interface-input.js');
  const cursors=read('wwwroot/cursors-haptics.js');
  const css=read('wwwroot/css/universal-interface.css');
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
  assert.match(index,/universal-interface-input\.js\?v=20260930-semantic-controls-2/);
  assert.match(index,/universal-interface\.css\?v=20260930-semantic-controls-2/);
});


test('analog center tap selects the asset currently under the cursor',()=>{
  const razor=read('Components/UniversalInterface.razor');
  const semantic=read('Components/UniversalInterface.SemanticControls.cs');
  const input=read('wwwroot/universal-interface-input.js');

  assert.match(input,/const ANALOG_SELECT_RADIUS = 0\.46;/);
  assert.match(input,/const ANALOG_SELECT_MOVE_PX = 10;/);
  assert.match(input,/selectCandidate =[\s\S]{0,100}?Math\.hypot\(pointerAnalogX, pointerAnalogY\) <= ANALOG_SELECT_RADIUS/);
  assert.match(input,/if \(shouldSelect\) invoke\("select"\)/);
  assert.match(input,/function cursorTarget\(reticle = currentReticle\(\)\)/);
  assert.match(input,/document\.elementFromPoint/);
  assert.match(input,/\.asset-source-explorer \.linked-asset/);
  assert.match(input,/target\.click\(\)/);
  assert.match(razor,/ReceiveSemanticHardwareInputAsync\(control,direction\)/);
  assert.match(semantic,/case "select":[\s\S]{0,180}?Action\.Select/);
  assert.match(semantic,/case UniversalSemanticControls\.Action\.Select:[\s\S]{0,120}?SelectSemanticAsync\(\)/);
  assert.match(semantic,/SelectSemanticAsync\(\)[\s\S]{0,320}?CursorMode[\s\S]{0,120}?ActivateBrowseCursorTargetAsync\(\)/);
});


test('asset activation is select once and place on the second activation',()=>{
  const razor=read('Components/UniversalInterface.razor');
  assert.match(razor,/void SelectGameAsset\(string key\)=>ActivateAssetFromBrowser\(key\)/);
  assert.match(razor,/void SelectMyAsset\(string key\)=>ActivateAssetFromBrowser\(key\)/);
  assert.match(razor,/if\(string\.Equals\(_selectedAssetKey,key,StringComparison\.Ordinal\)\)[\s\S]*?BeginSelectedAssetPlacement\(\)/);
  assert.match(razor,/void BeginSelectedAssetPlacement\(\)[\s\S]*?_stage=Stage\.Scale/);
  assert.match(razor,/Stage\.BrowsePlace=>string\.IsNullOrWhiteSpace\(_selectedAssetKey\)\?"BROWSE":SelectedAssetName/);
  assert.doesNotMatch(razor,/Stage\.BrowsePlace=>"SELECT"/);
  assert.match(razor,/ONCE SELECTS · AGAIN PLACES/);
});

test('Universal Start menu keeps controller visible and reuses Save Load and exit hooks',()=>{
  const razor=read('Components/UniversalInterface.razor');
  const host=read('wwwroot/worldbuilder-source-host.js');
  const start=read('wwwroot/start-menu.js');
  const css=read('wwwroot/css/universal-interface.css');
  const index=read('wwwroot/index.html');

  assert.match(razor,/data-universal-start-save/);
  assert.match(razor,/data-universal-start-load/);
  assert.match(razor,/data-universal-start-exit/);
  assert.match(razor,/RistStartMenu\.open","universal"/);
  assert.match(razor,/SaveUniversalFromStartAsync\(\)[\s\S]*?\.InvokeVoidAsync\("save",_worldBuilderFrame\)/);
  assert.match(razor,/LoadUniversalFromStartAsync\(\)[\s\S]*?\.InvokeVoidAsync\("reload",_worldBuilderFrame,source\)/);
  assert.match(host,/export async function save\(frame\)/);
  assert.match(host,/export function reload\(frame,worldSource\)/);
  assert.match(start,/data-start-action="save"/);
  assert.match(start,/data-start-action="load"/);
  assert.match(start,/Exit Game/);
  assert.match(start,/rist-start-universal-controller/);
  assert.match(css,/bottom:var\(--rist-start-controller-reserve,220px\)!important/);
  assert.match(index,/start-menu\.js\?v=20260928-grid-density-1/);
});

test('mobile expanded context is contained and avoids iOS form zoom',()=>{
  const css=read('wwwroot/css/universal-interface.css');
  assert.match(css,/\.asset-context-pip\.expanded\{[\s\S]*?left:8px!important;[\s\S]*?right:8px!important;[\s\S]*?width:auto!important/);
  assert.match(css,/\.asset-context-fields input,[\s\S]*?\.asset-context-fields textarea\{[\s\S]*?font-size:16px!important/);
  assert.match(css,/resize:none!important/);
});


test('Universal open directly on Shaelvien Legacy and RIST choices',()=>{
  const razor=read('Components/UniversalInterface.razor');

  assert.match(razor,/bool _universalStartRevealed=true;/);
  assert.match(razor,/<strong>CHOOSE ENVIRONMENT<\/strong>/);
  assert.match(razor,/environment-choice-label">SHAELVIEN/);
  assert.match(razor,/environment-choice-label">RIST/);
  assert.match(razor,/string AnalogModeLabel=>_stage==Stage\.Environment&&_universalStartRevealed[\s\S]{0,120}?"LEGACY"/);
  assert.match(razor,/class="analog-start-button"[\s\S]{0,220}?@onclick="HandleStartButtonAsync"/);
});


test('START Interface separates overlay viewer grid and asset grid',()=>{
  const start=read('wwwroot/start-menu.js');
  const sourceCss=read('css-source/start-menu.css');
  const shellCss=read('wwwroot/css/universal-interface.css');
  const prototype=read('wwwroot/prototype/prototype.js');
  const prototypeCss=read('wwwroot/prototype/prototype.css');
  const prototypeIndex=read('wwwroot/prototype/index.html');
  const index=read('wwwroot/index.html');

  assert.match(start,/Interface:null/);
  assert.match(start,/data-interface-overlay="on"/);
  assert.match(start,/data-interface-overlay="off"/);
  assert.match(start,/data-interface-view-grid="square"/);
  assert.match(start,/data-interface-view-grid="hex"/);
  assert.match(start,/data-interface-asset-grid="square"/);
  assert.match(start,/data-interface-asset-grid="hex"/);
  assert.match(start,/data-interface-grid-count="viewer-columns"/);
  assert.match(start,/data-interface-grid-count="viewer-rows"/);
  assert.match(start,/data-interface-grid-count="asset-columns"/);
  assert.match(start,/data-interface-grid-count="asset-rows"/);
  assert.match(start,/min="1" max="64"/);
  assert.match(start,/rist\.viewer\.grid\.v1/);
  assert.match(start,/rist\.asset\.grid\.v1/);
  assert.match(sourceCss,/Interface segmented controls/);
  assert.match(shellCss,/START Interface overlay authority/);
  assert.match(shellCss,/rist-viewer-overlays-off/);
  assert.match(prototype,/function applyViewerGridMode/);
  assert.match(prototype,/function applyAssetGridMode/);
  assert.match(prototype,/function snapAssetPoint/);
  assert.match(prototype,/viewerGridColumns=30,viewerGridRows=30,assetGridColumns=30,assetGridRows=30/);
  assert.match(prototype,/function configuredGridCellCenter/);
  assert.match(prototype,/stage\.dataset\.viewerGridColumns/);
  assert.match(prototype,/stage\.dataset\.assetGridColumns/);
  assert.match(prototype,/nearestAllowedRegionCell\(regionCell,allowed,regionGridShape\)/);
  assert.match(prototypeCss,/\.viewer-grid-overlay/);
  assert.doesNotMatch(prototypeCss,/repeating-linear-gradient\(0deg,rgba\(178,221,236,\.045\)/);
  assert.match(prototypeIndex,/prototype\.css\?v=20260928-canonical-spatial-1/);
  assert.match(prototypeIndex,/prototype\.js\?v=[0-9]{8}-[a-z0-9-]+/i);
  assert.match(index,/start-menu\.js\?v=20260928-grid-density-1/);
  assert.match(index,/universal-interface\.css\?v=20260930-semantic-controls-2/);
});


test('image tool is labeled IMAGES and exposes existing libraries plus upload',()=>{
  const razor=read('Components/UniversalInterface.razor');
  assert.match(razor,/ArtMethods=\["DRAW","CAD","IMAGES","SPRITE","AUDIO","VIDEO"\]/);
  assert.match(razor,/case "IMAGES":[\s\S]{0,120}?PrepareAssetSource\("IMAGE"\)/);
  assert.match(razor,/ImageSources=\["GAME IMAGES","MY IMAGES","UPLOAD"\]/);
  assert.doesNotMatch(razor,/ArtMethods=\[[^\]]*"IMPORT IMAGE"/);
});

test('viewer top menu exposes back undo cut copy redo paste and forward',()=>{
  const razor=read('Components/UniversalInterface.razor');
  const host=read('wwwroot/worldbuilder-source-host.js');
  const prototype=read('wwwroot/prototype/prototype.js');
  const css=read('wwwroot/css/universal-interface.css');

  assert.match(razor,/class="viewer-menu-bar"[\s\S]{0,900}?BACK[\s\S]{0,200}?UNDO[\s\S]{0,200}?CUT[\s\S]{0,200}?COPY[\s\S]{0,200}?REDO[\s\S]{0,200}?PASTE[\s\S]{0,200}?FORWARD/);
  assert.match(razor,/HandleViewerMenuCommandAsync\("back"\)/);
  assert.match(razor,/HandleViewerMenuCommandAsync\("forward"\)/);
  assert.match(host,/export async function editCommand\(frame,command\)/);
  assert.match(prototype,/async function runViewerEditCommand\(command\)/);
  assert.match(prototype,/command==='copy'/);
  assert.match(prototype,/command==='cut'/);
  assert.match(prototype,/command==='paste'/);
  assert.match(prototype,/command==='undo'/);
  assert.match(prototype,/command==='redo'/);
  assert.match(prototype,/editCommand:runViewerEditCommand/);
  assert.match(css,/Viewer command menu authority/);
});

test('Shaelvien GameMaster opens the permission-driven deed map without the legacy Shaelvien selector',()=>{
  const razor=read('Components/UniversalInterface.razor');
  const mmo=read('Components/UniversalInterface.MmoMap.cs');
  const land=read('WorldSession.MmoLand.cs');

  assert.match(razor,/case Stage\.Role:[\s\S]{0,900}?EnterMmoMapAsync\(inspect:false\)/);
  assert.doesNotMatch(razor,/_stage=Stage\.DeedSelect;/);
  assert.doesNotMatch(razor,/<ShaelvienDeedGate/);
  assert.match(razor,/Stage\.PathSelect=>IsShaelvienDeedHome\?"WORLD BUILDER"/);
  assert.match(razor,/Stage\.PathSelect=>IsShaelvienDeedHome\?"CONTEXT"/);
  assert.match(razor,/World Builder is on the left; Context is on the right/);
  assert.match(mmo,/"ENTER COORDINATES"/);
  assert.match(mmo,/new\("ENDEMAR", "owned", WorldSession\.EndemarOriginCell\)/);
  assert.match(mmo,/COORDINATES \/ MY ZONES/);
  assert.match(mmo,/Session\.IsMmoParcelOwnedByCurrentUser/);
  assert.match(mmo,/new\("EDIT", "edit"\)/);
  assert.match(mmo,/new\("VIEW", "view"\)/);
  assert.match(mmo,/new\("ROLEPLAY", "roleplay"\), new\("INSPECT", "inspect"\)/);
  assert.match(mmo,/new\("PRIVATE", "private"\)/);
  assert.match(mmo,/new\("CLAIM", "claim"\)/);
  assert.match(mmo,/new\("PURCHASE TOKEN AND CLAIM", "purchase"\)/);
  assert.match(land,/UnspentMmoWorldTokenCount/);
});

test('Explore shows geometrically open zones even without a token',()=>{
  const deed=read('Components/ShaelvienDeedGate.razor');
  const land=read('WorldSession.MmoLand.cs');

  assert.match(land,/public bool IsMmoParcelOpen\(int cellIndex\)/);
  assert.match(land,/public bool IsMmoParcelClaimable\(int cellIndex\) =>[\s\S]{0,100}?HasUnspentMmoWorldToken && IsMmoParcelOpen\(cellIndex\)/);
  assert.match(deed,/Session\.IsMmoParcelOpen\(_selectedCell\)/);
  assert.match(deed,/return Session\.IsMmoParcelOpen\(cell\)/);
  assert.match(deed,/No unspent Shaelvien Token is available\. You can continue exploring\./);
  assert.match(deed,/Session\.IsMmoParcelOpen\(cell\)\)return Session\.IsMmoParcelClaimable\(cell\)/);
  assert.match(deed,/Open Shaelvien zone \{CellCoordinate\(cell\)\}; explore now, token required to claim/);
});

test('developer Inspect is a deed-map oversight action and audited edits return to the MMO map',()=>{
  const razor=read('Components/UniversalInterface.razor');
  const mmo=read('Components/UniversalInterface.MmoMap.cs');

  assert.match(mmo,/Session\.TrustedPlatformDeveloper[\s\S]{0,260}?new\("ROLEPLAY", "roleplay"\), new\("INSPECT", "inspect"\)/);
  assert.match(mmo,/EnterMmoInspectSelectionAsync/);
  assert.match(mmo,/new\("MANAGE", "manage"\)/);
  assert.match(razor,/OPEN WORLD BUILDER/);
  assert.doesNotMatch(razor,/<ShaelvienDeedGate/);
  assert.match(razor,/_inspectionEditMode/);
  assert.match(razor,/REASON FOR NEXT EDIT/);
  assert.match(razor,/RequireInspectionReason\(\)/);
  assert.match(razor,/AppendInspectionAudit\(root,"SAVE WORLD REPRESENTATION",inspectionReason\)/);
  assert.match(razor,/MergeWorldBuilderRepresentationState\([\s\S]{0,120}?current\?\.State,[\s\S]{0,100}?SelectedDeedRegionId/);
  assert.match(razor,/ConsumeInspectionReason\(\)/);
  assert.match(razor,/ReturnToInspectMapAsync\(\)[\s\S]{0,220}?EnterMmoMapAsync\(inspect:true\)/);
  assert.match(razor,/void ReturnToShaelvienDeedSelector\(\)[\s\S]{0,360}?_stage=Stage\.MmoMap/);
  assert.match(razor,/RecordInspectionAuditAsync\(\$"CREATE \{CurrentBuilderScope\}",inspectionReason\)/);
  assert.match(razor,/var access=_exploreReadOnlyMode[\s\S]{0,180}?_inspectionEditMode&&Session\.TrustedPlatformDeveloper/);
});

test('Explore exposes open public and restricted MMO zones while Inspect can audit visibility edits',()=>{
  const razor=read('Components/UniversalInterface.razor');
  const deed=read('Components/ShaelvienDeedGate.razor');
  const session=read('WorldSession.MmoLand.cs');
  const client=read('AwsAuthorityClient.cs');

  assert.match(deed,/OPEN/);
  assert.match(deed,/PUBLIC \/ VIEWABLE|Public \/ viewable/);
  assert.match(deed,/RESTRICTED|Restricted/);
  assert.match(deed,/Restricted Shaelvien zone .* name only/);
  assert.match(deed,/SaveInspectionZoneEditAsync/);
  assert.match(deed,/SAVE ZONE EDIT/);
  assert.match(deed,/OPEN WORLD EDITOR WITH REASON/);
  assert.match(session,/InspectEditMmoParcelAsync/);
  assert.match(client,/\/world\/parcels\/inspect-edit/);
  assert.match(client,/string Visibility = "Restricted"/);
  const authority=read('WorldSession.WorldAuthority.cs');
  assert.match(authority,/public bool TrustedPlatformDeveloper => _trustedPlatformDeveloper/);
  assert.match(authority,/access\.developer/);
  assert.match(razor,/var platformDeveloper=Session\.TrustedPlatformDeveloper/);
  assert.match(razor,/if\(platformDeveloper\)[\s\S]{0,260}?"Inspect"[\s\S]{0,120}?"SHAELVIEN_INSPECT"/);
  assert.match(razor,/BeginInspectionEditAsync[\s\S]{0,180}?if\(!Session\.TrustedPlatformDeveloper\)/);
  assert.match(razor,/\["regionId"\]=SelectedDeedRegionId/);
});

test('controller Save reacts immediately, commits canonical placement, and stays on the same Art method',()=>{
  const razor=read('Components/UniversalInterface.razor');
  const host=read('wwwroot/worldbuilder-source-host.js');
  const prototype=read('wwwroot/prototype/prototype.js');

  assert.match(razor,/Stage\.SaveCancel=>_assetSavePending\?"SAVING…":"SAVE"/);
  assert.match(razor,/case Stage\.SaveCancel:[\s\S]{0,600}?_assetSavePending=true;[\s\S]{0,220}?InvokeAsync\(StateHasChanged\)[\s\S]{0,260}?CommitCurrentAssetToCanonicalViewerAsync\(\)/);
  assert.match(razor,/case Stage\.SaveCancel:[\s\S]{0,1300}?_stage=Stage\.ArtMethod/);
  assert.match(razor,/\{CurrentArtMethod\} remains selected/);
  assert.doesNotMatch(razor,/case Stage\.SaveCancel:[\s\S]{0,180}?SaveCurrentAssetToViewer\(\)/);
  assert.match(razor,/InvokeAsync<bool>\([\s\S]{0,220}?"placeAsset"/);
  assert.match(host,/async function waitForPrototype\(frame,timeoutMs=3000\)/);
  assert.match(prototype,/async function placeExternalAsset\(raw=\{\}\)/);
  assert.match(prototype,/const saved=await saveWorldBuilder\(\)/);
});

test('Back follows semantic flowchart reverse from Art to Layer to Tier',()=>{
  const razor=read('Components/UniversalInterface.razor');
  assert.match(razor,/case Stage\.ArtMethod:[\s\S]{0,180}?_stage=Stage\.WorldBuilderLayer/);
  assert.match(razor,/case Stage\.WorldBuilderLayer:[\s\S]{0,180}?_stage=Stage\.WorldBuilderTier/);
  assert.match(razor,/case Stage\.WorldBuilderTier:[\s\S]{0,320}?Stage\.PathSelect/);
});

test('selected deed region identity is captured and Endemar uses trusted platform authority',()=>{
  const razor=read('Components/UniversalInterface.razor');
  assert.match(razor,/string _selectedDeedRegionId=""/);
  assert.match(razor,/_selectedDeedRegionId=option\.Parcel\?\.RegionId\?\.Trim\(\)\?\?""/);
  assert.match(razor,/SelectedDeedRegionId[\s\S]{0,180}?_selectedDeedRegionId/);
  assert.doesNotMatch(razor,/SelectedDeedRegionId[\s\S]{0,260}?Session\.MmoParcels\.FirstOrDefault/);
  assert.match(razor,/var platformOwner=Session\.TrustedPlatformOwner/);
  assert.match(razor,/var endemarOwner=platformOwner\|\|Session\.OwnsCanonicalGeonaphZone/);
  assert.match(razor,/if\(endemarOwner\)[\s\S]{0,600}?SHAELVIEN_ORIGIN/);
  assert.match(razor,/await Session\.RefreshTrustedWorldAuthorityAsync\(\);[\s\S]{0,160}?await Session\.RefreshMmoLandAsync\(\)/);
});

test('outer depth drives embedded canonical tier and layer',()=>{
  const razor=read('Components/UniversalInterface.razor');
  const host=read('wwwroot/worldbuilder-source-host.js');
  const prototype=read('wwwroot/prototype/prototype.js');

  assert.match(razor,/case Stage\.WorldBuilderTier:[\s\S]{0,220}?SyncWorldBuilderDepthAsync/);
  assert.match(razor,/case Stage\.WorldBuilderLayer:[\s\S]{0,220}?SyncWorldBuilderDepthAsync/);
  assert.match(razor,/InvokeVoidAsync\("setDepth",_worldBuilderFrame,_tier,_layer,CurrentBuilderScope,CurrentSpatialNodeId,CurrentSpatialPath\)/);
  assert.match(host,/export function setDepth\(frame,tier,layer,scope,spatialNodeId="",spatialPath=""\)/);
  assert.match(prototype,/function setExternalDepth\(raw=\{\}\)/);
});

test('zoom hands representation from World to Region Local and Instance',()=>{
  const prototype=read('wwwroot/prototype/prototype.js');

  assert.match(prototype,/SPATIAL_SCOPE_THRESHOLDS=Object\.freeze/);
  assert.match(prototype,/REGION:REGION_ENHANCE_ENTER/);
  assert.match(prototype,/LOCAL:REGION_ENHANCE_ENTER\*4/);
  assert.match(prototype,/INSTANCE:REGION_ENHANCE_ENTER\*16/);
  assert.match(prototype,/function currentSpatialScope\(\)/);
  assert.match(prototype,/if\(ratio>=SPATIAL_SCOPE_THRESHOLDS\.INSTANCE\)return'INSTANCE'/);
  assert.match(prototype,/if\(ratio>=SPATIAL_SCOPE_THRESHOLDS\.LOCAL\)return'LOCAL'/);
  assert.match(prototype,/if\(ratio>=SPATIAL_SCOPE_THRESHOLDS\.REGION\)return'REGION'/);
  assert.match(prototype,/worldVisible=!DEED_REGION_ID&&\(spatialScope==='WORLD'\|\|\(spatialScope==='REGION'&&!regionEnhanceActive\)\)/);
  assert.match(prototype,/const itemScope=normalizeSpatialScope/);
  assert.match(prototype,/itemScope===spatialScope/);
  assert.match(prototype,/spatialScope!=='WORLD'[\s\S]{0,180}?rotateX\(15deg\)/);
});

test('canonical placements retain their World Region Local or Instance scope',()=>{
  const prototype=read('wwwroot/prototype/prototype.js');

  assert.match(prototype,/scope:normalizeSpatialScope\(item\.scope\|\|'WORLD'\)/);
  assert.match(prototype,/scope:normalizeSpatialScope\(raw\.scope\|\|'WORLD'\)/);
  assert.match(prototype,/externalSpatialScope='WORLD'/);
  assert.match(prototype,/const scope=normalizeSpatialScope\(raw\.scope\|\|externalSpatialScope\)/);
});


test('selected Shaelvien deed identity drives the embedded map and Sunken Tundra pack',()=>{
  const razor=read('Components/UniversalInterface.razor');
  const prototype=read('wwwroot/prototype/prototype.js');

  assert.match(razor,/deedRegionId=\{deedRegionId\}/);
  assert.match(razor,/deedZone=\{deedZone\}/);
  assert.match(razor,/SelectedDeedZoneId/);
  assert.match(prototype,/const DEED_REGION_ID=String\(QUERY\.get\('deedRegionId'\)/);
  assert.match(prototype,/async function hydrateSelectedDeedZone\(options=\{\}\)/);
  assert.match(prototype,/\/Game\/assets\/zones\/\$\{encodeURIComponent\(DEED_ZONE_ID\)\}\//);
  assert.match(prototype,/const worldVisible=!DEED_REGION_ID/);
  assert.match(prototype,/const itemRegionId=String\(item\.regionId\|\|''\)\.trim\(\)/);
  assert.match(prototype,/const deedVisible=DEED_REGION_ID[\s\S]{0,180}?item\.deedZoneLayer\|\|itemRegionId===DEED_REGION_ID[\s\S]{0,180}?IS_ENDEMAR_SEED\?!itemRegionId:true/);
  assert.match(prototype,/item\.deedZoneLayer=true/);
  assert.match(prototype,/hydrateSelectedDeedZone\(\{preserveView:true\}\)/);
  assert.match(prototype,/const preserveView=options\?\.preserveView===true/);
  assert.match(prototype,/if\(preserveView\)[\s\S]{0,180}?viewerTier=preservedTier;[\s\S]{0,120}?viewerLayer=preservedLayer/);
});
