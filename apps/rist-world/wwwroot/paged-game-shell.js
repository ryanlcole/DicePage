(()=>{
 'use strict';
 const interactive='button,[href],input,select,textarea,[role="button"],[tabindex]:not([tabindex="-1"])';
 let ticker=null,pager=null,lastButtons=[];
 const world=()=>document.querySelector('.rist.release-world');
 const menuOpen=()=>{const el=document.querySelector('.rist-start-overlay');return !!el&&!el.hidden};
 function ensureChrome(){
  if(!ticker){
   ticker=document.querySelector('.rist-bottom-ticker');
   if(!ticker){
    ticker=document.createElement('div');
    ticker.className='rist-bottom-ticker';
    ticker.setAttribute('aria-label','Copyright and contact');
    ticker.textContent='© 2026 Ryan L. Cole / ReLiCGameMaster · Shaelvien and RIST · ReLiCGameMaster.com · Contact';
    document.body.appendChild(ticker);
   }
  }
  if(!pager){
   pager=document.querySelector('.rist-page-controls');
   if(!pager){
    pager=document.createElement('nav');
    pager.className='rist-page-controls';
    pager.setAttribute('aria-label','Page navigation');
    pager.innerHTML='<button type="button" data-page-up aria-label="Page up">PAGE UP</button><button type="button" data-page-down aria-label="Page down">PAGE DOWN</button>';
    document.body.appendChild(pager);
    pager.querySelector('[data-page-up]').addEventListener('click',()=>page(-1));
    pager.querySelector('[data-page-down]').addEventListener('click',()=>page(1));
   }
  }
 }
 function page(direction){const el=world();if(!el)return;el.scrollBy({top:direction*el.clientHeight,behavior:'smooth'})}
 function home(){const el=world();if(el)el.scrollTo({top:0,behavior:'smooth'})}
 function end(){const el=world();if(el)el.scrollTo({top:el.scrollHeight,behavior:'smooth'})}
 function openStart(){window.RistStartMenu?.open?.()}
 function keydown(e){
  const active=document.activeElement;
  const typing=active&&(/^(INPUT|TEXTAREA|SELECT)$/.test(active.tagName)||active.isContentEditable);
  if(e.key==='Escape'){
   if(menuOpen())return;
   e.preventDefault();e.stopPropagation();openStart();return;
  }
  if(typing)return;
  if(e.key==='PageUp'){e.preventDefault();page(-1)}
  else if(e.key==='PageDown'){e.preventDefault();page(1)}
  else if(e.key==='Home'){e.preventDefault();home()}
  else if(e.key==='End'){e.preventDefault();end()}
 }
 function selectAsTouch(){
  const focused=document.activeElement;
  const target=focused&&focused!==document.body&&focused.matches?.(interactive)
   ?focused
   :document.elementFromPoint(innerWidth/2,innerHeight/2)?.closest?.(interactive);
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
   if(rising(9))openStart();        // Standard mapping: Start
   if(rising(8))selectAsTouch();    // Standard mapping: Back/Select
   lastButtons[i]=(pad.buttons||[]).map(b=>!!b.pressed);
  }
  requestAnimationFrame(pollGamepads);
 }
 function start(){ensureChrome();document.addEventListener('keydown',keydown,true);requestAnimationFrame(pollGamepads)}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.RistPagedShell={page,home,end,selectAsTouch};
})();
