const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {JSDOM}=require('jsdom');

const root=path.join(__dirname,'../wwwroot/prototype');

function fixture(flow='new',options={}){
  const dom=new JSDOM(fs.readFileSync(path.join(root,'index.html'),'utf8'),{
    url:`https://viewer.test/Game/prototype/index.html?live-worldbuilder=1&mode=regiondefiner&seed=empty&worldId=deed-runtime-test&access=edit&regionFlow=${flow}&regionId=${flow==='existing'?'region-test':''}`,
    runScripts:'outside-only',
    pretendToBeVisual:true
  });
  const w=dom.window,d=w.document,stage=d.getElementById('stage');
  stage.getBoundingClientRect=()=>({x:0,y:0,left:0,top:0,right:800,bottom:600,width:800,height:600});
  w.HTMLElement.prototype.getClientRects=function(){return this.closest('[hidden]')?[]:[{}]};
  w.matchMedia=()=>({matches:false});
  if(options.sessionToken)w.sessionStorage.setItem('rist.session',options.sessionToken);
  w.fetch=options.fetch||(async()=>({ok:false,status:404}));
  w.ResizeObserver=class{observe(){}disconnect(){}};
  for(const file of ['viewer-input.js','prototype.js']){
    vm.runInContext(fs.readFileSync(path.join(root,file),'utf8'),dom.getInternalVMContext(),{filename:file});
  }
  return{w,d,stage,close(){w.close()}};
}

const deed={
  id:'region-test',
  name:'Test deed',
  tierIndex:0,
  gridShape:'hex',
  selectedCells:[32,33,62,63],
  sourceLayerOffsets:[0,1,2,3,4,5,6,7,8,9]
};
const image='data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs';

function host(f,type,data={}){
  f.w.dispatchEvent(new f.w.MessageEvent('message',{
    origin:f.w.location.origin,
    source:f.w.parent,
    data:{source:'shaelvien-regiondefiner-host',type,...data}
  }));
}
function tick(){return new Promise(resolve=>setTimeout(resolve,20))}
function tab(f,name){
  const button=Array.from(f.d.querySelectorAll('#keyboardTabs button')).find(x=>x.textContent===name);
  assert.ok(button,`Missing ${name} tab`);
  button.click();
}
function clickKey(f,text){
  const button=Array.from(f.d.querySelectorAll('#keyboardKeys button')).find(x=>x.textContent.includes(text));
  assert.ok(button,`Missing keyboard key containing ${text}`);
  button.click();
}
function projectedState(overrides={}){
  return{
    projection:'region-world-z-v2',
    worldId:'deed-runtime-test',
    regionId:'region-test',
    parentTierIndex:0,
    gridShape:'hex',
    sourcePixelWidth:300,
    sourcePixelHeight:300,
    selectedCells:[32,33,62,63],
    sourceCells:[32,33,62,63].map(cell=>({id:'source-'+cell,cellIndex:cell})),
    sourceTileIndex:[{id:'source-32',cellIndex:32,layerOffset:0,image}],
    publicTilePattern:'/Game/prototype/region-cells/geonaph/{shape}/0/{cell}.webp',
    tiles:[{id:'lake',name:'Lake',image,tierIndex:0,layerOffset:2,x:.1,y:.1}],
    sourceUserLayers:[
      {kind:'label',id:'world-city',name:'World City',text:'World City',tier:0,layer:2,x:.1,y:.1,committed:true}
    ],
    userLayers:[
      {kind:'label',id:'region-city',regionId:'region-test',name:'Region City',text:'Region City',
       tier:0,worldLayer:2,layer:2,regionLayer:1,z100:201,x:.1,y:.1,committed:true}
    ],
    zModel:{worldIntegerMin:0,worldIntegerMax:9,regionHundredthMin:1,regionHundredthMax:9,storage:'z100'},
    ...overrides
  };
}

test('successful deed removes selection grid and transitions directly into the editor',async()=>{
  const f=fixture('new');
  try{
    f.d.querySelector('[data-tier-select]').click();
    assert.ok(f.d.querySelector('.region-definition-grid'),'new deed must expose selection grid');
    host(f,'region-created',{
      region:deed,
      worldSource:{
        worldId:'deed-runtime-test',
        regionId:'region-test',
        activeRegionId:'region-test',
        state:projectedState()
      }
    });
    await tick();await tick();
    assert.equal(f.d.querySelector('.region-definition-grid'),null);
    assert.ok(f.stage.classList.contains('region-cropped'));
    assert.ok(f.stage.classList.contains('region-build-mode'));
    assert.ok(f.stage.classList.contains('region-free-placement'));
    assert.equal(f.stage.dataset.cropMode,'selected-source-cells');
    assert.equal(f.stage.dataset.regionEntry,'editor');
    assert.equal(f.stage.dataset.sourceScope,'selected-parent-cells');
    assert.equal(f.d.getElementById('world').style.maskImage,'none');
    assert.equal(f.d.getElementById('viewerKeyboard').hidden,false);
    assert.ok(Array.from(f.d.querySelectorAll('#keyboardTabs button')).some(x=>x.textContent==='Image'));
  }finally{f.close()}
});

