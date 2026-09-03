(()=>{
 'use strict';
 const bound=new WeakSet();
 function enhance(rail){
  if(bound.has(rail))return;
  const hasFolders=()=>!!rail.querySelector('.rist-bottom-folder-card');
  rail.style.touchAction='none';
  let g=null,suppress=false;
  rail.addEventListener('pointerdown',e=>{
   if(!hasFolders())return;
   if(e.pointerType&&e.pointerType!=='touch'&&e.pointerType!=='pen')return;
   if(e.target.closest('.rist-rail-nav,.rist-bottom-asset-card'))return;
   g={id:e.pointerId,x:e.clientX,y:e.clientY,left:rail.scrollLeft,moved:false};
   try{rail.setPointerCapture(e.pointerId)}catch{}
  },true);
  rail.addEventListener('pointermove',e=>{
   if(!g||g.id!==e.pointerId)return;
   const dx=e.clientX-g.x,dy=e.clientY-g.y;
   if(!g.moved&&Math.abs(dx)<5&&Math.abs(dy)<5)return;
   if(Math.abs(dx)>=Math.abs(dy)*.65){
    g.moved=true;suppress=true;
    e.preventDefault();e.stopPropagation();
    rail.scrollLeft=g.left-dx;
   }
  },{capture:true,passive:false});
  const finish=e=>{
   if(!g||g.id!==e.pointerId)return;
   if(g.moved){e.preventDefault();e.stopPropagation();suppress=true;setTimeout(()=>suppress=false,180)}
   try{rail.releasePointerCapture(e.pointerId)}catch{}
   g=null;
  };
  rail.addEventListener('pointerup',finish,{capture:true,passive:false});
  rail.addEventListener('pointercancel',e=>{if(g&&g.id===e.pointerId)g=null},true);
  rail.addEventListener('click',e=>{
   if(suppress&&e.target.closest('.rist-bottom-folder-card')){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation()}
  },true);
  bound.add(rail);
 }
 function scan(){document.querySelectorAll('.rist-bottom-assets-strip').forEach(enhance)}
 let raf=0;const schedule=()=>{if(!raf)raf=requestAnimationFrame(()=>{raf=0;scan()})};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',scan,{once:true});else scan();
 new MutationObserver(schedule).observe(document.documentElement,{childList:true,subtree:true});
})();
