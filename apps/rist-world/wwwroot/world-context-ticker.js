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
 function makeHeaderStartOnly(){
  const strip=document.querySelector('.world-context-strip');
  if(!strip)return;
  textOnly(strip.querySelector('.world-context-menu'));
  strip.querySelectorAll('.world-context-action,.world-context-utc').forEach(textOnly);
  const track=strip.querySelector('.world-context-track');
  if(track){track.setAttribute('aria-label','Open Start Menu');track.setAttribute('role','button');track.tabIndex=0}
  strip.setAttribute('data-start-menu-authority','1');
  removeLegacyPopouts();
 }
 function openStart(event){
  const strip=event.target instanceof Element?event.target.closest('.world-context-strip'):null;
  if(!strip)return;
  if(event.target instanceof Element&&event.target.closest('.world-context-login'))return;
  if(event.type==='keydown'&&event.key!=='Enter'&&event.key!==' ')return;
  event.preventDefault();event.stopPropagation();event.stopImmediatePropagation?.();
  window.RistStartMenu?.open?.();
 }
 function tick(){
  makeHeaderStartOnly();
  const now=new Date();
  const date=document.querySelector('.world-context-date time');
  const utc=document.querySelector('.world-context-utc time');
  if(date){const value=`${pad(now.getMonth()+1)}/${pad(now.getDate())}/${now.getFullYear()}`;if(date.textContent!==value)date.textContent=value;}
  if(utc){const value=`${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())}:${pad(now.getUTCSeconds())}`;if(utc.textContent!==value)utc.textContent=value;}
 }
 function start(){
  tick();if(!timer)timer=setInterval(tick,1000);
  document.addEventListener('click',openStart,true);
  document.addEventListener('keydown',openStart,true);
  if(!observer){observer=new MutationObserver(()=>{makeHeaderStartOnly();removeLegacyPopouts()});observer.observe(document.body,{childList:true,subtree:true})}
 }
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)tick()});
 document.addEventListener('rist:game-start',tick);
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.RistWorldContext={edit:()=>{},openClock:()=>{},close:()=>{removeLegacyPopouts()}};
 window.RistWorldTicker={tick};
})();
