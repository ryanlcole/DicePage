(()=>{
 const closeClass='map-viewer-close';
 let viewerResizeObserver=null;

 function clickButton(selector){
  const button=document.querySelector(selector);
  if(button){button.click();return true;}
  return false;
 }

 function closeTarget(target){
  if(target.matches('.root-menu-panel')){
   return clickButton('#header-slider .root-menu-button.active[aria-expanded="true"]');
  }
  if(target.matches('.release-action-menu.save-menu')){
   return clickButton('#header-slider .root-menu-button[aria-label="Save and export"]');
  }
  if(target.matches('.release-action-menu.load-menu')){
   return clickButton('#header-slider .root-menu-button[aria-label="Load"]');
  }
  if(target.matches('#card-library')){
   return clickButton('#header-slider .root-menu-button[aria-label="Cards"]');
  }
  if(target.matches('.asset-slider-stack')){
   return clickButton('#header-slider .root-menu-button[aria-label="Browse asset library"]');
  }
  if(target.matches('.rist-tutorial-shell')){
   const buttons=[...target.querySelectorAll('button')];
   const skip=buttons.find(button=>/skip tutorial|close/i.test(button.textContent||''));
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
  button.addEventListener('click',event=>{
   event.preventDefault();
   event.stopPropagation();
   closeTarget(target);
  });
  target.prepend(button);
 }

 function ensureSquareGridAuthority(){
  if(document.getElementById('rist-viewer-square-grid-authority'))return;
  const style=document.createElement('style');
  style.id='rist-viewer-square-grid-authority';
  style.textContent=`
   .rist.release-world .map:has(.grid.square)::before{
    background-size:var(--rist-viewer-square-cell,64px) var(--rist-viewer-square-cell,64px)!important;
   }
  `;
  document.head.appendChild(style);
 }

 function updateSquareCellSize(map){
  if(!map)return;
  const rect=map.getBoundingClientRect();
  if(rect.width<2||rect.height<2)return;
  /* One new square covers the area of four old squares: double both side lengths. */
  const cell=Math.max(24,Math.round(Math.min(rect.width,rect.height)/10));
  map.style.setProperty('--rist-viewer-square-cell',`${cell}px`);
 }

 function fixViewer(){
  const shell=document.querySelector('.release-map-region .map-shell');
  const map=shell?.querySelector(':scope > .map');
  const stage=map?.querySelector(':scope > .world-stage');
  if(!shell||!map)return;

  const important=(el,name,value)=>el.style.setProperty(name,value,'important');

  important(map,'box-sizing','border-box');
  important(map,'grid-column','2');
  important(map,'grid-row','2');
  important(map,'position','relative');
  important(map,'width','100%');
  important(map,'height','100%');
  important(map,'min-width','0');
  important(map,'min-height','0');
  important(map,'max-width','none');
  important(map,'max-height','none');
  important(map,'aspect-ratio','auto');
  important(map,'margin','0');
  important(map,'overflow','hidden');

  if(stage){
   important(stage,'position','absolute');
   important(stage,'inset','0');
   important(stage,'width','100%');
   important(stage,'height','100%');
   important(stage,'min-width','0');
   important(stage,'min-height','0');
   important(stage,'max-width','none');
   important(stage,'max-height','none');
   important(stage,'aspect-ratio','auto');
  }

  ensureSquareGridAuthority();
  updateSquareCellSize(map);

  if(!viewerResizeObserver){
   viewerResizeObserver=new ResizeObserver(entries=>{
    for(const entry of entries){
     if(entry.target.matches?.('.release-map-region .map-shell>.map'))updateSquareCellSize(entry.target);
    }
   });
  }
  if(!map.dataset.viewerSquareObserved){
   map.dataset.viewerSquareObserved='1';
   viewerResizeObserver.observe(map);
  }
 }

 /* Stars row bulletin authority.
    Menu and Login remain fixed outside the middle slot. The middle slot is the
    Stars bulletin while closed and the existing main-menu slider while open. */
 function layoutBulletinMenu(){
  const strip=document.querySelector('.world-context-strip');
  const menu=strip?.querySelector(':scope > .world-context-menu');
  const login=strip?.querySelector(':scope > .world-context-login');
  const bulletin=strip?.querySelector(':scope > .world-context-track');
  const region=document.querySelector('.release-menu-region');
  const header=region?.querySelector(':scope > #header-slider');
  const shell=document.querySelector('.rist.release-world > .release-world-shell');
  if(!strip||!menu||!login||!bulletin||!region||!header||!shell)return;

  const important=(el,name,value)=>el.style.setProperty(name,value,'important');
  const open=menu.classList.contains('active')||menu.getAttribute('aria-pressed')==='true';
  const stripRect=strip.getBoundingClientRect();
  const menuRect=menu.getBoundingClientRect();
  const loginRect=login.getBoundingClientRect();
  const gap=4;
  const left=Math.round(menuRect.right+gap);
  const right=Math.round(loginRect.left-gap);
  const width=Math.max(0,right-left);

  important(bulletin,'display',open?'none':'flex');

  important(region,'position','fixed');
  important(region,'z-index','2400');
  important(region,'top',`${Math.round(stripRect.top)}px`);
  important(region,'left',`${left}px`);
  important(region,'right','auto');
  important(region,'width',`${width}px`);
  important(region,'height',`${Math.round(stripRect.height)}px`);
  important(region,'min-height','0');
  important(region,'max-height',`${Math.round(stripRect.height)}px`);
  important(region,'margin','0');
  important(region,'padding','0');
  important(region,'overflow','hidden');
  important(region,'display',open?'block':'none');

  important(header,'position','relative');
  important(header,'inset','auto');
  important(header,'display','grid');
  important(header,'grid-template-columns','20px minmax(0,1fr) 20px');
  important(header,'align-items','center');
  important(header,'width','100%');
  important(header,'height','100%');
  important(header,'min-height','0');
  important(header,'max-height','100%');
  important(header,'margin','0');
  important(header,'padding','0');
  important(header,'overflow','hidden');

  const track=header.querySelector(':scope > .release-root-track');
  if(track){
   important(track,'grid-column','2');
   important(track,'grid-row','1');
   important(track,'height','22px');
   important(track,'min-height','22px');
   important(track,'max-height','22px');
   important(track,'align-self','center');
   important(track,'overflow-x','auto');
   important(track,'overflow-y','hidden');
  }
  const prev=header.querySelector(':scope > .rail-scroll-prev');
  const next=header.querySelector(':scope > .rail-scroll-next');
  for(const [arrow,column] of [[prev,'1'],[next,'3']]){
   if(!arrow)continue;
   important(arrow,'grid-column',column);
   important(arrow,'grid-row','1');
   important(arrow,'position','relative');
   important(arrow,'inset','auto');
   important(arrow,'width','20px');
   important(arrow,'height','22px');
   important(arrow,'min-height','22px');
   important(arrow,'max-height','22px');
   important(arrow,'align-self','center');
  }

  /* Portrait used to dedicate a whole row to the menu. Remove only that row.
     Landscape already shares the old menu row with the lower control deck. */
  if(matchMedia('(orientation: portrait)').matches){
   important(shell,'grid-template-rows','var(--rist-assets-h) minmax(0,1fr) var(--rist-assets-h) var(--rist-footer-h)');
  }else{
   shell.style.removeProperty('grid-template-rows');
  }
 }

 function enhance(){
  document.querySelectorAll('.root-menu-panel,.release-action-menu,#card-library,.asset-slider-stack,.rist-tutorial-shell').forEach(addClose);
  fixViewer();
  layoutBulletinMenu();
 }

 let queued=false;
 function queue(){
  if(queued)return;
  queued=true;
  requestAnimationFrame(()=>{queued=false;enhance();});
 }

 function start(){
  enhance();
  new MutationObserver(queue).observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['class','aria-pressed']});
  window.addEventListener('resize',queue,{passive:true});
  window.addEventListener('orientationchange',()=>setTimeout(queue,100),{passive:true});
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
