(()=>{
 'use strict';
 let timer=0;
 const pad=value=>String(value).padStart(2,'0');
 function openStartMenu(event){
  event?.preventDefault?.();
  event?.stopPropagation?.();
  event?.stopImmediatePropagation?.();
  window.RistStartMenu?.open?.();
 }
 function makeTickerChildrenPresentationOnly(track){
  track.querySelectorAll('.world-context-action,.world-context-utc').forEach(el=>{
   el.setAttribute('tabindex','-1');
   el.setAttribute('aria-hidden','true');
   el.style.pointerEvents='none';
  });
 }
 function ensureStartMenuLabel(){
  const track=document.querySelector('.world-context-track');
  if(!track)return;
  track.setAttribute('role','button');
  track.setAttribute('tabindex','0');
  track.setAttribute('aria-label','Open Start Menu');
  if(track.dataset.startMenuBound!=='1'){
   track.dataset.startMenuBound='1';
   track.addEventListener('click',openStartMenu,true);
   track.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){openStartMenu(event)}},true);
  }
  const utcNodes=[...track.querySelectorAll('.world-context-utc')];
  for(const utc of utcNodes){
   const next=utc.nextElementSibling;
   if(next?.classList?.contains('world-context-start-menu'))continue;
   const label=document.createElement('span');
   label.className='world-context-readout world-context-start-menu';
   label.textContent='Start Menu';
   label.setAttribute('aria-hidden','true');
   utc.insertAdjacentElement('afterend',label);
  }
  makeTickerChildrenPresentationOnly(track);
 }
 function tick(){
  const now=new Date();
  const date=document.querySelector('.world-context-date time');
  const utc=document.querySelector('.world-context-utc time');
  if(date){const value=`${pad(now.getMonth()+1)}/${pad(now.getDate())}/${now.getFullYear()}`;if(date.textContent!==value)date.textContent=value;}
  if(utc){const value=`${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())}:${pad(now.getUTCSeconds())}`;if(utc.textContent!==value)utc.textContent=value;}
  ensureStartMenuLabel();
 }
 function start(){tick();if(!timer)timer=setInterval(tick,1000)}
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)tick()});
 document.addEventListener('rist:game-start',tick);
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.RistWorldTicker={tick};
})();
