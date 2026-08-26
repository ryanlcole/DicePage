(()=>{
 const clamp=(n,min,max)=>Math.max(min,Math.min(max,n));
 function setup(editor){
  if(!editor||editor.dataset.livePortrait==='1')return;
  const crop=editor.querySelector('.portrait-crop');
  const img=crop?.querySelector('img');
  const ranges=[...editor.querySelectorAll('.portrait-adjustments input[type="range"]')];
  if(!crop||!img||ranges.length<3)return;
  editor.dataset.livePortrait='1';
  const [zoom,x,y]=ranges;
  crop.style.overflow='hidden';
  crop.style.touchAction='none';
  img.style.transformOrigin='50% 50%';
  img.style.willChange='transform';
  img.style.userSelect='none';
  img.style.webkitUserDrag='none';

  const render=()=>{
   const z=clamp(parseFloat(zoom.value)||1,1,3);
   const xp=clamp(parseFloat(x.value)||50,0,100);
   const yp=clamp(parseFloat(y.value)||50,0,100);
   // Full slider travel now moves the source image a complete crop diameter
   // in either direction instead of stopping at half a diameter.
   const dx=((xp-50)/50)*crop.clientWidth;
   const dy=((yp-50)/50)*crop.clientHeight;
   img.style.transform=`translate(${dx}px,${dy}px) scale(${z})`;
  };
  ranges.forEach(r=>r.addEventListener('input',render,{passive:true}));

  let pointers=new Map(),startX=50,startY=50,startZoom=1,startDistance=0;
  const commit=()=>ranges.forEach(r=>r.dispatchEvent(new Event('change',{bubbles:true})));
  const pointDistance=()=>{const p=[...pointers.values()];return p.length<2?0:Math.hypot(p[0].x-p[1].x,p[0].y-p[1].y)};

  crop.addEventListener('pointerdown',e=>{
   crop.setPointerCapture?.(e.pointerId);
   pointers.set(e.pointerId,{x:e.clientX,y:e.clientY,sx:e.clientX,sy:e.clientY});
   if(pointers.size===1){startX=parseFloat(x.value)||50;startY=parseFloat(y.value)||50;}
   if(pointers.size===2){startZoom=parseFloat(zoom.value)||1;startDistance=pointDistance();}
   e.preventDefault();
  });
  crop.addEventListener('pointermove',e=>{
   const p=pointers.get(e.pointerId);if(!p)return;
   p.x=e.clientX;p.y=e.clientY;
   if(pointers.size>=2){
    const d=pointDistance();if(startDistance>0)zoom.value=String(clamp(startZoom*(d/startDistance),1,3));
   }else{
    const dx=e.clientX-p.sx,dy=e.clientY-p.sy;
    x.value=String(clamp(startX+(dx/Math.max(1,crop.clientWidth))*100,0,100));
    y.value=String(clamp(startY+(dy/Math.max(1,crop.clientHeight))*100,0,100));
   }
   render();e.preventDefault();
  });
  const end=e=>{if(!pointers.has(e.pointerId))return;pointers.delete(e.pointerId);commit();render();};
  crop.addEventListener('pointerup',end);crop.addEventListener('pointercancel',end);
  render();
 }
 function scan(){document.querySelectorAll('.portrait-editor').forEach(setup)}
 const mo=new MutationObserver(scan);mo.observe(document.body,{childList:true,subtree:true});
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',scan,{once:true});else scan();
})();
