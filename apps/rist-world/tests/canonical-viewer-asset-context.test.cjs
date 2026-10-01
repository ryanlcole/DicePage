const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

const root=path.resolve(__dirname,'..');
const read=relative=>fs.readFileSync(path.join(root,relative),'utf8');

test('embedded World Builder publishes stable placed-asset context to the universal viewer',()=>{
  const prototype=read('wwwroot/prototype/prototype.js');
  assert.match(prototype,/function worldBuilderSelectionContext\(item=selectedImage\)/);
  assert.match(prototype,/placementId:String\(item\.id\|\|''\)/);
  assert.match(prototype,/postWorldBuilderHostMessage\('selection-context'/);
  assert.match(prototype,/function selectUserImage\(item\)[\s\S]*?publishWorldBuilderSelectionContext\(\);/);
  assert.match(prototype,/function deselectUserImage\(announceChange=false\)[\s\S]*?publishWorldBuilderSelectionContext\(\);/);
});

test('host bridge forwards placed selection identity into the Blazor controller',()=>{
  const bridge=read('wwwroot/worldbuilder-source-host.js');
  assert.match(bridge,/data\.type==="selection-context"/);
  assert.match(bridge,/ReceiveWorldBuilderSelectionContextAsync/);
});

test('map saves preserve canonical Asset Context extensions',()=>{
  const razor=read('Components/UniversalInterface.razor');
  const source=read('WorldSession.WorldBuilderSource.cs');
  assert.match(razor,/MergeWorldBuilderRepresentationState\([\s\S]{0,120}?current\?\.State,[\s\S]{0,100}?SelectedDeedRegionId/);
  assert.match(source,/if \(!incoming\.ContainsKey\(property\.Key\)\)[\s\S]{0,120}?property\.Value\?\.DeepClone\(\)/);
  assert.match(source,/string\.Equals\(property\.Key, "userLayers", StringComparison\.Ordinal\)/);
  assert.match(razor,/SaveWorldBuilderSourceAsync\([\s\S]{0,120}?mergedState,[\s\S]{0,100}?_inspectionEditMode,[\s\S]{0,100}?inspectionReason/);
});

test('asset context prioritizes placed identity and persists it in canonical world source context',()=>{
  const razor=read('Components/UniversalInterface.razor');
  assert.match(razor,/HasWorldBuilderSelection=>!string\.IsNullOrWhiteSpace\(_worldBuilderSelectionId\)/);
  assert.match(razor,/\?\$"placement:\{_worldBuilderSelectionId\}"/);
  assert.match(razor,/entry\["placementId"\]=placementId/);
  assert.match(razor,/await Session\.SaveWorldBuilderSourceAsync\([\s\S]{0,140}?document\.RootElement\.Clone\(\),[\s\S]{0,100}?_inspectionEditMode,[\s\S]{0,100}?inspectionReason/);
  assert.match(razor,/if\(IsBuilderStage\)[\s\S]*?ToggleAssetContext\(\)/);
});
