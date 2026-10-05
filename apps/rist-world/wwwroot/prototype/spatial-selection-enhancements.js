(() => {
'use strict';

const query=new URLSearchParams(location.search);
if(window.parent===window||query.get('live-worldbuilder')!=='1'||String(query.get('mode')||'worldbuilder').toLowerCase()==='regiondefiner')return;

const baseApi=window.ShaelvienPrototype;
if(!baseApi)return;

const context={
  worldId:String(query.get('worldId')||''),
  deedId:String(query.get('deedId')||''),
  deedRegionId:String(query.get('deedRegionId')||''),
  deedZoneId:String(query.get('deedZone')||''),
  seed:String(query.get('seed')||'')
};

const BORDER_PALETTES=Object.freeze([
  Object.freeze({key:'gold',label:'GOLD',dark:'#6f4708',base:'#d1a13b',light:'#fff0a3'}),
  Object.freeze({key:'silver',label:'SILVER',dark:'#4d5960',base:'#b9c4ca',light:'#ffffff'}),
  Object.freeze({key:'cyan',label:'CYAN',dark:'#07536d',base:'#35c7f4',light:'#d9f8ff'}),
  Object.freeze({key:'magenta',label:'MAGENTA',dark:'#6d145b',base:'#e865ce',light:'#ffe2fa'}),
  Object.freeze({key:'white',label:'WHITE',dark:'#696969',base:'#ededed',light:'#ffffff'}),
  Object.freeze({key:'black',label:'BLACK',dark:'#000000',base:'#262626',light:'#9a9a9a'})
]);

let active=false;
let phase='idle'; // idle -> reference -> xy -> z -> ready
let autoFill=true;
let borderIndex=0;
let optionMode='autofill';
let overlayObserver=null;
let parentObserver=null;
let depthPerspectiveObserver=null;
let decorating=false;
let decorateQueued=false;
let parentOriginal=null;
let swipeStart=null;
let suppressClickUntil=0;
let footprintSnapshot=null;
let referenceTier=0;
let referenceLayer=0;
let zMinTier=null;
let zMaxTier=null;
let zLayersPerTier=10;
let originalViewAngle=0;
const boundParentButtons=new WeakSet();
const boundParentSliders=new WeakSet();

const clamp=(value,min,max)=>Math.min(max,Math.max(min,value));
const palette=()=>BORDER_PALETTES[borderIndex]||BORDER_PALETTES[0];

function announce(text){
  const live=document.getElementById('live');
  if(!live)return;
  live.textContent='';
  requestAnimationFrame(()=>{live.textContent=text});
}

function postSelectionCount(snapshot,force=false){
  if((!active&&!force)||!snapshot)return;
  try{
    window.parent.postMessage({
      source:'shaelvien-worldbuilder',
      type:'spatial-selection-change',
      ...context,
      selection:{active:true,count:snapshot.selectedCells.length,gridShape:snapshot.gridShape||'hex'}
    },location.origin);
  }catch{}
}

function rawSnapshot(){
  try{return baseApi?.getSpatialSelection?.()||null}catch{return null}
}

function cellRow(cell,columns){return Math.floor(cell/columns)}
function cellColumn(cell,columns){return cell%columns}

function hexNeighbors(cell,columns,rows){
  const row=cellRow(cell,columns),column=cellColumn(cell,columns),odd=(row&1)===1;
  const offsets=odd
    ?[[0,-1],[0,1],[-1,0],[-1,1],[1,0],[1,1]]
    :[[0,-1],[0,1],[-1,-1],[-1,0],[1,-1],[1,0]];
  const result=[];
  for(const [dr,dc] of offsets){
    const rr=row+dr,cc=column+dc;
    if(rr>=0&&rr<rows&&cc>=0&&cc<columns)result.push(rr*columns+cc);
  }
  return result;
}

function squareNeighbors(cell,columns,rows){
  const row=cellRow(cell,columns),column=cellColumn(cell,columns),result=[];
  for(const [dr,dc] of [[-1,0],[1,0],[0,-1],[0,1]]){
    const rr=row+dr,cc=column+dc;
    if(rr>=0&&rr<rows&&cc>=0&&cc<columns)result.push(rr*columns+cc);
  }
  return result;
}

function filledSelection(snapshot){
  const columns=Math.max(1,Math.trunc(Number(snapshot?.columns)||30));
  const rows=Math.max(1,Math.trunc(Number(snapshot?.rows)||30));
  const selected=new Set((Array.isArray(snapshot?.selectedCells)?snapshot.selectedCells:[])
    .map(value=>Math.trunc(Number(value)))
    .filter(value=>Number.isInteger(value)&&value>=0&&value<columns*rows));
  if(!autoFill||!selected.size)return selected;

  const outside=new Set(),queue=[];
  const enqueue=cell=>{
    if(selected.has(cell)||outside.has(cell))return;
    outside.add(cell);queue.push(cell);
  };

  for(let column=0;column<columns;column++){
    enqueue(column);enqueue((rows-1)*columns+column);
  }
  for(let row=0;row<rows;row++){
    enqueue(row*columns);enqueue(row*columns+(columns-1));
  }

  const isHex=String(snapshot?.gridShape||'hex').toLowerCase()!=='square';
  for(let head=0;head<queue.length;head++){
    const neighbors=isHex?hexNeighbors(queue[head],columns,rows):squareNeighbors(queue[head],columns,rows);
    for(const neighbor of neighbors)enqueue(neighbor);
  }

  const filled=new Set(selected);
  for(let cell=0;cell<columns*rows;cell++){
    if(!selected.has(cell)&&!outside.has(cell))filled.add(cell);
  }
  return filled;
}

function localBounds(snapshot,cells){
  if(!cells.size)return null;
  const columns=Math.max(1,Math.trunc(Number(snapshot.columns)||30));
  const rows=Math.max(1,Math.trunc(Number(snapshot.rows)||30));
  const isHex=String(snapshot.gridShape||'hex').toLowerCase()!=='square';
  const viewWidth=isHex?columns+.5:columns;
  let minX=1,minY=1,maxX=0,maxY=0;
  for(const cell of cells){
    const row=cellRow(cell,columns),column=cellColumn(cell,columns),offset=isHex&&(row&1)?0.5:0;
    minX=Math.min(minX,(column+offset)/viewWidth);maxX=Math.max(maxX,(column+offset+1)/viewWidth);
    minY=Math.min(minY,row/rows);maxY=Math.max(maxY,(row+1)/rows);
  }
  return{minX:clamp(minX,0,1),minY:clamp(minY,0,1),maxX:clamp(maxX,0,1),maxY:clamp(maxY,0,1)};
}

function canonicalCells(snapshot,cells){
  const columns=Math.max(1,Math.trunc(Number(snapshot.columns)||30));
  const rows=Math.max(1,Math.trunc(Number(snapshot.rows)||30));
  const isHex=String(snapshot.gridShape||'hex').toLowerCase()!=='square';
  const viewWidth=isHex?columns+.5:columns;
  const minX=clamp(Number(snapshot.viewMinX)||0,0,1),minY=clamp(Number(snapshot.viewMinY)||0,0,1);
  const maxX=clamp(Number(snapshot.viewMaxX)||1,minX,1),maxY=clamp(Number(snapshot.viewMaxY)||1,minY,1);
  const result=new Set();
  for(const cell of cells){
    const row=cellRow(cell,columns),column=cellColumn(cell,columns),offset=isHex&&(row&1)?0.5:0;
    const lx=(column+offset+.5)/viewWidth,ly=(row+.5)/rows;
    const px=minX+(lx*(maxX-minX)),py=minY+(ly*(maxY-minY));
    const cx=clamp(Math.floor(px*300),0,299),cy=clamp(Math.floor(py*300),0,299);
    result.add(cy*300+cx);
  }
  return[...result].sort((a,b)=>a-b);
}

function augmentedSnapshot(snapshot=rawSnapshot()){
  if(!snapshot||!active)return snapshot;
  const cells=filledSelection(snapshot),selectedCells=[...cells].sort((a,b)=>a-b),bounds=localBounds(snapshot,cells);
  const minX=clamp(Number(snapshot.viewMinX)||0,0,1),minY=clamp(Number(snapshot.viewMinY)||0,0,1);
  const maxX=clamp(Number(snapshot.viewMaxX)||1,minX,1),maxY=clamp(Number(snapshot.viewMaxY)||1,minY,1);
  const mapX=value=>minX+(value*(maxX-minX)),mapY=value=>minY+(value*(maxY-minY));
  return{
    ...snapshot,
    selectedCells,
    canonicalCells:canonicalCells(snapshot,cells),
    canonicalMinX:bounds?mapX(bounds.minX):Number(snapshot.canonicalMinX)||minX,
    canonicalMinY:bounds?mapY(bounds.minY):Number(snapshot.canonicalMinY)||minY,
    canonicalMaxX:bounds?mapX(bounds.maxX):Number(snapshot.canonicalMaxX)||maxX,
    canonicalMaxY:bounds?mapY(bounds.maxY):Number(snapshot.canonicalMaxY)||maxY,
    autoFill,
    borderColor:palette().key,
    borderLabel:palette().label
  };
}

function cellPolygon(cell,columns){
  const row=cellRow(cell,columns),column=cellColumn(cell,columns),x=column+((row&1)?0.5:0),y=row;
  return `${x+.25},${y} ${x+.75},${y} ${x+1},${y+.5} ${x+.75},${y+1} ${x+.25},${y+1} ${x},${y+.5}`;
}

function renderEnhancedSvg(snapshot,focusPoints=''){
  const columns=Math.max(1,Math.trunc(Number(snapshot.columns)||30));
  const rows=Math.max(1,Math.trunc(Number(snapshot.rows)||30));
  const isHex=String(snapshot.gridShape||'hex').toLowerCase()!=='square';
  const viewWidth=isHex?columns+.5:columns,cells=filledSelection(snapshot),p=palette(),figures=[];
  for(const cell of [...cells].sort((a,b)=>a-b)){
    const row=cellRow(cell,columns),column=cellColumn(cell,columns);
    if(isHex)figures.push(`<polygon points="${cellPolygon(cell,columns)}" fill="rgba(69,178,221,.27)" stroke="rgba(69,178,221,.24)" stroke-width=".08"/>`);
    else figures.push(`<rect x="${column}" y="${row}" width="1" height="1" fill="rgba(69,178,221,.27)" stroke="rgba(69,178,221,.24)" stroke-width=".05"/>`);
  }
  const focus=focusPoints&&isHex
    ?`<polygon class="focus" points="${focusPoints}" fill="rgba(255,255,255,.05)" stroke="${p.light}" stroke-width=".07" vector-effect="non-scaling-stroke"/>`
    :'';
  return `<svg data-selection-enhanced="true" viewBox="0 0 ${viewWidth} ${rows}" preserveAspectRatio="none" aria-hidden="true">
    <defs><filter id="spatialMetalBorder" x="-12%" y="-12%" width="124%" height="124%" color-interpolation-filters="sRGB">
      <feMorphology in="SourceAlpha" operator="dilate" radius=".11" result="outerDilate"/><feComposite in="outerDilate" in2="SourceAlpha" operator="out" result="outerRing"/><feFlood flood-color="${p.dark}" result="outerColor"/><feComposite in="outerColor" in2="outerRing" operator="in" result="outerStroke"/>
      <feMorphology in="SourceAlpha" operator="dilate" radius=".07" result="midDilate"/><feComposite in="midDilate" in2="SourceAlpha" operator="out" result="midRing"/><feFlood flood-color="${p.base}" result="midColor"/><feComposite in="midColor" in2="midRing" operator="in" result="midStroke"/>
      <feMorphology in="SourceAlpha" operator="dilate" radius=".028" result="shineDilate"/><feComposite in="shineDilate" in2="SourceAlpha" operator="out" result="shineRing"/><feFlood flood-color="${p.light}" result="shineColor"/><feComposite in="shineColor" in2="shineRing" operator="in" result="shineStroke"/>
      <feMerge><feMergeNode in="outerStroke"/><feMergeNode in="midStroke"/><feMergeNode in="shineStroke"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter></defs><g filter="url(#spatialMetalBorder)">${figures.join('')}</g>${focus}</svg>`;
}

function selectionSignature(snapshot,focusPoints){
  const selected=Array.isArray(snapshot?.selectedCells)?snapshot.selectedCells.join(','):'';
  return `${snapshot?.gridShape||'hex'}|${snapshot?.columns||30}x${snapshot?.rows||30}|${selected}|${focusPoints}|${autoFill?'1':'0'}|${palette().key}`;
}

function scheduleDecorate(){
  if(!active||decorateQueued)return;
  decorateQueued=true;
  requestAnimationFrame(()=>{decorateQueued=false;decorateOverlay()});
}

function decorateOverlay(){
  if(!active||decorating)return;
  const overlay=document.querySelector('.spatial-selection-grid.active'),snapshot=rawSnapshot();
  if(!overlay||!snapshot)return;
  const currentSvg=overlay.querySelector('svg'),focusPoints=currentSvg?.querySelector('.focus')?.getAttribute('points')||'';
  const signature=selectionSignature(snapshot,focusPoints);
  if(currentSvg?.dataset.selectionEnhanced==='true'&&overlay.dataset.enhancedSignature===signature)return;
  decorating=true;
  try{
    const effective=augmentedSnapshot(snapshot);
    overlay.innerHTML=renderEnhancedSvg(snapshot,focusPoints);
    overlay.dataset.enhancedSignature=signature;
    overlay.dataset.autoFill=autoFill?'true':'false';overlay.dataset.borderColor=palette().key;
    overlay.setAttribute('aria-label',`${effective.selectedCells.length} ${snapshot.gridShape||'hex'} cells selected. Autofill ${autoFill?'on':'off'}. Border ${palette().label}.`);
    postSelectionCount(effective);
  }finally{decorating=false}
}

function startOverlayObserver(){
  stopOverlayObserver();
  const overlay=document.querySelector('.spatial-selection-grid.active');
  if(!overlay)return;
  overlayObserver=new MutationObserver(()=>{if(active&&!decorating)scheduleDecorate()});
  overlayObserver.observe(overlay,{childList:true,subtree:true});scheduleDecorate();
}
function stopOverlayObserver(){overlayObserver?.disconnect();overlayObserver=null}

function parentNodes(){
  try{
    const doc=window.parent.document,button=doc.querySelector('.control-display-right');
    return{doc,button,slider:button?.closest('.display-slider-right')||null,shell:doc.querySelector('.universal-shell')};
  }catch{return{doc:null,button:null,slider:null,shell:null}}
}

function bindParentControls(){
  if(!active)return;
  const {button,slider}=parentNodes();
  if(button&&!boundParentButtons.has(button)){
    boundParentButtons.add(button);
    button.addEventListener('click',event=>{
      if(!active)return;
      event.preventDefault();event.stopImmediatePropagation();
      if(performance.now()<suppressClickUntil)return;
      if(optionMode==='autofill')toggleAutoFill();else cycleBorder(1);
    },true);
  }
  if(slider&&!boundParentSliders.has(slider)){
    boundParentSliders.add(slider);
    slider.addEventListener('pointerdown',event=>{if(active)swipeStart={id:event.pointerId,x:event.clientX,y:event.clientY}},true);
    slider.addEventListener('pointerup',event=>{
      if(!active||!swipeStart||swipeStart.id!==event.pointerId)return;
      const dx=event.clientX-swipeStart.x,dy=event.clientY-swipeStart.y;swipeStart=null;
      if(Math.abs(dx)<30||Math.abs(dx)<Math.abs(dy)*1.2)return;
      event.preventDefault();event.stopImmediatePropagation();suppressClickUntil=performance.now()+450;
      optionMode=optionMode==='autofill'?'border':'autofill';applyParentPresentation();
    },true);
    slider.addEventListener('pointercancel',()=>{swipeStart=null},true);
  }
}

function rememberParentPresentation(button){
  if(parentOriginal||!button)return;
  parentOriginal={button,eyebrow:button.querySelector('small')?.textContent||'',value:button.querySelector('strong')?.textContent||'',prompt:button.querySelector('span')?.textContent||'',aria:button.getAttribute('aria-label')||''};
}

function applyParentPresentation(){
  if(!active)return;
  const {button,shell}=parentNodes();if(!button)return;
  rememberParentPresentation(button);bindParentControls();shell?.classList.add('spatial-selection-options-active');
  const eyebrow=button.querySelector('small'),value=button.querySelector('strong'),prompt=button.querySelector('span');
  if(eyebrow)eyebrow.textContent='SELECTION OPTIONS';
  if(optionMode==='autofill'){
    if(value)value.textContent=`AUTOFILL · ${autoFill?'ON':'OFF'}`;
    if(prompt)prompt.textContent='SWIPE ↔ BORDER · TOUCH TOGGLE';
    button.setAttribute('aria-label',`Selection options. Autofill ${autoFill?'on':'off'}. Touch to toggle. Swipe horizontally for border color.`);
  }else{
    if(value)value.textContent=`BORDER · ${palette().label}`;
    if(prompt)prompt.textContent='SWIPE ↔ AUTOFILL · TOUCH COLOR';
    button.setAttribute('aria-label',`Selection options. Border ${palette().label}. Touch to change color. Swipe horizontally for autofill.`);
  }
}

function startParentObserver(){
  stopParentObserver();const {doc}=parentNodes();if(!doc?.body)return;
  parentObserver=new MutationObserver(()=>{if(active)requestAnimationFrame(applyParentPresentation)});
  parentObserver.observe(doc.body,{childList:true,subtree:true,characterData:true});applyParentPresentation();
}
function stopParentObserver(){parentObserver?.disconnect();parentObserver=null}
function restoreParentPresentation(){
  stopParentObserver();
  try{
    const {shell}=parentNodes();shell?.classList.remove('spatial-selection-options-active');
    if(parentOriginal?.button?.isConnected){
      const button=parentOriginal.button,eyebrow=button.querySelector('small'),value=button.querySelector('strong'),prompt=button.querySelector('span');
      if(eyebrow)eyebrow.textContent=parentOriginal.eyebrow;if(value)value.textContent=parentOriginal.value;if(prompt)prompt.textContent=parentOriginal.prompt;if(parentOriginal.aria)button.setAttribute('aria-label',parentOriginal.aria);
    }
  }catch{}
  parentOriginal=null;
}

function toggleAutoFill(){
  autoFill=!autoFill;const overlay=document.querySelector('.spatial-selection-grid.active');if(overlay)delete overlay.dataset.enhancedSignature;
  scheduleDecorate();applyParentPresentation();announce(`Autofill ${autoFill?'on':'off'}.`);return autoFill;
}
function cycleBorder(direction=1){
  const step=Math.sign(Number(direction)||1)||1;borderIndex=(borderIndex+step+BORDER_PALETTES.length)%BORDER_PALETTES.length;
  const overlay=document.querySelector('.spatial-selection-grid.active');if(overlay)delete overlay.dataset.enhancedSignature;
  scheduleDecorate();applyParentPresentation();announce(`Selection border ${palette().label}.`);return palette().key;
}

function applyEffectiveMask(snapshot){
  if(!snapshot?.selectedCells?.length)return;
  const columns=Math.max(1,Math.trunc(Number(snapshot.columns)||30)),rows=Math.max(1,Math.trunc(Number(snapshot.rows)||30));
  const isHex=String(snapshot.gridShape||'hex').toLowerCase()!=='square',viewWidth=isHex?columns+.5:columns;
  const minX=clamp(Number(snapshot.viewMinX)||0,0,1),minY=clamp(Number(snapshot.viewMinY)||0,0,1),maxX=clamp(Number(snapshot.viewMaxX)||1,minX,1),maxY=clamp(Number(snapshot.viewMaxY)||1,minY,1);
  const mapPoint=(ux,uy)=>({x:(minX+(clamp(ux/viewWidth,0,1)*(maxX-minX)))*1000,y:(minY+(clamp(uy/rows,0,1)*(maxY-minY)))*1000}),figures=[];
  for(const cell of snapshot.selectedCells){
    const row=cellRow(cell,columns),column=cellColumn(cell,columns);
    if(isHex){
      const offset=(row&1)?0.5:0,x0=column+offset,y0=row,local=[[x0+.25,y0],[x0+.75,y0],[x0+1,y0+.5],[x0+.75,y0+1],[x0+.25,y0+1],[x0,y0+.5]];
      figures.push(`<polygon points="${local.map(([px,py])=>{const p=mapPoint(px,py);return `${p.x},${p.y}`}).join(' ')}" fill="white"/>`);
    }else{
      const a=mapPoint(column,row),b=mapPoint(column+1,row+1);figures.push(`<rect x="${a.x}" y="${a.y}" width="${Math.max(.1,b.x-a.x)}" height="${Math.max(.1,b.y-a.y)}" fill="white"/>`);
    }
  }
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" preserveAspectRatio="none">${figures.join('')}</svg>`,world=document.getElementById('world');if(!world)return;
  const url=`url("data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}")`;
  world.style.maskImage=url;world.style.webkitMaskImage=url;world.style.maskSize='100% 100%';world.style.webkitMaskSize='100% 100%';world.style.maskRepeat='no-repeat';world.style.webkitMaskRepeat='no-repeat';
}

function clearEffectiveMask(){
  const world=document.getElementById('world');if(!world)return;
  world.style.maskImage='none';world.style.webkitMaskImage='none';world.style.maskSize='';world.style.webkitMaskSize='';world.style.maskRepeat='';world.style.webkitMaskRepeat='';
}

function enforceSixtyDegreeView(){
  if(phase!=='z'&&phase!=='ready')return;
  const world=document.getElementById('world');if(!world)return;
  const current=String(world.style.transform||'');
  const next=/rotateX\([^)]*\)/.test(current)?current.replace(/rotateX\([^)]*\)/,'rotateX(60deg)'):`${current} rotateX(60deg)`;
  if(next!==current)world.style.transform=next;
  const stage=document.getElementById('stage');if(stage)stage.dataset.spatialDepthAngle='60';
}

