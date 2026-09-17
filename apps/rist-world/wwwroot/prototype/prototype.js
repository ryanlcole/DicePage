(() => {
'use strict';
const ASSET_ROOT='https://d2d6rnm6fnsp89.cloudfront.net/library/terrains/standard/world/whole_maps/geonaph/';
const LAYERS_PER_TIER=10;
const STRATA=[['universe','Universe',30],['sky','Sky',20],['weather','Weather',10],['surface','Surface',0],['subterranean','Subterranean',-10],['depths','Depths',-20],['core','Core',-30]].map(([key,label,z])=>Object.freeze({key,label,z}));
const ROOT_OPTIONS=Object.freeze([...STRATA,Object.freeze({key:'all',label:'All parallax',z:null})]);
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
const stage=$('stage'),world=$('world'),surface=$('surfacePlane'),highlands=$('highlandsPlane'),mountains=$('mountainPlane'),loading=$('loading'),shortcut=$('stratumShortcut'),viewLabel=$('viewLabel'),zoomLabel=$('zoomLabel'),pathLabel=$('pathLabel'),stratumNote=$('stratumNote'),focusSelect=$('focusSelect'),focusLevel=$('focusLevel'),focusLock=$('focusLock'),focusBack=$('focusBack'),focusTrail=$('focusTrail'),battle=$('battleInstance'),battleText=$('battleText'),keyboard=$('viewerKeyboard'),keyboardToggle=$('keyboardToggle'),keyboardTabs=$('keyboardTabs'),keyboardKeys=$('keyboardKeys'),live=$('live');
const planeByKey={surface,highlands,mountains};
const layerReady={surface:false,highlands:false,mountains:false};
const pointers=new Map();
let naturalWidth=1,naturalHeight=1,scale=1,minScale=.1,maxScale=12,x=0,y=0,fitX=0,fitY=0,panStart=null,pinchStart=null,viewerZ=0,activeStratum='surface',parallaxOverride=false,focusPath=[],focusSelected='surface',keyboardMode='Viewer',toolMode='Inspect',lastMix={zoomZ:0,highlands:1,mountains:.82},tiltBaseline=null,tiltTargetX=0,tiltTargetY=0,tiltX=0,tiltY=0,tiltFrame=0;

function splitZ(z){const tierIndex=Math.floor(z/LAYERS_PER_TIER);return{tierIndex,layerOffset:z-tierIndex*LAYERS_PER_TIER}}
function stratumByKey(key){return STRATA.find(s=>s.key===key)||STRATA.find(s=>s.key==='surface')}
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

// Zoom reveals the registered surface stack as overlapping depth planes.
// Peak artwork starts translucent so the second plane is already readable beneath it.
// The peak -> highlands handoff is shorter; highlands -> surface intentionally spans
// a wider zoom interval so the viewer has time to read the middle representation.
function parallaxMix(){
  const zoomRatio=Math.max(.01,scale/Math.max(minScale,.00001));
  const zoomZ=Math.max(0,Math.log2(zoomRatio)*LAYERS_PER_TIER);
  const peakToHighlands=smoothstep(1.00,1.60,zoomRatio);
  const highlandsToSurface=smoothstep(1.45,2.75,zoomRatio);
  let mountainAlpha=.82*(1-peakToHighlands);
  let highlandAlpha=1-highlandsToSurface;
  if(!layerReady.highlands)highlandAlpha=0;
  if(!layerReady.mountains)mountainAlpha=0;
  return{zoomRatio,zoomZ,highlands:clamp(highlandAlpha,0,1),mountains:clamp(mountainAlpha,0,1)};
}
function applyParallax(mix=parallaxMix()){
  const dx=x-fitX,dy=y-fitY;
  surface.style.opacity='1';
  surface.style.transform='translate3d(0,0,0)';
  const layers=[
    {node:highlands,sceneZ:4,alpha:mix.highlands},
    {node:mountains,sceneZ:7,alpha:mix.mountains}
  ];
  for(const layer of layers){
    const depth=layer.sceneZ/LAYERS_PER_TIER;
    const panStrength=depth*.055;
    const tiltStrength=.42+(depth*.78);
    const localX=((-dx*panStrength)+(tiltX*tiltStrength))/Math.max(scale,.00001);
    const localY=((-dy*panStrength)+(tiltY*tiltStrength))/Math.max(scale,.00001);
    layer.node.style.opacity=layer.alpha.toFixed(3);
    layer.node.style.transform=`translate3d(${localX.toFixed(2)}px,${localY.toFixed(2)}px,0)`;
  }
  lastMix=mix;
}
function updateReadouts(){
  const s=stratumByKey(activeStratum),mix=lastMix;
  const label=parallaxOverride?'All parallax':s.label;
  viewLabel.textContent=`${label} · Z ${viewerZ}`;
  pathLabel.textContent='Focus: '+(focusPath.length?focusPath.map(p=>p.label).join(' › '):'Parallax');
  const zoomRatio=Math.max(.01,scale/Math.max(minScale,.00001));
  const fit=Math.abs(x-fitX)<.5&&Math.abs(y-fitY)<.5&&Math.abs(scale-minScale)<.0001;
  zoomLabel.textContent=`${fit?'Fit · ':''}${zoomRatio.toFixed(2)}× · PZ ${mix.zoomZ.toFixed(1)}`;
  stratumNote.innerHTML=`<strong>${label}</strong> · H ${Math.round(mix.highlands*100)}% · M ${Math.round(mix.mountains*100)}%`;
  stratumNote.setAttribute('aria-label',`${label}. Highlands detail layer ${Math.round(mix.highlands*100)} percent visible. Mountain and snow peak layer ${Math.round(mix.mountains*100)} percent visible. Upper layers fade after the viewer passes their parallax depth.`);
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

function setViewerZ(value,reason){viewerZ=Math.trunc(value);parallaxOverride=false;shortcut.value=activeStratum;renderState();announce(`${reason}. Viewer Z ${viewerZ}. World truth unchanged.`)}
function jumpStratum(key){
  if(key==='all'){
    parallaxOverride=true;activeStratum='surface';viewerZ=0;focusPath=[];focusSelected='all';shortcut.value='all';renderState();announce('All parallax viewer mode. The complete registered visual stack is visible at world view and each layer fades only after its depth is passed.');return;
  }
  const s=stratumByKey(key);
  parallaxOverride=false;activeStratum=s.key;viewerZ=s.z;focusPath=[];focusSelected=s.key;shortcut.value=s.key;renderState();announce(`${s.label} viewer shortcut. Z ${s.z}. Focus reset; map truth unchanged.`);
}
function selectFocus(key){
  const match=focusOptions().find(o=>o.key===key);if(!match)return;
  focusSelected=match.key;
  if(focusPath.length===0){
    if(match.key==='all'){parallaxOverride=true;shortcut.value='all'}
    else{const s=stratumByKey(match.key);activeStratum=s.key;viewerZ=s.z;parallaxOverride=false;shortcut.value=s.key}
  }
  renderState();announce(`${match.label} selected. Lock to reveal ${focusPath.length===0?'Category':nextLevel()}.`);
}
function lockFocus(){
  const match=selectedOption();if(!match)return;
  focusPath.push({level:match.level,key:match.key,label:match.label});
  if(match.level==='Parallax'){
    if(match.key==='all'){parallaxOverride=true;activeStratum='surface';viewerZ=0;shortcut.value='all'}
    else{const s=stratumByKey(match.key);parallaxOverride=false;activeStratum=s.key;viewerZ=s.z;shortcut.value=s.key}
  }
  focusSelected=focusOptions()[0]?.key||'';
  renderState();
  announce(match.level==='Entity'?`${match.label} locked. Battle Instance revealed.`:`${match.label} locked. ${nextLevel()} revealed.`);
}
function unlockFocus(){if(!focusPath.length)return;const removed=focusPath.pop();const opts=focusOptions();focusSelected=opts.some(o=>o.key===removed.key)?removed.key:(opts[0]?.key||'');renderState();announce(`Returned from ${removed.label} to ${nextLevel()}.`)}
function rewindFocus(index){while(focusPath.length>index+1)focusPath.pop();focusSelected=focusOptions()[0]?.key||'';renderState();announce(`Focus returned to ${focusPath[index]?.label||'Surface'}.`)}
function resetFocus(){jumpStratum('surface')}
function renderFocus(){
  normalizeFocusSelection();
  const opts=focusOptions(),entityLocked=focusPath.some(p=>p.level==='Entity'),level=entityLocked?'Battle Instance':nextLevel();
  focusLevel.textContent=level;
  focusSelect.replaceChildren();
  if(opts.length){
    opts.forEach(o=>{const el=document.createElement('option');el.value=o.key;el.textContent=o.label;focusSelect.append(el)});
    focusSelect.value=focusSelected;
  }else{
    const el=document.createElement('option');el.textContent=entityLocked?'Battle Instance':'No content';el.value='';focusSelect.append(el);
  }
  focusSelect.disabled=!opts.length||entityLocked;
  focusLock.disabled=!opts.length||entityLocked;
  focusLock.classList.toggle('active',!!opts.length&&!entityLocked);
  focusLock.textContent=entityLocked?'LOCKED':'LOCK';
  focusBack.disabled=!focusPath.length;
  focusTrail.replaceChildren();
  focusPath.forEach((p,i)=>{const b=document.createElement('button');b.type='button';b.className='crumb';b.textContent=p.label;b.setAttribute('aria-label','Return focus to '+p.label);b.addEventListener('click',()=>rewindFocus(i));focusTrail.append(b)});
  stage.classList.toggle('focus-deep',focusPath.length>0);
  battle.hidden=!entityLocked;
  if(entityLocked){const e=focusPath.find(p=>p.level==='Entity');battleText.textContent=`${e?.label||'Entity'} focus · tactical viewer representation. Canonical XYZ identity remains unchanged.`}
}
function renderState(){renderFocus();applyTransform();renderKeyboardKeys()}

const KEYBOARD_MODES=['Viewer','Pixels','Tiles','Sprites','Labels','Litch','CAD','Stylus','Tethers','Metadata','Selected'];
function toolKey(label,sub,fn,disabled=false){const b=document.createElement('button');b.type='button';b.disabled=disabled;b.innerHTML=`<strong>${label}</strong><small>${sub}</small>`;b.addEventListener('click',fn);return b}
function setTool(name){toolMode=name;announce(`${name} tool selected. Prototype tool mode changes controls only; world truth is not altered.`);renderKeyboardKeys()}
function renderKeyboardTabs(){keyboardTabs.replaceChildren();KEYBOARD_MODES.forEach(mode=>{const b=document.createElement('button');b.type='button';b.role='tab';b.textContent=mode;b.classList.toggle('active',mode===keyboardMode);b.setAttribute('aria-selected',String(mode===keyboardMode));b.addEventListener('click',()=>{keyboardMode=mode;renderKeyboardTabs();renderKeyboardKeys();announce(`${mode} keyboard opened.`)});keyboardTabs.append(b)})}
function renderKeyboardKeys(){
  if(!keyboardKeys)return;
  keyboardKeys.replaceChildren();
  const z=splitZ(viewerZ);
  if(keyboardMode==='Viewer'){
    keyboardKeys.append(
      toolKey('Z −','layer',()=>setViewerZ(viewerZ-1,'Viewer moved down one layer')),
      toolKey('Z +','layer',()=>setViewerZ(viewerZ+1,'Viewer moved up one layer')),
      toolKey('T −','tier',()=>setViewerZ(viewerZ-LAYERS_PER_TIER,'Viewer moved down one tier')),
      toolKey('T +','tier',()=>setViewerZ(viewerZ+LAYERS_PER_TIER,'Viewer moved up one tier')),
      toolKey('−','zoom',()=>{const r=stage.getBoundingClientRect();zoomAt(r.left+r.width/2,r.top+r.height/2,1/1.22)}),
      toolKey('+','zoom',()=>{const r=stage.getBoundingClientRect();zoomAt(r.left+r.width/2,r.top+r.height/2,1.22)}),
      toolKey('FIT','camera',fitMap),
      toolKey('ALL','parallax',()=>jumpStratum('all'))
    );
    const read=toolKey(`T${z.tierIndex} L${z.layerOffset}`,'Z '+viewerZ,()=>{},true);read.classList.add('readout');keyboardKeys.append(read);return;
  }
  if(keyboardMode==='Selected'){
    keyboardKeys.append(toolKey('LOCK','focus',lockFocus,!focusOptions().length||focusPath.some(p=>p.level==='Entity')),toolKey('BACK','focus',unlockFocus,!focusPath.length),toolKey('HOME','Surface',resetFocus),toolKey('INSPECT','viewer',()=>setTool('Inspect')),toolKey('META','viewer',()=>setTool('Metadata')));return;
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

shortcut.addEventListener('change',()=>jumpStratum(shortcut.value));
focusSelect.addEventListener('change',()=>selectFocus(focusSelect.value));
focusLock.addEventListener('click',lockFocus);
focusBack.addEventListener('click',unlockFocus);
$('focusReset').addEventListener('click',resetFocus);
$('fit').addEventListener('click',fitMap);
$('zoomIn').addEventListener('click',()=>{const r=stage.getBoundingClientRect();zoomAt(r.left+r.width/2,r.top+r.height/2,1.22)});
$('zoomOut').addEventListener('click',()=>{const r=stage.getBoundingClientRect();zoomAt(r.left+r.width/2,r.top+r.height/2,1/1.22)});
$('back').addEventListener('click',()=>{if(history.length>1)history.back();else location.href='/Game/index.html'});
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
  getViewerState:()=>({activeStratum,viewerZ,...splitZ(viewerZ),parallaxOverride,parallax:lastMix,focusPath:focusPath.map(v=>({...v})),focusSelected,keyboardOpen:!keyboard.hidden,keyboardMode,toolMode})
});
shortcut.value='surface';
renderKeyboardTabs();
renderState();
})();