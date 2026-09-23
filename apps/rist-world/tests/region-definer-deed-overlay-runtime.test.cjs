// Exercise the real viewer UI/parent bridge. prototype.js is an IIFE: its
// internal functions are intentionally NOT globals accessible to vm.runInContext.
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
  for(const file of ['viewer-input.js','prototype.js']){
    vm.runInContext(fs.readFileSync(path.join(root,file),'utf8'),dom.getInternalVMContext(),{filename:file});
  }
  return{w,d,stage,close(){w.close()}};
}

const deed={id:'region-test',name:'Test deed',tierIndex:0,gridShape:'hex',selectedCells:[32,33,62,63]};
function host(f,type,data={}){
  f.w.dispatchEvent(new f.w.MessageEvent('message',{
    origin:f.w.location.origin,source:f.w.parent,
    data:{source:'shaelvien-regiondefiner-host',type,...data}
  }));
}
function tick(){return new Promise(resolve=>setTimeout(resolve,20))}
function tab(f,name){
  const button=Array.from(f.d.querySelectorAll('#keyboardTabs button')).find(x=>x.textContent===name);
  assert.ok(button,`Missing ${name} tab`);
  button.click();
}
function tier(f,name){
  f.d.getElementById('tierToggle').click();
  const button=f.d.querySelector(`#tierMenu button[aria-label="${name}"]`);
  assert.ok(button,`Missing ${name} tier`);button.click();
}

test('successful deed detaches the claim grid and Select never restores it',async()=>{
  const f=fixture('new');try{
    f.d.querySelector('[data-tier-select]').click();
    assert.ok(f.d.querySelector('.region-definition-grid'),'a new deed has a selection grid');
    host(f,'region-created',{region:deed});
    await tick();
    assert.equal(f.d.querySelector('.region-definition-grid'),null);
    assert.ok(f.stage.classList.contains('region-cropped'));
    assert.equal(f.stage.dataset.cropMode,'visibility-mask');
    tab(f,'Select');
    assert.equal(f.d.querySelector('.region-definition-grid'),null);
    assert.ok(f.d.getElementById('keyboardTabs').textContent.includes('Tiles'));
  }finally{f.close()}
});

test('opening existing deed never creates a selectable grid',async()=>{
  const f=fixture('existing');try{
    assert.equal(f.d.querySelector('.region-definition-grid'),null);
    host(f,'catalog',{regions:[deed]});
    await tick();
    tab(f,'Select');
    assert.equal(f.d.querySelector('.region-definition-grid'),null);
    assert.ok(f.stage.classList.contains('region-cropped'));
  }finally{f.close()}
});

test('base world city stays locked; distinct city registered as regional overlay is editable above deed tier',async()=>{
  const f=fixture('existing');try{
    host(f,'catalog',{regions:[deed]});
    host(f,'world-source',{worldSource:{
      worldId:'deed-runtime-test',activeRegionId:'region-test',
      state:{worldId:'deed-runtime-test',userLayers:[
        {kind:'label',id:'world-city',name:'World city',text:'World city',tier:0,layer:1,x:.15,y:.15,committed:true},
        {kind:'label',id:'region-city',regionId:'region-test',name:'Region city',text:'Region city',
         tier:0,layer:1,x:.15,y:.15,committed:true}
      ]}
    }});
    await tick();await tick();
    const base=Array.from(f.d.querySelectorAll('.user-label-placement')).find(n=>n.textContent==='World city');
    const region=Array.from(f.d.querySelectorAll('.user-label-placement')).find(n=>n.textContent==='Region city');
    assert.ok(base,'parent-world item is present only as visual context');
    assert.ok(region,'region item must be hydrated');
    const layer=f.d.querySelector('.region-edit-layer');
    assert.ok(layer&&!layer.hidden);
    assert.equal(layer.dataset.tier,'0');
    assert.equal(layer.style.zIndex,'180');
    assert.equal(region.parentElement,layer);
    assert.equal(base.parentElement,f.d.getElementById('world'));
    assert.equal(base.style.pointerEvents,'none');
    assert.equal(region.style.pointerEvents,'auto');
    tab(f,'Select');
    const options=Array.from(f.d.querySelectorAll('.placed-content-select option')).map(x=>x.textContent);
    assert.ok(options.some(x=>x.includes('Region city')));
    assert.ok(!options.some(x=>x.includes('World city')),'world source is never an editable option');
    const event=new f.w.Event('pointerdown',{bubbles:true,cancelable:true});
    for(const [key,value] of Object.entries({pointerType:'touch',pointerId:42,button:0,clientX:160,clientY:160}))
      Object.defineProperty(event,key,{value});
    region.dispatchEvent(event);
    assert.equal(region.classList.contains('selected'),true);
    assert.equal(event.defaultPrevented,true);
    tier(f,'Hills / Low Clouds');
    assert.equal(layer.hidden,true);
    tier(f,'Sea Level');
    assert.equal(layer.hidden,false);
  }finally{f.close()}
});
