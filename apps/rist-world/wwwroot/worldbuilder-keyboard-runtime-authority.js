(()=>{
 'use strict';

 let keyboard=null;
 let touch=null;
 let frame=0;
 let observer=null;
 let lastResume=0;

 const studio=()=>document.querySelector('.worldbuilder-studio');
 const host=()=>studio()?.querySelector('.wb-device-keyboard')||null;
 const buttonFrom=target=>target?.closest?.('.wb-device-keyboard button')||null;
 const distance=(a,b)=>Math.hypot((a?.clientX||0)-(b?.clientX||0),(a?.clientY||0)-(b?.clientY||0));

 function refreshAuthorities(){
  try{window.RistWorldBuilderShaelvienKeyboardSkin?.refresh?.()}catch{}
  try{window.RistWorldBuilderGridCursor?.refresh?.()}catch{}
  try{window.RistWorldBuilderModeKeyboardRelocation?.refresh?.()}catch{}
  try{window.RistWorldTickerData?.refresh?.()}catch{}
  try{window.ristViewerNavigation?.refresh?.()}catch{}
  try{window.ristViewerAuthority?.refresh?.()}catch{}
 }

 function installTouch(next){
  if(!next||next.dataset.touchAuthority==='1')return;
  next.dataset.touchAuthority='1';

  next.addEventListener('touchstart',event=>{
   if(event.touches.length!==1)return;
   const button=buttonFrom(event.target);
   if(!button||button.disabled)return;
   const point=event.touches[0];
   touch={button,start:{clientX:point.clientX,clientY:point.clientY},moved:false};
   button.classList.add('wb-touch-active');
  },{passive:true});

  next.addEventListener('touchmove',event=>{
   if(!touch||event.touches.length!==1)return;
   const point=event.touches[0];
   if(distance(touch.start,point)>12){
    touch.moved=true;
    touch.button?.classList.remove('wb-touch-active');
   }
  },{passive:true});

  const finish=event=>{
   if(!touch)return;
   const state=touch;touch=null;
   state.button?.classList.remove('wb-touch-active');
   if(state.moved||state.button?.disabled||!state.button?.isConnected)return;
   const changed=event.changedTouches?.[0];
   const endedOn=changed?document.elementFromPoint(changed.clientX,changed.clientY):null;
   if(endedOn&&!state.button.contains(endedOn))return;
   /* Prevent Safari's delayed synthetic click, then issue exactly one semantic click. */
   event.preventDefault();
   state.button.classList.add('wb-touch-active');
   state.button.click();
   setTimeout(()=>state.button?.classList.remove('wb-touch-active'),110);
  };
  next.addEventListener('touchend',finish,{passive:false});
  next.addEventListener('touchcancel',()=>{
   touch?.button?.classList.remove('wb-touch-active');
   touch=null;
  },{passive:true});
 }

 function ensureKeyboard(){
  const next=host();
  if(!next)return;
  keyboard=next;
  installTouch(next);
  next.style.pointerEvents='auto';
  next.querySelectorAll('.wb-device-mode,.wb-device-key,.wb-dpad-key,.wb-device-menu,.wb-device-collapse,.wb-device-grabber').forEach(button=>{
   button.style.pointerEvents='auto';
   button.style.touchAction='manipulation';
  });
  refreshAuthorities();
 }

 function repaintWorld(){
  const root=studio();
  if(!root)return;
  root.hidden=false;
  root.classList.remove('wb-gesture-panning','wb-gesture-pinching');
  root.style.setProperty('visibility','visible','important');
  root.style.setProperty('opacity','1','important');
  if(getComputedStyle(root).display==='none')root.style.setProperty('display','grid','important');

  const app=document.getElementById('app');
  if(app){app.style.setProperty('visibility','visible','important');app.style.setProperty('opacity','1','important')}
  document.documentElement.style.setProperty('visibility','visible','important');
  document.body.style.setProperty('visibility','visible','important');

  const visibleNodes=root.querySelectorAll('.studio-viewer,.studio-viewer-canvas,.map-shell,.map,.world-stage');
  visibleNodes.forEach(node=>{
   node.style.setProperty('visibility','visible','important');
   node.style.setProperty('opacity','1','important');
  });

  /* Force WebKit to rebuild stale compositing layers without changing world truth. */
  root.classList.add('wb-resume-repaint');
  void root.offsetHeight;
  requestAnimationFrame(()=>root.classList.remove('wb-resume-repaint'));
 }

 function resume(source='resume'){
  const now=Date.now();
  if(now-lastResume<80)return;
  lastResume=now;
  const run=()=>{
   if(document.hidden)return;
   repaintWorld();
   ensureKeyboard();
   try{window.dispatchEvent(new Event('resize'))}catch{}
   try{window.dispatchEvent(new CustomEvent('rist:viewer-state',{detail:{source}}))}catch{}
  };
  requestAnimationFrame(()=>requestAnimationFrame(run));
  setTimeout(run,180);
  setTimeout(run,650);
 }

 function schedule(){
  if(frame)return;
  frame=requestAnimationFrame(()=>{frame=0;ensureKeyboard()});
 }

 function start(){
  ensureKeyboard();
  observer=new MutationObserver(schedule);
  observer.observe(document.documentElement,{childList:true,subtree:true});
  window.addEventListener('pageshow',()=>resume('pageshow'));
  window.addEventListener('focus',()=>resume('focus'),{passive:true});
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)resume('visibilitychange')});
  window.addEventListener('orientationchange',()=>resume('orientationchange'),{passive:true});
 }

 window.RistWorldBuilderKeyboardRuntime={
  refresh:()=>{ensureKeyboard();refreshAuthorities()},
  resume,
  state:()=>({mounted:!!keyboard?.isConnected,touchAuthority:keyboard?.dataset?.touchAuthority==='1',hidden:document.hidden})
 };

 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
