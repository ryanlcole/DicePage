let quickDropCleanup=null;

export function viewerPoint(element,clientX,clientY){
 if(!element)return null;
 const rect=element.getBoundingClientRect();
 if(rect.width<1||rect.height<1)return null;
 return [
  Math.max(0,Math.min(1,(clientX-rect.left)/rect.width)),
  Math.max(0,Math.min(1,(clientY-rect.top)/rect.height))
 ];
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
 element.addEventListener('wheel',onWheel,{passive:false});
 element.addEventListener('pointerdown',onPointerDown,{passive:true});
 element.addEventListener('pointermove',onPointerMove,{passive:false});
 element.addEventListener('pointerup',release,{passive:true});
 element.addEventListener('pointercancel',release,{passive:true});
 return {dispose(){
  element.removeEventListener('wheel',onWheel);
  element.removeEventListener('pointerdown',onPointerDown);
  element.removeEventListener('pointermove',onPointerMove);
  element.removeEventListener('pointerup',release);
  element.removeEventListener('pointercancel',release);
  pointers.clear();
  if(quickDropCleanup)quickDropCleanup();
  const style=document.getElementById(styleId);
  if(style)style.remove();
 }};
}