test('opening an existing deed never creates a second selectable grid',async()=>{
  const f=fixture('existing');
  try{
    assert.equal(f.d.querySelector('.region-definition-grid'),null);
    host(f,'catalog',{regions:[deed]});
    await tick();
    tab(f,'Select');
    assert.equal(f.d.querySelector('.region-definition-grid'),null);
    assert.ok(f.stage.classList.contains('region-cropped'));
  }finally{f.close()}
});

test('hex selection uses the same canonical cell geometry as the claimed coordinates',async()=>{
  const f=fixture('new');
  try{
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
    await tick();
  }finally{f.close()}
});

test('region placement stays continuous inside the deed instead of snapping to cell centers',async()=>{
  const f=fixture('existing');
  try{
    host(f,'catalog',{regions:[deed]});
    host(f,'world-source',{worldSource:{
      worldId:'deed-runtime-test',
      regionId:'region-test',
      activeRegionId:'region-test',
      state:projectedState()
    }});
    await tick();await tick();

    const geometry=f.w.ShaelvienPrototype.regionGeometry;
    const center=geometry.center(32,'hex');
    const free={x:center.x+.003,y:center.y+.004};
    assert.equal(geometry.cellAt(free.x,free.y,'hex'),32);
    const kept=geometry.constrain(free.x,free.y);
    assert.ok(Math.abs(kept.x-free.x)<1e-12);
    assert.ok(Math.abs(kept.y-free.y)<1e-12);
    assert.ok(Math.abs(kept.x-center.x)>.001,'valid placement must not be recentered');

    const outside=geometry.center(400,'hex');
    const constrained=geometry.constrain(outside.x,outside.y);
    assert.ok(deed.selectedCells.includes(geometry.cellAt(constrained.x,constrained.y,'hex')));
  }finally{f.close()}
});

test('RegionDefiner build controls stay lifted and the claim grid cannot cover asset editing',()=>{
  const css=fs.readFileSync(path.join(root,'prototype.css'),'utf8');
  assert.ok(css.includes('.stage.region-definer-mode .keyboard{bottom:var(--region-control-lift)}'));
  assert.ok(css.includes('.stage.region-definer-mode.keyboard-open .bottom-slider{bottom:calc(min(36vh,290px) + var(--region-control-lift))}'));
  assert.ok(css.includes('.stage.region-build-mode .region-definition-grid,.stage.region-asset-moving .region-definition-grid{display:none!important;opacity:0!important;pointer-events:none!important}'));
});

test('saved personal region assets keep stable identity and retry authenticated hydration',async()=>{
  let storageAttempts=0;
  const f=fixture('existing',{
    sessionToken:'test-session',
    fetch:async url=>{
      const href=String(url||'');
      if(href.includes('auth-config.json'))return{
        ok:true,status:200,json:async()=>({apiBaseUrl:'https://storage.test'})
      };
      if(href.startsWith('https://storage.test/storage/download')){
        storageAttempts++;
        if(storageAttempts===1)throw new Error('auth bridge still warming');
        return{ok:true,status:200,json:async()=>({url:'https://signed.test/city.png'})};
      }
      return{ok:false,status:404,blob:async()=>({})};
    }
  });
  try{
    host(f,'catalog',{regions:[deed]});
    host(f,'world-source',{worldSource:{
      worldId:'deed-runtime-test',
      regionId:'region-test',
      activeRegionId:'region-test',
      state:projectedState({userLayers:[{
        kind:'image',id:'saved-city',regionId:'region-test',name:'Saved City',
        assetId:'private:uploads/images/my-images/city.png',
        personalAssetKey:'uploads/images/my-images/city.png',
        originalSrc:'',transparentSrc:'',transparent:false,
        tier:0,worldLayer:0,layer:0,regionLayer:1,z100:1,x:.1,y:.1,size:1,rotation:0,opacity:1,committed:true
      }]})
    }});
    await new Promise(resolve=>setTimeout(resolve,650));
    const city=Array.from(f.d.querySelectorAll('img.user-image-placement')).find(node=>node.alt==='Saved City');
    assert.ok(city,'saved personal image must remain in the restored layer list while auth reconnects');
    assert.equal(city.dataset.assetPending,'false');
    assert.ok(city.src.includes('https://signed.test/city.png'));
    assert.ok(storageAttempts>=2,'personal asset hydration must retry after an early auth/storage failure');
  }finally{f.close()}
});

test('RegionDefiner save bridge performs canonical read-after-write verification',()=>{
  const hostSource=fs.readFileSync(path.join(root,'../region-definer-host.js'),'utf8');
  assert.ok(hostSource.includes('GetRegionSourceForPrototypeAsync'));
  assert.ok(hostSource.includes('verified=wanted.every(id=>persisted.has(id))'));
  const prototype=fs.readFileSync(path.join(root,'prototype.js'),'utf8');
  assert.ok(prototype.includes('Region database verification did not confirm the save.'));
});

