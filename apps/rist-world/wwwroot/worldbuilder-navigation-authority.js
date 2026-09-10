(()=>{
 'use strict';
 let pointer=null;
 let viewX=Number(localStorage.getItem('rist.world.viewX'))||0;
 let viewY=Number(localStorage.getItem('rist.world.viewY'))||0;
 let observer=null;
 let axisBinding=null;

 const studio=()=>document.querySelector('.worldbuilder-studio');
 const canvas=()=>studio()?.querySelector('.studio-viewer-canvas');
 const stage=()=>studio()?.querySelector('.world-stage');
 const grid=()=>studio()?.querySelector('.studio-viewer-grid');
 const isUnlocked=()=>{
  const root=studio();
  if(root)return !root.classList.contains('viewer-locked');
  return localStorage.getItem('rist.world.viewerLocked')==='false';
 };
 const gridCellSize=()=>{
  const g=grid()||canvas();const r=g?.getBoundingClientRect();
  return r&&r.width>0&&r.height>0?[r.width/30,r.height/30]:[1,1];
 };
 const asInt=value=>Math.round(Number(value)||0);
 function panPixels(){const [cw,ch]=gridCellSize();return {panX:viewX*cw,panY:viewY*ch};}
 function applyPan(){
  const world=stage();if(!world)return;
  // X/Y are world-cell coordinates, not viewport pixels. Percentage translation
  // keeps the same logical viewer position when mobile Safari changes its visual
  // viewport while backgrounding/restoring the page.
  const panXPct=(viewX/30)*100,panYPct=(viewY/30)*100;
  const {panX,panY}=panPixels();
  world.style.setProperty('--wb-pan-x',`${panXPct}%`);
  world.style.setProperty('--wb-pan-y',`${panYPct}%`);
  document.documentElement.style.setProperty('--wb-ruler-x-offset',`${panX}px`);
  document.documentElement.style.setProperty('--wb-ruler-y-offset',`${panY}px`);
 }
 function publish(){
  const {panX,panY}=panPixels();
  window.dispatchEvent(new CustomEvent('rist:viewer-pan',{detail:{x:viewX,y:viewY,panX,panY}}));
 }
 function setPosition(x,y,force=false){
  if(!force&&!isUnlocked())return getState();
  viewX=asInt(x);viewY=asInt(y);
  localStorage.setItem('rist.world.viewX',String(viewX));
  localStorage.setItem('rist.world.viewY',String(viewY));
  applyPan();publish();
  return getState();
 }
 function setPan(x,y,snapToGrid=true,force=false){
  if(!force&&!isUnlocked())return getState();
  const [cw,ch]=gridCellSize();
  const nextX=snapToGrid?Math.round((Number(x)||0)/Math.max(cw,1)):(Number(x)||0)/Math.max(cw,1);
  const nextY=snapToGrid?Math.round((Number(y)||0)/Math.max(ch,1)):(Number(y)||0)/Math.max(ch,1);
  return setPosition(nextX,nextY,force);
 }
 function getState(){const {panX,panY}=panPixels();return {x:viewX,y:viewY,panX,panY,unlocked:isUnlocked()};}
 window.ristViewerNavigation={
  get:getState,
  setPosition,
  setPan,
  nudge(axis,steps){if(!isUnlocked())return getState();return axis==='x'?setPosition(viewX+asInt(steps),viewY):setPosition(viewX,viewY+asInt(steps));},
  resync(){resume();return getState();}
 };

 function syncMode(){
  const unlocked=isUnlocked();
  document.documentElement.classList.toggle('rist-wb-z-unlocked',unlocked);
  const view=canvas();if(view)view.dataset.zUnlocked=unlocked?'true':'false';
  if(!unlocked)pointer=null;
  applyPan();
 }
 function resume(){
  // Never derive a new X/Y from restored DOM geometry. Restore the last committed
  // integer coordinates only, then repaint them against the current viewport.
  pointer=null;
  viewX=asInt(localStorage.getItem('rist.world.viewX'));
  viewY=asInt(localStorage.getItem('rist.world.viewY'));
  requestAnimationFrame(()=>{syncMode();publish();});
 }
 function suspend(){
  // iOS can deliver a partial pointer sequence while the app is being backgrounded.
  // Discard that gesture instead of allowing it to become a new map position.
  pointer=null;
 }
 function onDown(e){
  if(!isUnlocked()||(e.pointerType==='mouse'&&e.button!==0))return;
  if(e.target?.closest?.('.studio-command-slider,.studio-top-slider,.map-frame-controls,.desktop-map-zoom,.wb-z-ruler,.wb-x-ruler,.wb-y-ruler,.wb-modal,.world-stage .tile-cell'))return;
  if(pointer)return;
  pointer={id:e.pointerId,x:e.clientX,y:e.clientY,startX:viewX,startY:viewY};
 }
 function onMove(e){
  if(!pointer||pointer.id!==e.pointerId||!isUnlocked())return;
  const dx=e.clientX-pointer.x,dy=e.clientY-pointer.y;
  if(Math.abs(dx)+Math.abs(dy)<.5)return;
  const [cw,ch]=gridCellSize();
  viewX=pointer.startX+Math.round(dx/Math.max(cw,1));
  viewY=pointer.startY+Math.round(dy/Math.max(ch,1));
  applyPan();e.preventDefault();
 }
 function release(e){
  if(pointer?.id!==e.pointerId)return;
  pointer=null;
  localStorage.setItem('rist.world.viewX',String(viewX));
  localStorage.setItem('rist.world.viewY',String(viewY));
  publish();
 }
 const style=document.createElement('style');style.id='rist-worldbuilder-viewer-navigation';style.textContent=`
  .worldbuilder-studio .studio-viewer-canvas .world-stage{transform:translate(var(--wb-pan-x,0%),var(--wb-pan-y,0%)) scale(var(--wb-z-scale,1))!important}
  html.rist-wb-z-unlocked .worldbuilder-studio .studio-viewer-canvas{touch-action:none!important;cursor:grab!important}
  html.rist-wb-z-unlocked .worldbuilder-studio .studio-viewer-canvas:active{cursor:grabbing!important}
 `;document.head.appendChild(style);
 async function start(){
  const root=studio();if(!root)return setTimeout(start,100);
  const view=canvas();view?.addEventListener('pointerdown',onDown,{passive:true});view?.addEventListener('pointermove',onMove,{passive:false});view?.addEventListener('pointerup',release,{passive:true});view?.addEventListener('pointercancel',release,{passive:true});
  observer=new MutationObserver(()=>requestAnimationFrame(syncMode));observer.observe(root,{attributes:true,attributeFilter:['class'],subtree:false});syncMode();
  try{const module=await import('./worldbuilder-axis-rulers.js?v=20260910-rulers-6');axisBinding=module.attachAxisRulers(view);}catch{}
  window.addEventListener('pageshow',resume);
  window.addEventListener('pagehide',suspend);
  window.addEventListener('resize',()=>requestAnimationFrame(applyPan));
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')resume();else suspend();});
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
