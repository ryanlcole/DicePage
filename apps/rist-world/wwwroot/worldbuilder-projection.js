(()=>{
 'use strict';
 const TILE_SELECTOR='.worldbuilder-studio .world-stage > .tile-cell';
 let visuals=[];
 let observer=null;
 let raf=0;

 try{
  localStorage.removeItem('rist.world.distancePerSquareKmAtZ0');
  localStorage.removeItem('rist.world.tileSizeKmAtOrigin');
 }catch{}

 const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
 const smoothstep=(a,b,v)=>{
  const t=clamp((v-a)/(b-a),0,1);
  return t*t*(3-(2*t));
 };
 const studio=()=>document.querySelector('.worldbuilder-studio');
 const stage=()=>studio()?.querySelector('.world-stage');
 const map=()=>studio()?.querySelector('.map');
 const tiles=()=>[...(studio()?.querySelectorAll(TILE_SELECTOR)||[])];
 const viewZoom=()=>{
  const value=Number(map()?.dataset.zoom);
  return Number.isFinite(value)&&value>0?value:1;
 };
 const sceneZFor=v=>Number(v?.sceneZ??v?.SceneZ??((Number(v?.tierIndex??v?.TierIndex??0)*10)+Number(v?.layerOffset??v?.LayerOffset??0)))||0;

 function representationFor(zoom){
  if(zoom>=1.35)return 'local-spatial';
  if(zoom>=1)return 'site-spatial';
  if(zoom>=.75)return 'cartographic-local';
  if(zoom>=.6)return 'cartographic-region';
  return 'cartographic-world';
 }

 function apply(){
  raf=0;
  const root=studio(),world=stage();
  if(!root||!world)return;
  const zoom=viewZoom();
  const spatialWeight=smoothstep(.5,1,zoom);
  root.dataset.projectionRepresentation=representationFor(zoom);
  root.style.setProperty('--wb-cartographic-blend',String(1-spatialWeight));

  const list=tiles();
  list.forEach((tile,index)=>{
   const visual=visuals[index]||{};
   const sceneZ=sceneZFor(visual);
   const r=tile.getBoundingClientRect();
   const sr=world.getBoundingClientRect();
   const centerX=(r.left+(r.width/2))-(sr.left+(sr.width/2));
   const centerY=(r.top+(r.height/2))-(sr.top+(sr.height/2));

   const height=clamp(sceneZ,-60,60);
   const scale=clamp(1+(height*.0075*spatialWeight),.72,1.45);
   const radial=height*.0018*spatialWeight;
   const shiftX=clamp(centerX*radial,-28,28);
   const shiftY=clamp(centerY*radial,-28,28);
   const stackZ=1000000+((sceneZ+1000)*1000)+index;

   tile.dataset.sceneZ=String(sceneZ);
   tile.dataset.stackIndex=String(index);
   tile.style.setProperty('--wb-stack-z',String(stackZ));
   tile.style.setProperty('--wb-parallax-scale',scale.toFixed(5));
   tile.style.setProperty('--wb-parallax-x',`${shiftX.toFixed(3)}px`);
   tile.style.setProperty('--wb-parallax-y',`${shiftY.toFixed(3)}px`);
  });
 }

 const schedule=()=>{if(!raf)raf=requestAnimationFrame(apply);};

 window.ristDepth={
  set(next){visuals=Array.isArray(next)?next:[];schedule();}
 };
 window.ristProjection={
  apply:schedule,
  getState(){const zoom=viewZoom();return{cellKm:1,cellVolumeKm3:1,zoom,representation:representationFor(zoom),cartographicBlend:1-smoothstep(.5,1,zoom)};}
 };

 const style=document.createElement('style');
 style.id='rist-worldbuilder-projection-authority';
 style.textContent=`
  .worldbuilder-studio .studio-viewer-canvas .world-stage>.tile-cell{
   z-index:var(--wb-stack-z,1000000)!important;
  }
  .worldbuilder-studio .studio-viewer-canvas .world-stage>.tile-cell>.tile-image-crop{
   transform:translate(var(--wb-parallax-x,0px),var(--wb-parallax-y,0px)) scale(var(--wb-parallax-scale,1)) rotate(var(--wb-rotation,0deg))!important;
   transform-origin:center center!important;
   transition:transform 90ms linear!important;
  }
  .worldbuilder-studio .world-stage>.tile-cell.treatment-blend>.tile-image-crop{
   opacity:.86!important;
   mix-blend-mode:multiply!important;
  }
  .worldbuilder-studio .world-stage>.tile-cell.treatment-crop>.tile-image-crop{
   clip-path:inset(1px)!important;
  }
 `;
 document.head.appendChild(style);

 function start(){
  const root=studio();
  if(!root)return setTimeout(start,100);
  observer=new MutationObserver(schedule);
  observer.observe(root,{subtree:true,childList:true,attributes:true,attributeFilter:['data-zoom','style']});
  window.addEventListener('resize',schedule,{passive:true});
  window.addEventListener('pageshow',schedule);
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')schedule();});
  schedule();
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
