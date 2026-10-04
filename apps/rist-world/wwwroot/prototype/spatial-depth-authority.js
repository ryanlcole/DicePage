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
  // The frozen visible viewport stays identical, but the selection mesh is
  // deliberately coarse enough for touch: 10×10 rather than 30×30 makes
  // each hex about three times wider/taller over the same map window.
  const options={...raw,gridShape:'hex',columns:10,rows:10};
  const started=baseApi?.beginSpatialSelection?.(options);
  if(!started)return started;

  const snapshot=baseApi?.getSpatialSelection?.()||{};
  const layers=Array.isArray(snapshot.visibleLayerOffsets)?snapshot.visibleLayerOffsets:[];
  mirrorDepth({
    tier:Math.max(0,Math.trunc(Number(snapshot.tierIndex)||0)),
    layer:layers.length===1?Math.max(0,Math.trunc(Number(layers[0])||0)):0
  });
  active=true;

  // Lifecycle only. The parent UniversalInterface owns the semantic
  // Tier -> Layer -> Save controls, validates deed height, and pushes the
  // authoritative depth back through setExternalDepth(). The iframe mirrors
  // that value exactly; it never edits parent controls or parent state.
  post('spatial-depth-control-begin');
  return started;
}

function setExternalDepth(raw={}){
  const next=mirrorDepth(raw);
  const payload={...raw,tier:next.tier,layer:next.layer};
  const result=applyBaseDepth(payload);
  // Selection startup installs the frozen-map wrappers immediately after the
  // first render. Reassert the same parent-owned depth after those frames so
  // the initial picture cannot remain on a stale top parallax tier until the
  // user moves the Tier control.
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

function cleanup(){
  cancelDepthSettlement();
  depthSyncSerial++;
  if(!active)return;
  active=false;
  post('spatial-depth-control-end');
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
  setExternalDepth,
  getSpatialSelection,
  finishSpatialSelection,
  cancelSpatialSelection
});

window.addEventListener('pagehide',()=>{
  cancelDepthSettlement();
  depthSyncSerial++;
  active=false;
},{once:true});
})();
