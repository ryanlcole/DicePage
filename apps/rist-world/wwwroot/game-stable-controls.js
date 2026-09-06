(()=>{
 'use strict';

 // Stable game-page additions layered over the restored Sep 3 build.
 // Security/authentication is intentionally untouched here.
 let mapEditEnabled=false;
 let scanQueued=false;
 let tickerStarted=false;
 let tickerPauseUntil=0;
 let tickerLast=0;

 const q=(selector,root=document)=>root?.querySelector(selector);
 const currentSection=()=>q('.rist-section-list>button.active')?.dataset.section||'';

 function setEditButtonState(button){
  if(!button)return;
  button.textContent='Edit';
  button.setAttribute('aria-pressed',mapEditEnabled?'true':'false');
  button.title=mapEditEnabled?'Terrain tile editing enabled':'Enable terrain tile editing';
  button.style.borderColor=mapEditEnabled?'#d7be80':'';
  button.style.background=mapEditEnabled?'#172229':'';
  button.style.boxShadow=mapEditEnabled?'inset 0 0 0 1px #d7be80':'';
 }

 function installMapEditButton(){
  const panel=q('.rist-map-tools-panel');
  if(!panel)return;
  let button=q('[data-map-edit-toggle]',panel);
  if(!button){
   button=document.createElement('button');
   button.type='button';
   button.dataset.mapEditToggle='1';
   button.addEventListener('click',event=>{
    event.preventDefault();
    event.stopPropagation();
    mapEditEnabled=!mapEditEnabled;
    document.documentElement.dataset.ristMapEdit=mapEditEnabled?'on':'off';
    setEditButtonState(button);
   });
   panel.prepend(button);
  }
  setEditButtonState(button);
  const note=q('.rist-map-tools-note');
  if(note)note.textContent='Edit enables terrain tiles. Tokens and other objects remain placeable.';
 }

 function isTileInteraction(target){
  if(!(target instanceof Element))return false;
  if(target.closest('.tray-item.tile,.tile-cell,.library-tile .tile-drag-source'))return true;
  const bottomAsset=target.closest('.rist-bottom-asset-card');
  if(bottomAsset){
   const section=currentSection();
   if(section==='tiles'||section==='terrain')return true;
  }
  return false;
 }

 // Terrain is the only placement family gated by Edit. Minis, tokens, pins,
 // dice and other map objects keep their existing always-placeable behavior.
 document.addEventListener('pointerdown',event=>{
  if(mapEditEnabled||!isTileInteraction(event.target))return;
  event.preventDefault();
  event.stopPropagation();
  event.stopImmediatePropagation();
 },true);

 function startTicker(){
  if(tickerStarted)return;
  tickerStarted=true;
  const pause=()=>{tickerPauseUntil=performance.now()+3500;};
  document.addEventListener('pointerdown',event=>{if(event.target instanceof Element&&event.target.closest('.world-context-track'))pause();},{passive:true});
  document.addEventListener('wheel',event=>{if(event.target instanceof Element&&event.target.closest('.world-context-track'))pause();},{passive:true});
  const tick=now=>{
   const track=q('.world-context-track');
   if(track&&track.scrollWidth>track.clientWidth+2&&now>=tickerPauseUntil){
    if(!tickerLast)tickerLast=now;
    const dt=Math.min(60,now-tickerLast);
    const max=Math.max(0,track.scrollWidth-track.clientWidth);
    track.scrollLeft+=dt*.025;
    if(track.scrollLeft>=max-1){
     track.scrollLeft=0;
     tickerPauseUntil=now+700;
    }
   }
   tickerLast=now;
   requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
 }

 function scan(){
  installMapEditButton();
  startTicker();
 }
 function queueScan(){
  if(scanQueued)return;
  scanQueued=true;
  requestAnimationFrame(()=>{scanQueued=false;scan();});
 }
 function start(){
  document.documentElement.dataset.ristMapEdit='off';
  scan();
  new MutationObserver(queueScan).observe(document.body,{childList:true,subtree:true});
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});
 else start();
})();
