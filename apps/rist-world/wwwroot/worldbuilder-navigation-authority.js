(()=>{
 'use strict';
 let pointer=null;
 let viewX=Number(localStorage.getItem('rist.world.viewX'))||0;
 let viewY=Number(localStorage.getItem('rist.world.viewY'))||0;
 let observer=null;
 let axisBinding=null;
 const touchPointers=new Map();
 const rulerZPointers=new Map();
 let fallbackPinch=false,fallbackPinchDistance=0,rulerZPinchDistance=0,rulerPointer=null;

 const studio=()=>document.querySelector('.worldbuilder-studio');
 const canvas=()=>studio()?.querySelector('.studio-viewer-canvas');
 const stage=()=>studio()?.querySelector('.world-stage');
 const grid=()=>studio()?.querySelector('.studio-viewer-grid');
 const isLocked=()=>localStorage.getItem('rist.world.viewerLocked')!=='false';
 const isUnlocked=()=>!isLocked();
 const gridCellSize=()=>{
  const g=grid()||canvas();const r=g?.getBoundingClientRect();
  return r&&r.width>0&&r.height>0?[r.width/30,r.height/30]:[1,1];
 };
 const asInt=value=>Math.round(Number(value)||0);
 const worldExtentCells=()=>{
  const raw=document.querySelector('.site-ticker-root')?.dataset?.worldLimit;
  if(raw==='unbounded')return null;
  const parsed=Number(raw);
  return Number.isFinite(parsed)&&parsed>=30?Math.round(parsed):300;
 };
 const clampAxis=value=>{
  const next=asInt(value),extent=worldExtentCells();
  if(extent===null)return next;
  const maxOffset=Math.max(0,Math.floor((extent-30)/2));
  return Math.max(-maxOffset,Math.min(maxOffset,next));
 };
 function normalizeExtent(){
  const nextX=clampAxis(viewX),nextY=clampAxis(viewY);
  if(nextX===viewX&&nextY===viewY)return;
  viewX=nextX;viewY=nextY;
  localStorage.setItem('rist.world.viewX',String(viewX));
  localStorage.setItem('rist.world.viewY',String(viewY));
 }
 function panPixels(){const [cw,ch]=gridCellSize();return {panX:viewX*cw,panY:viewY*ch};}
 function applyPan(){
  normalizeExtent();
  const world=stage();if(!world)return;
  const panXPct=(viewX/30)*100,panYPct=(viewY/30)*100;
  const {panX,panY}=panPixels();
  world.style.setProperty('--wb-pan-x',`${panXPct}%`);
  world.style.setProperty('--wb-pan-y',`${panYPct}%`);
  document.documentElement.style.setProperty('--wb-ruler-x-offset',`${panX}px`);
  document.documentElement.style.setProperty('--wb-ruler-y-offset',`${panY}px`);
 }
 function publish(){
  const {panX,panY}=panPixels();
  window.dispatchEvent(new CustomEvent('rist:viewer-pan',{detail:{x:viewX,y:viewY,panX,panY,extent:worldExtentCells()}}));
 }
 function setPosition(x,y,force=false){
  if(!force&&isLocked())return getState();
  viewX=clampAxis(x);viewY=clampAxis(y);
  localStorage.setItem('rist.world.viewX',String(viewX));
  localStorage.setItem('rist.world.viewY',String(viewY));
  applyPan();publish();
  return getState();
 }
 function setPan(x,y,snapToGrid=true,force=false){
  if(!force&&isLocked())return getState();
  const [cw,ch]=gridCellSize();
  const nextX=snapToGrid?Math.round((Number(x)||0)/Math.max(cw,1)):(Number(x)||0)/Math.max(cw,1);
  const nextY=snapToGrid?Math.round((Number(y)||0)/Math.max(ch,1)):(Number(y)||0)/Math.max(ch,1);
  return setPosition(nextX,nextY,force);
 }
 function getState(){normalizeExtent();const {panX,panY}=panPixels();return {x:viewX,y:viewY,panX,panY,unlocked:isUnlocked(),extent:worldExtentCells()};}
 function pointDistance(points){const v=[...points.values()];if(v.length<2)return 0;return Math.hypot(v[0].x-v[1].x,v[0].y-v[1].y);}
 function sendZWheel(deltaY){const view=canvas();if(!view)return;view.dispatchEvent(new WheelEvent('wheel',{deltaY,bubbles:true,cancelable:true}));}
 function rulerAxis(target){const ruler=target?.closest?.('.wb-axis-ruler,.wb-z-ruler,.wb-x-ruler,.wb-y-ruler');if(!ruler)return null;if(ruler.dataset.axis)return {ruler,axis:ruler.dataset.axis};if(ruler.classList.contains('wb-z-ruler'))return {ruler,axis:'z'};if(ruler.classList.contains('wb-x-ruler'))return {ruler,axis:'x'};if(ruler.classList.contains('wb-y-ruler'))return {ruler,axis:'y'};return null;}
 function captureDown(e){
  if(isLocked())return;
  const axisHit=rulerAxis(e.target);
  if(axisHit){
   if(axisHit.axis==='z'){
    rulerZPointers.set(e.pointerId,{x:e.clientX,y:e.clientY,lastY:e.clientY});
    if(rulerZPointers.size===2)rulerZPinchDistance=pointDistance(rulerZPointers);
   }else{
    rulerPointer={id:e.pointerId,axis:axisHit.axis,startX:e.clientX,startY:e.clientY,startViewX:viewX,startViewY:viewY};
   }
   e.preventDefault();e.stopImmediatePropagation();return;
  }
  if(e.pointerType!=='touch'||!e.target?.closest?.('.studio-viewer-canvas'))return;
  touchPointers.set(e.pointerId,{x:e.clientX,y:e.clientY,blocked:!!e.target?.closest?.('.world-stage .tile-cell')});
  if(touchPointers.size===2&&[...touchPointers.values()].some(p=>p.blocked)){
   fallbackPinch=true;fallbackPinchDistance=pointDistance(touchPointers);
   e.preventDefault();e.stopImmediatePropagation();
  }
 }
 function captureMove(e){
  if(isLocked())return;
  if(rulerZPointers.has(e.pointerId)){
   const p=rulerZPointers.get(e.pointerId);p.x=e.clientX;p.y=e.clientY;
   if(rulerZPointers.size===2){
    const next=pointDistance(rulerZPointers);
    if(rulerZPinchDistance){const ratio=next/rulerZPinchDistance;if(Math.abs(ratio-1)>.012){sendZWheel(ratio>1?-340:340);rulerZPinchDistance=next;}}
    else rulerZPinchDistance=next;
   }else{
    const dy=e.clientY-p.lastY;
    if(Math.abs(dy)>=14){sendZWheel(dy>0?340:-340);p.lastY=e.clientY;}
   }
   e.preventDefault();e.stopImmediatePropagation();return;
  }
  if(rulerPointer&&rulerPointer.id===e.pointerId){
   const [cw,ch]=gridCellSize(),dx=e.clientX-rulerPointer.startX,dy=e.clientY-rulerPointer.startY;
   if(rulerPointer.axis==='x')setPosition(rulerPointer.startViewX+Math.round(dx/Math.max(cw,1)),rulerPointer.startViewY);
   else setPosition(rulerPointer.startViewX,rulerPointer.startViewY+Math.round(dy/Math.max(ch,1)));
   e.preventDefault();e.stopImmediatePropagation();return;
  }
  if(!touchPointers.has(e.pointerId))return;
  const p=touchPointers.get(e.pointerId);p.x=e.clientX;p.y=e.clientY;
  if(!fallbackPinch||touchPointers.size<2)return;
  const next=pointDistance(touchPointers);
  if(fallbackPinchDistance){const ratio=next/fallbackPinchDistance;if(Math.abs(ratio-1)>.012){sendZWheel(ratio>1?-340:340);fallbackPinchDistance=next;}}
  else fallbackPinchDistance=next;
  e.preventDefault();e.stopImmediatePropagation();
 }
 function captureRelease(e){
  if(rulerZPointers.has(e.pointerId)){rulerZPointers.delete(e.pointerId);if(rulerZPointers.size<2)rulerZPinchDistance=0;e.preventDefault();e.stopImmediatePropagation();return;}
  if(rulerPointer?.id===e.pointerId){rulerPointer=null;e.preventDefault();e.stopImmediatePropagation();return;}
  if(!touchPointers.has(e.pointerId))return;
  touchPointers.delete(e.pointerId);
  if(touchPointers.size<2){fallbackPinch=false;fallbackPinchDistance=0;}
 }
 document.addEventListener('pointerdown',captureDown,{capture:true,passive:false});
 document.addEventListener('pointermove',captureMove,{capture:true,passive:false});
 document.addEventListener('pointerup',captureRelease,{capture:true,passive:false});
 document.addEventListener('pointercancel',captureRelease,{capture:true,passive:false});
 window.ristViewerNavigation={
  get:getState,
  setPosition,
  setPan,
  nudge(axis,steps){if(isLocked())return getState();return axis==='x'?setPosition(viewX+asInt(steps),viewY):setPosition(viewX,viewY+asInt(steps));},
  resync(){resume();return getState();}
 };

 function syncMode(){
  const locked=isLocked(),unlocked=!locked;
  const root=studio();if(root)root.classList.toggle('viewer-locked',locked);
  document.documentElement.classList.toggle('rist-wb-z-unlocked',unlocked);
  const view=canvas();if(view)view.dataset.zUnlocked=unlocked?'true':'false';
  if(locked){pointer=null;touchPointers.clear();rulerZPointers.clear();rulerPointer=null;fallbackPinch=false;fallbackPinchDistance=0;rulerZPinchDistance=0;}
  applyPan();
 }
 function resume(){
  pointer=null;
  viewX=clampAxis(localStorage.getItem('rist.world.viewX'));
  viewY=clampAxis(localStorage.getItem('rist.world.viewY'));
  localStorage.setItem('rist.world.viewX',String(viewX));
  localStorage.setItem('rist.world.viewY',String(viewY));
  requestAnimationFrame(()=>requestAnimationFrame(()=>{syncMode();applyPan();publish();}));
 }
 function suspend(){pointer=null;touchPointers.clear();rulerZPointers.clear();rulerPointer=null;fallbackPinch=false;fallbackPinchDistance=0;rulerZPinchDistance=0;}
 function onDown(e){
  if(isLocked()||(e.pointerType==='mouse'&&e.button!==0))return;
  if(e.target?.closest?.('.studio-command-slider,.studio-top-slider,.map-frame-controls,.desktop-map-zoom,.wb-z-ruler,.wb-x-ruler,.wb-y-ruler,.wb-modal,.world-stage .tile-cell'))return;
  if(pointer)return;
  pointer={id:e.pointerId,x:e.clientX,y:e.clientY,startX:viewX,startY:viewY};
 }
 function onMove(e){
  if(!pointer||pointer.id!==e.pointerId||isLocked())return;
  const dx=e.clientX-pointer.x,dy=e.clientY-pointer.y;
  if(Math.abs(dx)+Math.abs(dy)<.5)return;
  const [cw,ch]=gridCellSize();
  viewX=clampAxis(pointer.startX+Math.round(dx/Math.max(cw,1)));
  viewY=clampAxis(pointer.startY+Math.round(dy/Math.max(ch,1)));
  applyPan();e.preventDefault();
 }
 function release(e){
  if(pointer?.id!==e.pointerId)return;
  if(isLocked()){pointer=null;return;}
  pointer=null;normalizeExtent();
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
  try{const module=await import('./worldbuilder-axis-rulers.js?v=20260911-rulers-8');axisBinding=module.attachAxisRulers(view);}catch{}
  window.addEventListener('pageshow',resume);
  window.addEventListener('pagehide',suspend);
  window.addEventListener('resize',()=>requestAnimationFrame(applyPan));
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')resume();else suspend();});
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
