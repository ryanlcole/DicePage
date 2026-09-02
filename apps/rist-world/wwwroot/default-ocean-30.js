(()=>{
 'use strict';
 const COLS=30,ROWS=30;
 function install(){
  if(!window.ristWorld?.tileDropPoint)return false;
  window.ristWorld.tileDropPoint=(el,x,y,panX,panY,zoom)=>{
   const r=el.getBoundingClientRect();
   const inside=x>=r.left&&x<=r.right&&y>=r.top&&y<=r.bottom;
   if(!inside)return [0,0,0];
   const sx=(Math.floor(Math.max(0,Math.min(.999999,(x-r.left)/r.width))*COLS)+.5)/COLS;
   const sy=(Math.floor(Math.max(0,Math.min(.999999,(y-r.top)/r.height))*ROWS)+.5)/ROWS;
   const z=Math.max(Number(zoom)||1,.01);
   return [1,((sx-.5)/z)+.5-(Number(panX)||0)/(r.width*z),((sy-.5)/z)+.5-(Number(panY)||0)/(r.height*z)];
  };
  document.documentElement.dataset.worldGrid='30x30';
  return true;
 }
 function patchLabels(){
  document.querySelectorAll('.map .status,.map-frame-status,[data-grid-status]').forEach(el=>{
   if(el.childElementCount)return;
   el.textContent=(el.textContent||'').replace(/20\s*[×x]\s*13/g,'30×30').replace(/5(?:\.0+)?\s*mi\/sq/gi,'1 mi/sq');
  });
 }
 function start(){if(!install())setTimeout(start,50);patchLabels();new MutationObserver(()=>requestAnimationFrame(patchLabels)).observe(document.body,{childList:true,subtree:true,characterData:true});}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
