(()=>{
 'use strict';
 const LOCK_KEY='rist.world.viewerLocked';
 let observer=null;
 let frame=0;
 let lastGrid=null;
 let lastLock=null;

 const studio=()=>document.querySelector('.worldbuilder-studio');
 const commandButton=label=>{
  const root=studio();
  if(!root)return null;
  return [...root.querySelectorAll('.studio-command-rail button')]
   .find(button=>button.querySelector('strong')?.textContent?.trim()===label)||null;
 };
 const readSmall=button=>button?.querySelector('small')?.textContent?.trim()||'';
 const readStoredLock=()=>{
  try{return localStorage.getItem(LOCK_KEY)!=='false'}catch{return true}
 };
 const writeStoredLock=locked=>{
  try{localStorage.setItem(LOCK_KEY,locked?'true':'false')}catch{}
 };

 function installStyle(){
  if(document.getElementById('rist-worldbuilder-view-controls-style'))return;
  const style=document.createElement('style');
  style.id='rist-worldbuilder-view-controls-style';
  style.textContent=`
   html body .worldbuilder-studio.viewer-grid-disabled .studio-viewer-canvas .world-stage>.grid{
    display:none!important;
    visibility:hidden!important;
    background:none!important;
    background-image:none!important;
   }
  `;
  document.head.appendChild(style);
 }

 function syncGrid(root){
  const button=commandButton('View');
  if(!button)return;
  const text=readSmall(button).toLowerCase();
  const enabled=!text.includes('off');
  root.classList.toggle('viewer-grid-disabled',!enabled);
  button.classList.toggle('active',enabled);
  button.setAttribute('aria-pressed',enabled?'true':'false');
  button.setAttribute('aria-label',`Viewer grid ${enabled?'on':'off'}`);
  lastGrid=enabled;
 }

 function syncLock(root){
  const button=commandButton('Z-Lock');
  if(!button)return;
  const text=readSmall(button).toLowerCase();
  const locked=!text.includes('unlocked');
  const stored=readStoredLock();
  if(stored!==locked){
   writeStoredLock(locked);
   window.ristViewerNavigation?.resync?.();
  }
  root.classList.toggle('viewer-locked',locked);
  root.classList.toggle('viewer-unlocked',!locked);
  button.classList.toggle('active',locked);
  button.setAttribute('aria-pressed',locked?'true':'false');
  button.setAttribute('aria-label',`Viewer ${locked?'locked':'unlocked'}. Click to ${locked?'unlock':'lock'}.`);
  lastLock=locked;
 }

 function sync(){
  installStyle();
  const root=studio();
  if(!root)return false;
  syncGrid(root);
  syncLock(root);
  return true;
 }
 function schedule(){
  if(frame)return;
  frame=requestAnimationFrame(()=>{frame=0;sync()});
 }
 function start(){
  if(!sync())return setTimeout(start,100);
  observer=new MutationObserver(schedule);
  observer.observe(studio(),{childList:true,subtree:true,characterData:true});
  window.addEventListener('pageshow',schedule);
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')schedule()});
 }

 window.ristWorldBuilderViewControls={
  sync,
  state:()=>({grid:lastGrid,locked:lastLock,storedLocked:readStoredLock()})
 };
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});
 else start();
})();
