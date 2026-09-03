(()=>{
 'use strict';
 let queued=false;
 const q=(s,r=document)=>r?.querySelector?.(s)||null;
 function apply(){
  const shell=q('.release-map-region .map-shell');
  const map=q(':scope > .map',shell);
  const stage=q(':scope > .world-stage',map);
  if(!shell||!map)return;
  const set=(el,name,value)=>el?.style.setProperty(name,value,'important');
  set(map,'grid-column','1 / -1');
  set(map,'grid-row','1 / -1');
  set(map,'position','relative');
  set(map,'inset','auto');
  set(map,'display','block');
  set(map,'visibility','visible');
  set(map,'opacity','1');
  set(map,'width','100%');
  set(map,'height','100%');
  set(map,'min-width','0');
  set(map,'min-height','0');
  set(map,'max-width','none');
  set(map,'max-height','none');
  if(stage){
   set(stage,'position','absolute');
   set(stage,'inset','0');
   set(stage,'display','block');
   set(stage,'visibility','visible');
   set(stage,'opacity','1');
   set(stage,'width','100%');
   set(stage,'height','100%');
   set(stage,'min-width','0');
   set(stage,'min-height','0');
   set(stage,'max-width','none');
   set(stage,'max-height','none');
  }
 }
 function queue(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;apply()})}
 function start(){apply();new MutationObserver(queue).observe(q('#app')||document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['style','class']});window.addEventListener('resize',queue,{passive:true});window.addEventListener('orientationchange',()=>setTimeout(queue,100),{passive:true});setInterval(apply,750)}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();