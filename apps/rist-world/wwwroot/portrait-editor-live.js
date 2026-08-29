(()=>{
 'use strict';
 const clamp=(n,min,max)=>Math.max(min,Math.min(max,n));
 function setup(editor){
  if(!editor||editor.dataset.livePortrait==='2')return;
  const crop=editor.querySelector('.portrait-crop'),img=crop?.querySelector('img');
  const ranges=[...editor.querySelectorAll('.portrait-adjustments input[type="range"]')];
  if(!crop||!img||ranges.length<3)return;
  editor.dataset.livePortrait='2';
  const [zoom,x,y]=ranges;
  crop.style.overflow='hidden';crop.style.touchAction='none';
  img.style.transformOrigin='50% 50%';img.style.willChange='transform';img.style.userSelect='none';img.style.webkitUserDrag='none';img.draggable=false;
  const render=()=>{
   const z=clamp(parseFloat(zoom.value)||1,1,3),xp=clamp(parseFloat(x.value)||50,0,100),yp=clamp(parseFloat(y.value)||50,0,100);
   const dx=((xp-50)/50)*crop.clientWidth,dy=((yp-50)/50)*crop.clientHeight;
   img.style.transform=`translate(${dx}px,${dy}px) scale(${z})`;
  };
  ranges.forEach(range=>range.addEventListener('input',render,{passive:true}));
  const pointers=new Map();let startX=50,startY=50,startZoom=1,startDistance=0;
  const commit=()=>ranges.forEach(range=>range.dispatchEvent(new Event('change',{bubbles:true})));
  const distance=()=>{const points=[...pointers.values()];return points.length<2?0:Math.hypot(points[0].x-points[1].x,points[0].y-points[1].y)};
  crop.addEventListener('pointerdown',e=>{
   crop.setPointerCapture?.(e.pointerId);pointers.set(e.pointerId,{x:e.clientX,y:e.clientY,sx:e.clientX,sy:e.clientY});
   if(pointers.size===1){startX=parseFloat(x.value)||50;startY=parseFloat(y.value)||50}
   if(pointers.size===2){startZoom=parseFloat(zoom.value)||1;startDistance=distance()}
   e.preventDefault();
  },{passive:false});
  crop.addEventListener('pointermove',e=>{
   const point=pointers.get(e.pointerId);if(!point)return;point.x=e.clientX;point.y=e.clientY;
   if(pointers.size>=2){const current=distance();if(startDistance>0)zoom.value=String(clamp(startZoom*(current/startDistance),1,3))}
   else{x.value=String(clamp(startX+((e.clientX-point.sx)/Math.max(1,crop.clientWidth))*100,0,100));y.value=String(clamp(startY+((e.clientY-point.sy)/Math.max(1,crop.clientHeight))*100,0,100))}
   render();e.preventDefault();
  },{passive:false});
  const end=e=>{if(!pointers.has(e.pointerId))return;pointers.delete(e.pointerId);commit();render()};
  crop.addEventListener('pointerup',end);crop.addEventListener('pointercancel',end);
  render();
 }
 const scan=()=>document.querySelectorAll('.portrait-editor').forEach(setup);
 document.addEventListener('rist:dom-change',scan);scan();
})();
