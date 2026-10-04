(() => {
'use strict';

function activeMapSelector(){
  const overlay=document.querySelector('.spatial-selection-grid.active[data-coordinate-space="world-map"]');
  return overlay&&overlay.offsetParent!==null?overlay:null;
}

function isTextEditingTarget(target){
  if(!(target instanceof Element))return false;
  return !!target.closest('input,textarea,select,[contenteditable="true"],.label-text-input');
}

function blockTouchCameraMove(event){
  const overlay=activeMapSelector();
  if(!overlay)return;
  const target=event.target instanceof Element?event.target:null;
  if(!target||!overlay.contains(target))return;
  event.preventDefault();
  event.stopImmediatePropagation();
}

document.addEventListener('pointermove',event=>{
  if(event.pointerType==='touch')blockTouchCameraMove(event);
},{capture:true,passive:false});

document.addEventListener('touchmove',blockTouchCameraMove,{capture:true,passive:false});

document.addEventListener('keydown',event=>{
  if(!activeMapSelector()||isTextEditingTarget(event.target))return;
  const key=String(event.key||'').toLowerCase();
  if(!['+','=','-','_','f','t'].includes(key))return;
  event.preventDefault();
  event.stopImmediatePropagation();
},{capture:true});
})();