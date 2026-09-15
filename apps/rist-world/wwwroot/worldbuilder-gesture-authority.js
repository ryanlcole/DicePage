(()=>{
 'use strict';

 const pointers=new Map();
 const studio=()=>document.querySelector('.worldbuilder-studio');
 const canvas=()=>studio()?.querySelector('.studio-viewer-canvas');
 const authority=()=>window.ristViewerAuthority;
 const locked=()=>authority()?.get?.().locked??(localStorage.getItem('rist.world.viewerLocked')!=='false');
 const readZoom=()=>authority()?.getZoom?.()??Number(document.querySelector('.studio-viewer-canvas .map')?.dataset?.zoom||1);
 const targetBlocked=target=>!!target?.closest?.('.studio-library-shade,.studio-mini-panel,.studio-load-panel,.wb-modal,.locked-tile-menu,.recursive-region-actions,.region-player-picker,.description-mode-toggle,.desktop-map-zoom,.wb-viewer-optics');
 const assetTarget=target=>!!target?.closest?.('.world-stage .tile-cell,.world-stage .piece,.world-stage .rolled-die,.world-stage button');
 const insideViewer=target=>{const view=canvas();return !!view&&!!target&&view.contains(target)&&!targetBlocked(target)};

 function onPointerDown(event){
  if(!insideViewer(event.target))return;
  if(event.pointerType==='mouse'&&event.button!==0)return;
  pointers.set(event.pointerId,{asset:assetTarget(event.target)});
 }

 function onPointerMove(event){
  const pointer=pointers.get(event.pointerId);
  if(!pointer||!locked()||pointer.asset||pointers.size>=2)return;
  // Viewer lock gates only single-pointer camera pan. The event is stopped before
  // WorldMap sees movement, while taps, wheel zoom and two-finger pinch remain native.
  event.preventDefault();
  event.stopPropagation();
  event.stopImmediatePropagation();
 }

 function finishPointer(event){pointers.delete(event.pointerId)}

 function onKeyDown(event){
  if(!locked())return;
  const view=canvas();
  if(!view||!view.contains(event.target))return;
  const key=(event.key||'').toLowerCase();
  if(!['arrowleft','arrowright','arrowup','arrowdown','a','d','w','s'].includes(key))return;
  event.preventDefault();
  event.stopPropagation();
  event.stopImmediatePropagation();
 }

 function setZoom(value){return authority()?.setZoom?.(value,{mode:'manual',source:'gesture-adapter'})}
 function zoomAt(_clientX,_clientY,value){return setZoom(value)}
 function install(){
  window.addEventListener('pointerdown',onPointerDown,{capture:true,passive:true});
  window.addEventListener('pointermove',onPointerMove,{capture:true,passive:false});
  window.addEventListener('pointerup',finishPointer,{capture:true,passive:true});
  window.addEventListener('pointercancel',finishPointer,{capture:true,passive:true});
  window.addEventListener('keydown',onKeyDown,{capture:true});
 }

 window.ristWorldBuilderGestures={
  ownsViewerGestures:false,
  getZoom:readZoom,
  zoomAt,
  setZoom,
  state:()=>({locked:locked(),zoom:readZoom(),pointerCount:pointers.size})
 };
 install();
})();
