(()=>{
 const SELECTORS={
  '#header-slider':'.header-circular-set',
  '#public-assets-slider':'.public-assets-items',
  '#private-assets-slider':'.private-assets-items',
  '#footer-slider':'.dice-circular-set',
  '#asset-main-rail':'.asset-horizontal-rail',
  '#initiative-slider':'.initiative-strip',
  '#pallet-slider':null
 };
 const FALLBACKS=['.header-circular-set','.public-assets-items','.private-assets-items','.dice-circular-set','.asset-horizontal-rail','.initiative-strip'];

 function shellFor(target){return typeof target==='string'?document.querySelector(target):target;}
 function railFor(shell,selector){
  if(!shell)return null;
  const mapped=selector&&SELECTORS[selector];
  if(mapped){const node=shell.querySelector(mapped);if(node)return node;}
  if(shell.id&&SELECTORS[`#${shell.id}`]){const node=shell.querySelector(SELECTORS[`#${shell.id}`]);if(node)return node;}
  for(const candidate of FALLBACKS){const node=shell.querySelector(candidate);if(node)return node;}
  return shell;
 }
 function verticalFor(shell,rail){
  if(rail?.classList?.contains('rist-section-list'))return true;
  if(rail?.classList?.contains('tile-browser-slider'))return true;
  const adaptive=shell?.classList?.contains('desktop-arrow-adaptive')||rail?.classList?.contains('desktop-arrow-adaptive');
  return !!adaptive&&matchMedia('(orientation: landscape)').matches;
 }
 function ensureAssetHint(selector,text){
  const rail=document.querySelector(selector);if(!rail)return;
  let hint=rail.querySelector(':scope > .rist-rail-drop-hint');
  if(!hint){hint=document.createElement('span');hint.className='rist-rail-drop-hint';hint.setAttribute('aria-hidden','true');hint.style.cssText='flex:0 0 auto;align-self:center;padding:0 10px;color:#8f8879;font:700 10px/1 system-ui;white-space:nowrap;pointer-events:none;';rail.appendChild(hint);}
  hint.textContent=text;
 }
 function normalize(shell,rail){
  if(!shell||!rail)return;
  const vertical=verticalFor(shell,rail);
  shell.style.minWidth='0';rail.style.boxSizing='border-box';rail.style.minWidth='0';rail.style.scrollBehavior='smooth';rail.style.scrollbarWidth='none';
  rail.style.webkitOverflowScrolling='touch';
  if(vertical){rail.style.overflowX='hidden';rail.style.overflowY='auto';rail.style.touchAction='pan-y';rail.style.overscrollBehaviorY='contain';}
  else{rail.style.overflowX='auto';rail.style.overflowY='hidden';rail.style.touchAction='pan-x';rail.style.overscrollBehaviorX='contain';}
  if(getComputedStyle(rail).display==='flex')rail.style.flexWrap='nowrap';
  for(const child of rail.children)child.style.flexShrink='0';
 }
 function pageAmount(shell,rail){const vertical=verticalFor(shell,rail);return Math.max(96,Math.floor((vertical?rail.clientHeight:rail.clientWidth)*.82));}
 function scrollRail(selectorOrElement,direction){
  const shell=shellFor(selectorOrElement);if(!shell)return;
  const selector=typeof selectorOrElement==='string'?selectorOrElement:null;
  const rail=railFor(shell,selector);if(!rail)return;
  normalize(shell,rail);
  const vertical=verticalFor(shell,rail),dir=Number(direction)<0?-1:1;
  const current=vertical?rail.scrollTop:rail.scrollLeft;
  const max=Math.max(0,(vertical?rail.scrollHeight-rail.clientHeight:rail.scrollWidth-rail.clientWidth));
  const amount=dir*pageAmount(shell,rail);
  /* The top menu is circular: crossing either end continues from the other end. */
  if(!vertical&&(selector==='#header-slider'||shell.id==='header-slider')&&max>2){
   if(dir>0&&current>=max-3){rail.scrollTo({left:0,top:0,behavior:'smooth'});return;}
   if(dir<0&&current<=3){rail.scrollTo({left:max,top:0,behavior:'smooth'});return;}
  }
  if(vertical)rail.scrollBy({top:amount,left:0,behavior:'smooth'});
  else rail.scrollBy({left:amount,top:0,behavior:'smooth'});
 }
 function bind(shell){
  if(!shell)return;const rail=railFor(shell,shell.id?`#${shell.id}`:null);if(!rail)return;normalize(shell,rail);if(rail.dataset.ristReleaseSlider==='1')return;rail.dataset.ristReleaseSlider='1';
  let pointerId=null,startPrimary=0,startScroll=0,dragged=false,suppressClick=false;
  rail.addEventListener('pointerdown',e=>{if(e.pointerType==='mouse'&&e.button!==0)return;if(e.target.closest('select,input,textarea,[contenteditable="true"]'))return;const vertical=verticalFor(shell,rail);pointerId=e.pointerId;startPrimary=vertical?e.clientY:e.clientX;startScroll=vertical?rail.scrollTop:rail.scrollLeft;dragged=false;suppressClick=false;try{rail.setPointerCapture(pointerId);}catch{}},true);
  rail.addEventListener('pointermove',e=>{if(pointerId!==e.pointerId)return;const vertical=verticalFor(shell,rail);const primary=vertical?e.clientY:e.clientX;const delta=primary-startPrimary;if(Math.abs(delta)>5)dragged=true;if(!dragged)return;suppressClick=true;if(vertical)rail.scrollTop=startScroll-delta;else rail.scrollLeft=startScroll-delta;e.preventDefault();},{passive:false,capture:true});
  const finish=e=>{if(pointerId!==e.pointerId)return;try{rail.releasePointerCapture(pointerId);}catch{}pointerId=null;if(dragged){const vertical=verticalFor(shell,rail);if(!vertical&&shell.id==='header-slider'){const max=Math.max(0,rail.scrollWidth-rail.clientWidth);if(max>2&&rail.scrollLeft<=1&&e.clientX>startPrimary)rail.scrollLeft=max;else if(max>2&&rail.scrollLeft>=max-1&&e.clientX<startPrimary)rail.scrollLeft=0;}setTimeout(()=>{suppressClick=false;},80);}};
  rail.addEventListener('pointerup',finish,true);rail.addEventListener('pointercancel',finish,true);
  rail.addEventListener('click',e=>{if(!suppressClick)return;e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();suppressClick=false;},true);
  rail.addEventListener('wheel',e=>{const vertical=verticalFor(shell,rail);const max=vertical?rail.scrollHeight-rail.clientHeight:rail.scrollWidth-rail.clientWidth;if(max<=2)return;const delta=vertical?(Math.abs(e.deltaY)>=Math.abs(e.deltaX)?e.deltaY:e.deltaX):(Math.abs(e.deltaX)>Math.abs(e.deltaY)?e.deltaX:e.deltaY);if(vertical)rail.scrollTop+=delta;else rail.scrollLeft+=delta;e.preventDefault();},{passive:false});
 }
 function applyReleasePlacement(){
  const pallet=document.querySelector('#pallet-slider');if(pallet){pallet.style.removeProperty('display');pallet.removeAttribute('aria-hidden');}
  ensureAssetHint('#public-assets-slider .public-assets-items','Drag public assets here');ensureAssetHint('#private-assets-slider .private-assets-items','Drag private assets here');
 }
 function bindAll(){applyReleasePlacement();for(const selector of Object.keys(SELECTORS))bind(document.querySelector(selector));document.querySelectorAll('.desktop-arrow-slider').forEach(bind);}
 window.ristWorld=window.ristWorld||{};window.ristWorld.scrollRail=scrollRail;window.RistSlider={bindAll,scrollRail};
 let queued=false;function queueBind(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;bindAll();});}
 const observer=new MutationObserver(queueBind);function start(){bindAll();observer.observe(document.body,{childList:true,subtree:true});window.addEventListener('resize',queueBind,{passive:true});window.addEventListener('orientationchange',queueBind,{passive:true});}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
