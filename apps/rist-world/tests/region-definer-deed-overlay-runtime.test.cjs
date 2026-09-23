const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {JSDOM}=require('jsdom');

const root=path.join(__dirname,'../wwwroot/prototype');
function fixture(flow='new'){
  const dom=new JSDOM(fs.readFileSync(path.join(root,'index.html'),'utf8'),{
    url:`https://viewer.test/Game/prototype/index.html?live-worldbuilder=1&mode=regiondefiner&seed=empty&worldId=deed-runtime-test&access=edit&regionFlow=${flow}&regionId=${flow==='existing'?'region-test':''}`,
    runScripts:'outside-only',pretendToBeVisual:true
  });
  const w=dom.window,d=w.document,stage=d.getElementById('stage');
  stage.getBoundingClientRect=()=>({x:0,y:0,left:0,top:0,right:800,bottom:600,width:800,height:600});
  w.HTMLElement.prototype.getClientRects=function(){return this.closest('[hidden]')?[]:[{}]};
  w.matchMedia=()=>({matches:false});
  w.ResizeObserver=class{observe(){}disconnect(){}};
  const ctx=dom.getInternalVMContext();
  for(const file of ['viewer-input.js','prototype.js']){
    vm.runInContext(fs.readFileSync(path.join(root,file),'utf8'),ctx,{filename:file});
  }
  return{w,d,stage,ctx,close(){w.close()}};
}

const deed={id:'region-test',name:'Test deed',tierIndex:0,gridShape:'hex',selectedCells:[32,33,62,63]};

test('deed acceptance fully detaches the grid and keyboard rerenders do not revive it',()=>{
  const f=fixture('new');try{
    vm.runInContext("chooseRegionClaimTier('sea')",f.ctx);
    assert.ok(f.d.querySelector('.region-definition-grid'),'new deed must have a selection grid');
    vm.runInContext(`applyClaimedRegionCrop(${JSON.stringify(deed)})`,f.ctx);
    assert.equal(f.d.querySelector('.region-definition-grid'),null);
    assert.ok(f.stage.classList.contains('region-cropped'),'canonical deed mask remains');
    assert.match(f.d.getElementById('world').style.maskImage,/url\\(/);
    vm.runInContext("keyboardMode='Select';renderKeyboardTabs();renderKeyboardKeys();updateRegionSelectionOverlay()",f.ctx);
    assert.equal(f.d.querySelector('.region-definition-grid'),null);
    assert.ok(f.d.getElementById('keyboardTabs').textContent.includes('Tiles'),'WorldBuilder tools are active');
    vm.runInContext("startRegionClaim();chooseRegionClaimTier('sea')",f.ctx);
    assert.ok(f.d.querySelector('.region-definition-grid'),'new region starts with an independent selection grid');
  }finally{f.close()}
});

test('opening an existing deed never creates the grid, including before metadata arrives',()=>{
  const f=fixture('existing');try{
    assert.equal(f.d.querySelector('.region-definition-grid'),null);
    vm.runInContext(`applyClaimedRegionCrop(${JSON.stringify(deed)})`,f.ctx);
    vm.runInContext("renderKeyboardTabs();renderKeyboardKeys();updateRegionSelectionOverlay()",f.ctx);
    assert.equal(f.d.querySelector('.region-definition-grid'),null);
  }finally{f.close()}
});