test('claimed RegionDefiner loads only selected WorldBuilder cells and keeps parent content locked',async()=>{
  const f=fixture('existing');
  try{
    host(f,'catalog',{regions:[deed]});
    host(f,'world-source',{worldSource:{
      worldId:'deed-runtime-test',
      regionId:'region-test',
      activeRegionId:'region-test',
      state:projectedState()
    }});
    await tick();await tick();

    assert.equal(f.stage.dataset.sourceScope,'selected-parent-cells');
    assert.equal(f.stage.dataset.sourceCellCount,'4');
    assert.equal(f.stage.dataset.renderer,'region-world-z-v2');
    assert.equal(f.d.querySelectorAll('.region-world-source-tier-image').length,0);
    assert.equal(f.d.getElementById('surfacePlane').getAttribute('src'),null);

    const cells=Array.from(f.d.querySelectorAll('.region-world-source-cell'));
    assert.equal(cells.length,4);
    assert.deepEqual(cells.map(n=>Number(n.dataset.cell)).sort((a,b)=>a-b),[32,33,62,63]);

    const lake=f.d.querySelector('.region-world-source-tile[aria-label="Lake"]');
    assert.ok(lake);
    assert.equal(lake.dataset.sourceLocked,'true');

    const worldLabel=Array.from(f.d.querySelectorAll('.user-label-placement')).find(n=>n.textContent==='World City');
    const regionLabel=Array.from(f.d.querySelectorAll('.user-label-placement')).find(n=>n.textContent==='Region City');
    assert.ok(worldLabel);
    assert.ok(regionLabel);
    assert.equal(worldLabel.style.pointerEvents,'none','WorldBuilder source stays locked');
    assert.equal(regionLabel.style.pointerEvents,'auto','regional overlay stays editable');
    assert.equal(worldLabel.dataset.z100,'200');
    assert.equal(regionLabel.dataset.z100,'201');
    assert.equal(regionLabel.dataset.tier,'0','regional overlay never creates a new WorldBuilder tier');

    tab(f,'Select');
    const picker=f.d.querySelector('.placed-content-select');
    assert.ok(picker);
    const labels=Array.from(picker.options).map(x=>x.textContent);
    assert.ok(labels.some(x=>x.includes('Region City')));
    assert.ok(!labels.some(x=>x.includes('World City')),'locked parent object cannot enter editable dropdown');
  }finally{f.close()}
});

test('region overlays use exact hundredths and stay map-attached while World Z remains integer',async()=>{
  const f=fixture('existing');
  try{
    host(f,'catalog',{regions:[deed]});
    host(f,'world-source',{worldSource:{
      worldId:'deed-runtime-test',
      regionId:'region-test',
      activeRegionId:'region-test',
      state:projectedState()
    }});
    await tick();await tick();

    tab(f,'Select');
    const picker=f.d.querySelector('.placed-content-select');
    picker.value='region-city';
    picker.dispatchEvent(new f.w.Event('change',{bubbles:true}));
    assert.equal(
      Array.from(f.d.querySelectorAll('#keyboardTabs button')).find(b=>b.textContent==='Labels')?.getAttribute('aria-selected'),
      'true'
    );

    let state=f.w.ShaelvienPrototype.getViewerState();
    let city=state.userLayers.find(x=>x.id==='region-city');
    assert.equal(city.worldLayer,2);
    assert.equal(city.regionLayer,1);
    assert.equal(city.z100,201);
    assert.equal(city.parallaxMode,'anchored');
    assert.equal(city.parallaxX,0);
    assert.equal(city.parallaxY,0);

    clickKey(f,'REGION L +');
    state=f.w.ShaelvienPrototype.getViewerState();
    city=state.userLayers.find(x=>x.id==='region-city');
    assert.equal(city.worldLayer,2);
    assert.equal(city.regionLayer,2);
    assert.equal(city.z100,202);

    clickKey(f,'WORLD Z +');
    state=f.w.ShaelvienPrototype.getViewerState();
    city=state.userLayers.find(x=>x.id==='region-city');
    assert.equal(city.worldLayer,3);
    assert.equal(city.regionLayer,2);
    assert.equal(city.z100,302);
    assert.equal(city.tier,0,'fractional region depth must not promote object to a new WorldBuilder tier');
    assert.equal(city.parallaxMode,'anchored');
  }finally{f.close()}
});

test('stale database error cannot cover an already loaded filtered region',async()=>{
  const f=fixture('existing');
  try{
    host(f,'catalog',{regions:[deed]});
    host(f,'world-source',{worldSource:{
      worldId:'deed-runtime-test',
      regionId:'region-test',
      activeRegionId:'region-test',
      state:projectedState({tiles:[],sourceUserLayers:[],userLayers:[]})
    }});
    await tick();await tick();

    const loading=f.d.getElementById('loading');
    assert.equal(f.stage.dataset.sourceScope,'selected-parent-cells');
    assert.equal(loading.hidden,true);

    host(f,'map-load-error',{message:'stale initial request failed'});
    await tick();

    assert.equal(loading.hidden,true);
    assert.equal(f.stage.dataset.sourceScope,'selected-parent-cells');
  }finally{f.close()}
});
