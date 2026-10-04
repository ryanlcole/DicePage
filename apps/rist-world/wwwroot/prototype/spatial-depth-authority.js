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

function beginSpatialSelection(raw={}){
  const started=baseApi?.beginSpatialSelection?.(raw);
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
  return baseApi?.setExternalDepth?.(payload);
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

window.ShaelvienPrototype=Object.freeze({
  ...baseApi,
  beginSpatialSelection,
  setExternalDepth,
  getSpatialSelection,
  finishSpatialSelection,
  cancelSpatialSelection
});

window.addEventListener('pagehide',()=>{active=false},{once:true});
})();
