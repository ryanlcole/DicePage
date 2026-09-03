(()=>{
 'use strict';
 const SELECTORS=['.rist-bottom-assets-strip','.rist-folder-breadcrumb','.rist-map-tools-panel','.rist-section-list'];
 const state=new WeakMap();
 const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
 const isVertical=rail=>rail.matches('.rist-section-list');
 const maxScroll=rail=>isVertical(rail)?Math.max(0,rail.scrollHeight-rail.clientHeight):Math.max(0,rail.scrollWidth-rail.clientWidth);
 const position=rail=>isVertical(rail)?rail.scrollTop:rail.scrollLeft;
 const setPosition=(rail,value,behavior='smooth')=>{
  if(isVertical(rail))rail.scrollTo({top:value,behavior});
  else rail.scrollTo({left:value,behavior});
 };
 const stepSize=rail=>Math.max(64,(isVertical(rail)?rail.clientHeight:rail.clientWidth)*.72);
 function move(rail,dir,behavior='smooth'){
  const max=maxScroll(rail);if(max<=1)return;
  const cur=position(rail),step=stepSize(rail),edge=12;
  let next=cur+dir*step;
  if(dir>0&&cur>=max-edge)next=0;
  else if(dir<0&&cur<=edge)next=max;
  else next=clamp(next,0,max);
  setPosition(rail,next,behavior);
 }
 function button(label,dir,vertical){
  const b=document.createElement('button');
  b.type='button';b.className='rist-rail-nav '+(dir<0?'prev':'next');
  b.setAttribute('aria-label',label);
  b.textContent=vertical?(dir<0?'▲':'▼'):(dir<0?'‹':'›');
  return b;
 }
 function bindRepeat(b,rail,dir){
  let timer=0,repeat=0;
  const stop=()=>{clearTimeout(timer);clearInterval(repeat);timer=repeat=0;b.classList.remove('holding')};
  const start=e=>{
   if(e.button!=null&&e.button!==0)return;
   e.preventDefault();e.stopPropagation();
   move(rail,dir,'smooth');b.classList.add('holding');
   timer=setTimeout(()=>{repeat=setInterval(()=>move(rail,dir,'auto'),130)},360);
  };
  b.addEventListener('pointerdown',start);
  ['pointerup','pointercancel','pointerleave','lostpointercapture'].forEach(t=>b.addEventListener(t,stop));
  b.addEventListener('click',e=>{e.preventDefault();e.stopPropagation()});
 }
 function suppressSwipeClicks(rail){
  let gesture=null;
  rail.addEventListener('pointerdown',e=>{
   if(!e.isTrusted||!e.target.closest('.rist-bottom-folder-card'))return;
   gesture={id:e.pointerId,x:e.clientX,y:e.clientY,moved:false};
  },{capture:true,passive:true});
  rail.addEventListener('pointermove',e=>{
   if(!gesture||gesture.id!==e.pointerId)return;
   if(Math.abs(e.clientX-gesture.x)>8||Math.abs(e.clientY-gesture.y)>8)gesture.moved=true;
  },{capture:true,passive:true});
  rail.addEventListener('click',e=>{
   if(gesture?.moved&&e.target.closest('.rist-bottom-folder-card')){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation()}
   gesture=null;
  },true);
  rail.addEventListener('pointercancel',()=>{if(gesture)gesture.moved=true},{capture:true,passive:true});
 }
 function enhance(rail){
  if(state.has(rail))return;
  const vertical=isVertical(rail);
  rail.tabIndex=rail.tabIndex>=0?rail.tabIndex:0;
  rail.setAttribute('role','region');
  if(!rail.getAttribute('aria-label'))rail.setAttribute('aria-label',vertical?'Scrollable section selector':'Scrollable control rail');
  const prev=button(vertical?'Previous controls':'Previous controls',-1,vertical);
  const next=button(vertical?'Next controls':'Next controls',1,vertical);
  bindRepeat(prev,rail,-1);bindRepeat(next,rail,1);
  rail.prepend(prev);rail.append(next);
  rail.addEventListener('keydown',e=>{
   const key=e.key;
   const backward=vertical?'ArrowUp':'ArrowLeft',forward=vertical?'ArrowDown':'ArrowRight';
   if(key===backward||key===forward){e.preventDefault();move(rail,key===backward?-1:1,'smooth')}
   else if(key==='Home'){e.preventDefault();setPosition(rail,0,'smooth')}
   else if(key==='End'){e.preventDefault();setPosition(rail,maxScroll(rail),'smooth')}
  });
  if(rail.matches('.rist-bottom-assets-strip'))suppressSwipeClicks(rail);
  state.set(rail,{prev,next});
 }
 function scan(){for(const sel of SELECTORS)document.querySelectorAll(sel).forEach(enhance)}
 let raf=0;const schedule=()=>{if(raf)return;raf=requestAnimationFrame(()=>{raf=0;scan()})};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',scan,{once:true});else scan();
 new MutationObserver(schedule).observe(document.documentElement,{childList:true,subtree:true});
})();