function startDepthPerspective(angle){
  stopDepthPerspective(false);
  originalViewAngle=Math.max(0,Number(angle)||0);
  try{baseApi?.setViewAngle?.(45,{persist:false,announceChange:false})}catch{}
  phase='z';
  const world=document.getElementById('world');
  enforceSixtyDegreeView();
  if(world){
    depthPerspectiveObserver=new MutationObserver(()=>enforceSixtyDegreeView());
    depthPerspectiveObserver.observe(world,{attributes:true,attributeFilter:['style']});
  }
  try{parentNodes().shell?.classList.add('spatial-map-selecting')}catch{}
}

function stopDepthPerspective(restore=true){
  depthPerspectiveObserver?.disconnect();depthPerspectiveObserver=null;
  const stage=document.getElementById('stage');if(stage)delete stage.dataset.spatialDepthAngle;
  try{parentNodes().shell?.classList.remove('spatial-map-selecting')}catch{}
  if(restore){try{baseApi?.setViewAngle?.(originalViewAngle,{persist:false,announceChange:false})}catch{}}
}

function beginSpatialSelection(raw={}){
  const started=baseApi?.beginSpatialSelection?.({...raw,gridShape:'hex',columns:30,rows:30});
  if(!started)return started;
  phase='reference';active=false;footprintSnapshot=null;zMinTier=zMaxTier=null;referenceTier=0;referenceLayer=0;zLayersPerTier=10;
  autoFill=true;borderIndex=0;optionMode='autofill';
  announce('Choose the reference Tier and Layer first. X/Y hex selection is locked until that depth is confirmed.');
  return true;
}

