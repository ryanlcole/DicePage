(()=>{
 'use strict';
 const LOCK_KEY='rist.world.viewerLocked';
 let observer=null,frame=0,lastGrid=null,lastLock=null;
 const studio=()=>document.querySelector('.worldbuilder-studio');
 const railButtons=()=>[...(studio()?.querySelectorAll('.studio-command-rail button')||[])];
 const commandButton=label=>railButtons().find(button=>button.querySelector('strong')?.textContent?.trim()===label)||null;
 const lockButton=()=>railButtons().find(button=>{
  const strong=button.querySelector('strong')?.textContent?.trim();
  const small=button.querySelector('small')?.textContent?.trim().toLowerCase()||'';
  return strong==='Z-Lock'||strong==='Lock'||strong==='Unlock'||small.includes('viewer locked')||small.includes('viewer unlocked');
 })||null;
 const readStoredLock=()=>{try{return localStorage.getItem(LOCK_KEY)!=='false'}catch{return true}};
 function installStyle(){
  if(document.getElementById('rist-worldbuilder-view-controls-style'))return;
  const style=document.createElement('style');style.id='rist-worldbuilder-view-controls-style';style.textContent=`
   html body .worldbuilder-studio.viewer-grid-disabled .studio-viewer-canvas .world-stage>.grid{display:none!important;visibility:hidden!important;background:none!important;background-image:none!important}
  `;document.head.appendChild(style);
 }
 function syncGrid(root){
  const marker=root.querySelector('.studio-viewer-grid');
  const enabled=!marker?.classList.contains('off');
  root.classList.toggle('viewer-grid-disabled',!enabled);
  const button=commandButton('View');if(button){button.classList.toggle('active',enabled);button.setAttribute('aria-pressed',enabled?'true':'false');button.setAttribute('aria-label',`Viewer grid ${enabled?'on':'off'}`)}
  lastGrid=enabled;
 }
 function syncLock(root){
  const isLocked=readStoredLock();
  root.classList.toggle('viewer-locked',isLocked);root.classList.toggle('viewer-unlocked',!isLocked);
  const button=lockButton();if(button){button.classList.toggle('active',isLocked);button.setAttribute('aria-pressed',isLocked?'true':'false');button.setAttribute('aria-label',`Viewer ${isLocked?'locked':'unlocked'}. Pinch zoom remains available.`)}
  lastLock=isLocked;
 }
 function sync(){installStyle();const root=studio();if(!root)return false;syncGrid(root);syncLock(root);return true}
 function schedule(){if(frame)return;frame=requestAnimationFrame(()=>{frame=0;sync()})}
 function start(){
  if(!sync())return setTimeout(start,100);
  observer=new MutationObserver(schedule);observer.observe(studio(),{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['class']});
  window.addEventListener('pageshow',schedule,{passive:true});window.addEventListener('storage',event=>{if(event.key===LOCK_KEY)schedule()});
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')schedule()});
 }
 window.ristWorldBuilderViewControls={sync,state:()=>({grid:lastGrid,locked:lastLock,storedLocked:readStoredLock()})};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
