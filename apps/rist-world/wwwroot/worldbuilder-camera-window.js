(()=>{
 'use strict';

 const LOCAL_GRID_CELLS=30;
 const MIN_VISIBLE_CELLS=10;
 const MAX_VISIBLE_CELLS=16;
 const TARGET_CELL_PX=30;
 const MIN_ZOOM=LOCAL_GRID_CELLS/MAX_VISIBLE_CELLS;
 const MAX_ZOOM=LOCAL_GRID_CELLS/MIN_VISIBLE_CELLS;
 const ZOOM_KEY='rist.world.viewerZoom';
 const MODE_KEY='rist.world.viewerZoom.cameraWindowV2';

 let observer=null;
 let raf=0;
 const touches=new Set();

 const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
 const studio=()=>document.querySelector('.worldbuilder-studio');
 const canvas=()=>studio()?.querySelector('.studio-viewer-canvas');
 const map=()=>studio()?.querySelector('.studio-viewer-canvas .map');
 const stage=()=>studio()?.querySelector('.studio-viewer-canvas .world-stage');

 function desiredVisibleCells(){
  const surface=map()||canvas();
  const rect=surface?.getBoundingClientRect();
  if(!rect||rect.width<1||rect.height<1)return 12;
  const usable=Math.min(rect.width,rect.height);
  return clamp(Math.round(usable/TARGET_CELL_PX),MIN_VISIBLE_CELLS,MAX_VISIBLE_CELLS);
 }

 function zoomForCells(cells){
  return clamp(LOCAL_GRID_CELLS/clamp(cells,MIN_VISIBLE_CELLS,MAX_VISIBLE_CELLS),MIN_ZOOM,MAX_ZOOM);
 }

 function storedZoom(){
  const value=Number(localStorage.getItem(ZOOM_KEY));
  return Number.isFinite(value)&&value>0?clamp(value,MIN_ZOOM,MAX_ZOOM):null;
 }

 function isAuto(){
  return localStorage.getItem(MODE_KEY)!=='manual';
 }

 function publish(zoom,visibleCells){
  const root=studio();
  if(root){
   root.dataset.cameraVisibleCells=String(visibleCells);
   root.dataset.cameraZoom=zoom.toFixed(4);
  }
  window.dispatchEvent(new CustomEvent('rist:camera-window',{
   detail:{zoom,visibleCells,localGridCells:LOCAL_GRID_CELLS}
  }));
 }

 function applyZoomValue(zoom,visibleCells=LOCAL_GRID_CELLS/zoom){
  const next=clamp(Number(zoom)||MIN_ZOOM,MIN_ZOOM,MAX_ZOOM);
  localStorage.setItem(ZOOM_KEY,String(next));
  const view=canvas();
  const world=stage();
  if(view)view.style.setProperty('--wb-view-zoom',String(next));
  if(world)world.style.setProperty('--wb-view-zoom',String(next));
  publish(next,Math.round(visibleCells));
  window.ristProjection?.apply?.();
  requestAnimationFrame(clampPan);
  return next;
 }

 function applyAutoZoom(){
  const visible=desiredVisibleCells();
  localStorage.setItem(MODE_KEY,'auto');
  return applyZoomValue(zoomForCells(visible),visible);
 }

 function applyStoredZoom(){
  const visible=desiredVisibleCells();
  const zoom=storedZoom()??zoomForCells(visible);
  return applyZoomValue(zoom,LOCAL_GRID_CELLS/zoom);
 }

 function cameraZoom(){
  return storedZoom()??zoomForCells(desiredVisibleCells());
 }

 function clampPan(){
  const navigation=window.ristViewerNavigation;
  if(!navigation?.get||!navigation?.setPosition)return;
  const zoom=cameraZoom();
  const visible=LOCAL_GRID_CELLS/zoom;
  const maxOffset=Math.max(0,Math.floor((LOCAL_GRID_CELLS-visible)/2));
  const state=navigation.get();
  const x=clamp(Math.round(Number(state?.x)||0),-maxOffset,maxOffset);
  const y=clamp(Math.round(Number(state?.y)||0),-maxOffset,maxOffset);
  if(x!==(Number(state?.x)||0)||y!==(Number(state?.y)||0))navigation.setPosition(x,y,true);
 }

 function markManual(){
  if(localStorage.getItem(MODE_KEY)==='manual')return;
  localStorage.setItem(MODE_KEY,'manual');
  const root=studio();
  if(root)root.dataset.cameraMode='manual';
 }

 function sync(){
  raf=0;
  if(!studio())return;
  if(isAuto())applyAutoZoom();
  else applyStoredZoom();
  clampPan();
 }

 function schedule(){
  if(!raf)raf=requestAnimationFrame(sync);
 }

 function onPointerDown(event){
  if(event.pointerType!=='touch'||!canvas()?.contains(event.target))return;
  touches.add(event.pointerId);
 }

 function onPointerMove(event){
  if(event.pointerType!=='touch'||!touches.has(event.pointerId))return;
  if(touches.size>=2)markManual();
  requestAnimationFrame(()=>{
   if(!isAuto())applyStoredZoom();
   clampPan();
  });
 }

 function onPointerEnd(event){
  touches.delete(event.pointerId);
  requestAnimationFrame(()=>{
   if(!isAuto())applyStoredZoom();
   clampPan();
  });
 }

 function onViewportChange(){
  requestAnimationFrame(()=>{
   if(isAuto())applyAutoZoom();
   else applyStoredZoom();
   clampPan();
  });
 }

 function initialize(){
  const root=studio();
  if(!root){setTimeout(initialize,100);return;}

  /* V2 migrates every pre-single-grid camera state. In particular, an old
     optics pinch could persist zoom values below the camera-window minimum,
     compressing the 30-cell construction grid into a dense micro-grid. */
  if(localStorage.getItem(MODE_KEY)!=='auto'&&localStorage.getItem(MODE_KEY)!=='manual'){
   localStorage.setItem(MODE_KEY,'auto');
  }
  root.dataset.cameraMode=isAuto()?'auto':'manual';

  sync();
  observer=new MutationObserver(schedule);
  observer.observe(root,{childList:true,subtree:true});

  window.addEventListener('resize',onViewportChange,{passive:true});
  window.addEventListener('orientationchange',onViewportChange,{passive:true});
  window.addEventListener('pageshow',onViewportChange,{passive:true});
  window.addEventListener('rist:viewer-pan',()=>requestAnimationFrame(clampPan));
  window.addEventListener('rist-parallax-settings',schedule);
  window.addEventListener('pointerdown',onPointerDown,{capture:true,passive:true});
  window.addEventListener('pointermove',onPointerMove,{capture:true,passive:true});
  window.addEventListener('pointerup',onPointerEnd,{capture:true,passive:true});
  window.addEventListener('pointercancel',onPointerEnd,{capture:true,passive:true});
 }

 window.ristCameraWindow={
  minZoom:MIN_ZOOM,
  maxZoom:MAX_ZOOM,
  getZoom:cameraZoom,
  setZoom(value){markManual();return applyZoomValue(value);},
  resetAuto:applyAutoZoom,
  sync:schedule
 };

 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialize,{once:true});
 else initialize();
})();
