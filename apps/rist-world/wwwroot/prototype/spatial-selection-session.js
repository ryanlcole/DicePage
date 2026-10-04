(() => {
'use strict';

const query=new URLSearchParams(location.search);
if(window.parent===window||query.get('live-worldbuilder')!=='1'||String(query.get('mode')||'worldbuilder').toLowerCase()==='regiondefiner')return;

const host=window.parent;
const baseApi=window.ShaelvienPrototype;
if(!baseApi)return;

let frozenWindow=null;
let cameraVisual=null;
let cameraObserver=null;
let restoringCamera=false;

const clamp=(value,min,max)=>Math.min(max,Math.max(min,value));

function worldNode(){return document.getElementById('world')}
function stageNode(){return document.getElementById('stage')}

function freezeWindow(snapshot,raw={}){
  if(!snapshot||typeof snapshot!=='object')return null;
  const requestedKind=String(raw.kind||snapshot.kind||'REGION').toUpperCase();
  const rawLayers=Array.isArray(snapshot.visibleLayerOffsets)?snapshot.visibleLayerOffsets:[];
  return{
    kind:requestedKind==='INSTANCE'?'INSTANCE':requestedKind==='LOCAL'?'LOCAL':'REGION',
    scope:String(snapshot.scope||'WORLD').toUpperCase(),
    zoomRatio:Math.max(1,Number(snapshot.zoomRatio)||1),
    viewAngle:Math.max(0,Number(snapshot.viewAngle)||0),
    viewMinX:clamp(Number(snapshot.viewMinX)||0,0,1),
    viewMinY:clamp(Number(snapshot.viewMinY)||0,0,1),
    viewMaxX:clamp(Number(snapshot.viewMaxX)||1,0,1),
    viewMaxY:clamp(Number(snapshot.viewMaxY)||1,0,1),
    tierIndex:Math.max(0,Math.trunc(Number(snapshot.tierIndex)||0)),
    visibleTierIndices:Array.isArray(snapshot.visibleTierIndices)?[...snapshot.visibleTierIndices]:[],
    visibleLayerOffsets:[...rawLayers],
    parentSpatialNodeId:String(snapshot.parentSpatialNodeId||''),
    spatialPath:String(snapshot.spatialPath||'')
  };
}

function captureCameraVisual(){
  const world=worldNode(),stage=stageNode();
  if(!world||!stage)return null;
  return{
    transform:world.style.transform,
    transformOrigin:world.style.transformOrigin,
    width:world.style.width,
    height:world.style.height,
    scrollLeft:stage.scrollLeft,
    scrollTop:stage.scrollTop
  };
}

function restoreCameraVisual(){
  const world=worldNode(),stage=stageNode(),camera=cameraVisual;
  if(!world||!stage||!camera||restoringCamera)return;
  restoringCamera=true;
  try{
    if(world.style.transform!==camera.transform)world.style.transform=camera.transform;
    if(world.style.transformOrigin!==camera.transformOrigin)world.style.transformOrigin=camera.transformOrigin;
    if(world.style.width!==camera.width)world.style.width=camera.width;
    if(world.style.height!==camera.height)world.style.height=camera.height;
    if(stage.scrollLeft!==camera.scrollLeft)stage.scrollLeft=camera.scrollLeft;
    if(stage.scrollTop!==camera.scrollTop)stage.scrollTop=camera.scrollTop;
  }finally{
    restoringCamera=false;
  }
}

function startCameraVisualLock(){
  stopCameraVisualLock();
  const world=worldNode();
  if(!world||!cameraVisual)return;
  restoreCameraVisual();
  cameraObserver=new MutationObserver(()=>{
    if(frozenWindow)restoreCameraVisual();
  });
  cameraObserver.observe(world,{attributes:true,attributeFilter:['style']});
}

function stopCameraVisualLock(){
  cameraObserver?.disconnect();
  cameraObserver=null;
}

function ensureParentFocusStyle(){
  const doc=host.document;
  if(!doc||doc.getElementById('rist-spatial-map-edit-style'))return;
  const style=doc.createElement('style');
  style.id='rist-spatial-map-edit-style';
  style.textContent=`
.universal-shell.spatial-map-selecting .viewer-compass,
.universal-shell.spatial-map-selecting .viewer-legend,
.universal-shell.spatial-map-selecting .asset-context-pip,
.universal-shell.spatial-map-selecting .viewer-reticle{
  opacity:0!important;
  visibility:hidden!important;
  pointer-events:none!important;
}
.universal-shell.spatial-map-selecting .depth-pip{
  opacity:1!important;
  visibility:visible!important;
  pointer-events:none!important;
}
`;
  doc.head?.appendChild(style);
}

function setParentEditFocus(active){
  ensureParentFocusStyle();
  const shell=host.document?.querySelector('.universal-shell');
  shell?.classList.toggle('spatial-map-selecting',!!active);
}

function beginSpatialSelection(raw={}){
  // Freeze the exact world window BEFORE the canonical selector changes any
  // viewer/grid state. The camera is a lens; Select Area must not reframe it.
  const preSelection=baseApi?.getSpatialSelection?.();
  const preCamera=captureCameraVisual();
  const preWindow=freezeWindow(preSelection,raw);
  const started=baseApi?.beginSpatialSelection?.(raw);
  if(!started)return started;

  frozenWindow=preWindow;
  cameraVisual=preCamera;
  setParentEditFocus(true);
  startCameraVisualLock();
  requestAnimationFrame(restoreCameraVisual);
  return started;
}

function getSpatialSelection(){
  const snapshot=baseApi?.getSpatialSelection?.();
  if(!snapshot||!frozenWindow)return snapshot;
  return{
    ...snapshot,
    kind:frozenWindow.kind,
    scope:frozenWindow.scope,
    zoomRatio:frozenWindow.zoomRatio,
    viewAngle:frozenWindow.viewAngle,
    viewMinX:frozenWindow.viewMinX,
    viewMinY:frozenWindow.viewMinY,
    viewMaxX:frozenWindow.viewMaxX,
    viewMaxY:frozenWindow.viewMaxY,
    tierIndex:frozenWindow.tierIndex,
    visibleTierIndices:[...frozenWindow.visibleTierIndices],
    visibleLayerOffsets:[...frozenWindow.visibleLayerOffsets],
    parentSpatialNodeId:frozenWindow.parentSpatialNodeId,
    spatialPath:frozenWindow.spatialPath
  };
}

function releaseSelectionSession(){
  stopCameraVisualLock();
  setParentEditFocus(false);
  frozenWindow=null;
  cameraVisual=null;
}

function finishSpatialSelection(focus=true){
  const result=baseApi?.finishSpatialSelection?.(focus);
  releaseSelectionSession();
  return result;
}

function cancelSpatialSelection(){
  const result=baseApi?.cancelSpatialSelection?.();
  releaseSelectionSession();
  return result;
}

window.ShaelvienPrototype=Object.freeze({
  ...baseApi,
  beginSpatialSelection,
  getSpatialSelection,
  finishSpatialSelection,
  cancelSpatialSelection
});

window.addEventListener('pagehide',releaseSelectionSession,{once:true});
})();
