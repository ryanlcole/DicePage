(()=>{
 'use strict';
 const interactive='button,[href],input,select,textarea,[role="button"],[tabindex]:not([tabindex="-1"])';
 let ticker=null,lastButtons=[];
 const menuOpen=()=>{const el=document.querySelector('.rist-start-overlay');return !!el&&!el.hidden};
 function buildBottomTicker(){
  const message='© 2026 Ryan L. Cole / ReLiCGameMaster · Shaelvien and RIST · ReLiCGameMaster.com · Contact';
  if(!ticker){
   ticker=document.querySelector('.rist-bottom-ticker');
   if(!ticker){ticker=document.createElement('div');ticker.className='rist-bottom-ticker';document.body.appendChild(ticker)}
  }
  ticker.setAttribute('aria-label','Copyright and contact');
  if(!ticker.querySelector('.rist-bottom-ticker-track')){
   ticker.textContent='';
   const track=document.createElement('div');
   track.className='rist-bottom-ticker-track';
   for(let i=0;i<3;i++){
    const item=document.createElement('span');
    item.className='rist-bottom-ticker-item';
    item.textContent=message;
    if(i>0)item.setAttribute('aria-hidden','true');
    track.appendChild(item);
   }
   ticker.appendChild(track);
  }
 }
 function ensureChrome(){buildBottomTicker();document.querySelector('.rist-page-controls')?.remove()}
 function openStart(){window.RistStartMenu?.open?.()}
 function keydown(e){
  if(e.key!=='Escape')return;
  const active=document.activeElement;
  const typing=active&&(/^(INPUT|TEXTAREA|SELECT)$/.test(active.tagName)||active.isContentEditable);
  if(typing||menuOpen())return;
  e.preventDefault();e.stopPropagation();openStart();
 }
 function selectAsTouch(){
  const focused=document.activeElement;
  const target=focused&&focused!==document.body&&focused.matches?.(interactive)?focused:document.elementFromPoint(innerWidth/2,innerHeight/2)?.closest?.(interactive);
  if(!target)return;
  try{target.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,pointerType:'touch',isPrimary:true,clientX:innerWidth/2,clientY:innerHeight/2}));}catch{}
  target.click?.();
  try{target.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,pointerType:'touch',isPrimary:true,clientX:innerWidth/2,clientY:innerHeight/2}));}catch{}
 }
 function pollGamepads(){
  const pads=navigator.getGamepads?.()||[];
  for(let i=0;i<pads.length;i++){
   const pad=pads[i];if(!pad)continue;
   const prev=lastButtons[i]||[];
   const pressed=n=>!!pad.buttons?.[n]?.pressed;
   const rising=n=>pressed(n)&&!prev[n];
   if(rising(9))openStart();
   if(rising(8))selectAsTouch();
   lastButtons[i]=(pad.buttons||[]).map(b=>!!b.pressed);
  }
  requestAnimationFrame(pollGamepads);
 }
 function start(){ensureChrome();document.addEventListener('keydown',keydown,true);requestAnimationFrame(pollGamepads)}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.RistAppShell={selectAsTouch};
})();
