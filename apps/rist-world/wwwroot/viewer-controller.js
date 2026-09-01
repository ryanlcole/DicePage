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

 function enhance(){
  document.querySelectorAll('.root-menu-panel,.release-action-menu,#card-library,.asset-slider-stack,.rist-tutorial-shell').forEach(addClose);
  fixViewer();
 }

 let queued=false;
 function queue(){
  if(queued)return;
  queued=true;
  requestAnimationFrame(()=>{queued=false;enhance();});
 }

 function start(){
  enhance();
  new MutationObserver(queue).observe(document.body,{childList:true,subtree:true});
  window.addEventListener('resize',queue,{passive:true});
  window.addEventListener('orientationchange',()=>setTimeout(queue,100),{passive:true});
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
