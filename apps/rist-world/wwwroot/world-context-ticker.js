(()=>{
 'use strict';
 let timer=0,observer=null,marqueeFrame=0,lastMarqueeTime=0,syncing=false;
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
 function rebuildLoop(track){
  if(syncing)return;
  syncing=true;
  try{
   track.querySelectorAll('[data-ticker-clone="1"]').forEach(node=>node.remove());
   const originals=[...track.children];
   originals.forEach(node=>{
    const clone=node.cloneNode(true);
    clone.dataset.tickerClone='1';
    clone.setAttribute('aria-hidden','true');
    clone.removeAttribute('id');
    clone.style.pointerEvents='none';
    track.appendChild(clone);
   });
  }finally{syncing=false;}
 }
 function makeHeaderTickerOnly(){
  if(syncing)return;
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
   track.style.display='flex';
   track.style.alignItems='center';
   track.style.gap='8px';
   track.style.width='100%';
   track.style.minWidth='0';
   track.style.overflowX='hidden';
   track.style.overflowY='hidden';
   track.style.whiteSpace='nowrap';
   track.style.scrollBehavior='auto';
   track.style.scrollbarWidth='none';
   track.style.webkitOverflowScrolling='touch';
   if(!track.querySelector('[data-start-menu-label]:not([data-ticker-clone="1"])')){
    const label=document.createElement('span');
    label.className='world-context-readout world-context-start-menu';
    label.dataset.startMenuLabel='1';
    label.innerHTML='<strong>Start Menu</strong>';
    track.appendChild(label);
   }
   rebuildLoop(track);
  }
  strip.style.gridTemplateColumns='minmax(0,1fr)';
  strip.style.position='relative';
  strip.style.zIndex='2147480000';
  strip.style.overflow='hidden';
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
  const now=new Date();
  const date=document.querySelector('.world-context-date:not([data-ticker-clone="1"]) time');
  const utc=document.querySelector('.world-context-utc:not([data-ticker-clone="1"]) time');
  if(date){const value=`${pad(now.getMonth()+1)}/${pad(now.getDate())}/${now.getFullYear()}`;if(date.textContent!==value)date.textContent=value;}
  if(utc){const value=`${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())}:${pad(now.getUTCSeconds())}`;if(utc.textContent!==value)utc.textContent=value;}
  makeHeaderTickerOnly();
 }
 function loopBoundary(track){
  const firstClone=track.querySelector('[data-ticker-clone="1"]');
  return firstClone?firstClone.offsetLeft:0;
 }
 function marquee(now){
  const track=document.querySelector('.world-context-track');
  if(track&&!document.hidden&&track.scrollWidth>track.clientWidth){
   if(lastMarqueeTime){
    const delta=Math.min(50,now-lastMarqueeTime);
    track.scrollLeft+=delta*0.035;
    const boundary=loopBoundary(track);
    if(boundary>0&&track.scrollLeft>=boundary)track.scrollLeft-=boundary;
   }
  }else if(track&&track.scrollLeft!==0){track.scrollLeft=0;}
  lastMarqueeTime=now;
  marqueeFrame=requestAnimationFrame(marquee);
 }
 function start(){
  tick();if(!timer)timer=setInterval(tick,1000);
  document.addEventListener('click',toggleStart,true);
  document.addEventListener('keydown',toggleStart,true);
  if(!observer){observer=new MutationObserver(()=>{if(!syncing){makeHeaderTickerOnly();removeLegacyPopouts()}});observer.observe(document.body,{childList:true,subtree:true})}
  if(!marqueeFrame)marqueeFrame=requestAnimationFrame(marquee);
 }
 document.addEventListener('visibilitychange',()=>{if(!document.hidden){lastMarqueeTime=0;tick()}});
 document.addEventListener('rist:game-start',tick);
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.RistWorldContext={edit:()=>{},openClock:()=>{},close:()=>{removeLegacyPopouts()}};
 window.RistWorldTicker={tick};
})();
