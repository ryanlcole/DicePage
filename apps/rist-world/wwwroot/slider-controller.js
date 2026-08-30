(()=>{
 const SELECTORS={
  '#header-slider':'.header-circular-set',
  '#public-assets-slider':'.public-assets-items',
  '#private-assets-slider':'.private-assets-items',
  '#footer-slider':'.dice-circular-set'
 };

 function resolveRail(selectorOrElement){
  const shell=typeof selectorOrElement==='string'?document.querySelector(selectorOrElement):selectorOrElement;
  if(!shell)return null;
  const selector=typeof selectorOrElement==='string'?SELECTORS[selectorOrElement]:null;
  if(selector){const inner=shell.querySelector(selector);if(inner)return inner;}
  if(shell.matches?.('#header-slider'))return shell.querySelector('.header-circular-set')||shell;
  if(shell.matches?.('#public-assets-slider'))return shell.querySelector('.public-assets-items')||shell;
  if(shell.matches?.('#private-assets-slider'))return shell.querySelector('.private-assets-items')||shell;
  if(shell.matches?.('#footer-slider'))return shell.querySelector('.dice-circular-set')||shell;
  return shell;
 }

 function normalizeRail(shell,rail){
  rail.style.boxSizing='border-box';
  rail.style.width='100%';
  rail.style.maxWidth='100%';
  rail.style.minWidth='0';
  rail.style.overflowX='auto';
  rail.style.overflowY='hidden';
  rail.style.webkitOverflowScrolling='touch';
  rail.style.touchAction='pan-x';
  rail.style.scrollBehavior='smooth';
  rail.style.scrollbarWidth='none';
  if(shell.matches?.('#header-slider,#footer-slider')){
   shell.style.overflow='hidden';
   rail.style.flexWrap='nowrap';
  }
 }

 function pageAmount(rail){return Math.max(96,Math.floor(rail.clientWidth*.78));}

 function scrollRail(selector,direction){
  const rail=resolveRail(selector);if(!rail)return;
  const dir=Number(direction)<0?-1:1;
  rail.scrollBy({left:dir*pageAmount(rail),top:0,behavior:'smooth'});
 }

 function bindRail(shell){
  if(!shell)return;
  const rail=resolveRail(shell);if(!rail)return;
  normalizeRail(shell,rail);
  if(shell.dataset.ristSliderBound==='1')return;
  shell.dataset.ristSliderBound='1';

  let pointerId=null,startX=0,startLeft=0,moved=false;
  rail.addEventListener('pointerdown',e=>{
   if(e.pointerType==='mouse'&&e.button!==0)return;
   if(e.target.closest('select,input,textarea'))return;
   pointerId=e.pointerId;startX=e.clientX;startLeft=rail.scrollLeft;moved=false;
   try{rail.setPointerCapture(pointerId);}catch{}
  });
  rail.addEventListener('pointermove',e=>{
   if(pointerId!==e.pointerId)return;
   const dx=e.clientX-startX;
   if(Math.abs(dx)>4)moved=true;
   if(moved){rail.scrollLeft=startLeft-dx;e.preventDefault();}
  },{passive:false});
  const finish=e=>{
   if(pointerId!==e.pointerId)return;
   try{rail.releasePointerCapture(pointerId);}catch{}
   pointerId=null;
  };
  rail.addEventListener('pointerup',finish);
  rail.addEventListener('pointercancel',finish);
  rail.addEventListener('wheel',e=>{
   if(rail.scrollWidth<=rail.clientWidth+2)return;
   const delta=Math.abs(e.deltaX)>Math.abs(e.deltaY)?e.deltaX:e.deltaY;
   rail.scrollLeft+=delta;
   e.preventDefault();
  },{passive:false});
 }

 function bindAll(){
  Object.keys(SELECTORS).forEach(selector=>bindRail(document.querySelector(selector)));
  document.querySelectorAll('.desktop-arrow-slider').forEach(bindRail);
 }

 window.ristWorld=window.ristWorld||{};
 window.ristWorld.scrollRail=scrollRail;
 window.RistSlider={bindAll,scrollRail};

 const observer=new MutationObserver(()=>requestAnimationFrame(bindAll));
 function start(){bindAll();observer.observe(document.body,{childList:true,subtree:true});}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
