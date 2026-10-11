const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

const root=path.resolve(__dirname,'..');
const razor=fs.readFileSync(path.join(root,'Components/UniversalInterface.razor'),'utf8');
const prototype=fs.readFileSync(path.join(root,'wwwroot/prototype/prototype.js'),'utf8');

test('World Builder enters WORLD before any Region takeover',()=>{
  assert.match(razor,/void BeginGameMasterPath\(\)[\s\S]*?_builderChainIndex=0;[\s\S]*?_assetScope="WORLD";[\s\S]*?_stage=Stage\.WorldHome;/);
  assert.doesNotMatch(razor,/void BeginGameMasterPath\(\)[\s\S]{0,900}?_regionDefinerOpen=true;/);
});

test('WORLD HOME primary action edits World depth before Region definition',()=>{
  assert.match(razor,/case Stage\.WorldHome:[\s\S]{0,240}?_stage=Stage\.WorldBuilderTier;[\s\S]{0,240}?SyncWorldBuilderDepthAsync/);
});

test('Region definition remains an explicit child action',()=>{
  assert.match(razor,/BeginOrSaveVisibleSpatialSelectionAsync\(\)[\s\S]*?_regionDefinerOpen=true;[\s\S]*?_builderChainIndex=1;[\s\S]*?_assetScope="REGION";/);
});

test('recursive scope and cube constants remain ordered',()=>{
  assert.match(prototype,/SCOPE_ORDER=Object\.freeze\(\['WORLD','REGION','LOCAL','INSTANCE'\]\)/);
  assert.match(prototype,/SCOPE_DEPTH_PREFIX=Object\.freeze\(\{WORLD:'Z',REGION:'R',LOCAL:'L',INSTANCE:'I'\}\)/);
  assert.match(prototype,/const SCOPE_GRID_COLUMNS=300;/);
  assert.match(prototype,/const SCOPE_GRID_ROWS=300;/);
  assert.match(prototype,/const LAYERS_PER_TIER=10;/);
});
