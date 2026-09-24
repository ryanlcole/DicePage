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
  // Prevent real asynchronous image collision fetches outliving JSDOM.close();
  // these tests exercise interaction geometry, not external asset decoding.
  w.fetch=async()=>({ok:false});
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
    // Same selection path auto-opens the editor; image/sprite choose Image.
    assert.equal(Array.from(f.d.querySelectorAll('#keyboardTabs button')).find(b=>b.textContent==='Labels')?.getAttribute('aria-selected'),'true');
    // Region tiers are independent of world tiers. A new regional cake
    // leaves the base city attached to the same immutable parent terrain.
    tab(f,'Tiers');
    const addTier=Array.from(f.d.querySelectorAll('#keyboardKeys button')).find(b=>b.textContent.includes('NEW TIER'));
    assert.ok(addTier);addTier.click();
    tier(f,'Region Tier 2');
    assert.equal(layer.hidden,false);
    assert.equal(region.hidden,false,'base city persists below the upper regional tier');
    tier(f,'Region Base');
    assert.equal(layer.hidden,false);
  }finally{f.close()}
});


test('hex hitbox and snap coordinates share the same column-staggered geometry',async()=>{
  const f=fixture('new');try{
    const geometry=f.w.ShaelvienPrototype.regionGeometry;
    assert.ok(geometry);
    assert.equal(geometry.extents('hex').width,22.75);
    assert.equal(geometry.extents('hex').height,30.5);
    f.d.querySelector('[data-tier-select]').click();
    for(const cell of [0,31,319,899]){
      const button=f.d.querySelector('.region-definition-cell[data-cell="'+cell+'"]');
      assert.ok(button);
      const center=geometry.center(cell,'hex'),extent=geometry.extents('hex');
      assert.ok(Math.abs((parseFloat(button.style.left)+50/extent.width)/100-center.x)<1e-9);
      assert.ok(Math.abs((parseFloat(button.style.top)+50/extent.height)/100-center.y)<1e-9);
      assert.equal(geometry.cellAt(center.x,center.y,'hex'),cell);
    }
    assert.equal(geometry.cellAt(.5,.5,'square'),15*30+15);
    // Let fit/preview requestAnimationFrame work finish while JSDOM is alive.
    await tick();await tick();await tick();
  }finally{f.close()}
});



test('canonical lake persists under an editable city attached to the SAME world tier',async()=>{
  const f=fixture('existing');try{
    host(f,'catalog',{regions:[deed]});
    host(f,'world-source',{worldSource:{
      worldId:'deed-runtime-test',activeRegionId:'region-test',
      state:{worldId:'deed-runtime-test',tiles:[
        {id:'lake-source',name:'Lake',image:'data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs',
         tierIndex:0,layerOffset:2,x:.07,y:.07,placementZoom:1}
      ],userLayers:[
        {id:'test-city',regionId:'region-test',assetId:'city-registered-asset',name:'Regional City',
         kind:'image',originalSrc:'data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs',
         tier:0,layer:3,x:.088,y:.082,committed:true}
      ]}
    }});
    await tick();await tick();
    const lake=f.d.querySelector('.region-world-source-tile[aria-label="Lake"]');
    const city=f.d.querySelector('.region-edit-layer img.user-image-placement');
    assert.ok(lake,'the full canonical source includes its lake tile');
    assert.ok(city,'the placed city is a separate editable overlay');
    assert.equal(lake.style.display,'block','source lake must remain visible at the selected tier');
    assert.equal(lake.dataset.sourceLocked,'true','the lake belongs to the locked world map');
    assert.equal(city.dataset.tier,'0');
    assert.equal(city.dataset.layer,'3');
    assert.equal(city.style.pointerEvents,'auto');
    assert.equal(city.style.visibility,'visible');
    assert.equal(f.d.querySelector('.region-edit-layer').dataset.tier,'0');
    const initial=f.w.ShaelvienPrototype.getViewerState().userLayers.find(x=>x.id==='test-city');
    assert.equal(initial.parallaxMode,'anchored');
    assert.equal(initial.parallaxX,0);
    assert.equal(initial.parallaxY,0);
    // Move the camera like an iPhone swipe. Neither the lake nor the city
    // receives independent parallax while editing the same parent world tier.
    const pointer=(kind,cx,cy)=>{
      const event=new f.w.Event(kind,{bubbles:true,cancelable:true});
      for(const [name,value] of Object.entries({pointerType:'touch',pointerId:71,button:0,clientX:cx,clientY:cy}))
        Object.defineProperty(event,name,{value});
      f.stage.dispatchEvent(event);
    };
    pointer('pointerdown',220,210);
    pointer('pointermove',352,272);
    pointer('pointerup',352,272);
    const moved=f.w.ShaelvienPrototype.getViewerState().userLayers.find(x=>x.id==='test-city');
    assert.equal(moved.parallaxMode,'anchored');
    assert.equal(moved.parallaxX,0);
    assert.equal(moved.parallaxY,0);
    assert.equal(f.d.getElementById('surfacePlane').dataset.parallaxX,'0.0000');
    assert.equal(lake.style.display,'block','camera movement must not hide world lakes');
    tab(f,'Select');
    const select=f.d.querySelector('.placed-content-select');
    assert.ok(select);select.value='test-city';
    select.dispatchEvent(new f.w.Event('change',{bubbles:true}));
    assert.ok(f.d.getElementById('keyboardKeys').textContent.includes('MAP ATTACHED'));
    assert.ok(f.d.getElementById('keyboardKeys').textContent.includes('LAYER 4'));
  }finally{f.close()}
});


