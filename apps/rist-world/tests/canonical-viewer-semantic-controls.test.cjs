const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

const root=path.resolve(__dirname,'..');
const read=relative=>fs.readFileSync(path.join(root,relative),'utf8');

test('Sheet 14 semantic contract owns intent through outcome without inventing unknown rules',()=>{
  const contract=read('UniversalSemanticControls.cs');
  assert.match(contract,/ContractId = "rist\.semantic-controls\.v1"/);
  for(const id of ['intent','target','method','modify','confirm','resolve','outcome','followup','custom.procedure']){
    assert.ok(contract.includes(`"${id}"`),`missing semantic id ${id}`);
  }
  assert.match(contract,/CanonicalPlayFlow/);
  assert.match(contract,/GenericTtrpgRulesAdapter/);
  assert.match(contract,/UNKNOWN_RULES_REMAIN_UNKNOWN/);
  assert.match(contract,/manual-or-custom/);
});

test('touch keyboard and gamepad all enter the same semantic dispatcher',()=>{
  const razor=read('Components/UniversalInterface.razor');
  const semantic=read('Components/UniversalInterface.SemanticControls.cs');
  const input=read('wwwroot/universal-interface-input.js');

  assert.match(razor,/data-semantic-contract="@SemanticContractId"/);
  assert.match(razor,/ReceiveSemanticHardwareInputAsync\(control,direction\)/);
  assert.match(razor,/DispatchSemanticActionAsync\(CurrentLeftSemanticId\)/);
  assert.match(razor,/DispatchSemanticActionAsync\(CurrentRightSemanticId\)/);
  assert.match(semantic,/case "x":[\s\S]{0,180}?Action\.NavigateX/);
  assert.match(semantic,/case "y":[\s\S]{0,180}?Action\.NavigateY/);
  assert.match(semantic,/case "select":[\s\S]{0,180}?Action\.Select/);
  assert.match(input,/edgeButton\(gamepad, 0, "left"\)/);
  assert.match(input,/edgeButton\(gamepad, 1, "right"\)/);
  assert.match(input,/edgeButton\(gamepad, 10, "select"\)/);
});

test('Sheet 14 experience modes and alternate controller representations are selectable',()=>{
  const razor=read('Components/UniversalInterface.razor');
  const semantic=read('Components/UniversalInterface.SemanticControls.cs');
  const css=read('wwwroot/css/universal-interface.css');

  assert.match(semantic,/ANALOG POSITION", "EXPERIENCE", "CONTROL SKIN/);
  assert.match(semantic,/GUIDED", "STANDARD", "FAST/);
  assert.match(semantic,/LINEAR", "QUICK DECK", "RADIAL", "DUAL RAIL/);
  assert.match(razor,/ShowQuickDeck/);
  assert.match(razor,/SemanticQuickDeck/);
  assert.match(razor,/ShowRadialDeck/);
  assert.match(razor,/SemanticRadialDeck/);
  assert.match(razor,/SemanticCurrentValueCount/);
  assert.match(css,/Sheet 14 semantic controller overlays/);
  assert.match(css,/\.semantic-quick-deck/);
  assert.match(css,/\.semantic-radial-deck/);
  assert.match(css,/\.semantic-skin-dual-rail/);
});

test('unbound rules and GM semantic actions fail closed instead of aliasing the current primary button',()=>{
  const semantic=read('Components/UniversalInterface.SemanticControls.cs');
  assert.match(semantic,/new GenericTtrpgRulesAdapter\(\)\.Plan\(actionId\)/);
  assert.match(semantic,/Bind a campaign\/system adapter before rules execution/);
  assert.match(semantic,/no campaign\/system handler is bound in this Shaep/);
  assert.match(semantic,/No unrelated contextual action was executed/);
});

test('Legacy archives preserve source bytes and gain semantic controller metadata',()=>{
  const legacy=read('LegacyArchiveImport.cs');
  const gate=read('Components/LegacyWorldGate.razor');
  const input=read('wwwroot/universal-interface-input.js');

  assert.match(legacy,/ControlProfileKey\(string worldId\)/);
  assert.match(legacy,/EnsureSemanticControlProfileAsync/);
  assert.match(legacy,/CreateLegacyImportProfile\(worldId\)/);
  assert.match(legacy,/"rist-legacy-archive",3/);
  assert.match(legacy,/ControlContract=UniversalSemanticControls\.ContractId/);
  assert.match(legacy,/UploadBytesAsync\(sourceKey,zipBytes,"application\/zip"\)/);
  assert.match(gate,/ReceiveControlAsync\(string control,int direction\)/);
  assert.match(gate,/EnsureSemanticControlProfileAsync\(world\.WorldId,Auth\)/);
  assert.match(gate,/id="legacy-import-zip"/);
  assert.match(gate,/id="legacy-import-files"/);
  assert.match(input,/openFilePicker\(id\)/);
});

test('sandbox Roleplayer path is connected and universal assets share one cache generation',()=>{
  const interfaceRazor=read('Components/UniversalInterface.razor');
  const semantic=read('Components/UniversalInterface.SemanticControls.cs');
  const auth=read('Components/AuthenticatedWorld.razor');
  const index=read('wwwroot/index.html');

  assert.match(interfaceRazor,/await OpenRoleplayerFromUniversalAsync\(\)/);
  assert.match(semantic,/OpenRoleplayerFromUniversalAsync\(\)/);
  const start=auth.indexOf('async Task EnterUniversalRoleplayAsync');
  const end=auth.indexOf('async Task ReturnToStartAsync',start);
  assert.ok(start>=0&&end>start);
  assert.doesNotMatch(auth.slice(start,end),/if\(!Session\.IsGeonaphWorld\)return;/);
  assert.match(index,/universal-interface\.css\?v=20261001-zone-fill-endemar-2/);
  assert.match(index,/universal-interface-input\.js\?v=20261001-world-home-fill-1/);
});


test('Shaelvien skips the redundant Roleplayer or GameMaster chooser and opens the deed map',()=>{
  const razor=read('Components/UniversalInterface.razor');

  const pressLeftStart=razor.indexOf('async Task PressLeft()');
  const pressLeftEnd=razor.indexOf('case Stage.Role:',pressLeftStart);
  assert.ok(pressLeftStart>=0&&pressLeftEnd>pressLeftStart);
  const shaelvienEntry=razor.slice(pressLeftStart,pressLeftEnd);

  assert.match(shaelvienEntry,/_selectedEnvironment="SHAELVIEN"/);
  assert.match(shaelvienEntry,/await EnterMmoMapAsync\(inspect:false\)/);
  assert.doesNotMatch(shaelvienEntry,/_stage=Stage\.Role/);

  const backStart=razor.indexOf('case Stage.MmoMap:',razor.indexOf('void GoBack()'));
  const backEnd=razor.indexOf('case Stage.HistoryCampaign:',backStart);
  assert.ok(backStart>=0&&backEnd>backStart);
  assert.match(razor.slice(backStart,backEnd),/_stage=Stage\.Environment/);
});

test('deed map itself exposes play and edit choices without a preselected role',()=>{
  const map=read('Components/UniversalInterface.MmoMap.cs');

  assert.match(map,/if \(MmoCanGameMasterSelected\)[\s\S]{0,120}?EDIT[\s\S]{0,120}?ROLEPLAY/);
  assert.match(map,/if \(MmoSelectedIsCanonicalGeonaph\)[\s\S]{0,220}?EnterGeonaphHistoryCampaign\(\)/);
  assert.doesNotMatch(map,/if \(_mmoRoleplayerMode && MmoSelectedIsCanonicalGeonaph\)/);
});
