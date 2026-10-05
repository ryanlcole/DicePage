(() => {
'use strict';

const query=new URLSearchParams(location.search);
if(window.parent===window||query.get('live-worldbuilder')!=='1'||String(query.get('mode')||'worldbuilder').toLowerCase()==='regiondefiner')return;
if(String(query.get('access')||'view').toLowerCase()!=='edit')return;

const host=window.parent;
const baseApi=window.ShaelvienPrototype;
if(!baseApi)return;

const context={
  worldId:String(query.get('worldId')||''),
  deedId:String(query.get('deedId')||''),
  deedRegionId:String(query.get('deedRegionId')||''),
  deedZoneId:String(query.get('deedZone')||''),
  seed:String(query.get('seed')||'')
};

let active=false;
let footprintEnabled=false;
let depth={tier:0,layer:0};
let settleFrame=0;
let settleTimer=0;
let depthSyncSerial=0;

function post(type,extra={}){
  try{host.postMessage({source:'shaelvien-worldbuilder',type,...context,...extra},location.origin)}catch{}
}

function mirrorDepth(raw={}){
  depth={
    tier:Math.max(0,Math.trunc(Number(raw.tier)||0)),
    layer:Math.max(0,Math.trunc(Number(raw.layer)||0))
  };
  return depth;
}

function selectionOverlay(){return document.querySelector('.spatial-selection-grid')}

function setFootprintOverlayEnabled(enabled){
  footprintEnabled=!!enabled;
  const overlay=selectionOverlay();
  if(!overlay)return;
  overlay.style.visibility=footprintEnabled?'':'hidden';
  overlay.style.pointerEvents=footprintEnabled?'':'none';
  overlay.setAttribute('aria-hidden',footprintEnabled?'false':'true');
  if(footprintEnabled){
    try{overlay.focus({preventScroll:true})}catch{try{overlay.focus()}catch{}}
  }
}

function cancelDepthSettlement(){
  if(settleFrame)cancelAnimationFrame(settleFrame);
  if(settleTimer)clearTimeout(settleTimer);
  settleFrame=0;
  settleTimer=0;
}

function applyBaseDepth(payload){
  return baseApi?.setExternalDepth?.(payload);
}

function settleDepth(payload){
  cancelDepthSettlement();
  const serial=++depthSyncSerial;
  const apply=()=>{
    if(!active||serial!==depthSyncSerial)return false;
    return applyBaseDepth(payload);
  };

  settleFrame=requestAnimationFrame(()=>{
    apply();
    settleFrame=requestAnimationFrame(()=>{
      settleFrame=0;
      apply();
    });
  });
  settleTimer=setTimeout(()=>{
    settleTimer=0;
    apply();
  },120);
}

function beginSpatialSelection(raw={}){
  // Select Area starts by choosing the reference Tier/Layer. The 30×30 X/Y
  // mesh exists underneath so the camera can freeze immediately, but it is
  // intentionally hidden and non-interactive until the parent reaches the
  // footprint-selection step.
  const options={...raw,gridShape:'hex',columns:30,rows:30};
  const started=baseApi?.beginSpatialSelection?.(options);
  if(!started)return started;

  const snapshot=baseApi?.getSpatialSelection?.()||{};
  const layers=Array.isArray(snapshot.visibleLayerOffsets)?snapshot.visibleLayerOffsets:[];
  mirrorDepth({
    tier:Math.max(0,Math.trunc(Number(snapshot.tierIndex)||0)),
    layer:layers.length===1?Math.max(0,Math.trunc(Number(layers[0])||0)):0
  });
  active=true;
  setFootprintOverlayEnabled(false);

  // The parent owns Tier/Layer semantics. At this point it is selecting the
  // source slice for the footprint; no X/Y hex can be selected yet.
  post('spatial-depth-control-begin',{phase:'reference'});
  return started;
}

function activateSpatialFootprint(){
  if(!active)return false;
  setFootprintOverlayEnabled(true);
  return true;
}

function finishSpatialFootprint(focus=true){
  if(!active||!footprintEnabled)return false;
  const result=baseApi?.finishSpatialSelection?.(focus);
  footprintEnabled=false;
  return result;
}

function beginSpatialVolumeDepth(){
  if(!active)active=true;
  footprintEnabled=false;
  post('spatial-depth-control-begin',{phase:'volume'});
  return true;
}

function setExternalDepth(raw={}){
  const next=mirrorDepth(raw);
  const payload={...raw,tier:next.tier,layer:next.layer};
  const result=applyBaseDepth(payload);
  if(active)settleDepth(payload);
  return result;
}

function applyAuthoritySync(raw={}){
  if(!active)return false;
  const snapshot=baseApi?.getSpatialSelection?.()||{};
  return setExternalDepth({
    tier:raw.tier,
    layer:raw.layer,
    scope:String(snapshot.scope||'WORLD'),
    spatialNodeId:String(snapshot.parentSpatialNodeId||''),
    spatialPath:String(snapshot.spatialPath||'')
  });
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

function moveSpatialSelectionCursor(columnDelta,rowDelta){
  if(!active||!footprintEnabled)return false;
  return baseApi?.moveSpatialSelectionCursor?.(columnDelta,rowDelta)??false;
}

function toggleSpatialSelectionCursor(){
  if(!active||!footprintEnabled)return false;
  return baseApi?.toggleSpatialSelectionCursor?.()??false;
}

function cleanup(){
  cancelDepthSettlement();
  depthSyncSerial++;
  const wasActive=active;
  active=false;
  footprintEnabled=false;
  const overlay=selectionOverlay();
  if(overlay){overlay.style.visibility='';overlay.style.pointerEvents='';overlay.removeAttribute('aria-hidden')}
  if(wasActive)post('spatial-depth-control-end');
}

function finishSpatialSelection(focus=true){
  const hadActive=active;
  if(footprintEnabled)baseApi?.finishSpatialSelection?.(focus);
  cleanup();
  return hadActive;
}

function cancelSpatialSelection(){
  const hadActive=active;
  if(footprintEnabled)baseApi?.cancelSpatialSelection?.();
  else{
    // The underlying selection session may still be camera-frozen even while
    // its mesh is hidden during reference-depth selection.
    baseApi?.cancelSpatialSelection?.();
  }
  cleanup();
  return hadActive;
}

window.addEventListener('message',event=>{
  if(event.origin!==location.origin||event.source!==host)return;
  const data=event.data;
  if(!data||data.source!=='shaelvien-worldbuilder-host'||data.type!=='spatial-depth-authority-sync')return;
  const result=data.result&&typeof data.result==='object'?data.result:{};
  if(result.canEdit===false)return;
  applyAuthoritySync(result);
},false);

window.ShaelvienPrototype=Object.freeze({
  ...baseApi,
  beginSpatialSelection,
  activateSpatialFootprint,
  finishSpatialFootprint,
  beginSpatialVolumeDepth,
  setExternalDepth,
  getSpatialSelection,
  moveSpatialSelectionCursor,
  toggleSpatialSelectionCursor,
  finishSpatialSelection,
  cancelSpatialSelection
});

window.addEventListener('pagehide',()=>{
  cancelDepthSettlement();
  depthSyncSerial++;
  active=false;
  footprintEnabled=false;
},{once:true});
})();
