(()=>{
 'use strict';
 let pointer=null;
 let panX=Number(localStorage.getItem('rist.world.panX'))||0;
 let panY=Number(localStorage.getItem('rist.world.panY'))||0;
 let observer=null;
 let axisBinding=null;

 const studio=()=>document.querySelector('.worldbuilder-studio');
 const canvas=()=>studio()?.querySelector('.studio-viewer-canvas');
 const stage=()=>studio()?.querySelector('.world-stage');
 const isUnlocked=()=>{
  const root=studio();
  if(root)return !root.classList.contains('viewer-locked');
  return localStorage.getItem('rist.world.viewerLocked')==='false';
 };
 const cellSize=()=>{
  const s=stage();const r=s?.getBoundingClientRect();
  return r&&r.width>0&&r.height>0?[r.width/30,r.height/30]:[1,1];
 };
 const snap=(value,step)=>Math.round(value/Math.max(step,1))*Math.max(step,1);
 function applyPan(){
  const world=stage();if(!world)return;
  world.style.setProperty('--wb-pan-x',`${panX}px`);
  world.style.setProperty('--wb-pan-y',`${panY}px`);
  document.documentElement.style.setProperty('--wb-ruler-x-offset',`${panX}px`);
  document.documentElement.style.setProperty('--wb-ruler-y-offset',`${panY}px`);
 }
 function setPan(x,y,snapToGrid=true){
  const [cw,ch]=cellSize();
  panX=snapToGrid?snap(Number(x)||0,cw):Number(x)||0;
  panY=snapToGrid?snap(Number(y)||0,ch):Number(y)||0;
  localStorage.setItem('rist.world.panX',String(panX));
  localStorage.setItem('rist.world.panY',String(panY));
  applyPan();
  window.dispatchEvent(new CustomEvent('rist:viewer-pan',{detail:{panX,panY}}));
  return {panX,panY};
 }
 window.ristViewerNavigation={get:()=>({panX,panY,unlocked:isUnlocked()}),setPan,nudge(axis,steps){const [cw,ch]=cellSize();return axis==='x'?setPan(panX+(steps*cw),panY):setPan(panX,panY+(steps*ch));}};

 function syncMode(){
  const unlocked=isUnlocked();
  document.documentElement.classList.toggle('rist-wb-z-unlocked',unlocked);
  const view=canvas();if(view)view.dataset.zUnlocked=unlocked?'true':'false';
  if(!unlocked)pointer=null;
  applyPan();
 }
 function onDown(e){
  if(!isUnlocked()||(e.pointerType==='mouse'&&e.button!==0))return;
  if(e.target?.closest?.('.studio-command-slider,.studio-top-slider,.map-frame-controls,.desktop-map-zoom,.wb-z-ruler,.wb-x-ruler,.wb-y-ruler,.wb-modal,.world-stage .tile-cell'))return;
  if(pointer)return;
  pointer={id:e.pointerId,x:e.clientX,y:e.clientY,startPanX:panX,startPanY:panY};
 }
 function onMove(e){
  if(!pointer||pointer.id!==e.pointerId||!isUnlocked())return;
  const dx=e.clientX-pointer.x,dy=e.clientY-pointer.y;
  if(Math.abs(dx)+Math.abs(dy)<.5)return;
  const [cw,ch]=cellSize();
  panX=snap(pointer.startPanX+dx,cw);panY=snap(pointer.startPanY+dy,ch);
  applyPan();e.preventDefault();
 }
 function release(e){
  if(pointer?.id!==e.pointerId)return;
  pointer=null;localStorage.setItem('rist.world.panX',String(panX));localStorage.setItem('rist.world.panY',String(panY));
  window.dispatchEvent(new CustomEvent('rist:viewer-pan',{detail:{panX,panY}}));
 }
 const style=document.createElement('style');style.id='rist-worldbuilder-viewer-navigation';style.textContent=`
  .worldbuilder-studio .studio-viewer-canvas .world-stage{transform:translate(var(--wb-pan-x,0px),var(--wb-pan-y,0px)) scale(var(--wb-z-scale,1))!important}
  html.rist-wb-z-unlocked .worldbuilder-studio .studio-viewer-canvas{touch-action:none!important;cursor:grab!important}
  html.rist-wb-z-unlocked .worldbuilder-studio .studio-viewer-canvas:active{cursor:grabbing!important}
 `;document.head.appendChild(style);
 async function start(){
  const root=studio();if(!root)return setTimeout(start,100);
  const view=canvas();view?.addEventListener('pointerdown',onDown,{passive:true});view?.addEventListener('pointermove',onMove,{passive:false});view?.addEventListener('pointerup',release,{passive:true});view?.addEventListener('pointercancel',release,{passive:true});
  observer=new MutationObserver(()=>requestAnimationFrame(syncMode));observer.observe(root,{attributes:true,attributeFilter:['class'],subtree:false});syncMode();
  try{const module=await import('./worldbuilder-axis-rulers.js?v=20260910-rulers-2');axisBinding=module.attachAxisRulers(view);}catch{}
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
