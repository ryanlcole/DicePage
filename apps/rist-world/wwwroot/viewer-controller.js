(()=>{
 const closeClass='map-viewer-close';

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

 function enhance(){
  document.querySelectorAll('.root-menu-panel,.release-action-menu,#card-library,.asset-slider-stack,.rist-tutorial-shell').forEach(addClose);
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
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
