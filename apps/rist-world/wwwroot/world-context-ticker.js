(()=>{
 'use strict';
 let timer=0,observer=null;
 const pad=value=>String(value).padStart(2,'0');
 const legacyPopouts=[
  '.world-context-dialog','.world-context-popover','.world-context-popup',
  '.rist-world-context-dialog','.rist-world-context-popover','.rist-world-context-popup',
  '[data-world-context-dialog]','[data-world-context-popover]','[data-world-context-popup]'
 ].join(',');
 function removeLegacyPopouts(){document.querySelectorAll(legacyPopouts).forEach(node=>node.remove())}
 function textOnly(node){
  if(!(node instanceof HTMLButtonElement))return node;
  const span=document.createElement('span');
  span.className=node.className;
  for(const attr of node.attributes){if(attr.name.startsWith('data-'))span.setAttribute(attr.name,attr.value)}
  span.innerHTML=node.innerHTML;
  node.replaceWith(span);
  return span;
 }
 function makeHeaderTickerOnly(){
  const strip=document.querySelector('.world-context-strip');
  if(!strip)return;
  strip.querySelector('.world-context-menu')?.remove();
  strip.querySelector('.world-context-login')?.remove();
  strip.querySelectorAll('.world-context-action,.world-context-utc').forEach(textOnly);
  const track=strip.querySelector('.world-context-track');
  if(track){
   track.setAttribute('aria-label','Toggle Start Menu');
   track.setAttribute('role','button');
   track.tabIndex=0;
   if(!track.querySelector('[data-start-menu-label]')){
    const label=document.createElement('span');
    label.className='world-context-readout world-context-start-menu';
    label.dataset.startMenuLabel='1';
    label.innerHTML='<strong>Start Menu</strong>';
    track.appendChild(label);
   }
  }
  strip.style.gridTemplateColumns='minmax(0,1fr)';
  strip.style.position='relative';
  strip.style.zIndex='2147480000';
  strip.setAttribute('data-start-menu-authority','1');
  removeLegacyPopouts();
 }
 function toggleStart(event){
  const strip=event.target instanceof Element?event.target.closest('.world-context-strip'):null;
  if(!strip)return;
  if(event.type==='keydown'&&event.key!=='Enter'&&event.key!==' ')return;
  event.preventDefault();event.stopPropagation();event.stopImmediatePropagation?.();
  const overlay=document.querySelector('.rist-start-overlay');
  const open=overlay&&!overlay.hidden;
  if(open)window.RistStartMenu?.close?.();
  else window.RistStartMenu?.open?.();
 }
 function tick(){
  makeHeaderTickerOnly();
  const now=new Date();
  const date=document.querySelector('.world-context-date time');
  const utc=document.querySelector('.world-context-utc time');
  if(date){const value=`${pad(now.getMonth()+1)}/${pad(now.getDate())}/${now.getFullYear()}`;if(date.textContent!==value)date.textContent=value;}
  if(utc){const value=`${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())}:${pad(now.getUTCSeconds())}`;if(utc.textContent!==value)utc.textContent=value;}
 }
 function start(){
  tick();if(!timer)timer=setInterval(tick,1000);
  document.addEventListener('click',toggleStart,true);
  document.addEventListener('keydown',toggleStart,true);
  if(!observer){observer=new MutationObserver(()=>{makeHeaderTickerOnly();removeLegacyPopouts()});observer.observe(document.body,{childList:true,subtree:true})}
 }
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)tick()});
 document.addEventListener('rist:game-start',tick);
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.RistWorldContext={edit:()=>{},openClock:()=>{},close:()=>{removeLegacyPopouts()}};
 window.RistWorldTicker={tick};
})();
