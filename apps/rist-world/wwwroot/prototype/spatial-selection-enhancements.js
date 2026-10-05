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
let autoFill=true;
let borderIndex=0;
let optionMode='autofill';
let overlayObserver=null;
let parentObserver=null;
let decorating=false;
let decorateQueued=false;
let parentOriginal=null;
let swipeStart=null;
let suppressClickUntil=0;
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

function postSelectionCount(snapshot){
  if(!active||!snapshot)return;
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
  const columns=Math.max(1,Math.trunc(Number(snapshot?.columns)||10));
  const rows=Math.max(1,Math.trunc(Number(snapshot?.rows)||10));
  const selected=new Set((Array.isArray(snapshot?.selectedCells)?snapshot.selectedCells:[])
    .map(value=>Math.trunc(Number(value)))
    .filter(value=>Number.isInteger(value)&&value>=0&&value<columns*rows));
  if(!autoFill||!selected.size)return selected;

  const outside=new Set();
  const queue=[];
  const enqueue=cell=>{
    if(selected.has(cell)||outside.has(cell))return;
    outside.add(cell);queue.push(cell);
  };

  for(let column=0;column<columns;column++){
    enqueue(column);
    enqueue((rows-1)*columns+column);
  }
  for(let row=0;row<rows;row++){
    enqueue(row*columns);
    enqueue(row*columns+(columns-1));
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
  const columns=Math.max(1,Math.trunc(Number(snapshot.columns)||10));
  const rows=Math.max(1,Math.trunc(Number(snapshot.rows)||10));
  const isHex=String(snapshot.gridShape||'hex').toLowerCase()!=='square';
  const viewWidth=isHex?columns+.5:columns;
  let minX=1,minY=1,maxX=0,maxY=0;
  for(const cell of cells){
    const row=cellRow(cell,columns),column=cellColumn(cell,columns),offset=isHex&&(row&1)?0.5:0;
    minX=Math.min(minX,(column+offset)/viewWidth);
    maxX=Math.max(maxX,(column+offset+1)/viewWidth);
    minY=Math.min(minY,row/rows);
    maxY=Math.max(maxY,(row+1)/rows);
  }
  return{minX:clamp(minX,0,1),minY:clamp(minY,0,1),maxX:clamp(maxX,0,1),maxY:clamp(maxY,0,1)};
}

function canonicalCells(snapshot,cells){
  const columns=Math.max(1,Math.trunc(Number(snapshot.columns)||10));
  const rows=Math.max(1,Math.trunc(Number(snapshot.rows)||10));
  const isHex=String(snapshot.gridShape||'hex').toLowerCase()!=='square';
  const viewWidth=isHex?columns+.5:columns;
  const minX=clamp(Number(snapshot.viewMinX)||0,0,1),minY=clamp(Number(snapshot.viewMinY)||0,0,1);
  const maxX=clamp(Number(snapshot.viewMaxX)||1,minX,1),maxY=clamp(Number(snapshot.viewMaxY)||1,minY,1);
  const result=new Set();
  for(const cell of cells){
    const row=cellRow(cell,columns),column=cellColumn(cell,columns),offset=isHex&&(row&1)?0.5:0;
    const lx=(column+offset+.5)/viewWidth,ly=(row+.5)/rows;
    const x=minX+(lx*(maxX-minX)),y=minY+(ly*(maxY-minY));
    const cx=clamp(Math.floor(x*300),0,299),cy=clamp(Math.floor(y*300),0,299);
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
  const columns=Math.max(1,Math.trunc(Number(snapshot.columns)||10));
  const rows=Math.max(1,Math.trunc(Number(snapshot.rows)||10));
  const isHex=String(snapshot.gridShape||'hex').toLowerCase()!=='square';
  const viewWidth=isHex?columns+.5:columns;
  const cells=filledSelection(snapshot),p=palette();
  const figures=[];
  for(const cell of [...cells].sort((a,b)=>a-b)){
    const row=cellRow(cell,columns),column=cellColumn(cell,columns);
    if(isHex)figures.push(`<polygon points="${cellPolygon(cell,columns)}" fill="rgba(69,178,221,.27)" stroke="rgba(69,178,221,.24)" stroke-width=".08"/>`);
    else figures.push(`<rect x="${column}" y="${row}" width="1" height="1" fill="rgba(69,178,221,.27)" stroke="rgba(69,178,221,.24)" stroke-width=".05"/>`);
  }
  const focus=focusPoints&&isHex
    ?`<polygon points="${focusPoints}" fill="rgba(255,255,255,.05)" stroke="${p.light}" stroke-width=".07" vector-effect="non-scaling-stroke"/>`
    :'';
  return `<svg viewBox="0 0 ${viewWidth} ${rows}" preserveAspectRatio="none" aria-hidden="true">
    <defs>
      <filter id="spatialMetalBorder" x="-12%" y="-12%" width="124%" height="124%" color-interpolation-filters="sRGB">
        <feMorphology in="SourceAlpha" operator="dilate" radius=".11" result="outerDilate"/>
        <feComposite in="outerDilate" in2="SourceAlpha" operator="out" result="outerRing"/>
        <feFlood flood-color="${p.dark}" result="outerColor"/>
        <feComposite in="outerColor" in2="outerRing" operator="in" result="outerStroke"/>
        <feMorphology in="SourceAlpha" operator="dilate" radius=".07" result="midDilate"/>
        <feComposite in="midDilate" in2="SourceAlpha" operator="out" result="midRing"/>
        <feFlood flood-color="${p.base}" result="midColor"/>
        <feComposite in="midColor" in2="midRing" operator="in" result="midStroke"/>
        <feMorphology in="SourceAlpha" operator="dilate" radius=".028" result="shineDilate"/>
        <feComposite in="shineDilate" in2="SourceAlpha" operator="out" result="shineRing"/>
        <feFlood flood-color="${p.light}" result="shineColor"/>
        <feComposite in="shineColor" in2="shineRing" operator="in" result="shineStroke"/>
        <feMerge><feMergeNode in="outerStroke"/><feMergeNode in="midStroke"/><feMergeNode in="shineStroke"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
    </defs>
    <g filter="url(#spatialMetalBorder)">${figures.join('')}</g>${focus}
  </svg>`;
}

function scheduleDecorate(){
  if(!active||decorateQueued)return;
  decorateQueued=true;
  requestAnimationFrame(()=>{decorateQueued=false;decorateOverlay()});
}

function decorateOverlay(){
  if(!active||decorating)return;
  const overlay=document.querySelector('.spatial-selection-grid.active');
  const snapshot=rawSnapshot();
  if(!overlay||!snapshot)return;
  const currentSvg=overlay.querySelector('svg');
  const focusPoints=currentSvg?.querySelector('.focus')?.getAttribute('points')||'';
  decorating=true;
  try{
    const effective=augmentedSnapshot(snapshot);
    overlay.innerHTML=renderEnhancedSvg(snapshot,focusPoints);
    overlay.dataset.autoFill=autoFill?'true':'false';
    overlay.dataset.borderColor=palette().key;
    overlay.setAttribute('aria-label',`${effective.selectedCells.length} ${snapshot.gridShape||'hex'} cells selected. Autofill ${autoFill?'on':'off'}. Border ${palette().label}.`);
    postSelectionCount(effective);
  }finally{decorating=false}
}

function startOverlayObserver(){
  stopOverlayObserver();
  const overlay=document.querySelector('.spatial-selection-grid.active');
  if(!overlay)return;
  overlayObserver=new MutationObserver(()=>{
    if(active&&!decorating)scheduleDecorate();
  });
  overlayObserver.observe(overlay,{childList:true,subtree:true});
  scheduleDecorate();
}

function stopOverlayObserver(){
  overlayObserver?.disconnect();
  overlayObserver=null;
}

function parentNodes(){
  try{
    const doc=window.parent.document;
    const button=doc.querySelector('.control-display-right');
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
    slider.addEventListener('pointerdown',event=>{
      if(!active)return;
      swipeStart={id:event.pointerId,x:event.clientX,y:event.clientY};
    },true);
    slider.addEventListener('pointerup',event=>{
      if(!active||!swipeStart||swipeStart.id!==event.pointerId)return;
      const dx=event.clientX-swipeStart.x,dy=event.clientY-swipeStart.y;
      swipeStart=null;
      if(Math.abs(dx)<30||Math.abs(dx)<Math.abs(dy)*1.2)return;
      event.preventDefault();event.stopImmediatePropagation();
      suppressClickUntil=performance.now()+450;
      optionMode=optionMode==='autofill'?'border':'autofill';
      applyParentPresentation();
      announce(optionMode==='autofill'?`Autofill ${autoFill?'on':'off'}. Touch the right display to toggle it.`:`Border ${palette().label}. Touch the right display to change color.`);
    },true);
    slider.addEventListener('pointercancel',()=>{swipeStart=null},true);
  }
}

function rememberParentPresentation(button){
  if(parentOriginal||!button)return;
  parentOriginal={
    button,
    eyebrow:button.querySelector('small')?.textContent||'',
    value:button.querySelector('strong')?.textContent||'',
    prompt:button.querySelector('span')?.textContent||'',
    aria:button.getAttribute('aria-label')||''
  };
}

function applyParentPresentation(){
  if(!active)return;
  const {button,shell}=parentNodes();
  if(!button)return;
  rememberParentPresentation(button);
  bindParentControls();
  shell?.classList.add('spatial-selection-options-active');
  const eyebrow=button.querySelector('small'),value=button.querySelector('strong'),prompt=button.querySelector('span');
  if(eyebrow&&eyebrow.textContent!=='SELECTION OPTIONS')eyebrow.textContent='SELECTION OPTIONS';
  if(optionMode==='autofill'){
    const text=`AUTOFILL · ${autoFill?'ON':'OFF'}`;
    if(value&&value.textContent!==text)value.textContent=text;
    if(prompt&&prompt.textContent!=='SWIPE ↔ BORDER · TOUCH TOGGLE')prompt.textContent='SWIPE ↔ BORDER · TOUCH TOGGLE';
    button.setAttribute('aria-label',`Selection options. Autofill ${autoFill?'on':'off'}. Touch to toggle. Swipe horizontally for border color.`);
  }else{
    const text=`BORDER · ${palette().label}`;
    if(value&&value.textContent!==text)value.textContent=text;
    if(prompt&&prompt.textContent!=='SWIPE ↔ AUTOFILL · TOUCH COLOR')prompt.textContent='SWIPE ↔ AUTOFILL · TOUCH COLOR';
    button.setAttribute('aria-label',`Selection options. Border ${palette().label}. Touch to change color. Swipe horizontally for autofill.`);
  }
}

function startParentObserver(){
  stopParentObserver();
  const {doc}=parentNodes();
  if(!doc?.body)return;
  parentObserver=new MutationObserver(()=>{
    if(active)requestAnimationFrame(applyParentPresentation);
  });
  parentObserver.observe(doc.body,{childList:true,subtree:true,characterData:true});
  applyParentPresentation();
}

function stopParentObserver(){
  parentObserver?.disconnect();
  parentObserver=null;
}

function restoreParentPresentation(){
  stopParentObserver();
  try{
    const {shell}=parentNodes();
    shell?.classList.remove('spatial-selection-options-active');
    if(parentOriginal?.button?.isConnected){
      const button=parentOriginal.button,eyebrow=button.querySelector('small'),value=button.querySelector('strong'),prompt=button.querySelector('span');
      if(eyebrow)eyebrow.textContent=parentOriginal.eyebrow;
      if(value)value.textContent=parentOriginal.value;
      if(prompt)prompt.textContent=parentOriginal.prompt;
      if(parentOriginal.aria)button.setAttribute('aria-label',parentOriginal.aria);
    }
  }catch{}
  parentOriginal=null;
}

function toggleAutoFill(){
  autoFill=!autoFill;
  scheduleDecorate();
  applyParentPresentation();
  announce(`Autofill ${autoFill?'on':'off'}. ${autoFill?'Closed selection loops now include every cell inside them.':'Only cells you explicitly select will be saved.'}`);
  return autoFill;
}

function cycleBorder(direction=1){
  const step=Math.sign(Number(direction)||1)||1;
  borderIndex=(borderIndex+step+BORDER_PALETTES.length)%BORDER_PALETTES.length;
  scheduleDecorate();
  applyParentPresentation();
  announce(`Selection border ${palette().label}.`);
  return palette().key;
}

function applyEffectiveMask(snapshot){
  if(!snapshot?.selectedCells?.length)return;
  const columns=Math.max(1,Math.trunc(Number(snapshot.columns)||10)),rows=Math.max(1,Math.trunc(Number(snapshot.rows)||10));
  const isHex=String(snapshot.gridShape||'hex').toLowerCase()!=='square',viewWidth=isHex?columns+.5:columns;
  const minX=clamp(Number(snapshot.viewMinX)||0,0,1),minY=clamp(Number(snapshot.viewMinY)||0,0,1);
  const maxX=clamp(Number(snapshot.viewMaxX)||1,minX,1),maxY=clamp(Number(snapshot.viewMaxY)||1,minY,1);
  const mapPoint=(ux,uy)=>({x:(minX+(clamp(ux/viewWidth,0,1)*(maxX-minX)))*1000,y:(minY+(clamp(uy/rows,0,1)*(maxY-minY)))*1000});
  const figures=[];
  for(const cell of snapshot.selectedCells){
    const row=cellRow(cell,columns),column=cellColumn(cell,columns);
    if(isHex){
      const offset=(row&1)?0.5:0,x0=column+offset,y0=row;
      const local=[[x0+.25,y0],[x0+.75,y0],[x0+1,y0+.5],[x0+.75,y0+1],[x0+.25,y0+1],[x0,y0+.5]];
      figures.push(`<polygon points="${local.map(([px,py])=>{const p=mapPoint(px,py);return `${p.x},${p.y}`}).join(' ')}" fill="white"/>`);
    }else{
      const a=mapPoint(column,row),b=mapPoint(column+1,row+1);
      figures.push(`<rect x="${a.x}" y="${a.y}" width="${Math.max(.1,b.x-a.x)}" height="${Math.max(.1,b.y-a.y)}" fill="white"/>`);
    }
  }
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" preserveAspectRatio="none">${figures.join('')}</svg>`;
  const world=document.getElementById('world');
  if(!world)return;
  const url=`url("data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}")`;
  world.style.maskImage=url;world.style.webkitMaskImage=url;world.style.maskSize='100% 100%';world.style.webkitMaskSize='100% 100%';world.style.maskRepeat='no-repeat';world.style.webkitMaskRepeat='no-repeat';
}

function beginSpatialSelection(raw={}){
  // Select Area means the user is now authoring depth. Force the real rendered
  // world to Tier 0 / Layer 0 before the frozen selection session captures it.
  // The previous all-parallax representation must never masquerade as Tier 0.
  try{baseApi?.setExternalDepth?.({...raw,tier:0,layer:0})}catch{}
  const started=baseApi?.beginSpatialSelection?.(raw);
  if(!started)return started;
  active=true;
  autoFill=true;
  borderIndex=0;
  optionMode='autofill';
  requestAnimationFrame(()=>{
    startOverlayObserver();
    startParentObserver();
    const snapshot=augmentedSnapshot();
    if(snapshot)postSelectionCount(snapshot);
  });
  return started;
}

function getSpatialSelection(){return augmentedSnapshot()}

function finishSpatialSelection(focus=true){
  const snapshot=augmentedSnapshot();
  const result=baseApi?.finishSpatialSelection?.(focus);
  if(result!==false&&focus&&snapshot?.selectedCells?.length)requestAnimationFrame(()=>applyEffectiveMask(snapshot));
  cleanup();
  return result;
}

function cancelSpatialSelection(){
  const result=baseApi?.cancelSpatialSelection?.();
  cleanup();
  return result;
}

function cleanup(){
  active=false;
  stopOverlayObserver();
  restoreParentPresentation();
  swipeStart=null;
}

window.ShaelvienPrototype=Object.freeze({
  ...baseApi,
  beginSpatialSelection,
  getSpatialSelection,
  finishSpatialSelection,
  cancelSpatialSelection,
  toggleSpatialSelectionAutoFill:toggleAutoFill,
  cycleSpatialSelectionBorderColor:cycleBorder,
  getSpatialSelectionOptions:()=>({active,autoFill,borderColor:palette().key,borderLabel:palette().label,mode:optionMode})
});

window.addEventListener('pagehide',cleanup,{once:true});
})();
