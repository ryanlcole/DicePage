let quickDropCleanup=null;

export function viewerPoint(element,clientX,clientY){
 if(!element)return null;
 const rect=element.getBoundingClientRect();
 if(rect.width<1||rect.height<1)return null;
 const x=(clientX-rect.left)/rect.width;
 const y=(clientY-rect.top)/rect.height;
 if(x<0||x>1||y<0||y>1)return null;
 return [x,y];
}

export function beginQuickPointerDrop(dotnet,pointerId){
 if(quickDropCleanup)quickDropCleanup();
 const finish=()=>{
  document.removeEventListener('pointerup',onUp,true);
  document.removeEventListener('pointercancel',onCancel,true);
  quickDropCleanup=null;
 };
 const onUp=e=>{
  if(e.pointerId!==pointerId)return;
  finish();
  dotnet?.invokeMethodAsync('QuickPointerDrop',e.clientX,e.clientY).catch(()=>{});
 };
 const onCancel=e=>{
  if(e.pointerId!==pointerId)return;
  finish();
 };
 document.addEventListener('pointerup',onUp,true);
 document.addEventListener('pointercancel',onCancel,true);
 quickDropCleanup=finish;
}

export function attach(element,dotnet){
 if(!element)return {dispose(){}};
 const pointers=new Map();
 let pinchDistance=0;
 let wheelAccumulator=0;
 let quickPointer=null;

 // World Builder has one and only one grid authority: .studio-viewer-grid.
 // Legacy map/grid helpers may still render their own overlays for other
 // workspaces, so suppress every grid that lives inside the embedded map while
 // this workspace is mounted. The studio grid is a sibling of WorldMap and is
 // therefore intentionally unaffected.
 const styleId='rist-worldbuilder-single-grid-authority';
 let gridAuthority=document.getElementById(styleId);
 if(!gridAuthority){
  gridAuthority=document.createElement('style');
  gridAuthority.id=styleId;
  gridAuthority.textContent=`
   .worldbuilder-studio .studio-viewer-canvas .map [class*="grid"]{
    display:none!important;
    visibility:hidden!important;
    background:none!important;
    background-image:none!important;
    border:0!important;
    outline:0!important;
   }
   .worldbuilder-studio .studio-viewer-canvas .map::before,
   .worldbuilder-studio .studio-viewer-canvas .map::after,
   .worldbuilder-studio .studio-viewer-canvas .world-stage::before,
   .worldbuilder-studio .studio-viewer-canvas .world-stage::after{
    content:none!important;
    display:none!important;
    background:none!important;
    background-image:none!important;
   }
   .worldbuilder-studio .studio-viewer-canvas .coordinate-system,
   .worldbuilder-studio .studio-viewer-canvas .grid-coordinates,
   .worldbuilder-studio .studio-viewer-canvas .coordinate-grid,
   .worldbuilder-studio .studio-viewer-canvas .map-grid,
   .worldbuilder-studio .studio-viewer-canvas .grid-overlay{
    display:none!important;
    visibility:hidden!important;
   }
   .worldbuilder-studio .quick-slot.filled,
   .worldbuilder-studio .quick-slot.filled *{
    -webkit-user-select:none!important;
    user-select:none!important;
    -webkit-touch-callout:none!important;
    touch-action:none!important;
   }
  `;
  document.head.appendChild(gridAuthority);
 }

 const step=delta=>{if(!delta)return;dotnet.invokeMethodAsync('StepZ',delta).catch(()=>{});};
 const distance=()=>{const values=[...pointers.values()];if(values.length<2)return 0;const dx=values[0].x-values[1].x;const dy=values[0].y-values[1].y;return Math.hypot(dx,dy)};
 const onWheel=e=>{
  e.preventDefault();
  wheelAccumulator+=e.deltaY;
  if(Math.abs(wheelAccumulator)<70)return;
  const delta=wheelAccumulator>0?1:-1;
  wheelAccumulator=0;
  step(delta);
 };
 const onPointerDown=e=>{
  pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
  if(pointers.size===2)pinchDistance=distance();
 };
 const onPointerMove=e=>{
  if(!pointers.has(e.pointerId))return;
  pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
  if(pointers.size!==2)return;
  const next=distance();
  if(!pinchDistance){pinchDistance=next;return;}
  const ratio=next/pinchDistance;
  if(ratio>=1.16){step(-1);pinchDistance=next;}
  else if(ratio<=0.86){step(1);pinchDistance=next;}
  e.preventDefault();
 };
 const release=e=>{pointers.delete(e.pointerId);if(pointers.size<2)pinchDistance=0;};

 // iOS/Safari does not provide dependable native HTML drag-and-drop for touch.
 // Bridge touch/pen movement into the same Blazor dragstart/drop handlers the
 // desktop path already uses, while leaving mouse drag behavior native.
 const onQuickPointerDown=e=>{
  if(e.pointerType==='mouse')return;
  const button=e.target?.closest?.('.worldbuilder-studio .quick-slot.filled');
  if(!button)return;
  // Prevent Safari's text-selection/callout gesture from owning the hold before
  // we can turn it into a tile drag.
  e.preventDefault();
  quickPointer={id:e.pointerId,startX:e.clientX,startY:e.clientY,moved:false,button};
  try{button.setPointerCapture?.(e.pointerId);}catch{}
  button.dispatchEvent(new DragEvent('dragstart',{bubbles:true,cancelable:true,clientX:e.clientX,clientY:e.clientY}));
 };
 const onQuickPointerMove=e=>{
  if(!quickPointer||e.pointerId!==quickPointer.id)return;
  if(Math.abs(e.clientX-quickPointer.startX)+Math.abs(e.clientY-quickPointer.startY)>8)quickPointer.moved=true;
  e.preventDefault();
 };
 const onQuickPointerUp=e=>{
  if(!quickPointer||e.pointerId!==quickPointer.id)return;
  e.preventDefault();
  const current=quickPointer;
  quickPointer=null;
  try{current.button.releasePointerCapture?.(e.pointerId);}catch{}
  if(current.moved){
   const target=document.elementFromPoint(e.clientX,e.clientY);
   const viewer=target?.closest?.('.worldbuilder-studio .studio-viewer-canvas');
   if(viewer) viewer.dispatchEvent(new DragEvent('drop',{bubbles:true,cancelable:true,clientX:e.clientX,clientY:e.clientY}));
  }
  current.button.dispatchEvent(new DragEvent('dragend',{bubbles:true,cancelable:true,clientX:e.clientX,clientY:e.clientY}));
 };
 const onQuickPointerCancel=e=>{
  if(!quickPointer||e.pointerId!==quickPointer.id)return;
  const current=quickPointer;quickPointer=null;
  try{current.button.releasePointerCapture?.(e.pointerId);}catch{}
  current.button.dispatchEvent(new DragEvent('dragend',{bubbles:true,cancelable:true,clientX:e.clientX,clientY:e.clientY}));
 };

 element.addEventListener('wheel',onWheel,{passive:false});
 element.addEventListener('pointerdown',onPointerDown,{passive:true});
 element.addEventListener('pointermove',onPointerMove,{passive:false});
 element.addEventListener('pointerup',release,{passive:true});
 element.addEventListener('pointercancel',release,{passive:true});
 document.addEventListener('pointerdown',onQuickPointerDown,{capture:true,passive:false});
 document.addEventListener('pointermove',onQuickPointerMove,{capture:true,passive:false});
 document.addEventListener('pointerup',onQuickPointerUp,{capture:true,passive:false});
 document.addEventListener('pointercancel',onQuickPointerCancel,true);
 return {dispose(){
  element.removeEventListener('wheel',onWheel);
  element.removeEventListener('pointerdown',onPointerDown);
  element.removeEventListener('pointermove',onPointerMove);
  element.removeEventListener('pointerup',release);
  element.removeEventListener('pointercancel',release);
  document.removeEventListener('pointerdown',onQuickPointerDown,true);
  document.removeEventListener('pointermove',onQuickPointerMove,true);
  document.removeEventListener('pointerup',onQuickPointerUp,true);
  document.removeEventListener('pointercancel',onQuickPointerCancel,true);
  pointers.clear();
  quickPointer=null;
  if(quickDropCleanup)quickDropCleanup();
  const style=document.getElementById(styleId);
  if(style)style.remove();
 }};
}
