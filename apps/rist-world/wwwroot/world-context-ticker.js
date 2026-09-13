(()=>{
 'use strict';
 let timer=0,marqueeFrame=0,lastMarqueeTime=0;
 const footerTickerDurationMs=34000;
 const footerTickerFont='900 7px/19px system-ui,-apple-system,sans-serif';
 const footerTickerLetterSpacing='.08em';
 const reducedMotion=()=>window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches===true;
 const pad=value=>String(value).padStart(2,'0');
 const legacyPopouts=[
  '.world-context-dialog','.world-context-popover','.world-context-popup',
  '.rist-world-context-dialog','.rist-world-context-popover','.rist-world-context-popup',
  '[data-world-context-dialog]','[data-world-context-popover]','[data-world-context-popup]'
 ].join(',');
 function removeLegacyPopouts(){document.querySelectorAll(legacyPopouts).forEach(node=>node.remove())}
 function applyFooterTickerTypography(node){
  if(!(node instanceof HTMLElement))return;
  node.style.setProperty('font',footerTickerFont,'important');
  node.style.setProperty('letter-spacing',footerTickerLetterSpacing,'important');
  node.querySelectorAll('*').forEach(child=>{
   if(!(child instanceof HTMLElement))return;
   child.style.setProperty('font','inherit','important');
   child.style.setProperty('letter-spacing','inherit','important');
  });
 }
 function textOnly(node){
  if(!(node instanceof HTMLButtonElement))return node;
  const span=document.createElement('span');
  span.className=node.className;
  for(const attr of node.attributes){if(attr.name.startsWith('data-'))span.setAttribute(attr.name,attr.value)}
  span.innerHTML=node.innerHTML;
  node.replaceWith(span);
  return span;
 }
 function prepareItem(node){
  node.style.flex='0 0 auto';
  node.style.whiteSpace='nowrap';
  node.style.minWidth='max-content';
  applyFooterTickerTypography(node);
 }
 function buildLoop(track){
  if(track.dataset.tickerLoopReady==='2')return;
  const existing=[...track.children];
  const raw=existing.some(node=>node.matches?.('[data-ticker-group]'))
   ? [...(track.querySelector('[data-ticker-group="a"]')?.children||[])]
   : existing.filter(node=>!node.matches?.('[data-ticker-clone="1"]'));
  if(!raw.length)return;

  const groupA=document.createElement('span');
  groupA.dataset.tickerGroup='a';
  groupA.className='world-context-loop-group';
  const groupB=document.createElement('span');
  groupB.dataset.tickerGroup='b';
  groupB.className='world-context-loop-group';
  groupB.setAttribute('aria-hidden','true');
  groupB.style.pointerEvents='none';

  for(const node of raw){
   prepareItem(node);
   groupA.appendChild(node);
   const clone=node.cloneNode(true);
   clone.dataset.tickerClone='1';
   clone.removeAttribute('id');
   prepareItem(clone);
   groupB.appendChild(clone);
  }
  for(const group of [groupA,groupB]){
   group.style.display='inline-flex';
   group.style.alignItems='center';
   group.style.gap='8px';
   group.style.flex='0 0 auto';
   group.style.width='max-content';
   group.style.minWidth='max-content';
   group.style.whiteSpace='nowrap';
   group.style.paddingRight='8px';
   applyFooterTickerTypography(group);
  }
  track.replaceChildren(groupA,groupB);
  track.dataset.tickerLoopReady='2';
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
   track.style.display='flex';
   track.style.alignItems='center';
   track.style.gap='0';
   track.style.width='100%';
   track.style.minWidth='0';
   track.style.overflowX='hidden';
   track.style.overflowY='hidden';
   track.style.whiteSpace='nowrap';
   track.style.scrollBehavior='auto';
   track.style.scrollbarWidth='none';
   track.style.webkitOverflowScrolling='touch';
   applyFooterTickerTypography(track);
   if(!track.querySelector('[data-start-menu-label]:not([data-ticker-clone="1"])')){
    const target=track.querySelector('[data-ticker-group="a"]')||track;
    const label=document.createElement('span');
    label.className='world-context-readout world-context-start-menu';
    label.dataset.startMenuLabel='1';
    label.innerHTML='<strong>Start Menu</strong>';
    prepareItem(label);
    target.appendChild(label);
    track.dataset.tickerLoopReady='0';
   }
   buildLoop(track);
  }
  strip.style.gridTemplateColumns='minmax(0,1fr)';
  strip.style.position='relative';
  strip.style.zIndex='2147480000';
  strip.style.overflow='hidden';
  strip.style.setProperty('font',footerTickerFont,'important');
  strip.style.setProperty('letter-spacing',footerTickerLetterSpacing,'important');
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
  const dateValue=`${pad(now.getMonth()+1)}/${pad(now.getDate())}/${now.getFullYear()}`;
  const utcValue=`${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())}:${pad(now.getUTCSeconds())}`;
  document.querySelectorAll('.world-context-date time').forEach(node=>{if(node.textContent!==dateValue)node.textContent=dateValue;});
  document.querySelectorAll('.world-context-utc time').forEach(node=>{if(node.textContent!==utcValue)node.textContent=utcValue;});
 }
 function loopBoundary(track){
  const groupB=track.querySelector('[data-ticker-group="b"]');
  return groupB?groupB.offsetLeft:0;
 }
 function marquee(now){
  const track=document.querySelector('.world-context-track');
  const boundary=track?loopBoundary(track):0;
  if(track&&!document.hidden&&!reducedMotion()&&boundary>0&&track.scrollWidth>track.clientWidth){
   if(lastMarqueeTime){
    const delta=Math.min(50,now-lastMarqueeTime);
    track.scrollLeft+=delta*(boundary/footerTickerDurationMs);
    if(track.scrollLeft>=boundary)track.scrollLeft-=boundary;
   }
  }else if(track&&track.scrollLeft!==0){track.scrollLeft=0;}
  lastMarqueeTime=now;
  marqueeFrame=requestAnimationFrame(marquee);
 }
 function start(){
  tick();
  if(!timer)timer=setInterval(tick,1000);
  document.addEventListener('click',toggleStart,true);
  document.addEventListener('keydown',toggleStart,true);
  if(!marqueeFrame)marqueeFrame=requestAnimationFrame(marquee);
 }
 document.addEventListener('visibilitychange',()=>{if(!document.hidden){lastMarqueeTime=0;tick()}});
 document.addEventListener('rist:game-start',tick);
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.RistWorldContext={edit:()=>{},openClock:()=>{},close:()=>{removeLegacyPopouts()}};
 window.RistWorldTicker={tick};
})();