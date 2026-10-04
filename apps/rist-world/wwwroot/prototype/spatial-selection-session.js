(() => {
'use strict';

const query=new URLSearchParams(location.search);
if(window.parent===window||query.get('live-worldbuilder')!=='1'||String(query.get('mode')||'worldbuilder').toLowerCase()==='regiondefiner')return;

const host=window.parent;
const baseApi=window.ShaelvienPrototype;
if(!baseApi)return;

const LAYERS_PER_TIER=10;
const canAllocateDepth=String(query.get('access')||'view').toLowerCase()==='edit';
const maxHeight=Math.max(1,Math.trunc(Number(query.get('maxHeight'))||1));
const maxTierIndex=Math.max(0,Math.floor((maxHeight-1)/LAYERS_PER_TIER));

let frozenWindow=null;
let cameraVisual=null;
let cameraObserver=null;
let restoringCamera=false;
let depthPanel=null;

const clamp=(value,min,max)=>Math.min(max,Math.max(min,value));

function worldNode(){return document.getElementById('world')}
function stageNode(){return document.getElementById('stage')}
function live(message){const node=document.getElementById('live');if(node)node.textContent=String(message||'')}

function maxLayerForTier(tier){
  const remaining=maxHeight-(tier*LAYERS_PER_TIER);
  return clamp(remaining-1,0,LAYERS_PER_TIER-1);
}

function freezeWindow(snapshot,raw={}){
  if(!snapshot||typeof snapshot!=='object')return null;
  const requestedKind=String(raw.kind||snapshot.kind||'REGION').toUpperCase();
  const tierIndex=clamp(Math.max(0,Math.trunc(Number(snapshot.tierIndex)||0)),0,maxTierIndex);
  const rawLayers=Array.isArray(snapshot.visibleLayerOffsets)?snapshot.visibleLayerOffsets:[];
  const layerIndex=clamp(rawLayers.length===1?Math.trunc(Number(rawLayers[0])||0):0,0,maxLayerForTier(tierIndex));
  return{
    kind:requestedKind==='INSTANCE'?'INSTANCE':requestedKind==='LOCAL'?'LOCAL':'REGION',
    scope:String(snapshot.scope||'WORLD').toUpperCase(),
    zoomRatio:Math.max(1,Number(snapshot.zoomRatio)||1),
    viewAngle:Math.max(0,Number(snapshot.viewAngle)||0),
    viewMinX:clamp(Number(snapshot.viewMinX)||0,0,1),
    viewMinY:clamp(Number(snapshot.viewMinY)||0,0,1),
    viewMaxX:clamp(Number(snapshot.viewMaxX)||1,0,1),
    viewMaxY:clamp(Number(snapshot.viewMaxY)||1,0,1),
    tierIndex,
    layerIndex,
    visibleTierIndices:Array.isArray(snapshot.visibleTierIndices)?[...snapshot.visibleTierIndices]:[],
    visibleLayerOffsets:rawLayers,
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
.universal-shell.spatial-map-selecting .depth-pip,
.universal-shell.spatial-map-selecting .viewer-compass,
.universal-shell.spatial-map-selecting .viewer-legend,
.universal-shell.spatial-map-selecting .asset-context-pip,
.universal-shell.spatial-map-selecting .viewer-reticle{
  opacity:0!important;
  visibility:hidden!important;
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

function ensureDepthPanelStyle(){
  if(document.getElementById('spatial-selection-depth-style'))return;
  const style=document.createElement('style');
  style.id='spatial-selection-depth-style';
  style.textContent=`
.spatial-selection-depth-panel{position:absolute;z-index:24000;top:78px;left:14px;display:grid;gap:6px;width:min(188px,44vw);padding:9px;border:1px solid rgba(118,223,255,.72);border-radius:10px;background:rgba(4,14,21,.88);box-shadow:0 4px 16px rgba(0,0,0,.45);backdrop-filter:blur(5px);color:#e9f8ff;font:800 11px/1.1 system-ui,sans-serif;letter-spacing:.08em;pointer-events:auto;touch-action:manipulation}
.spatial-selection-depth-panel[hidden]{display:none!important}.spatial-selection-depth-panel>small{font-size:8px;color:#83dfff;letter-spacing:.16em}.spatial-selection-depth-row{display:grid;grid-template-columns:38px 1fr 38px;align-items:center;gap:6px}.spatial-selection-depth-row button{min-width:38px;min-height:38px;border:1px solid #4caed2;border-radius:8px;background:#0c2a38;color:#e9f8ff;font:900 21px/1 system-ui}.spatial-selection-depth-row button:disabled{opacity:.3}.spatial-selection-depth-row strong{text-align:center;font-size:13px;color:#fff0b4;white-space:nowrap}.spatial-selection-depth-panel footer{display:flex;justify-content:space-between;gap:8px;color:#9bb8c3;font-size:8px;letter-spacing:.08em}.spatial-selection-depth-panel footer b{color:#fff0b4}
`;
  document.head?.appendChild(style);
}

function renderDepthPanel(){
  if(!depthPanel||!frozenWindow)return;
  const tier=frozenWindow.tierIndex,layer=frozenWindow.layerIndex;
  const tierLabel=depthPanel.querySelector('[data-depth-tier-label]');
  const layerLabel=depthPanel.querySelector('[data-depth-layer-label]');
  const summary=depthPanel.querySelector('[data-depth-summary]');
  if(tierLabel)tierLabel.textContent=`TIER ${tier}`;
  if(layerLabel)layerLabel.textContent=`LAYER ${layer}`;
  if(summary)summary.textContent=`Z${(tier*LAYERS_PER_TIER)+layer}`;
  const tierDown=depthPanel.querySelector('[data-depth-tier="-1"]');
  const tierUp=depthPanel.querySelector('[data-depth-tier="1"]');
  const layerDown=depthPanel.querySelector('[data-depth-layer="-1"]');
  const layerUp=depthPanel.querySelector('[data-depth-layer="1"]');
  if(tierDown)tierDown.disabled=tier<=0;
  if(tierUp)tierUp.disabled=tier>=maxTierIndex;
  if(layerDown)layerDown.disabled=layer<=0;
  if(layerUp)layerUp.disabled=layer>=maxLayerForTier(tier);
}

function applySelectionDepth(tier,layer,{announce=true}={}){
  if(!frozenWindow||!canAllocateDepth)return false;
  tier=clamp(Math.trunc(Number(tier)||0),0,maxTierIndex);
  layer=clamp(Math.trunc(Number(layer)||0),0,maxLayerForTier(tier));
  frozenWindow.tierIndex=tier;
  frozenWindow.layerIndex=layer;
  frozenWindow.visibleTierIndices=[tier];
  frozenWindow.visibleLayerOffsets=[layer];
  try{
    baseApi?.setExternalDepth?.({
      tier,
      layer,
      scope:frozenWindow.scope,
      spatialNodeId:frozenWindow.parentSpatialNodeId,
      spatialPath:frozenWindow.spatialPath
    });
  }catch{}
  renderDepthPanel();
  requestAnimationFrame(restoreCameraVisual);
  if(announce)live(`GM deed depth: Tier ${tier}, Layer ${layer}. The X/Y selection and camera remain locked.`);
  return true;
}

function showDepthPanel(){
  if(!canAllocateDepth||!frozenWindow)return;
  ensureDepthPanelStyle();
  const stage=stageNode();
  if(!stage)return;
  if(!depthPanel){
    depthPanel=document.createElement('section');
    depthPanel.className='spatial-selection-depth-panel';
    depthPanel.setAttribute('aria-label','GM deed tier and layer');
    depthPanel.innerHTML=`<small>GM DEED DEPTH</small><div class="spatial-selection-depth-row"><button type="button" data-depth-tier="-1" aria-label="Previous tier">−</button><strong data-depth-tier-label>TIER 0</strong><button type="button" data-depth-tier="1" aria-label="Next tier">+</button></div><div class="spatial-selection-depth-row"><button type="button" data-depth-layer="-1" aria-label="Previous layer">−</button><strong data-depth-layer-label>LAYER 0</strong><button type="button" data-depth-layer="1" aria-label="Next layer">+</button></div><footer><span>DIRECT GM EDIT</span><b data-depth-summary>Z0</b></footer>`;
    depthPanel.addEventListener('click',event=>{
      const button=event.target instanceof Element?event.target.closest('button'):null;
      if(!button||!frozenWindow)return;
      const tierDelta=Number(button.getAttribute('data-depth-tier'))||0;
      const layerDelta=Number(button.getAttribute('data-depth-layer'))||0;
      if(tierDelta)applySelectionDepth(frozenWindow.tierIndex+tierDelta,frozenWindow.layerIndex);
      else if(layerDelta)applySelectionDepth(frozenWindow.tierIndex,frozenWindow.layerIndex+layerDelta);
    });
    stage.appendChild(depthPanel);
  }
  depthPanel.hidden=false;
  renderDepthPanel();
}

function hideDepthPanel(){
  if(depthPanel)depthPanel.hidden=true;
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

  // Only a GM/editor allocates deed depth. A requester selects X/Y and submits
  // a deed request; the GM later chooses the authoritative Tier/Layer slice.
  if(canAllocateDepth&&frozenWindow){
    applySelectionDepth(frozenWindow.tierIndex,frozenWindow.layerIndex,{announce:false});
    showDepthPanel();
  }

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
    visibleTierIndices:canAllocateDepth?[frozenWindow.tierIndex]:[...frozenWindow.visibleTierIndices],
    visibleLayerOffsets:canAllocateDepth?[frozenWindow.layerIndex]:[...frozenWindow.visibleLayerOffsets],
    parentSpatialNodeId:frozenWindow.parentSpatialNodeId,
    spatialPath:frozenWindow.spatialPath
  };
}

function releaseSelectionSession(){
  stopCameraVisualLock();
  setParentEditFocus(false);
  hideDepthPanel();
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