function activateFootprint(raw={}){
  const activated=baseApi?.activateSpatialFootprint?.(raw);
  if(!activated)return false;
  referenceTier=Math.max(0,Math.trunc(Number(raw.tier)||0));referenceLayer=Math.max(0,Math.trunc(Number(raw.layer)||0));
  phase='xy';active=true;autoFill=true;borderIndex=0;optionMode='autofill';
  requestAnimationFrame(()=>{startOverlayObserver();startParentObserver();const snapshot=augmentedSnapshot();if(snapshot)postSelectionCount(snapshot)});
  announce('30 by 30 footprint selection active. Select the X/Y cells that belong to this space.');
  return true;
}

function volumeSnapshot(){
  if(!footprintSnapshot||zMinTier===null||zMaxTier===null)return null;
  const min=Math.min(zMinTier,zMaxTier),max=Math.max(zMinTier,zMaxTier),tiers=[];
  for(let tier=min;tier<=max;tier++)tiers.push(tier);
  return{
    ...footprintSnapshot,
    active:false,
    tierIndex:referenceTier,
    visibleTierIndices:tiers,
    visibleLayerOffsets:Array.from({length:Math.max(1,zLayersPerTier)},(_,index)=>index),
    referenceTier,
    referenceLayer,
    zMinTier:min,
    zMaxTier:max
  };
}

