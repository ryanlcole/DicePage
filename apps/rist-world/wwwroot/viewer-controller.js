(()=>{
 const closeClass='map-viewer-close';
 let viewerResizeObserver=null;
 let bulletinMenuOpen=false;
 let bulletinBound=false;

 function clickButton(selector){
  const button=document.querySelector(selector);
  if(button){button.click();return true;}
  return false;
 }

 function closeTarget(target){
  if(target.matches('.root-menu-panel'))return clickButton('#header-slider .root-menu-button.active[aria-expanded="true"]');
  if(target.matches('.release-action-menu.save-menu'))return clickButton('#header-slider .root-menu-button[aria-label="Save and export"]');
  if(target.matches('.release-action-menu.load-menu'))return clickButton('#header-slider .root-menu-button[aria-label="Load"]');
  if(target.matches('#card-library'))return clickButton('#header-slider .root-menu-button[aria-label="Cards"]');
  if(target.matches('.asset-slider-stack'))return clickButton('#header-slider .root-menu-button[aria-label="Browse asset library"]');
  if(target.matches('.rist-tutorial-shell')){
   const skip=[...target.querySelectorAll('button')].find(button=>/skip tutorial|close/i.test(button.textContent||''));
   if(skip){skip.click();return true;}
  }
  return false;
 }

 function addClose(target){
  if(!target||target.querySelector(`:scope > .${closeClass}`))return;
  const button=document.createElement('button');
  button.type='button';
  button.className=closeClass;
  button.setAttribute('aria-label','Close');
  button.title='Close';
  button.textContent='×';
  button.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();closeTarget(target);});
  target.prepend(button);
 }

 function ensureSquareGridAuthority(){
  if(document.getElementById('rist-viewer-square-grid-authority'))return;
  const style=document.createElement('style');
  style.id='rist-viewer-square-grid-authority';
  style.textContent=`.rist.release-world .map:has(.grid.square)::before{background-size:var(--rist-viewer-square-cell,64px) var(--rist-viewer-square-cell,64px)!important;}`;
  document.head.appendChild(style);
 }

 function updateSquareCellSize(map){
  if(!map)return;
  const rect=map.getBoundingClientRect();
  if(rect.width<2||rect.height<2)return;
  const cell=Math.max(24,Math.round(Math.min(rect.width,rect.height)/10));
  map.style.setProperty('--rist-viewer-square-cell',`${cell}px`);
 }

 function fixViewer(){
  const shell=document.querySelector('.release-map-region .map-shell');
  const map=shell?.querySelector(':scope > .map');
  const stage=map?.querySelector(':scope > .world-stage');
  if(!shell||!map)return;
  const important=(el,name,value)=>el.style.setProperty(name,value,'important');
  for(const [name,value] of Object.entries({'box-sizing':'border-box','grid-column':'2','grid-row':'2','position':'relative','width':'100%','height':'100%','min-width':'0','min-height':'0','max-width':'none','max-height':'none','aspect-ratio':'auto','margin':'0','overflow':'hidden'}))important(map,name,value);
  if(stage)for(const [name,value] of Object.entries({'position':'absolute','inset':'0','width':'100%','height':'100%','min-width':'0','min-height':'0','max-width':'none','max-height':'none','aspect-ratio':'auto'}))important(stage,name,value);
  ensureSquareGridAuthority();
  updateSquareCellSize(map);
  if(!viewerResizeObserver)viewerResizeObserver=new ResizeObserver(entries=>{for(const entry of entries)if(entry.target.matches?.('.release-map-region .map-shell>.map'))updateSquareCellSize(entry.target);});
  if(!map.dataset.viewerSquareObserved){map.dataset.viewerSquareObserved='1';viewerResizeObserver.observe(map);}
 }

 function ensureBulletinStyle(){
  if(document.getElementById('rist-bulletin-authority'))return;
  const style=document.createElement('style');
  style.id='rist-bulletin-authority';
  style.textContent=`
   .world-context-track{position:relative!important;overflow:hidden!important;display:block!important;}
   .world-context-track>.bulletin-flow{position:absolute!important;inset:0 auto 0 0!important;display:flex!important;align-items:center!important;gap:4px!important;width:max-content!important;min-width:max-content!important;will-change:transform!important;animation:ristBulletinFlow 28s linear infinite!important;}
   .world-context-track:hover>.bulletin-flow,.world-context-track:focus-within>.bulletin-flow{animation-play-state:paused!important;}
   .world-context-track.menu-open>.bulletin-flow{display:none!important;}
   .world-context-track>.bulletin-menu-track{position:absolute!important;inset:0!important;display:none!important;align-items:center!important;gap:4px!important;overflow-x:auto!important;overflow-y:hidden!important;scrollbar-width:none!important;-webkit-overflow-scrolling:touch!important;}
   .world-context-track.menu-open>.bulletin-menu-track{display:flex!important;}
   .world-context-track>.bulletin-menu-track::-webkit-scrollbar{display:none!important;}
   .world-context-track>.bulletin-menu-track>.root-menu-button{flex:0 0 auto!important;height:22px!important;min-height:22px!important;max-height:22px!important;margin:0!important;padding:0 9px!important;}
   @keyframes ristBulletinFlow{from{transform:translateX(0)}to{transform:translateX(-50%)}}
   @media (orientation:portrait){
    .rist.release-world>.release-world-shell{grid-template-rows:var(--rist-assets-h) minmax(0,1fr) var(--rist-assets-h) var(--rist-footer-h)!important;}
    .rist.release-world .release-menu-region{display:none!important;}
    .rist.release-world .release-public-region{grid-row:1!important;}
    .rist.release-world .release-map-region{grid-row:2!important;}
    .rist.release-world .release-private-region{grid-row:3!important;}
    .rist.release-world .release-footer-region{grid-row:4!important;}
   }
  `;
  document.head.appendChild(style);
 }

 function buildBulletinFlow(track){
  if(track.querySelector(':scope>.bulletin-flow'))return;
  const originals=[...track.children];
  const flow=document.createElement('div');
  flow.className='bulletin-flow';
  originals.forEach(el=>flow.appendChild(el));
  [...flow.children].map(el=>el.cloneNode(true)).forEach(el=>{el.setAttribute('aria-hidden','true');el.querySelectorAll?.('[id]').forEach(x=>x.removeAttribute('id'));flow.appendChild(el);});
  track.appendChild(flow);
 }

 function rebuildMenuTrack(track,source){
  let menuTrack=track.querySelector(':scope>.bulletin-menu-track');
  if(!menuTrack){menuTrack=document.createElement('div');menuTrack.className='bulletin-menu-track';track.appendChild(menuTrack);}
  if(!bulletinMenuOpen)return;
  const originals=[...source.children].filter(el=>!el.classList.contains('door-button'));
  menuTrack.replaceChildren(...originals.map(el=>el.cloneNode(true)));
  [...menuTrack.children].forEach((clone,index)=>clone.addEventListener('click',event=>{event.preventDefault();originals[index]?.click();}));
 }

 function syncBulletinMenu(){
  const track=document.querySelector('.world-context-track');
  const source=document.querySelector('#header-slider .release-root-track');
  const button=document.querySelector('.world-context-menu');
  if(!track||!source||!button)return;
  track.classList.toggle('menu-open',bulletinMenuOpen);
  button.classList.toggle('active',bulletinMenuOpen);
  button.setAttribute('aria-pressed',String(bulletinMenuOpen));
  rebuildMenuTrack(track,source);
 }

 function bindBulletin(){
  ensureBulletinStyle();
  const track=document.querySelector('.world-context-track');
  const button=document.querySelector('.world-context-menu');
  if(!track||!button)return;
  buildBulletinFlow(track);
  if(!bulletinBound){
   bulletinBound=true;
   button.addEventListener('click',event=>{
    event.preventDefault();
    event.stopImmediatePropagation();
    bulletinMenuOpen=!bulletinMenuOpen;
    syncBulletinMenu();
    requestAnimationFrame(fixViewer);
   },true);
  }
  syncBulletinMenu();
 }

 function reclaimPortraitMenuSpace(){
  if(!matchMedia('(orientation:portrait)').matches)return;
  const shell=document.querySelector('.rist.release-world>.release-world-shell');
  const menu=document.querySelector('.release-menu-region');
  const pub=document.querySelector('.release-public-region');
  const map=document.querySelector('.release-map-region');
  const priv=document.querySelector('.release-private-region');
  const footer=document.querySelector('.release-footer-region');
  if(!shell||!menu||!pub||!map||!priv||!footer)return;
  shell.style.setProperty('grid-template-rows','var(--rist-assets-h) minmax(0,1fr) var(--rist-assets-h) var(--rist-footer-h)','important');
  menu.style.setProperty('display','none','important');
  pub.style.setProperty('grid-row','1','important');
  map.style.setProperty('grid-row','2','important');
  priv.style.setProperty('grid-row','3','important');
  footer.style.setProperty('grid-row','4','important');
 }

 function enhance(){
  document.querySelectorAll('.root-menu-panel,.release-action-menu,#card-library,.asset-slider-stack,.rist-tutorial-shell').forEach(addClose);
  bindBulletin();
  reclaimPortraitMenuSpace();
  fixViewer();
 }

 let queued=false;
 function queue(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;enhance();});}
 function start(){enhance();new MutationObserver(queue).observe(document.body,{childList:true,subtree:true});window.addEventListener('resize',queue,{passive:true});window.addEventListener('orientationchange',()=>setTimeout(queue,100),{passive:true});}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
