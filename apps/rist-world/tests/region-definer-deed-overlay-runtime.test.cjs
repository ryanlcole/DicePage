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
    assert.equal(f.stage.dataset.cropMode,'visibility-mask');
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


test('editable region objects render above their selected tier while the world remains locked',async()=>{
  const f=fixture('existing');try{
    vm.runInContext(`applyClaimedRegionCrop(${JSON.stringify(deed)})`,f.ctx);
    const base=await vm.runInContext(`attachRestoredLayer({
      kind:'label',id:'world-city',name:'World city',text:'World city',tier:0,layer:1,x:.15,y:.15,committed:true
    },{sourceLocked:true,regionOverlay:false,canonicalSource:true})`,f.ctx);
    const region=await vm.runInContext(`attachRestoredLayer({
      kind:'label',id:'region-city',regionId:'region-test',name:'Region city',text:'Region city',
      tier:0,layer:1,x:.15,y:.15,committed:true
    },{sourceLocked:false,regionOverlay:true,canonicalSource:true})`,f.ctx);
    vm.runInContext('updateLayerOrder();applyParallax()',f.ctx);
    const layer=f.d.querySelector('.region-edit-layer');
    assert.ok(layer&&!layer.hidden);
    assert.equal(layer.dataset.tier,'0');
    assert.equal(layer.style.zIndex,'180');
    assert.equal(region.node.parentElement,layer);
    assert.equal(base.node.parentElement,f.d.getElementById('world'));
    assert.equal(base.node.style.pointerEvents,'none');
    assert.equal(region.node.style.pointerEvents,'auto');
    assert.deepEqual(Array.from(vm.runInContext('selectablePlacedContent().map(item=>item.id)',f.ctx)),['region-city']);
    const event=new f.w.Event('pointerdown',{bubbles:true,cancelable:true});
    for(const [key,value] of Object.entries({pointerType:'touch',pointerId:42,button:0,clientX:160,clientY:160}))
      Object.defineProperty(event,key,{value});
    region.node.dispatchEvent(event);
    assert.equal(vm.runInContext('selectedImage?.id',f.ctx),'region-city');
    assert.equal(event.defaultPrevented,true);
    vm.runInContext("setViewerTier('hills')",f.ctx);
    assert.equal(layer.hidden,true,'overlay belongs to its deed tier only');
    vm.runInContext("setViewerTier('sea')",f.ctx);
    assert.equal(layer.hidden,false);
  }finally{f.close()}
});