test('claimed projection renders only selected parent cells, not full-world PNGs',async()=>{
  const f=fixture('existing');try{
    host(f,'catalog',{regions:[deed]});
    const image='data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs';
    host(f,'world-source',{worldSource:{
      worldId:'deed-runtime-test',regionId:'region-test',activeRegionId:'region-test',
      state:{
        projection:'region-child-v1',worldId:'deed-runtime-test',regionId:'region-test',
        parentTierIndex:0,gridShape:'hex',sourcePixelWidth:300,sourcePixelHeight:300,
        selectedCells:[32,33,62,63],
        sourceCells:[32,33,62,63].map(cell=>({id:'source-'+cell,cellIndex:cell})),
        sourceTileIndex:[{id:'source-32',cellIndex:32,layerOffset:0,image}],
        publicTilePattern:'/Game/prototype/region-cells/geonaph/{shape}/0/{cell}.webp',
        tiles:[{id:'lake',name:'Lake',image,tierIndex:0,layerOffset:1,x:.1,y:.1}],
        userLayers:[
          {id:'base-city',regionId:'region-test',assetId:'city-fixture',name:'Base City',kind:'image',originalSrc:image,
           tier:0,relativeTier:0,layer:2,x:.1,y:.1,committed:true},
          {id:'upper-city',regionId:'region-test',assetId:'city-fixture',name:'Upper City',kind:'image',originalSrc:image,
           tier:1,relativeTier:1,layer:2,x:.1,y:.1,committed:true}
        ],
        relativeTiers:[{id:'region-test:tier:0',index:0,label:'Region Base'},
                       {id:'region-test:tier:1',index:1,label:'Region Tier 2'}]
      }
    }});
    await tick();await tick();
    assert.equal(f.stage.dataset.sourceScope,'selected-parent-cells');
    assert.equal(f.stage.dataset.sourceCellCount,'4');
    assert.equal(f.d.querySelectorAll('.region-world-source-tier-image').length,0);
    assert.equal(f.d.getElementById('surfacePlane').getAttribute('src'),null);
    const sourceCells=Array.from(f.d.querySelectorAll('.region-world-source-cell'));
    assert.equal(sourceCells.length,4);
    assert.deepEqual(sourceCells.map(n=>Number(n.dataset.cell)).sort((a,b)=>a-b),[32,33,62,63]);
    assert.ok(!f.d.documentElement.innerHTML.includes('secret-99.webp'));
    const base=f.d.querySelector('.region-edit-layer [alt="Base City"]');
    const upper=f.d.querySelector('.region-edit-layer [alt="Upper City"]');
    assert.ok(base);assert.ok(upper);
    assert.equal(upper.hidden,true,'new regional tier does not appear before selection');
    const info=f.w.ShaelvienPrototype.getViewerState().regionChild;
    assert.equal(info.parentTierIndex,0);
    assert.equal(info.relativeTiers.length,2);
    tab(f,'Tiers');tier(f,'Region Tier 2');
    assert.equal(base.hidden,false);
    assert.equal(upper.hidden,false);
    assert.equal(f.d.querySelector('.region-world-source-tile[aria-label="Lake"]').dataset.sourceLocked,'true');
  }finally{f.close()}
});


test('stale database error cannot cover an already loaded claimed projection',async()=>{
  const f=fixture('existing');try{
    host(f,'catalog',{regions:[deed]});
    const image='data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs';
    host(f,'world-source',{worldSource:{
      worldId:'deed-runtime-test',regionId:'region-test',activeRegionId:'region-test',
      state:{
        projection:'region-child-v1',worldId:'deed-runtime-test',regionId:'region-test',
        parentTierIndex:0,gridShape:'hex',sourcePixelWidth:300,sourcePixelHeight:300,
        selectedCells:[32,33,62,63],
        sourceCells:[32,33,62,63].map(cell=>({id:'source-'+cell,cellIndex:cell})),
        sourceTileIndex:[{id:'source-32',cellIndex:32,layerOffset:0,image}],
        publicTilePattern:'/Game/prototype/region-cells/geonaph/{shape}/0/{cell}.webp',
        tiles:[],userLayers:[],relativeTiers:[{id:'region-test:tier:0',index:0,label:'Region Base'}]
      }
    }});
    await tick();await tick();
    const loading=f.d.getElementById('loading');
    assert.equal(f.stage.dataset.sourceScope,'selected-parent-cells');
    assert.equal(loading.hidden,true);
    host(f,'map-load-error',{message:'stale initial request failed'});
    await tick();
    assert.equal(loading.hidden,true,'a stale refresh error must not cover valid region cells');
    assert.equal(f.stage.dataset.sourceScope,'selected-parent-cells');
  }finally{f.close()}
});
