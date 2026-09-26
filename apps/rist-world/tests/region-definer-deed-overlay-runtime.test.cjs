const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {JSDOM}=require('jsdom');

const root=path.join(__dirname,'../wwwroot/prototype');

function fixture(flow='new',options={}){
  const mode=String(options.mode||'regiondefiner');
  const regionId=options.regionId!==undefined?String(options.regionId):(flow==='existing'?'region-test':'');
  const localId=options.localId!==undefined?String(options.localId):'';
  const dom=new JSDOM(fs.readFileSync(path.join(root,'index.html'),'utf8'),{
    url:`https://viewer.test/Game/prototype/index.html?live-worldbuilder=1&mode=${mode}&seed=empty&worldId=deed-runtime-test&access=edit&regionFlow=${flow}&regionId=${regionId}&localId=${localId}`,
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
  for(const file of ['viewer-input.js','image-engine.js','prototype.js']){
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
  const wanted=String(name||'').toUpperCase();
  const button=Array.from(f.d.querySelectorAll('#keyboardTabs button')).find(x=>String(x.textContent||'').toUpperCase()===wanted);
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
    assert.deepEqual(Array.from(f.d.querySelectorAll('#keyboardTabs button')).map(x=>x.textContent),['VIEW','BUILD','EDIT','LAYERS','MORE']);
  }finally{f.close()}
});

test('opening an existing deed never creates a second selectable grid',async()=>{
  const f=fixture('existing');
  try{
    assert.equal(f.d.querySelector('.region-definition-grid'),null);
    host(f,'catalog',{regions:[deed]});
    await tick();
    tab(f,'Edit');
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
  assert.ok(css.includes('.stage.region-definer-mode.keyboard-open .bottom-slider{bottom:calc(min(40vh,320px) + var(--region-control-lift))}'));
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

test('RegionDefiner save serializes objects mounted in the active deed even with stale item region ids',()=>{
  const prototype=fs.readFileSync(path.join(root,'prototype.js'),'utf8');
  assert.ok(prototype.includes('function regionSaveCandidates()'));
  assert.ok(prototype.includes('item.regionId=regionId;'));
  assert.ok(prototype.includes('regionEditLayer&&item.node.parentElement!==regionEditLayer'));
  assert.ok(prototype.includes("${LOCAL_DEFINER?'Local':'Region'} save payload was empty while"));
  assert.ok(prototype.includes('countMatches=persisted.size===Number(waiter.expectedCount||0)'));
});

test('RegionDefiner save bridge performs canonical read-after-write verification',()=>{
  const hostSource=fs.readFileSync(path.join(root,'../region-definer-host.js'),'utf8');
  assert.ok(hostSource.includes('GetRegionSourceForPrototypeAsync'));
  assert.ok(hostSource.includes('verified=wanted.every(id=>persisted.has(id))'));
  const prototype=fs.readFileSync(path.join(root,'prototype.js'),'utf8');
  assert.ok(prototype.includes('Region database verification did not confirm the save.'));
});

test('placed assets suppress native long-press menus and expose precise resizing',()=>{
  const source=fs.readFileSync(path.join(root,'prototype.js'),'utf8');
  const css=fs.readFileSync(path.join(root,'prototype.css'),'utf8');
  assert.ok(source.includes("stage.addEventListener('contextmenu'"));
  assert.ok(source.includes("function ensureAssetResizeOverlay()"));
  assert.ok(source.includes("asset-resize-handle"));
  assert.ok(source.includes("input.type='number';input.className='asset-size-number'"));
  assert.ok(source.includes("input.type='range';input.className='asset-size-range'"));
  assert.ok(css.includes('-webkit-touch-callout:none'));
  assert.ok(css.includes('.asset-resize-handle'));
});

test('sprite playback keeps a stable frame box and predecodes extracted frames',()=>{
  const source=fs.readFileSync(path.join(root,'prototype.js'),'utf8');
  assert.ok(source.includes('function stableAssetAspect(item)'));
  assert.ok(source.includes("item.node.style.aspectRatio=item.kind==='sprite'?String(stableAssetAspect(item)):''"));
  assert.ok(source.includes('await Promise.all(frames.map(src=>loadDataImage(src).catch(()=>null)))'));
  assert.ok(source.includes("if(item.kind!=='sprite')void primeCollisionMask(desired)"));
});

test('shared Worldbuilder and RegionDefiner asset keyboards filter selection by asset type',()=>{
  const source=fs.readFileSync(path.join(root,'prototype.js'),'utf8');
  assert.ok(source.includes('function selectablePlacedContentForMode(mode)'));
  assert.ok(source.includes("if(mode==='Sprites')return item.kind==='sprite'"));
  assert.ok(source.includes("if(mode==='Labels')return item.kind==='label'"));
  assert.ok(source.includes("if(mode==='Tiles')return !!item.libraryTile"));
  assert.ok(source.includes("typedPlacedContentSelect('Sprites')"));
  assert.ok(source.includes("typedPlacedContentSelect('Tiles')"));
  assert.ok(source.includes("typedPlacedContentSelect('Image')"));
  assert.ok(source.includes("toolKey('DELETE',mode.toLowerCase(),removeSelectedImage)"));
});

test('adaptive control contract preserves flow semantics and input independence',()=>{
  const contract=fs.readFileSync(path.join(__dirname,'../ADAPTIVE_CONTROL_FLOW_CONTRACT.md'),'utf8');
  assert.ok(contract.includes('VIEW — camera, zoom, fit, tilt, selection focus.'));
  assert.ok(contract.includes('BACK returns to the previous decision level'));
  assert.ok(contract.includes('UNDO reverses the most recent supported edit'));
  assert.ok(contract.includes('DONE finishes the current object'));
  assert.ok(contract.includes('No essential action may require drag, hover, multi-touch, device tilt'));
  assert.ok(contract.includes('approximately 44 by 44 CSS pixels'));
});

test('adaptive controls expose five primary nodes while preserving advanced tools',()=>{
  const source=fs.readFileSync(path.join(root,'prototype.js'),'utf8');
  const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
  const css=fs.readFileSync(path.join(root,'prototype.css'),'utf8');
  assert.ok(html.includes('id="keyboardFlow"'));
  assert.ok(source.includes("const PRIMARY_KEYBOARD_MODES=['View','Build','Edit','Layers','More']"));
  assert.ok(source.includes("function renderAdaptiveEditKeyboard()"));
  assert.ok(source.includes("function renderAdaptiveLayersKeyboard()"));
  assert.ok(source.includes("function renderMoreKeyboard()"));
  assert.ok(source.includes("toolKey('UNDO'"));
  assert.ok(source.includes("editFlow==='delete'"));
  assert.ok(css.includes('grid-template-columns:repeat(5,minmax(0,1fr))'));
  assert.ok(css.includes('.stage.large-controls .keyboard-keys'));
  assert.ok(css.includes('.stage.high-contrast .user-image-placement.selected'));
});

test('selected-object focus and underlay stay local to the selected footprint',()=>{
  const source=fs.readFileSync(path.join(root,'prototype.js'),'utf8');
  const css=fs.readFileSync(path.join(root,'prototype.css'),'utf8');
  assert.ok(source.includes('function selectedAssetNormalizedBounds('));
  assert.ok(source.includes('function focusSelectedAsset('));
  assert.ok(source.includes('const usableHeight=Math.max(120,r.height-controlsHeight-12)'));
  assert.ok(source.includes('function selectionUnderlayCandidate('));
  assert.ok(source.includes('function refreshSelectionUnderlay('));
  assert.ok(source.includes("toolKey(selectionUnderlayVisible?'UNDERLAY ✓':'UNDERLAY'"));
  assert.ok(css.includes('.selection-underlay-preview{position:absolute'));
});

test('shared sprite editor supports motion-only overlays and 60fps playback',()=>{
  const source=fs.readFileSync(path.join(root,'prototype.js'),'utf8');
  const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
  assert.ok(html.includes('id="spriteMotionOnly"'));
  assert.ok(html.includes('max="60"'));
  assert.ok(source.includes('function isolateSpriteMotion('));
  assert.ok(source.includes('spriteMotionOnly:definition.motionOnly===true'));
  assert.ok(source.includes('extractSpriteChainFrames(pages,{motionOnly:item.spriteMotionOnly})'));
  assert.ok(source.includes('requestAnimationFrame(step)'));
  assert.ok(source.includes("toolKey('FPS 60'"));
});

test('sprite chains persist ordered pages across Worldbuilder and RegionDefiner',()=>{
  const source=fs.readFileSync(path.join(root,'prototype.js'),'utf8');
  const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
  assert.ok(html.includes('id="spriteFile" type="file" accept="image/*" multiple'));
  assert.ok(source.includes('function normalizedSpritePages(definition)'));
  assert.ok(source.includes('async function extractSpriteChainFrames('));
  assert.ok(source.includes('spritePages:item.kind===\'sprite\''));
  assert.ok(source.includes('spriteChainId:item.spriteChainId||null'));
  assert.ok(source.includes("toolKey('ADD PAGE','append sprite set(s)'"));
  assert.ok(source.includes('item.frameSources=[...(item.frameSources||[]),...frames]'));
  assert.ok(source.includes('chainId:String(personalEntryValue(entry,\'ChainId\',\'\'))'));
  assert.ok(source.includes('chainIndex:Math.max(0,Math.trunc(Number(personalEntryValue(entry,\'ChainIndex\',0))||0))'));
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
    assert.equal(f.stage.dataset.renderer,'region-world-z-v2-legacy','legacy fixture must be marked compatibility-only');
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

    tab(f,'Edit');
    const picker=f.d.querySelector('.placed-content-select');
    assert.ok(picker);
    const labels=Array.from(picker.options).map(x=>x.textContent);
    assert.ok(labels.some(x=>x.includes('Region City')));
    assert.ok(!labels.some(x=>x.includes('World City')),'locked parent object cannot enter editable dropdown');
  }finally{f.close()}
});

test('Region Tier drives parallax while visual Layer alone drives composition',async()=>{
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

    tab(f,'Edit');
    const picker=f.d.querySelector('.placed-content-select');
    picker.value='region-city';
    picker.dispatchEvent(new f.w.Event('change',{bubbles:true}));
    assert.equal(
      Array.from(f.d.querySelectorAll('#keyboardTabs button')).find(b=>b.textContent==='EDIT')?.getAttribute('aria-selected'),
      'true'
    );

    clickKey(f,'DEPTH');
    let state=f.w.ShaelvienPrototype.getViewerState();
    let city=state.userLayers.find(x=>x.id==='region-city');
    assert.equal(city.worldLayer,2,'legacy World Z remains compatibility context');
    assert.equal(city.z100,201,'legacy exact-Z projection remains readable');
    assert.equal(city.parallaxMode,'recursive-region');
    assert.equal(city.recursive?.format,'RIST_RECURSIVE_SCOPE_V1');
    assert.equal(city.recursive?.scopeKind,'REGION');
    assert.equal(city.recursive?.scopeId,'region-test');
    assert.equal(city.recursive?.tier,1);
    assert.equal(city.recursive?.layer,1);
    assert.equal(city.recursive?.viewDegrees,15);

    const initialTier=city.recursive.tier;
    clickKey(f,'LAYER +');
    state=f.w.ShaelvienPrototype.getViewerState();
    city=state.userLayers.find(x=>x.id==='region-city');
    assert.equal(city.recursive.layer,2);
    assert.equal(city.recursive.tier,initialTier,'Layer must not mutate Region Tier');
    assert.equal(city.worldLayer,2,'Layer must not mutate legacy parent depth');
    assert.equal(city.z100,202,'z100 is only a compatibility projection of visual Layer');

    clickKey(f,'DEPTH +');
    state=f.w.ShaelvienPrototype.getViewerState();
    city=state.userLayers.find(x=>x.id==='region-city');
    assert.equal(city.recursive.tier,2);
    assert.equal(city.recursive.layer,2,'Tier must not mutate visual Layer');
    assert.equal(city.worldLayer,2,'Region Tier must not rewrite parent World depth');
    assert.equal(city.z100,202,'Region Tier must not feed legacy z100');
    assert.equal(city.tier,0,'Region depth must not promote the parent World Tier');

    for(let i=0;i<8;i++)clickKey(f,'LAYER +');
    state=f.w.ShaelvienPrototype.getViewerState();
    city=state.userLayers.find(x=>x.id==='region-city');
    assert.equal(city.recursive.layer,10,'canonical visual Layer is 1-based and not capped at the legacy 1..9 window');
    assert.equal(city.regionLayer,10,'Region diagnostics report canonical visual Layer');
    assert.equal(city.legacyRegionLayer,9,'legacy regionLayer remains a bounded compatibility projection');
    assert.equal(city.z100,209,'legacy z100 clamps only its compatibility layer component');
  }finally{f.close()}
});

test('Local scope restarts at root and keeps Tier separate from visual Layer',async()=>{
  const f=fixture('existing',{mode:'localdefiner',regionId:'region-test'});
  try{
    const region={...deed,canEdit:true};
    const regionAnchor={
      kind:'label',id:'region-city',regionId:'region-test',name:'Region City',text:'Region City',
      tier:0,worldLayer:2,layer:2,regionLayer:1,z100:201,x:.1,y:.1,committed:true,
      recursive:{
        format:'RIST_RECURSIVE_SCOPE_V1',assetId:'region-city',scopeKind:'REGION',scopeId:'region-test',
        parentScopeId:'deed-runtime-test',parentAssetId:'world:deed-runtime-test',
        x:.5,y:.5,tier:1,layer:1,viewDegrees:15,opacity:1,visible:true,locked:false,
        linkedGroupId:'',permissionResourceId:'asset:region-city'
      }
    };
    host(f,'catalog',{regions:[region]});
    host(f,'world-source',{worldSource:{
      worldId:'deed-runtime-test',regionId:'region-test',activeRegionId:'region-test',
      state:projectedState({userLayers:[regionAnchor]})
    }});
    await tick();await tick();

    const local={
      id:'local-test',name:'Old Tavern',regionId:'region-test',
      anchorObjectId:'region-city',anchorAssetId:'',anchorName:'Region City',anchorKind:'label',
      x:.1,y:.1,width:.12,height:.12,tier:0,layer:2,
      worldTier:0,worldLayer:2,regionTier:1,regionLayer:1,
      localTier:1,localLayer:1,instanceTier:0,instanceLayer:0,
      recursiveScopeFormat:'RIST_RECURSIVE_SCOPE_V1',viewDegrees:30,
      parentScopeId:'region-test',parentAssetId:'region-city',
      parentRegionTier:1,parentRegionLayer:1
    };
    host(f,'local-catalog',{locals:[local]});
    host(f,'local-opened',{
      localId:'local-test',
      localSource:{
        worldId:'deed-runtime-test',regionId:'region-test',localId:'local-test',
        state:{
          format:'RIST_LOCAL_MAP_V3',
          recursiveScopeFormat:'RIST_RECURSIVE_SCOPE_V1',
          coordinateSpace:'local-root-recursive-v1',
          userLayers:[{
            kind:'label',id:'local-child',regionId:'region-test',localId:'local-test',localOverlay:true,
            name:'Table',text:'Table',tier:0,worldTier:0,worldLayer:2,regionTier:1,regionLayer:1,
            localTier:1,localLayer:2,x:.1,y:.1,committed:true,
            recursive:{
              format:'RIST_RECURSIVE_SCOPE_V1',assetId:'local-child',scopeKind:'LOCAL',scopeId:'local-test',
              parentScopeId:'region-test',parentAssetId:'region-city',
              x:.2,y:0,tier:1,layer:2,viewDegrees:30,opacity:1,visible:true,locked:false,
              linkedGroupId:'',permissionResourceId:'asset:local-child'
            }
          }]
        }
      }
    });
    await tick();await tick();

    let state=f.w.ShaelvienPrototype.getViewerState();
    let child=state.userLayers.find(x=>x.id==='local-child');
    assert.ok(child,'Local child must restore');
    assert.equal(child.recursive?.scopeKind,'LOCAL');
    assert.equal(child.recursive?.scopeId,'local-test');
    assert.equal(child.recursive?.parentAssetId,'region-city');
    assert.equal(child.recursive?.viewDegrees,30);
    assert.ok(Math.abs(Number(child.recursive?.x)-.2)<1e-9,'Local X must survive parent projection round-trip');
    assert.ok(Math.abs(Number(child.recursive?.y)-0)<1e-9,'Local Y must survive parent projection round-trip');
    assert.equal(child.localTier,1);
    assert.equal(child.localLayer,2);
    assert.equal(child.legacyLocalLayer,2);

    tab(f,'Layers');
    const rootRow=f.d.querySelector('.recursive-root-row');
    assert.ok(rootRow,'Local list must expose the locked parent root');
    assert.equal(rootRow.dataset.root,'true');
    assert.ok(rootRow.textContent.includes('ROOT'));
    const rootButtons=Array.from(rootRow.querySelectorAll('button'));
    assert.ok(rootButtons.length>=2&&rootButtons.every(button=>button.disabled),'Local root row must be read only');

    const childRow=()=>f.d.querySelector('.recursive-asset-row[data-asset-id="local-child"]');
    assert.ok(childRow(),'Local child must appear in recursive asset list');
    for(let i=0;i<8;i++)childRow().querySelector('.recursive-layer button:last-of-type').click();

    state=f.w.ShaelvienPrototype.getViewerState();
    child=state.userLayers.find(x=>x.id==='local-child');
    assert.equal(child.recursive.layer,10,'Local visual Layer is unbounded by legacy window');
    assert.equal(child.localLayer,10,'Local diagnostics report canonical visual Layer');
    assert.equal(child.legacyLocalLayer,9,'legacy Local layer remains bounded');
    assert.equal(child.recursive.tier,1,'Layer changes must not mutate Local Tier');

    childRow().querySelector('.recursive-tier button:last-of-type').click();
    state=f.w.ShaelvienPrototype.getViewerState();
    child=state.userLayers.find(x=>x.id==='local-child');
    assert.equal(child.recursive.tier,2,'Local Tier changes spatial depth');
    assert.equal(child.recursive.layer,10,'Tier changes must not mutate visual Layer');
    assert.ok(Math.abs(Number(child.recursive.x)-.2)<1e-9,'Tier changes must not mutate Local X');
    assert.ok(Math.abs(Number(child.recursive.y)-0)<1e-9,'Tier changes must not mutate Local Y');
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
