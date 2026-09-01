(()=>{
 const closeClass='map-viewer-close';
 let viewerResizeObserver=null;

 function clickButton(selector){const button=document.querySelector(selector);if(button){button.click();return true;}return false;}
 function closeTarget(target){
  if(target.matches('.root-menu-panel'))return clickButton('#header-slider .root-menu-button.active[aria-expanded="true"]');
  if(target.matches('.release-action-menu.save-menu'))return clickButton('#header-slider .root-menu-button[aria-label="Save and export"]');
  if(target.matches('.release-action-menu.load-menu'))return clickButton('#header-slider .root-menu-button[aria-label="Load"]');
  if(target.matches('#card-library'))return clickButton('#header-slider .root-menu-button[aria-label="Cards"]');
  if(target.matches('.asset-slider-stack'))return clickButton('#header-slider .root-menu-button[aria-label="Browse asset library"]');
  if(target.matches('.rist-tutorial-shell')){const skip=[...target.querySelectorAll('button')].find(button=>/skip tutorial|close/i.test(button.textContent||''));if(skip){skip.click();return true;}}
  return false;
 }
 function addClose(target){if(!target||target.querySelector(`:scope > .${closeClass}`))return;const button=document.createElement('button');button.type='button';button.className=closeClass;button.setAttribute('aria-label','Close');button.title='Close';button.textContent='×';button.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();closeTarget(target);});target.prepend(button);}

 function ensureSquareGridAuthority(){if(document.getElementById('rist-viewer-square-grid-authority'))return;const style=document.createElement('style');style.id='rist-viewer-square-grid-authority';style.textContent=`.rist.release-world .map:has(.grid.square)::before{background-size:var(--rist-viewer-square-cell,64px) var(--rist-viewer-square-cell,64px)!important;}`;document.head.appendChild(style);}
 function updateSquareCellSize(map){if(!map)return;const rect=map.getBoundingClientRect();if(rect.width<2||rect.height<2)return;const cell=Math.max(24,Math.round(Math.min(rect.width,rect.height)/10));map.style.setProperty('--rist-viewer-square-cell',`${cell}px`);}
 function fixViewer(){
  const shell=document.querySelector('.release-map-region .map-shell');const map=shell?.querySelector(':scope > .map');const stage=map?.querySelector(':scope > .world-stage');if(!shell||!map)return;const important=(el,name,value)=>el.style.setProperty(name,value,'important');
  for(const [name,value] of Object.entries({'box-sizing':'border-box','grid-column':'2','grid-row':'2','position':'relative','width':'100%','height':'100%','min-width':'0','min-height':'0','max-width':'none','max-height':'none','aspect-ratio':'auto','margin':'0','overflow':'hidden'}))important(map,name,value);
  if(stage)for(const [name,value] of Object.entries({'position':'absolute','inset':'0','width':'100%','height':'100%','min-width':'0','min-height':'0','max-width':'none','max-height':'none','aspect-ratio':'auto'}))important(stage,name,value);
  ensureSquareGridAuthority();updateSquareCellSize(map);
  if(!viewerResizeObserver)viewerResizeObserver=new ResizeObserver(entries=>{for(const entry of entries)if(entry.target.matches?.('.release-map-region .map-shell>.map'))updateSquareCellSize(entry.target);});
  if(!map.dataset.viewerSquareObserved){map.dataset.viewerSquareObserved='1';viewerResizeObserver.observe(map);}
 }

 function ensureBulletinStyle(){
  if(document.getElementById('rist-bulletin-authority'))return;
  const style=document.createElement('style');style.id='rist-bulletin-authority';style.textContent=`
   .world-context-strip{box-sizing:border-box!important;position:relative!important;display:grid!important;grid-template-columns:10% 80% 10%!important;width:100%!important;max-width:100vw!important;padding:0!important;gap:0!important;overflow:hidden!important;}
   .world-context-menu{box-sizing:border-box!important;position:static!important;grid-column:1!important;justify-self:start!important;align-self:center!important;max-width:100%!important;transform:none!important;z-index:30!important;}
   .world-context-track{box-sizing:border-box!important;position:relative!important;grid-column:2!important;width:100%!important;min-width:0!important;max-width:100%!important;height:100%!important;overflow:hidden!important;contain:layout paint!important;z-index:10!important;}
   .world-context-login{box-sizing:border-box!important;position:static!important;grid-column:3!important;justify-self:end!important;align-self:center!important;max-width:100%!important;transform:none!important;z-index:30!important;background:#111920!important;}
   .world-context-track>.bulletin-flow{position:absolute!important;inset:0 auto 0 0!important;display:flex!important;align-items:center!important;gap:18px!important;width:max-content!important;min-width:max-content!important;max-width:none!important;white-space:nowrap!important;will-change:transform!important;animation:ristBulletinFlow 34s linear infinite!important;}
   .world-context-track>.bulletin-flow>*{box-sizing:border-box!important;flex:0 0 auto!important;width:auto!important;min-width:max-content!important;max-width:none!important;white-space:nowrap!important;overflow:visible!important;}
   .world-context-track:hover>.bulletin-flow,.world-context-track:focus-within>.bulletin-flow{animation-play-state:paused!important;}
   @keyframes ristBulletinFlow{from{transform:translateX(0)}to{transform:translateX(-50%)}}

   .rist.release-world>.release-world-shell{grid-template-rows:var(--rist-assets-h) minmax(0,1fr) var(--rist-assets-h) var(--rist-footer-h)!important;}
   .rist.release-world .release-menu-region{box-sizing:border-box!important;position:fixed!important;left:0!important;right:0!important;top:42px!important;width:100vw!important;height:42px!important;min-width:0!important;min-height:42px!important;max-width:100vw!important;max-height:42px!important;margin:0!important;padding:0!important;overflow:visible!important;z-index:2147483000!important;pointer-events:none!important;opacity:0!important;transform:translateY(-115%)!important;transition:transform .18s ease-out,opacity .12s linear!important;background:#05090cf7!important;border-bottom:1px solid #725d30!important;}
   .rist.release-world .release-menu-region.rist-os-menu-open{pointer-events:auto!important;opacity:1!important;transform:translateY(0)!important;}
   .rist.release-world .release-menu-region>#header-slider{box-sizing:border-box!important;position:relative!important;inset:auto!important;width:100%!important;height:42px!important;min-height:42px!important;max-height:42px!important;margin:0!important;overflow:visible!important;z-index:1!important;}
   .rist.release-world .release-menu-region #header-slider .release-root-track{box-sizing:border-box!important;height:42px!important;min-height:42px!important;max-height:42px!important;display:flex!important;align-items:center!important;overflow-x:auto!important;overflow-y:hidden!important;scrollbar-width:none!important;pointer-events:auto!important;}
   .rist.release-world .release-menu-region #header-slider .release-root-track::-webkit-scrollbar{display:none!important;}
   .rist.release-world .release-menu-region #header-slider>.rail-scroll-arrow{pointer-events:auto!important;z-index:5!important;}
   .rist.release-world .release-menu-region .root-menu-panel,.rist.release-world .release-menu-region .release-action-menu{z-index:2147483001!important;pointer-events:auto!important;}

   .rist.release-world .release-public-region{grid-row:1!important;grid-column:1!important;}
   .rist.release-world .release-map-region{grid-row:2!important;grid-column:1!important;}
   .rist.release-world .release-private-region{grid-row:3!important;grid-column:1!important;}
   .rist.release-world .release-footer-region{grid-row:4!important;grid-column:1!important;}
   @media (orientation:landscape){
    .rist.release-world>.release-world-shell{grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;grid-template-rows:minmax(0,1fr) 70px 84px!important;}
    .rist.release-world .release-map-region{grid-column:1/-1!important;grid-row:1!important;}
    .rist.release-world .release-public-region{grid-column:1/-1!important;grid-row:2!important;}
    .rist.release-world .release-footer-region{grid-column:1!important;grid-row:3!important;}
    .rist.release-world .release-private-region{grid-column:2!important;grid-row:3!important;}
   }
  `;document.head.appendChild(style);
 }
 function buildBulletinFlow(track){
  if(track.querySelector(':scope>.bulletin-flow'))return;
  const originals=[...track.children];const flow=document.createElement('div');flow.className='bulletin-flow';originals.forEach(el=>flow.appendChild(el));
  [...flow.children].map(el=>el.cloneNode(true)).forEach(el=>{el.setAttribute('aria-hidden','true');flow.appendChild(el);});track.appendChild(flow);
 }
 function syncOsMenu(){
  ensureBulletinStyle();
  const track=document.querySelector('.world-context-track');const button=document.querySelector('.world-context-menu');const region=document.querySelector('.release-menu-region');if(!track||!button||!region)return;
  buildBulletinFlow(track);
  const open=button.getAttribute('aria-pressed')==='true';
  region.classList.toggle('rist-os-menu-open',open);
  requestAnimationFrame(fixViewer);
 }
 function enhance(){document.querySelectorAll('.root-menu-panel,.release-action-menu,#card-library,.asset-slider-stack,.rist-tutorial-shell').forEach(addClose);syncOsMenu();fixViewer();}
 let queued=false;function queue(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;enhance();});}
 function start(){enhance();new MutationObserver(queue).observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['aria-pressed']});window.addEventListener('resize',queue,{passive:true});window.addEventListener('orientationchange',()=>setTimeout(queue,100),{passive:true});}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
