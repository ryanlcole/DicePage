(() => {
'use strict';

const query=new URLSearchParams(location.search);
if(window.parent===window||query.get('live-worldbuilder')!=='1'||String(query.get('mode')||'worldbuilder').toLowerCase()==='regiondefiner')return;
if(String(query.get('access')||'view').toLowerCase()!=='edit')return;

const host=window.parent;
const baseApi=window.ShaelvienPrototype;
if(!baseApi)return;

const LAYERS_PER_TIER=10;
const context={
  worldId:String(query.get('worldId')||''),
  deedId:String(query.get('deedId')||''),
  deedRegionId:String(query.get('deedRegionId')||''),
  deedZoneId:String(query.get('deedZone')||''),
  seed:String(query.get('seed')||'')
};

let maxHeight=Math.max(1,Math.trunc(Number(query.get('maxHeight'))||1));
let active=false;
let mode='tier';
let depth={tier:0,layer:0};
let parentObserver=null;
let overlayObserver=null;
let pointerStart=null;
let suppressNextClick=false;
let authorityRequestId='';

const clamp=(value,min,max)=>Math.min(max,Math.max(min,value));
const maxTierIndex=()=>Math.max(0,Math.floor((maxHeight-1)/LAYERS_PER_TIER));
const maxLayerForTier=tier=>clamp(maxHeight-(clamp(tier,0,maxTierIndex())*LAYERS_PER_TIER)-1,0,LAYERS_PER_TIER-1);

function selection(){return baseApi?.getSpatialSelection?.()||null}
function selectedCount(){const cells=selection()?.selectedCells;return Array.isArray(cells)?cells.length:0}
function leftButton(){return host.document?.querySelector('.control-display-left')||null}
function leftSlider(){return host.document?.querySelector('.display-slider-left')||null}
function depthPip(){return host.document?.querySelector('.depth-pip')||null}
function overlay(){return document.querySelector('.spatial-selection-grid.active')}
function live(message){const node=document.getElementById('live');if(node)node.textContent=String(message||'')}

function post(type,extra={}){
  try{host.postMessage({source:'shaelvien-worldbuilder',type,...context,...extra},location.origin)}catch{}
}

function clampDepth(){
  depth.tier=clamp(Math.trunc(Number(depth.tier)||0),0,maxTierIndex());
  depth.layer=clamp(Math.trunc(Number(depth.layer)||0),0,maxLayerForTier(depth.tier));
}

function syncDepthBox(){
  const pip=depthPip();
  if(!pip)return;
  pip.dataset.authoritativeTier=String(depth.tier);
  pip.dataset.authoritativeLayer=String(depth.layer);
  const header=pip.querySelector('header span');
  if(header&&header.textContent!==`TIER ${depth.tier} · LAYER ${depth.layer}`)header.textContent=`TIER ${depth.tier} · LAYER ${depth.layer}`;
  const footer=[...pip.querySelectorAll('footer span')];
  if(footer[0]&&footer[0].textContent!==`T${depth.tier}`)footer[0].textContent=`T${depth.tier}`;
  if(footer[1]&&footer[1].textContent!==`L${depth.layer}`)footer[1].textContent=`L${depth.layer}`;
  pip.setAttribute('aria-label',`Current deed depth Tier ${depth.tier}, Layer ${depth.layer}`);
}

function syncLeftDisplay(){
  if(!active)return;
  const button=leftButton();
  if(!button)return;
  const eyebrow=button.querySelector(':scope > small');
  const label=button.querySelector(':scope > strong');
  const prompt=button.querySelector(':scope > span');
  const count=selectedCount();

  let eyebrowText='DEPTH',labelText='',promptText='';
  if(mode==='tier'){
    labelText=`TIER ${depth.tier}`;
    promptText=maxTierIndex()>0?'SLIDE ↑↓ · TOUCH LAYER':'TIER FIXED · TOUCH LAYER';
  }else if(mode==='layer'){
    labelText=`LAYER ${depth.layer}`;
    promptText=maxLayerForTier(depth.tier)>0?'SLIDE ↑↓ · TOUCH SAVE':'LAYER FIXED · TOUCH SAVE';
  }else{
    eyebrowText='SPACE';
    labelText=count>0?`SAVE AREA · ${count}`:'SELECT HEXES';
    promptText=count>0?'TOUCH · NAME & SAVE':'TOUCH MAP HEXES';
  }

  if(eyebrow&&eyebrow.textContent!==eyebrowText)eyebrow.textContent=eyebrowText;
  if(label&&label.textContent!==labelText)label.textContent=labelText;
  if(prompt&&prompt.textContent!==promptText)prompt.textContent=promptText;
  button.setAttribute('aria-label',`Left display button: ${labelText}`);
  const slider=leftSlider();
  if(slider)slider.setAttribute('aria-label',mode==='save'?'Left display. Touch to name and save the selected area.':'Left display. Slide up or down to change deed depth, then touch to continue.');
  syncDepthBox();
}

function notifyDepth(){
  post('spatial-depth-change',{tier:depth.tier,layer:depth.layer});
}

function applyDepth({announce=true}={}){
  if(!active)return false;
  clampDepth();
  const snapshot=selection()||{};
  try{
    baseApi?.setExternalDepth?.({
      tier:depth.tier,
      layer:depth.layer,
      scope:String(snapshot.scope||'WORLD'),
      spatialNodeId:String(snapshot.parentSpatialNodeId||''),
      spatialPath:String(snapshot.spatialPath||'')
    });
  }catch{}
  notifyDepth();
  syncLeftDisplay();
  if(announce)live(`Tier ${depth.tier}, Layer ${depth.layer}. The deed X/Y selection remains locked.`);
  return true;
}

function changeDepth(delta){
  if(!active||mode==='save')return false;
  delta=Math.sign(Number(delta)||0);
  if(!delta)return false;
  if(mode==='tier'){
    depth.tier=clamp(depth.tier+delta,0,maxTierIndex());
    depth.layer=clamp(depth.layer,0,maxLayerForTier(depth.tier));
  }else{
    depth.layer=clamp(depth.layer+delta,0,maxLayerForTier(depth.tier));
  }
  return applyDepth();
}

function advanceMode(){
  if(!active)return;
  if(mode==='tier')mode='layer';
  else if(mode==='layer')mode='save';
  syncLeftDisplay();
}

function startUiObservers(){
  stopUiObservers();
  const doc=host.document;
  if(doc?.body){
    parentObserver=new MutationObserver(()=>queueMicrotask(syncLeftDisplay));
    parentObserver.observe(doc.body,{childList:true,subtree:true,characterData:true});
  }
  const mapOverlay=overlay();
  if(mapOverlay){
    overlayObserver=new MutationObserver(syncLeftDisplay);
    overlayObserver.observe(mapOverlay,{attributes:true,subtree:true,childList:true});
  }
}

function stopUiObservers(){
  parentObserver?.disconnect();
  overlayObserver?.disconnect();
  parentObserver=null;
  overlayObserver=null;
}

function requestAuthority(){
  authorityRequestId=`depth-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  post('spatial-depth-authority-request',{requestId:authorityRequestId});
}

function beginSpatialSelection(raw={}){
  const started=baseApi?.beginSpatialSelection?.(raw);
  if(!started)return started;
  const snapshot=baseApi?.getSpatialSelection?.()||{};
  const layers=Array.isArray(snapshot.visibleLayerOffsets)?snapshot.visibleLayerOffsets:[];
  depth={
    tier:Math.max(0,Math.trunc(Number(snapshot.tierIndex)||0)),
    layer:layers.length===1?Math.max(0,Math.trunc(Number(layers[0])||0)):0
  };
  clampDepth();
  active=true;
  mode='tier';
  applyDepth({announce:false});
  startUiObservers();
  syncLeftDisplay();
  requestAuthority();
  live(`Select deed hexes at Tier ${depth.tier}, Layer ${depth.layer}. Depth is controlled from the left display; no popup is used.`);
  return started;
}

function getSpatialSelection(){
  const snapshot=baseApi?.getSpatialSelection?.();
  if(!snapshot||!active)return snapshot;
  return{
    ...snapshot,
    tierIndex:depth.tier,
    visibleTierIndices:[depth.tier],
    visibleLayerOffsets:[depth.layer]
  };
}

function cleanup(){
  stopUiObservers();
  active=false;
  pointerStart=null;
  suppressNextClick=false;
}

function finishSpatialSelection(focus=true){
  const result=baseApi?.finishSpatialSelection?.(focus);
  cleanup();
  return result;
}

function cancelSpatialSelection(){
  const result=baseApi?.cancelSpatialSelection?.();
  cleanup();
  return result;
}

function isLeftTarget(target){return target instanceof Element&&!!target.closest('.control-display-left')}

host.document?.addEventListener('pointerdown',event=>{
  if(!active||!isLeftTarget(event.target))return;
  pointerStart={id:event.pointerId,y:event.clientY};
  event.stopImmediatePropagation();
},{capture:true});

host.document?.addEventListener('pointermove',event=>{
  if(!active||!pointerStart||pointerStart.id!==event.pointerId||!isLeftTarget(event.target))return;
  event.stopImmediatePropagation();
},{capture:true});

host.document?.addEventListener('pointerup',event=>{
  if(!active||!pointerStart||pointerStart.id!==event.pointerId||!isLeftTarget(event.target))return;
  const dy=event.clientY-pointerStart.y;
  pointerStart=null;
  event.stopImmediatePropagation();
  if(Math.abs(dy)>=18&&mode!=='save'){
    event.preventDefault();
    suppressNextClick=true;
    changeDepth(dy<0?1:-1);
  }
},{capture:true});

host.document?.addEventListener('click',event=>{
  if(!active||!isLeftTarget(event.target))return;
  if(suppressNextClick){
    suppressNextClick=false;
    event.preventDefault();
    event.stopImmediatePropagation();
    return;
  }
  if(mode==='save'){
    if(selectedCount()>0)return;
    event.preventDefault();
    event.stopImmediatePropagation();
    live('Select at least one map hex before saving the deed area.');
    return;
  }
  event.preventDefault();
  event.stopImmediatePropagation();
  advanceMode();
},{capture:true});

host.document?.addEventListener('wheel',event=>{
  if(!active||!isLeftTarget(event.target)||mode==='save')return;
  event.preventDefault();
  event.stopImmediatePropagation();
  changeDepth(event.deltaY<0?1:-1);
},{capture:true,passive:false});

host.document?.addEventListener('keydown',event=>{
  if(!active||!isLeftTarget(event.target))return;
  if((event.key==='ArrowUp'||event.key==='ArrowDown')&&mode!=='save'){
    event.preventDefault();
    event.stopImmediatePropagation();
    changeDepth(event.key==='ArrowUp'?1:-1);
    return;
  }
  if((event.key==='Enter'||event.key===' ')&&mode!=='save'){
    event.preventDefault();
    event.stopImmediatePropagation();
    advanceMode();
  }
},{capture:true});

window.addEventListener('message',event=>{
  if(event.origin!==location.origin||event.source!==host)return;
  const data=event.data;
  if(!data||data.source!=='shaelvien-worldbuilder-host'||data.type!=='spatial-depth-authority')return;
  if(String(data.requestId||'')!==authorityRequestId)return;
  const result=data.result&&typeof data.result==='object'?data.result:{};
  if(result.canEdit===false)return;
  const nextMax=Math.max(1,Math.trunc(Number(result.maxHeight)||maxHeight));
  maxHeight=nextMax;
  clampDepth();
  if(active)applyDepth({announce:false});
},false);

window.ShaelvienPrototype=Object.freeze({
  ...baseApi,
  beginSpatialSelection,
  getSpatialSelection,
  finishSpatialSelection,
  cancelSpatialSelection
});

window.addEventListener('pagehide',cleanup,{once:true});
})();
