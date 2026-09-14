(()=>{
 'use strict';
 const GRID_CELLS=30;
 const LOCK_KEY='rist.world.viewerLocked';
 const X_KEY='rist.world.viewX';
 const Y_KEY='rist.world.viewY';
 let viewX=readInt(X_KEY,0);
 let viewY=readInt(Y_KEY,0);
 let observer=null;
 let frame=0;

 const studio=()=>document.querySelector('.worldbuilder-studio');
 const stage=()=>studio()?.querySelector('.studio-viewer-canvas .world-stage');
 const grid=()=>studio()?.querySelector('.studio-viewer-grid');
 const canvas=()=>studio()?.querySelector('.studio-viewer-canvas');
 const locked=()=>{try{return localStorage.getItem(LOCK_KEY)!=='false'}catch{return true}};
 function readInt(key,fallback=0){try{const n=Number(localStorage.getItem(key));return Number.isFinite(n)?Math.round(n):fallback}catch{return fallback}}
 function store(){try{localStorage.setItem(X_KEY,String(viewX));localStorage.setItem(Y_KEY,String(viewY))}catch{}}
 function worldExtentCells(){
  const raw=document.querySelector('.site-ticker-root')?.dataset?.worldLimit;
  if(raw==='unbounded')return null;
  const parsed=Number(raw);
  return Number.isFinite(parsed)&&parsed>=GRID_CELLS?Math.round(parsed):300;
 }
 function clampAxis(value){
  const next=Math.round(Number(value)||0),extent=worldExtentCells();
  if(extent===null)return next;
  const maxOffset=Math.max(0,Math.floor((extent-GRID_CELLS)/2));
  return Math.max(-maxOffset,Math.min(maxOffset,next));
 }
 function normalize(){viewX=clampAxis(viewX);viewY=clampAxis(viewY)}
 function cellSize(){
  const rect=(grid()||canvas())?.getBoundingClientRect();
  return rect&&rect.width>0&&rect.height>0?[rect.width/GRID_CELLS,rect.height/GRID_CELLS]:[1,1];
 }
 function panPixels(){const [cw,ch]=cellSize();return{panX:viewX*cw,panY:viewY*ch}}
 function applyPan(){
  normalize();
  const world=stage();if(!world)return;
  world.style.setProperty('--wb-pan-x',`${(viewX/GRID_CELLS)*100}%`);
  world.style.setProperty('--wb-pan-y',`${(viewY/GRID_CELLS)*100}%`);
  const {panX,panY}=panPixels();
  document.documentElement.style.setProperty('--wb-ruler-x-offset',`${panX}px`);
  document.documentElement.style.setProperty('--wb-ruler-y-offset',`${panY}px`);
 }
 function publish(){
  const {panX,panY}=panPixels();
  window.dispatchEvent(new CustomEvent('rist:viewer-pan',{detail:{x:viewX,y:viewY,panX,panY,extent:worldExtentCells()}}));
 }
 function getState(){normalize();const {panX,panY}=panPixels();return{x:viewX,y:viewY,panX,panY,unlocked:!locked(),extent:worldExtentCells()}}
 function setPosition(x,y,force=false){
  if(!force&&locked())return getState();
  viewX=clampAxis(x);viewY=clampAxis(y);store();applyPan();publish();return getState();
 }
 function setPan(x,y,snapToGrid=true,force=false){
  if(!force&&locked())return getState();
  const [cw,ch]=cellSize();
  const px=(Number(x)||0)/Math.max(cw,1),py=(Number(y)||0)/Math.max(ch,1);
  return setPosition(snapToGrid?Math.round(px):px,snapToGrid?Math.round(py):py,force);
 }
 function syncMode(){
  const root=studio();if(!root)return;
  const isLocked=locked();
  root.classList.toggle('viewer-locked',isLocked);
  root.classList.toggle('viewer-unlocked',!isLocked);
  const view=canvas();if(view)view.dataset.viewerLocked=isLocked?'true':'false';
  applyPan();
 }
 function resync(){
  viewX=readInt(X_KEY,viewX);viewY=readInt(Y_KEY,viewY);
  normalize();store();syncMode();publish();return getState();
 }
 function schedule(){if(frame)return;frame=requestAnimationFrame(()=>{frame=0;syncMode()})}
 function start(){
  if(!studio())return setTimeout(start,100);
  syncMode();publish();
  observer=new MutationObserver(schedule);observer.observe(studio(),{childList:true,subtree:true});
  window.addEventListener('resize',schedule,{passive:true});
  window.addEventListener('orientationchange',schedule,{passive:true});
  window.addEventListener('pageshow',()=>resync(),{passive:true});
  window.addEventListener('storage',event=>{if([LOCK_KEY,X_KEY,Y_KEY].includes(event.key))resync()});
 }

 window.ristViewerNavigation={
  get:getState,
  setPosition,
  setPan,
  nudge(axis,steps){if(locked())return getState();const amount=Math.round(Number(steps)||0);return axis==='x'?setPosition(viewX+amount,viewY):setPosition(viewX,viewY+amount)},
  resync
 };
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
