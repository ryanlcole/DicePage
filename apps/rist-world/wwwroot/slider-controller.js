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

 function shellFor(target){
  if(!target)return null;
  if(typeof target==='string')return document.querySelector(target);
  return target;
 }

 function railFor(shell,selector){
  if(!shell)return null;
  const mapped=selector&&SELECTORS[selector];
  if(mapped){const found=shell.querySelector(mapped);if(found)return found;}
  if(shell.id&&SELECTORS[`#${shell.id}`]){
   const found=shell.querySelector(SELECTORS[`#${shell.id}`]);
   if(found)return found;
  }
  const candidates=['.header-circular-set','.public-assets-items','.private-assets-items','.dice-circular-set','.asset-horizontal-rail','.initiative-strip','.tray-scroll-track'];
  for(const candidate of candidates){const found=shell.querySelector(candidate);if(found)return found;}
  return shell;
 }

 function normalize(shell,rail){
  if(!shell||!rail)return;
  shell.style.minWidth='0';
  shell.style.overflow='hidden';
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
  for(const child of rail.children){
   if(child.classList.contains('rail-scroll-arrow'))continue;
   child.style.flexShrink='0';
  }

  // The primary menu is a three-column shell: arrow | viewport | arrow.
  // Older header rules allowed the middle flex row to grow to its content width,
  // leaving no overflow for Safari to scroll. Give it an explicit finite viewport.
  if(shell.id==='header-slider'){
   const prev=shell.querySelector(':scope > .rail-scroll-prev');
   const next=shell.querySelector(':scope > .rail-scroll-next');
   const prevWidth=prev?.getBoundingClientRect().width||30;
   const nextWidth=next?.getBoundingClientRect().width||30;
   const available=Math.max(1,Math.floor(shell.getBoundingClientRect().width-prevWidth-nextWidth));
   rail.style.width=`${available}px`;
   rail.style.maxWidth=`${available}px`;
   rail.style.justifyContent='flex-start';
  }else{
   rail.style.maxWidth='none';
  }
 }

 function pageAmount(rail){return Math.max(96,Math.floor(rail.clientWidth*.82));}

 function scrollRail(selectorOrElement,direction){
  const shell=shellFor(selectorOrElement);
  if(!shell)return;
  const selector=typeof selectorOrElement==='string'?selectorOrElement:null;
  const rail=railFor(shell,selector);
  if(!rail)return;
  normalize(shell,rail);
  const dir=Number(direction)<0?-1:1;
  rail.scrollBy({left:dir*pageAmount(rail),top:0,behavior:'smooth'});
 }

 function bind(shell){
  if(!shell)return;
  const rail=railFor(shell,shell.id?`#${shell.id}`:null);
  if(!rail)return;
  normalize(shell,rail);
  if(rail.dataset.ristSliderBound==='1')return;
  rail.dataset.ristSliderBound='1';

  let pointerId=null,startX=0,startLeft=0,moved=false;
  rail.addEventListener('pointerdown',e=>{
   if(e.pointerType==='mouse'&&e.button!==0)return;
   if(e.target.closest('select,input,textarea,a,[contenteditable="true"]'))return;
   pointerId=e.pointerId;
   startX=e.clientX;
   startLeft=rail.scrollLeft;
   moved=false;
   try{rail.setPointerCapture(pointerId);}catch{}
  },true);
  rail.addEventListener('pointermove',e=>{
   if(pointerId!==e.pointerId)return;
   const dx=e.clientX-startX;
   if(Math.abs(dx)>4)moved=true;
   if(!moved)return;
   rail.scrollLeft=startLeft-dx;
   e.preventDefault();
  },{passive:false,capture:true});
  const finish=e=>{
   if(pointerId!==e.pointerId)return;
   try{rail.releasePointerCapture(pointerId);}catch{}
   pointerId=null;
  };
  rail.addEventListener('pointerup',finish,true);
  rail.addEventListener('pointercancel',finish,true);
  rail.addEventListener('wheel',e=>{
   if(rail.scrollWidth<=rail.clientWidth+2)return;
   const delta=Math.abs(e.deltaX)>Math.abs(e.deltaY)?e.deltaX:e.deltaY;
   rail.scrollLeft+=delta;
   e.preventDefault();
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
 const queueBind=()=>{
  if(queued)return;
  queued=true;
  requestAnimationFrame(()=>{queued=false;bindAll();});
 };
 const observer=new MutationObserver(queueBind);
 function start(){bindAll();observer.observe(document.body,{childList:true,subtree:true});window.addEventListener('resize',queueBind,{passive:true});}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