function getSpatialSelection(){
  if(phase==='xy'){
    const snapshot=augmentedSnapshot();
    if(!snapshot?.selectedCells?.length)return snapshot;
    footprintSnapshot={...snapshot,selectedCells:[...snapshot.selectedCells],canonicalCells:[...(snapshot.canonicalCells||[])],visibleTierIndices:[...(snapshot.visibleTierIndices||[])],visibleLayerOffsets:[...(snapshot.visibleLayerOffsets||[])]};
    originalViewAngle=Math.max(0,Number(snapshot.viewAngle)||0);
    const focused=baseApi?.finishSpatialFootprint?.(true);
    if(focused!==false)requestAnimationFrame(()=>applyEffectiveMask(footprintSnapshot));
    postSelectionCount(footprintSnapshot,true);
    active=false;stopOverlayObserver();restoreParentPresentation();swipeStart=null;
    startDepthPerspective(originalViewAngle);
    setTimeout(()=>{baseApi?.beginSpatialVolumeDepth?.(footprintSnapshot)},0);
    announce('X/Y footprint saved. Everything outside it is hidden. The viewer is now at 60 degrees for Z-tier selection.');
    return null;
  }
  if(phase==='ready')return volumeSnapshot();
  if(phase==='z'||phase==='reference')return null;
  return augmentedSnapshot();
}

