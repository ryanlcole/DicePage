(()=>{
 const SELECTORS={
  '#header-slider':'.header-circular-set',
  '#public-assets-slider':'.public-assets-items',
  '#private-assets-slider':'.private-assets-items',
  '#footer-slider':'.dice-circular-set',
  '#asset-main-rail':'.asset-horizontal-rail',
  '#pallet-slider':'.tray-scroll-track',
  '#initiative-slider':'.initiative-strip'
 };
 const FALLBACKS=['.header-circular-set','.public-assets-items','.private-assets-items','.dice-circular-set','.asset-horizontal-rail','.initiative-strip','.tray-scroll-track'];

 function shellFor(target){return typeof target==='string'?document.querySelector(target):target;}
 function railFor(shell,selector){
  if(!shell)return null;
  const mapped=selector&&SELECTORS[selector];
  if(mapped){const node=shell.querySelector(mapped);if(node)return node;}
  if(shell.id&&SELECTORS[`#${shell.id}`]){const node=shell.querySelector(SELECTORS[`#${shell.id}`]);if(node)return node;}
  for(const candidate of FALLBACKS){const node=shell.querySelector(candidate);if(node)return node;}
  return shell;
 }

 function normalize(shell,rail){
  if(!shell||!rail)return;
  shell.style.minWidth='0';
  rail.style.boxSizing='border-box';
  rail.style.minWidth='0';
  rail.style.overflowX='auto';
  rail.style.overflowY='hidden';
  rail.style.webkitOverflowScrolling='touch';
  rail.style.touchAction='pan-x';
  rail.style.overscrollBehaviorX='contain';
  rail.style.scrollBehavior='smooth';
  rail.style.scrollbarWidth='none';
  if(getComputedStyle(rail).display==='flex')rail.style.flexWrap='nowrap';
  for(const child of rail.children)child.style.flexShrink='0';
 }

 function pageAmount(rail){return Math.max(96,Math.floor(rail.clientWidth*.82));}
 function scrollRail(selectorOrElement,direction){
  const shell=shellFor(selectorOrElement);if(!shell)return;
  const selector=typeof selectorOrElement==='string'?selectorOrElement:null;
  const rail=railFor(shell,selector);if(!rail)return;
  normalize(shell,rail);
  rail.scrollBy({left:(Number(direction)<0?-1:1)*pageAmount(rail),top:0,behavior:'smooth'});
 }

 function bind(shell){
  if(!shell)return;
  const rail=railFor(shell,shell.id?`#${shell.id}`:null);if(!rail)return;
  normalize(shell,rail);
  if(rail.dataset.ristReleaseSlider==='1')return;
  rail.dataset.ristReleaseSlider='1';

  let pointerId=null,startX=0,startLeft=0,dragged=false,suppressClick=false;
  rail.addEventListener('pointerdown',e=>{
   if(e.pointerType==='mouse'&&e.button!==0)return;
   if(e.target.closest('select,input,textarea,[contenteditable="true"]'))return;
   pointerId=e.pointerId;startX=e.clientX;startLeft=rail.scrollLeft;dragged=false;suppressClick=false;
   try{rail.setPointerCapture(pointerId);}catch{}
  },true);
  rail.addEventListener('pointermove',e=>{
   if(pointerId!==e.pointerId)return;
   const dx=e.clientX-startX;
   if(Math.abs(dx)>5)dragged=true;
   if(!dragged)return;
   suppressClick=true;
   rail.scrollLeft=startLeft-dx;
   e.preventDefault();
  },{passive:false,capture:true});
  const finish=e=>{
   if(pointerId!==e.pointerId)return;
   try{rail.releasePointerCapture(pointerId);}catch{}
   pointerId=null;
   if(dragged)setTimeout(()=>{suppressClick=false;},80);
  };
  rail.addEventListener('pointerup',finish,true);
  rail.addEventListener('pointercancel',finish,true);
  rail.addEventListener('click',e=>{
   if(!suppressClick)return;
   e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();
   suppressClick=false;
  },true);
  rail.addEventListener('wheel',e=>{
   if(rail.scrollWidth<=rail.clientWidth+2)return;
   const delta=Math.abs(e.deltaX)>Math.abs(e.deltaY)?e.deltaX:e.deltaY;
   rail.scrollLeft+=delta;e.preventDefault();
  },{passive:false});
 }

 function bindAll(){
  for(const selector of Object.keys(SELECTORS))bind(document.querySelector(selector));
  document.querySelectorAll('.desktop-arrow-slider').forEach(bind);
 }

 window.ristWorld=window.ristWorld||{};
 window.ristWorld.scrollRail=scrollRail;
 window.RistSlider={bindAll,scrollRail};

 let queued=false;
 function queueBind(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;bindAll();});}
 const observer=new MutationObserver(queueBind);
 function start(){bindAll();observer.observe(document.body,{childList:true,subtree:true});window.addEventListener('resize',queueBind,{passive:true});window.addEventListener('orientationchange',queueBind,{passive:true});}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
