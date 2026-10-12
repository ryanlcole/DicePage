(()=>{
'use strict';
const finePointer=matchMedia('(hover: hover) and (pointer: fine)');
const query=new URLSearchParams(location.search);
if(!finePointer.matches||String(query.get('mode')||'worldbuilder').toLowerCase()==='regiondefiner')return;

const stage=document.getElementById('stage');
const world=document.getElementById('world');
if(!stage||!world||!window.ShaelvienPrototype)return;

const api=window.ShaelvienPrototype;
const parentScopeOrder=['WORLD','REGION','LOCAL','INSTANCE'];
const scopeAngle={WORLD:0,REGION:15,LOCAL:30,INSTANCE:45};
const scopePrefix={WORLD:'Z',REGION:'R',LOCAL:'L',INSTANCE:'I'};
const frameInset=14;
const defaultFrame={left:.22,top:.22,width:.56,height:.56};
let camera={scale:1,tx:0,ty:0};
let cameraHistory=[];
let lastTargetBase=null;
let candidate=null;
let entered=false;
let priorScope='WORLD';
let drag=null;

const cameraNode=document.createElement('div');
cameraNode.className='desktop-crosshair-camera';
world.parentNode.insertBefore(cameraNode,world);
cameraNode.appendChild(world);

const overlay=document.createElement('div');
overlay.className='desktop-crosshair-zoom';
overlay.dataset.ui='crosshair-zoom';
overlay.innerHTML=`
  <div class="desktop-crosshair-gutter-strip top" data-zoom-out aria-label="Zoom out"></div>
  <div class="desktop-crosshair-gutter-strip right" data-zoom-out aria-label="Zoom out"></div>
  <div class="desktop-crosshair-gutter-strip bottom" data-zoom-out aria-label="Zoom out"></div>
  <div class="desktop-crosshair-gutter-strip left" data-zoom-out aria-label="Zoom out"></div>
  <div class="desktop-crosshair-frame" role="group" aria-label="Crosshair zoom target. Drag to move; resize from the lower-right corner; release to zoom.">
    <span class="desktop-crosshair-label">ZOOM TARGET</span>
    <span class="desktop-crosshair-center" aria-hidden="true"></span>
    <span class="desktop-crosshair-handle" role="button" tabindex="0" aria-label="Resize zoom target"></span>
  </div>`;
stage.appendChild(overlay);
const frame=overlay.querySelector('.desktop-crosshair-frame');
const handle=overlay.querySelector('.desktop-crosshair-handle');

function currentViewerState(){try{return api.getViewerState?.()||{}}catch{return{}}}
function explicitScope(){
  const raw=String(currentViewerState().authoringScope||priorScope||'WORLD').toUpperCase();
  return parentScopeOrder.includes(raw)?raw:'WORLD';
}
function nextScope(scope){const i=parentScopeOrder.indexOf(scope);return parentScopeOrder[Math.min(parentScopeOrder.length-1,Math.max(0,i)+1)]}
function contextEnvelope(){
  return{
    worldId:String(api.world?.id||query.get('worldId')||''),
    deedId:String(api.deed?.id||query.get('deedId')||''),
    deedRegionId:String(api.deed?.regionId||query.get('deedRegionId')||''),
    deedZoneId:String(api.deed?.zoneId||query.get('deedZone')||''),
    seed:String(api.world?.seed||query.get('seed')||'')
  };
}
function postExplicitScope(scope){
  const normalized=parentScopeOrder.includes(scope)?scope:'WORLD';
  const spatial={scope:normalized,zoomRatio:1,angle:scopeAngle[normalized],depthPrefix:scopePrefix[normalized]};
  try{window.parent.postMessage({source:'shaelvien-worldbuilder',type:'spatial-scope-change',...contextEnvelope(),spatial},location.origin)}catch{}
}
function topSelectButton(){
  try{
    const buttons=[...window.parent.document.querySelectorAll('.viewer-menu-bar button')];
    return buttons.find(button=>['SELECT','DESELECT'].includes(String(button.textContent||'').trim().toUpperCase()))||null;
  }catch{return null}
}
function setTopSelectLabel(label){
  const button=topSelectButton();if(!button)return;
  button.textContent=label;
  button.setAttribute('aria-label',label==='DESELECT'?'Deselect spatial view and return to parent controls':'Select the framed spatial area');
}
function setCamera(next){
  camera={scale:Math.max(1,Number(next.scale)||1),tx:Number(next.tx)||0,ty:Number(next.ty)||0};
  cameraNode.style.transform=`translate3d(${camera.tx.toFixed(2)}px,${camera.ty.toFixed(2)}px,0) scale(${camera.scale.toFixed(5)})`;
  stage.dataset.desktopCameraScale=camera.scale.toFixed(5);
}
function resetFrame(){
  const r=overlay.getBoundingClientRect();
  frame.style.left=`${r.width*defaultFrame.left}px`;
  frame.style.top=`${r.height*defaultFrame.top}px`;
  frame.style.width=`${r.width*defaultFrame.width}px`;
  frame.style.height=`${r.height*defaultFrame.height}px`;
}
function frameRect(){
  const o=overlay.getBoundingClientRect(),f=frame.getBoundingClientRect();
  return{left:f.left-o.left,top:f.top-o.top,width:f.width,height:f.height};
}
function screenRectToBase(rect){
  return{
    left:(rect.left-camera.tx)/camera.scale,
    top:(rect.top-camera.ty)/camera.scale,
    width:rect.width/camera.scale,
    height:rect.height/camera.scale
  };
}
function baseRectToScreen(rect){
  return{
    left:camera.tx+rect.left*camera.scale,
    top:camera.ty+rect.top*camera.scale,
    width:rect.width*camera.scale,
    height:rect.height*camera.scale
  };
}
function applyFrameZoom(){
  const stageRect=stage.getBoundingClientRect(),rect=frameRect();
  if(rect.width<36||rect.height<36)return;
  const targetBase=screenRectToBase(rect);
  const factor=Math.max(1,Math.min(stageRect.width/rect.width,stageRect.height/rect.height));
  if(factor<=1.005)return;
  cameraHistory.push({...camera});
  if(cameraHistory.length>12)cameraHistory.shift();
  const baseCx=targetBase.left+targetBase.width/2,baseCy=targetBase.top+targetBase.height/2;
  const nextScale=camera.scale*factor;
  setCamera({scale:nextScale,tx:stageRect.width/2-baseCx*nextScale,ty:stageRect.height/2-baseCy*nextScale});
  lastTargetBase=targetBase;
  resetFrame();
  announceCrosshair('Zoomed to framed area. Camera changed; spatial identity did not. Press SELECT to mark this area.');
}
function zoomOutOne(){
  clearCandidate(false);
  if(entered)deselectEntered();
  if(cameraHistory.length)setCamera(cameraHistory.pop());
  else setCamera({scale:1,tx:0,ty:0});
  lastTargetBase=null;
  resetFrame();
  announceCrosshair('Zoomed out one camera level.');
}
function announceCrosshair(text){
  const live=document.getElementById('live');if(!live)return;
  live.textContent='';requestAnimationFrame(()=>{live.textContent=text});
}
function clearCandidate(announce=true){
  candidate=null;
  stage.querySelectorAll('.desktop-spatial-dimmer,.desktop-spatial-color-window').forEach(node=>node.remove());
  stage.classList.remove('desktop-spatial-candidate');
  if(!entered)stage.classList.add('desktop-crosshair-visible');
  if(announce)announceCrosshair('Spatial selection cancelled. Standard camera controls restored.');
}
function visibleBaseRect(){
  const r=stage.getBoundingClientRect();
  return{left:(0-camera.tx)/camera.scale,top:(0-camera.ty)/camera.scale,width:r.width/camera.scale,height:r.height/camera.scale};
}
function drawCandidate(){
  clearCandidate(false);
  candidate=lastTargetBase?{...lastTargetBase}:visibleBaseRect();
  const r=stage.getBoundingClientRect(),s=baseRectToScreen(candidate);
  const left=Math.max(0,s.left),top=Math.max(0,s.top),right=Math.min(r.width,s.left+s.width),bottom=Math.min(r.height,s.top+s.height);
  if(right-left<8||bottom-top<8){candidate=visibleBaseRect();return drawCandidate()}
  const panels=[
    {left:0,top:0,width:r.width,height:top},
    {left:0,top:bottom,width:r.width,height:Math.max(0,r.height-bottom)},
    {left:0,top,width:left,height:Math.max(0,bottom-top)},
    {left:right,top,width:Math.max(0,r.width-right),height:Math.max(0,bottom-top)}
  ];
  for(const p of panels){
    if(p.width<=0||p.height<=0)continue;
    const node=document.createElement('div');node.className='desktop-spatial-dimmer';
    Object.assign(node.style,{left:`${p.left}px`,top:`${p.top}px`,width:`${p.width}px`,height:`${p.height}px`});
    stage.appendChild(node);
  }
  const color=document.createElement('button');color.type='button';color.className='desktop-spatial-color-window';
  color.setAttribute('aria-label',`Enter selected ${nextScope(explicitScope()).toLowerCase()} view`);
  Object.assign(color.style,{left:`${left}px`,top:`${top}px`,width:`${right-left}px`,height:`${bottom-top}px`});
  color.addEventListener('click',enterCandidate);
  stage.appendChild(color);
  stage.classList.add('desktop-spatial-candidate');stage.classList.remove('desktop-crosshair-visible');
  announceCrosshair(`Candidate ${nextScope(explicitScope()).toLowerCase()} selected. It remains in color while surrounding space is grayscale. Click the colored area to enter.`);
}
function enterCandidate(){
  if(!candidate||entered)return;
  priorScope=explicitScope();
  const target=nextScope(priorScope);
  entered=true;
  stage.querySelectorAll('.desktop-spatial-dimmer,.desktop-spatial-color-window').forEach(node=>node.remove());
  stage.classList.remove('desktop-spatial-candidate');stage.classList.add('desktop-spatial-entered');
  setTopSelectLabel('DESELECT');
  postExplicitScope(target);
  announceCrosshair(`Entered ${target.toLowerCase()} view. DESELECT returns to ${priorScope.toLowerCase()} controls.`);
}
function deselectEntered(){
  if(!entered)return false;
  entered=false;
  postExplicitScope(priorScope);
  stage.classList.remove('desktop-spatial-entered');stage.classList.add('desktop-crosshair-visible');
  setTopSelectLabel('SELECT');
  clearCandidate(false);
  announceCrosshair(`Returned to ${priorScope.toLowerCase()} controls. Camera position is preserved.`);
  return true;
}
function selectCommand(){
  if(entered){deselectEntered();return 'Spatial view deselected. Standard controls restored.'}
  if(candidate){clearCandidate(true);return 'Spatial candidate deselected. Crosshair controls restored.'}
  drawCandidate();
  return 'Spatial candidate selected. The selected area stays in color; click it to enter.';
}

function beginFramePointer(event,mode){
  if(event.pointerType!=='mouse'||event.button!==0)return;
  event.preventDefault();event.stopPropagation();
  const rect=frameRect();drag={id:event.pointerId,mode,startX:event.clientX,startY:event.clientY,...rect};
  frame.setPointerCapture?.(event.pointerId);stage.classList.add('desktop-crosshair-dragging');
}
frame.addEventListener('pointerdown',event=>{if(event.target===handle)return;beginFramePointer(event,'move')});
handle.addEventListener('pointerdown',event=>beginFramePointer(event,'resize'));
frame.addEventListener('pointermove',event=>{
  if(!drag||drag.id!==event.pointerId)return;
  event.preventDefault();event.stopPropagation();
  const r=overlay.getBoundingClientRect(),dx=event.clientX-drag.startX,dy=event.clientY-drag.startY;
  if(drag.mode==='move'){
    const left=Math.max(0,Math.min(r.width-drag.width,drag.left+dx));
    const top=Math.max(0,Math.min(r.height-drag.height,drag.top+dy));
    frame.style.left=`${left}px`;frame.style.top=`${top}px`;
  }else{
    const width=Math.max(96,Math.min(r.width-drag.left,drag.width+dx));
    const height=Math.max(72,Math.min(r.height-drag.top,drag.height+dy));
    frame.style.width=`${width}px`;frame.style.height=`${height}px`;
  }
});
function finishFramePointer(event){
  if(!drag||drag.id!==event.pointerId)return;
  event.preventDefault();event.stopPropagation();
  drag=null;stage.classList.remove('desktop-crosshair-dragging');
  if(frame.hasPointerCapture?.(event.pointerId))frame.releasePointerCapture(event.pointerId);
  applyFrameZoom();
}
frame.addEventListener('pointerup',finishFramePointer);frame.addEventListener('pointercancel',finishFramePointer);
for(const gutter of overlay.querySelectorAll('[data-zoom-out]'))gutter.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();zoomOutOne()});

const originalEdit=api.editCommand?.bind(api);
window.ShaelvienPrototype=Object.freeze({...api,
  editCommand:async command=>{
    const normalized=String(command||'').trim().toLowerCase();
    if(normalized==='select')return selectCommand();
    return typeof originalEdit==='function'?await originalEdit(normalized):'';
  },
  getCrosshairZoomState:()=>({camera:{...camera},candidate: candidate?{...candidate}:null,entered,priorScope})
});

function refreshVisibility(){
  const state=currentViewerState();
  const show=!entered&&!candidate&&String(state.viewerTier||'all')==='all';
  stage.classList.toggle('desktop-crosshair-visible',show);
}
new ResizeObserver(()=>{if(!drag)resetFrame();if(candidate)drawCandidate()}).observe(stage);
window.addEventListener('rist:spatial-scope-change',refreshVisibility);
resetFrame();refreshVisibility();setTopSelectLabel('SELECT');
announceCrosshair('Desktop crosshair zoom ready. Drag or resize the inset frame; release to zoom. Click the outer gutter to zoom back out.');
})();