function setSpatialDefinition(raw=null){
  if(raw&&typeof raw==='object'&&raw.beginSpatialFootprint===true)return activateFootprint(raw);
  if(raw&&typeof raw==='object'&&raw.spatialVolumeDepth===true){
    zMinTier=Math.max(0,Math.trunc(Number(raw.minTier)||0));zMaxTier=Math.max(0,Math.trunc(Number(raw.maxTier)||0));
    referenceTier=Math.max(0,Math.trunc(Number(raw.referenceTier)||referenceTier));referenceLayer=Math.max(0,Math.trunc(Number(raw.referenceLayer)||referenceLayer));
    zLayersPerTier=clamp(Math.trunc(Number(raw.layersPerTier)||10),1,100);phase='ready';
    enforceSixtyDegreeView();
    announce(zMinTier===zMaxTier?`Z Tier ${zMinTier} selected. Save the volume.`:`Z Tiers ${Math.min(zMinTier,zMaxTier)} through ${Math.max(zMinTier,zMaxTier)} selected. Save the volume.`);
    return true;
  }
  return baseApi?.setSpatialDefinition?.(raw);
}

function finishSpatialSelection(){
  const result=phase==='ready'&&footprintSnapshot?true:(baseApi?.finishSpatialSelection?.(true)??false);
  if(phase==='ready')baseApi?.finishSpatialSelection?.(false);
  stopDepthPerspective(true);
  active=false;stopOverlayObserver();restoreParentPresentation();swipeStart=null;
  phase='idle';footprintSnapshot=null;zMinTier=zMaxTier=null;
  return result;
}

function cancelSpatialSelection(){
  const result=baseApi?.cancelSpatialSelection?.()??false;
  stopDepthPerspective(true);clearEffectiveMask();active=false;stopOverlayObserver();restoreParentPresentation();swipeStart=null;
  phase='idle';footprintSnapshot=null;zMinTier=zMaxTier=null;
  return result;
}

window.ShaelvienPrototype=Object.freeze({
  ...baseApi,
  beginSpatialSelection,
  getSpatialSelection,
  setSpatialDefinition,
  finishSpatialSelection,
  cancelSpatialSelection,
  toggleSpatialSelectionAutoFill:toggleAutoFill,
  cycleSpatialSelectionBorderColor:cycleBorder,
  getSpatialSelectionOptions:()=>({active,phase,autoFill,borderColor:palette().key,borderLabel:palette().label,mode:optionMode,zMinTier,zMaxTier})
});

window.addEventListener('pagehide',()=>{stopDepthPerspective(false);stopOverlayObserver();stopParentObserver()},{once:true});
})();
