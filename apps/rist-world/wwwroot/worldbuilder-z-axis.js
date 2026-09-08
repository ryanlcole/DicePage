export function attach(element,dotnet){
 if(!element)return {dispose(){}};
 const pointers=new Map();
 let pinchDistance=0;
 let wheelAccumulator=0;
 const step=delta=>{if(!delta)return;dotnet.invokeMethodAsync('StepZ',delta).catch(()=>{});};
 const distance=()=>{const values=[...pointers.values()];if(values.length<2)return 0;const dx=values[0].x-values[1].x;const dy=values[0].y-values[1].y;return Math.hypot(dx,dy)};
 const onWheel=e=>{
  e.preventDefault();
  wheelAccumulator+=e.deltaY;
  if(Math.abs(wheelAccumulator)<70)return;
  // World Builder treats zoom as recursive depth navigation: zooming OUT
  // reveals/builds the next layer above the current slice; zooming IN returns
  // toward the layer below. The viewer itself never changes size.
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
 }};
}
