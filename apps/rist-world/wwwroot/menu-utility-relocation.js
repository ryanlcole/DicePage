(()=>{
 'use strict';
 const labels=['login','log in','settings','about'];
 const norm=v=>String(v||'').replace(/\s+/g,' ').trim().toLowerCase();
 const nameOf=el=>norm(el.getAttribute('aria-label')||el.getAttribute('title')||el.textContent);
 const isTarget=el=>{
  const name=nameOf(el);
  return labels.some(label=>name===label||name.startsWith(label+' '));
 };
 function targetRail(){return document.querySelector('.rist-section-list')}
 function plusButton(rail){return rail?.querySelector('button[data-section="add"],button[aria-label*="add" i],button[title*="add" i]')||null}
 function topCandidates(){
  const scopes=['#header-slider','.header-circular-set','.root-menu','.top-menu','.rist-top-menu'];
  const found=[];
  for(const scope of scopes){
   document.querySelectorAll(`${scope} button,${scope} [role="button"],${scope} a`).forEach(el=>{if(isTarget(el)&&!found.includes(el))found.push(el)})
  }
  return found;
 }
 function move(){
  const rail=targetRail();if(!rail)return;
  const plus=plusButton(rail);let anchor=plus;
  for(const el of topCandidates()){
   if(el.closest('.rist-section-list'))continue;
   el.classList.add('rist-section-utility');
   el.dataset.ristUtilityRelocated='1';
   if(anchor?.parentElement===rail){anchor.insertAdjacentElement('afterend',el)}else rail.appendChild(el);
   anchor=el;
  }
 }
 let queued=false;
 const schedule=()=>{if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;move()})};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',move,{once:true});else move();
 new MutationObserver(schedule).observe(document.documentElement,{childList:true,subtree:true});
})();
