(()=>{
 'use strict';
 const GRID_SIZE=30;
 const footprint=()=>{
  const strong=document.querySelector('.worldbuilder-studio .tile-size-button strong');
  const match=strong?.textContent?.match(/\d+/);
  return Math.max(1,Math.min(GRID_SIZE,Number(match?.[0]||1)));
 };
 const gridRect=()=>{
  const stage=document.querySelector('.worldbuilder-studio .studio-viewer-canvas .world-stage');
  return stage?.getBoundingClientRect?.()||null;
 };
 const resizeGhost=(x,y)=>{
  const ghost=document.querySelector('.wb-quick-drag-ghost');
  if(!ghost)return;
  const rect=gridRect();
  if(!rect||rect.width<1||rect.height<1)return;
  const count=footprint();
  const width=rect.width*count/GRID_SIZE;
  const height=rect.height*count/GRID_SIZE;
  ghost.style.setProperty('width',`${width}px`,'important');
  ghost.style.setProperty('height',`${height}px`,'important');
  ghost.style.setProperty('border-radius',count===1?'3px':'7px','important');
  const inside=x>=rect.left&&x<=rect.right&&y>=rect.top&&y<=rect.bottom;
  if(inside){
   const cellW=rect.width/GRID_SIZE;
   const cellH=rect.height/GRID_SIZE;
   const maxCol=Math.max(0,GRID_SIZE-count);
   const maxRow=Math.max(0,GRID_SIZE-count);
   const col=Math.max(0,Math.min(maxCol,Math.floor((x-rect.left)/cellW)));
   const row=Math.max(0,Math.min(maxRow,Math.floor((y-rect.top)/cellH)));
   ghost.style.setProperty('left',`${rect.left+col*cellW}px`,'important');
   ghost.style.setProperty('top',`${rect.top+row*cellH}px`,'important');
   ghost.style.setProperty('transform','none','important');
  }else{
   ghost.style.setProperty('left',`${x}px`,'important');
   ghost.style.setProperty('top',`${y}px`,'important');
   ghost.style.setProperty('transform','translate(-50%,-50%) scale(1.06)','important');
  }
 };
 document.addEventListener('pointermove',e=>resizeGhost(e.clientX,e.clientY),{capture:true,passive:true});
 document.addEventListener('dragover',e=>resizeGhost(e.clientX,e.clientY),{capture:true,passive:true});
 const observer=new MutationObserver(()=>{
  const ghost=document.querySelector('.wb-quick-drag-ghost');
  if(!ghost)return;
  const rect=ghost.getBoundingClientRect();
  resizeGhost(rect.left+rect.width/2,rect.top+rect.height/2);
 });
 const start=()=>observer.observe(document.body,{childList:true,subtree:true});
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
