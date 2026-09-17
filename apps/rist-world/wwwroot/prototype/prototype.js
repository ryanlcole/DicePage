(() => {
'use strict';
const ASSET_ROOT='https://d2d6rnm6fnsp89.cloudfront.net/library/terrains/standard/world/whole_maps/geonaph/';
const LAYERS_PER_TIER=10;
const STRATA=[['universe','Universe',30],['sky','Sky',20],['weather','Weather',10],['surface','Surface',0],['subterranean','Subterranean',-10],['depths','Depths',-20],['core','Core',-30]].map(([key,label,z])=>Object.freeze({key,label,z}));
const ROOT_OPTIONS=Object.freeze([Object.freeze({key:'all',label:'All parallax',z:null}),...STRATA]);
const SURFACE_CATEGORIES=[['mountain','Mountain'],['volcano','Volcano'],['hills','Hills'],['planes','Planes']].map(([key,label])=>Object.freeze({key,label,level:'Category'}));
const MAP_TRUTH=Object.freeze({
  id:'geonaph',
  origin:Object.freeze({x:0,y:0,z:0}),
  coordinateAuthority:'XYZ',
  layersPerTier:LAYERS_PER_TIER,
  assets:Object.freeze([
    Object.freeze({key:'surface',sceneZ:0,file:'geonaph_full_static_canonical_surface_v001.png',role:'base'}),
    Object.freeze({key:'highlands',sceneZ:4,file:'geonaph_full_static_highlands_rivers_v001.png',role:'parallax'}),
    Object.freeze({key:'mountains',sceneZ:7,file:'geonaph_full_static_mountain_volcanic_archipelago_v001.png',role:'parallax'})
  ])
});

const $=id=>document.getElementById(id);
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
const smoothstep=(a,b,v)=>{const t=clamp((v-a)/(b-a),0,1);return t*t*(3-2*t)};
const reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
const stage=$('stage'),world=$('world'),surface=$('surfacePlane'),highlands=$('highlandsPlane'),mountains=$('mountainPlane'),loading=$('loading'),shortcut=$('stratumShortcut'),viewLabel=$('viewLabel'),zoomLabel=$('zoomLabel'),pathLabel=$('pathLabel'),stratumNote=$('stratumNote'),focusLevel=$('focusLevel'),focusBack=$('focusBack'),focusTrail=$('focusTrail'),battle=$('battleInstance'),battleText=$('battleText'),keyboard=$('viewerKeyboard'),keyboardToggle=$('keyboardToggle'),keyboardTabs=$('keyboardTabs'),keyboardKeys=$('keyboardKeys'),live=$('live');
const planeByKey={surface,highlands,mountains};
const layerReady={surface:false,highlands:false,mountains:false};
const pointers=new Map();
let naturalWidth=1,naturalHeight=1,scale=1,minScale=.1,maxScale=12,x=0,y=0,fitX=0,fitY=0,panStart=null,pinchStart=null,viewerZ=0,activeStratum='surface',parallaxOverride=true,focusPath=[],focusSelected='all',keyboardMode='Viewer',toolMode='Inspect',lastMix={zoomZ:0,surface:1,highlands:1,mountains:.82},tiltBaseline=null,tiltTargetX=0,tiltTargetY=0,tiltX=0,tiltY=0,tiltFrame=0;

function splitZ(z){const tierIndex=Math.floor(z/LAYERS_PER_TIER);return{tierIndex,layerOffset:z-tierIndex*LAYERS_PER_TIER}}
function stratumByKey(key){return STRATA.find(s=>s.key===key)||STRATA.find(s=>s.key==='surface')}
function rootFocus(){return focusPath.find(p=>p.level==='Parallax')||null}
function lockedTier(){
  const root=rootFocus();
  if(parallaxOverride||!root||root.key==='all')return null;
  return splitZ(stratumByKey(root.key).z).tierIndex;
}
function clampToLockedTier(value){
  const tier=lockedTier(),z=Math.trunc(value);
  if(tier===null)return z;
  const low=tier*LAYERS_PER_TIER,high=low+LAYERS_PER_TIER-1;
  return clamp(z,low,high);
}
function registeredLayerWindow(){
  const tier=lockedTier();
  if(tier===null)return MAP_TRUTH.assets;
  return MAP_TRUTH.assets.filter(asset=>{
    const assetTier=splitZ(asset.sceneZ).tierIndex;
    return assetTier>=tier-1&&assetTier<=tier+1;
  });
}
function focusOptions(){
  switch(focusPath.length){
    case 0:return ROOT_OPTIONS.map(s=>({key:s.key,label:s.label,level:'Parallax'}));
    case 1:{const s=focusPath[0];return (s.key==='surface'||s.key==='all')?SURFACE_CATEGORIES.map(v=>({...v})):[{key:s.key+':all',label:'All '+s.label,level:'Category'}]}
    case 2:return[{key:'region',label:'Region',level:'Region'}];
    case 3:return[{key:'local',label:'Local',level:'Local'}];
    case 4:return[{key:'town',label:'Town',level:'Landmark'},{key:'cave',label:'Cave',level:'Landmark'}];
    case 5:return[{key:'npc',label:'NPC',level:'Entity'},{key:'object',label:'Object',level:'Entity'}];
    default:return[];
  }
}
function nextLevel(){return ['Parallax','Category','Region','Local','Landmark','Entity','Battle Instance'][Math.min(focusPath.length,6)]}
function announce(text){live.textContent='';requestAnimationFrame(()=>{live.textContent=text})}
function selectedOption(){const opts=focusOptions();return opts.find(o=>o.key===focusSelected)||opts[0]||null}
function normalizeFocusSelection(){const opts=focusOptions();if(!opts.some(o=>o.key===focusSelected))focusSelected=opts[0]?.key||''}

// All Parallax is the unrestricted viewer state: every registered plane remains
// eligible and zoom alone determines its perceptual handoff. A named stratum is
// different: selecting it creates a tier scope. Only the previous, selected, and
// next tier are eligible for presentation, and the selected registered layer plus
// one registered layer beneath it form the default locked view. Zoom then magnifies
// that locked representation; it never advances perception above the selected layer.
function allParallaxMix(zoomRatio,rawZoomZ){
  const peakToHighlands=smoothstep(1.00,1.60,zoomRatio);
  const highlandsToSurface=smoothstep(1.45,2.75,zoomRatio);
  return{
    zoomRatio,
    zoomZ:rawZoomZ,
    surface:layerReady.surface?1:0,
    highlands:layerReady.highlands?clamp(1-highlandsToSurface,0,1):0,
    mountains:layerReady.mountains?clamp(.82*(1-peakToHighlands),0,1):0
  };
}
function scopedParallaxMix(zoomRatio,rawZoomZ){
  const visible=registeredLayerWindow().filter(asset=>layerReady[asset.key]).sort((a,b)=>a.sceneZ-b.sceneZ);
  const atOrBelow=visible.filter(asset=>asset.sceneZ<=viewerZ);
  const selected=atOrBelow.at(-1)||visible[0]||null;
  const selectedIndex=selected?visible.indexOf(selected):-1;
  const below=selectedIndex>0?visible[selectedIndex-1]:null;
  const belowFade=1-smoothstep(1.25,3.10,zoomRatio);
  const alpha={surface:0,highlands:0,mountains:0};
  if(selected)alpha[selected.key]=1;
  if(below)alpha[below.key]=clamp(.82*belowFade,0,1);
  const selectedLayer=splitZ(viewerZ).layerOffset;
  return{
    zoomRatio,
    zoomZ:Math.min(rawZoomZ,selectedLayer),
    surface:alpha.surface,
    highlands:alpha.highlands,
    mountains:alpha.mountains
  };
}
function parallaxMix(){
  const zoomRatio=Math.max(.01,scale/Math.max(minScale,.00001));
  const rawZoomZ=Math.max(0,Math.log2(zoomRatio)*LAYERS_PER_TIER);
  return parallaxOverride?allParallaxMix(zoomRatio,rawZoomZ):scopedParallaxMix(zoomRatio,rawZoomZ);
}
function applyParallax(mix=parallaxMix()){
  const dx=x-fitX,dy=y-fitY;
  const layers=[
    {node:surface,sceneZ:0,alpha:mix.surface},
    {node:highlands,sceneZ:4,alpha:mix.highlands},
    {node:mountains,sceneZ:7,alpha:mix.mountains}
  ];
  for(const layer of layers){
    const depth=layer.sceneZ/LAYERS_PER_TIER;
    const panStrength=depth*.055;
    const tiltStrength=.42+(depth*.78);
    const localX=((-dx*panStrength)+(tiltX*tiltStrength))/Math.max(scale,.00001);
    const localY=((-dy*panStrength)+(tiltY*tiltStrength))/Math.max(scale,.00001);
    layer.node.style.opacity=clamp(Number(layer.alpha)||0,0,1).toFixed(3);
    layer.node.style.transform=`translate3d(${localX.toFixed(2)}px,${localY.toFixed(2)}px,0)`;
  }
  lastMix=mix;
}
function updateReadouts(){
  const s=stratumByKey(activeStratum),mix=lastMix,tier=lockedTier();
  const label=parallaxOverride?'All parallax':s.label;
  viewLabel.textContent=parallaxOverride?`${label} · Z ${viewerZ}`:`${label} · T${tier} · Z ${viewerZ}`;
  pathLabel.textContent='Focus: '+(focusPath.length?focusPath.map(p=>p.label).join(' › '):'Parallax');
  const zoomRatio=Math.max(.01,scale/Math.max(minScale,.00001));
  const fit=Math.abs(x-fitX)<.5&&Math.abs(y-fitY)<.5&&Math.abs(scale-minScale)<.0001;
  zoomLabel.textContent=`${fit?'Fit · ':''}${zoomRatio.toFixed(2)}× · PZ ${mix.zoomZ.toFixed(1)}`;
  stratumNote.innerHTML=`<strong>${label}</strong> · S ${Math.round(mix.surface*100)}% · H ${Math.round(mix.highlands*100)}% · M ${Math.round(mix.mountains*100)}%`;
  stratumNote.setAttribute('aria-label',parallaxOverride
    ?`${label}. All registered layers remain eligible; zoom controls their parallax handoff.`
    :`${label}. Tier ${tier} is locked for editing. The selected registered layer and one layer below are the default view; zoom magnifies the selected layer without crossing above it.`);
}
function applyTransform(){
  world.style.width=naturalWidth+'px';
  world.style.height=naturalHeight+'px';
  world.style.transform=`translate3d(${x}px,${y}px,0) scale(${scale})`;
  applyParallax();
  updateReadouts();
}
function fitMap(){
  if(!naturalWidth||!naturalHeight)return;
  const r=stage.getBoundingClientRect();
  minScale=Math.min(r.width/naturalWidth,r.height/naturalHeight);
  scale=minScale;
  maxScale=Math.max(minScale*24,8);
  x=fitX=(r.width-naturalWidth*scale)/2;
  y=fitY=(r.height-naturalHeight*scale)/2;
  applyTransform();
}
function zoomAt(cx,cy,factor){
  const r=stage.getBoundingClientRect(),sx=cx-r.left,sy=cy-r.top,old=scale,next=clamp(old*factor,minScale*.75,maxScale);
  if(Math.abs(next-old)<.0001)return;
  const wx=(sx-x)/old,wy=(sy-y)/old;
  scale=next;
  x=sx-wx*scale;
  y=sy-wy*scale;
  applyTransform();
}

function setViewerZ(value,reason){
  viewerZ=clampToLockedTier(value);
  renderState();
  announce(`${reason}. Viewer Z ${viewerZ}. ${lockedTier()===null?'All Parallax remains unrestricted.':`Editing remains locked to tier ${lockedTier()}.`}`);
}
function jumpStratum(key){
  if(key==='all'){
    parallaxOverride=true;activeStratum='surface';viewerZ=0;focusPath=[];focusSelected='all';shortcut.value='all';renderState();announce('All Parallax viewer mode. No tier scope hides registered layers; zoom alone controls their perceptual handoff.');return;
  }
  const s=stratumByKey(key);
  parallaxOverride=false;activeStratum=s.key;viewerZ=s.z;focusPath=[{level:'Parallax',key:s.key,label:s.label}];shortcut.value=s.key;
  focusSelected=focusOptions()[0]?.key||'';
  renderState();announce(`${s.label} selected at Z ${s.z}. Tier ${lockedTier()} locked automatically; editing is restricted to layers inside that tier.`);
}
function selectFocus(key){
  const match=focusOptions().find(o=>o.key===key);if(!match)return;
  if(focusPath.length===0){
    jumpStratum(match.key);
    return;
  }
  focusPath.push({level:match.level,key:match.key,label:match.label});
  focusSelected=focusOptions()[0]?.key||'';
  renderState();
  announce(match.level==='Entity'?`${match.label} selected. Battle Instance revealed.`:`${match.label} selected and locked automatically. ${nextLevel()} revealed.`);
}
function unlockFocus(){
  if(!focusPath.length)return;
  const removed=focusPath.pop();
  if(!focusPath.length){jumpStratum('all');announce(`Returned from ${removed.label} to All Parallax.`);return}
  const root=rootFocus();
  if(root&&root.key!=='all'){const s=stratumByKey(root.key);activeStratum=s.key;parallaxOverride=false;viewerZ=clampToLockedTier(viewerZ);shortcut.value=s.key}
  const opts=focusOptions();focusSelected=opts[0]?.key||'';
  renderState();announce(`Returned from ${removed.label} to ${nextLevel()}.`);
}
function rewindFocus(index){
  while(focusPath.length>index+1)focusPath.pop();
  const root=rootFocus();
  if(!root){jumpStratum('all');return}
  const s=stratumByKey(root.key);activeStratum=s.key;parallaxOverride=false;viewerZ=clampToLockedTier(viewerZ);shortcut.value=s.key;
  focusSelected=focusOptions()[0]?.key||'';renderState();announce(`Focus returned to ${focusPath[index]?.label||'All Parallax'}.`);
}
function resetFocus(){jumpStratum('all')}
function renderFocus(){
  normalizeFocusSelection();
  const opts=focusOptions(),entityLocked=focusPath.some(p=>p.level==='Entity'),level=entityLocked?'Battle Instance':nextLevel();
  focusLevel.textContent=level;
  shortcut.replaceChildren();
  if(opts.length){
    opts.forEach(o=>{const el=document.createElement('option');el.value=o.key;el.textContent=o.label;shortcut.append(el)});
    shortcut.value=focusSelected||opts[0].key;
    shortcut.disabled=false;
  }else{
    const el=document.createElement('option');el.textContent=entityLocked?'Battle Instance':'No content';el.value='';shortcut.append(el);
    shortcut.disabled=true;
  }
  shortcut.setAttribute('aria-label',focusPath.length===0
    ?'Choose All Parallax or a named Z stratum'
    :`Choose ${level.toLowerCase()} focus inside ${focusPath.at(-1)?.label||'the selected scope'}`);
  focusBack.disabled=!focusPath.length;
  focusTrail.replaceChildren();
  focusPath.forEach((p,i)=>{const b=document.createElement('button');b.type='button';b.className='crumb';b.textContent=p.label;b.setAttribute('aria-label','Return focus to '+p.label);b.addEventListener('click',()=>rewindFocus(i));focusTrail.append(b)});
  stage.classList.toggle('focus-deep',focusPath.length>0);
  battle.hidden=!entityLocked;
  if(entityLocked){const e=focusPath.find(p=>p.level==='Entity');battleText.textContent=`${e?.label||'Entity'} focus · tactical viewer representation. Canonical XYZ identity remains unchanged.`}
}
function renderState(){
  const tier=lockedTier();
  stage.dataset.parallaxScope=parallaxOverride?'all':'tier';
  stage.dataset.editTier=tier===null?'':String(tier);
  stage.dataset.viewerZ=String(viewerZ);
  renderFocus();applyTransform();renderKeyboardKeys()
}

const KEYBOARD_MODES=['Viewer','Pixels','Tiles','Sprites','Labels','Litch','CAD','Stylus','Tethers','Metadata','Selected'];
function toolKey(label,sub,fn,disabled=false){const b=document.createElement('button');b.type='button';b.disabled=disabled;b.innerHTML=`<strong>${label}</strong><small>${sub}</small>`;b.addEventListener('click',fn);return b}
function setTool(name){toolMode=name;announce(`${name} tool selected. Prototype tool mode changes controls only; world truth is not altered.`);renderKeyboardKeys()}
function renderKeyboardTabs(){keyboardTabs.replaceChildren();KEYBOARD_MODES.forEach(mode=>{const b=document.createElement('button');b.type='button';b.role='tab';b.textContent=mode;b.classList.toggle('active',mode===keyboardMode);b.setAttribute('aria-selected',String(mode===keyboardMode));b.addEventListener('click',()=>{keyboardMode=mode;renderKeyboardTabs();renderKeyboardKeys();announce(`${mode} keyboard opened.`)});keyboardTabs.append(b)})}
function renderKeyboardKeys(){
  if(!keyboardKeys)return;
  keyboardKeys.replaceChildren();
  const z=splitZ(viewerZ);
  if(keyboardMode==='Viewer'){
    const tier=lockedTier(),address=splitZ(viewerZ),tierLow=tier===null?null:tier*LAYERS_PER_TIER,tierHigh=tier===null?null:tierLow+LAYERS_PER_TIER-1;
    keyboardKeys.append(
      toolKey('Z −','layer',()=>setViewerZ(viewerZ-1,'Viewer moved down one layer'),tier!==null&&viewerZ<=tierLow),
      toolKey('Z +','layer',()=>setViewerZ(viewerZ+1,'Viewer moved up one layer'),tier!==null&&viewerZ>=tierHigh),
      toolKey('T −','tier',()=>setViewerZ(viewerZ-LAYERS_PER_TIER,'Viewer moved down one tier'),tier!==null),
      toolKey('T +','tier',()=>setViewerZ(viewerZ+LAYERS_PER_TIER,'Viewer moved up one tier'),tier!==null),
      toolKey('−','zoom',()=>{const r=stage.getBoundingClientRect();zoomAt(r.left+r.width/2,r.top+r.height/2,1/1.22)}),
      toolKey('+','zoom',()=>{const r=stage.getBoundingClientRect();zoomAt(r.left+r.width/2,r.top+r.height/2,1.22)}),
      toolKey('FIT','camera',fitMap),
      toolKey('ALL','parallax',()=>jumpStratum('all'))
    );
    const read=toolKey(`T${z.tierIndex} L${z.layerOffset}`,'Z '+viewerZ,()=>{},true);read.classList.add('readout');keyboardKeys.append(read);return;
  }
  if(keyboardMode==='Selected'){
    keyboardKeys.append(toolKey('BACK','focus',unlockFocus,!focusPath.length),toolKey('HOME','All Parallax',resetFocus),toolKey('INSPECT','viewer',()=>setTool('Inspect')),toolKey('META','viewer',()=>setTool('Metadata')));return;
  }
  const sets={Pixels:['Select','Paint','Erase','Fill'],Tiles:['Library','Place','Rotate','Scale'],Sprites:['Library','Place','Play','Speed'],Labels:['New Label','Style','Anchor','Offset'],Litch:['Light','Shadow','Intensity','Falloff'],CAD:['Line','Shape','Measure','Snap'],Stylus:['Draw','Pressure','Erase','Sample'],Tethers:['Link','Unlink','Anchor','Trace'],Metadata:['Inspect','Identity','Provenance','Relations']};
  (sets[keyboardMode]||['Inspect']).forEach(name=>keyboardKeys.append(toolKey(name,keyboardMode.toLowerCase(),()=>setTool(name))));
}
function openKeyboard(){keyboard.hidden=false;stage.classList.add('keyboard-open');keyboardToggle.setAttribute('aria-expanded','true');keyboardToggle.setAttribute('aria-label','Close World Builder keyboard');renderKeyboardTabs();renderKeyboardKeys();announce(`${keyboardMode} keyboard opened over viewer. Viewer size unchanged.`)}
function closeKeyboard(){keyboard.hidden=true;stage.classList.remove('keyboard-open');keyboardToggle.setAttribute('aria-expanded','false');keyboardToggle.setAttribute('aria-label','Open World Builder keyboard');announce('Keyboard hidden. Viewer unobstructed.')}

MAP_TRUTH.assets.forEach(asset=>{
  const node=planeByKey[asset.key];
  node.addEventListener('load',()=>{
    layerReady[asset.key]=true;
    if(asset.key==='surface'){
      naturalWidth=node.naturalWidth||1;
      naturalHeight=node.naturalHeight||1;
      loading.hidden=true;
      fitMap();
    }else renderState();
  });
  node.addEventListener('error',()=>{
    layerReady[asset.key]=false;
    if(asset.key==='surface'){loading.hidden=false;loading.textContent='SURFACE MAP ASSET UNAVAILABLE'}
    renderState();
  });
  node.src=ASSET_ROOT+asset.file;
});

function screenAdjusted(beta,gamma){
  const raw=Number(screen.orientation?.angle??window.orientation??0);
  const angle=((raw%360)+360)%360;
  if(angle===90)return{x:beta,y:-gamma};
  if(angle===270)return{x:-beta,y:gamma};
  if(angle===180)return{x:-gamma,y:-beta};
  return{x:gamma,y:beta};
}
function renderTilt(){
  tiltFrame=0;
  tiltX+=(tiltTargetX-tiltX)*.22;
  tiltY+=(tiltTargetY-tiltY)*.22;
  applyParallax();
  if(Math.abs(tiltTargetX-tiltX)>.03||Math.abs(tiltTargetY-tiltY)>.03)tiltFrame=requestAnimationFrame(renderTilt);
}
function scheduleTilt(){if(!tiltFrame)tiltFrame=requestAnimationFrame(renderTilt)}
function resetTilt(){
  tiltBaseline=null;
  tiltTargetX=0;
  tiltTargetY=0;
  scheduleTilt();
}
addEventListener('deviceorientation',event=>{
  const beta=Number(event.beta),gamma=Number(event.gamma);
  if(!Number.isFinite(beta)||!Number.isFinite(gamma))return;
  const axes=screenAdjusted(beta,gamma);
  if(!tiltBaseline){tiltBaseline={x:axes.x,y:axes.y};return;}
  tiltTargetX=clamp((axes.x-tiltBaseline.x)/20,-1,1)*22;
  tiltTargetY=clamp((axes.y-tiltBaseline.y)/20,-1,1)*16;
  scheduleTilt();
},{passive:true});
addEventListener('orientationchange',resetTilt,{passive:true});
screen.orientation?.addEventListener?.('change',resetTilt);

shortcut.addEventListener('change',()=>{if(focusPath.length===0)jumpStratum(shortcut.value);else selectFocus(shortcut.value)});
focusBack.addEventListener('click',unlockFocus);
$('focusReset').addEventListener('click',resetFocus);
$('fit').addEventListener('click',fitMap);
$('zoomIn').addEventListener('click',()=>{const r=stage.getBoundingClientRect();zoomAt(r.left+r.width/2,r.top+r.height/2,1.22)});
$('zoomOut').addEventListener('click',()=>{const r=stage.getBoundingClientRect();zoomAt(r.left+r.width/2,r.top+r.height/2,1/1.22)});
$('back').addEventListener('click',()=>{location.href='/Game/index.html'});
keyboardToggle.addEventListener('click',()=>keyboard.hidden?openKeyboard():closeKeyboard());
$('keyboardClose').addEventListener('click',closeKeyboard);

stage.addEventListener('wheel',e=>{if(e.target instanceof Element&&e.target.closest('[data-ui]'))return;e.preventDefault();zoomAt(e.clientX,e.clientY,e.deltaY<0?1.12:1/1.12)},{passive:false});
stage.addEventListener('pointerdown',e=>{
  if(e.target instanceof Element&&e.target.closest('[data-ui]'))return;
  if(e.pointerType==='mouse'&&e.button!==0)return;
  stage.setPointerCapture?.(e.pointerId);
  pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
  stage.classList.add('dragging');
  if(pointers.size===1){panStart={pointerX:e.clientX,pointerY:e.clientY,x,y};pinchStart=null}
  else if(pointers.size===2){
    const[a,b]=[...pointers.values()],r=stage.getBoundingClientRect(),cx=(a.x+b.x)/2-r.left,cy=(a.y+b.y)/2-r.top,d=Math.hypot(a.x-b.x,a.y-b.y)||1;
    pinchStart={distance:d,scale,worldX:(cx-x)/scale,worldY:(cy-y)/scale};
    panStart=null;
  }
});
stage.addEventListener('pointermove',e=>{
  if(!pointers.has(e.pointerId))return;
  pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
  if(pointers.size===1&&panStart){x=panStart.x+(e.clientX-panStart.pointerX);y=panStart.y+(e.clientY-panStart.pointerY);applyTransform();return}
  if(pointers.size===2&&pinchStart){
    const[a,b]=[...pointers.values()],r=stage.getBoundingClientRect(),cx=(a.x+b.x)/2-r.left,cy=(a.y+b.y)/2-r.top,d=Math.hypot(a.x-b.x,a.y-b.y)||1;
    scale=clamp(pinchStart.scale*(d/pinchStart.distance),minScale*.75,maxScale);
    x=cx-pinchStart.worldX*scale;
    y=cy-pinchStart.worldY*scale;
    applyTransform();
  }
});
function release(e){
  pointers.delete(e.pointerId);
  if(!pointers.size){panStart=pinchStart=null;stage.classList.remove('dragging')}
  else if(pointers.size===1){const[r]=[...pointers.values()];panStart={pointerX:r.x,pointerY:r.y,x,y};pinchStart=null}
}
stage.addEventListener('pointerup',release);
stage.addEventListener('pointercancel',release);
window.addEventListener('resize',fitMap,{passive:true});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!keyboard.hidden)closeKeyboard()});

window.ShaelvienPrototype=Object.freeze({
  mapTruth:MAP_TRUTH,
  getViewerState:()=>({activeStratum,viewerZ,...splitZ(viewerZ),parallaxOverride,lockedTier:lockedTier(),editableTier:lockedTier(),visibleTierWindow:lockedTier()===null?null:[lockedTier()-1,lockedTier(),lockedTier()+1],parallax:lastMix,focusPath:focusPath.map(v=>({...v})),focusSelected,keyboardOpen:!keyboard.hidden,keyboardMode,toolMode})
});
focusSelected='all';
renderKeyboardTabs();
renderState();
})();