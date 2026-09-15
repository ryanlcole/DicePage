(()=>{
 'use strict';
 const TILE_SELECTOR='.worldbuilder-studio .world-stage > .tile-cell';
 let visuals=[];
 let observer=null;
 let raf=0;
 let lastTopology={tops:{},tiers:[]};

 try{
  localStorage.removeItem('rist.world.distancePerSquareKmAtZ0');
  localStorage.removeItem('rist.world.tileSizeKmAtOrigin');
 }catch{}

 const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
 const smoothstep=(a,b,v)=>{const t=clamp((v-a)/(b-a),0,1);return t*t*(3-(2*t))};
 const studio=()=>document.querySelector('.worldbuilder-studio');
 const stage=()=>studio()?.querySelector('.world-stage');
 const map=()=>studio()?.querySelector('.map');
 const tiles=()=>[...(studio()?.querySelectorAll(TILE_SELECTOR)||[])];
 const number=(v,fallback=0)=>Number.isFinite(Number(v))?Number(v):fallback;
 const tierFor=v=>number(v?.tierIndex??v?.TierIndex,0);
 const layerFor=v=>number(v?.layerOffset??v?.LayerOffset,0);
 const sceneZFor=v=>number(v?.sceneZ??v?.SceneZ,(tierFor(v)*10)+layerFor(v));
 const tiltStrength=()=>clamp(number(window.ristParallax?.tiltStrength?.(),.65),0,1);
 const viewZoom=()=>{const value=Number(map()?.dataset.zoom);return Number.isFinite(value)&&value>0?value:1};

 function representationFor(zoom){
  if(zoom>=1.35)return 'local-spatial';
  if(zoom>=1)return 'site-spatial';
  if(zoom>=.75)return 'cartographic-local';
  if(zoom>=.6)return 'cartographic-region';
  return 'cartographic-world';
 }

 // The map stores only discrete tier/layer truth. The viewer derives a topology
 // from that truth: the greatest occupied layer in each tier is that tier's top
 // surface. Only top surfaces after the first can tilt against a previous top.
 function topologyFor(list){
  const tops=new Map();
  for(const visual of list){
   const tier=tierFor(visual),layer=layerFor(visual);
   tops.set(tier,Math.max(tops.get(tier)??Number.NEGATIVE_INFINITY,layer));
  }
  const tiers=[...tops.keys()].sort((a,b)=>a-b);
  const ranks=new Map(tiers.map((tier,index)=>[tier,index]));
  const previous=new Map(tiers.map((tier,index)=>[tier,index>0?tiers[index-1]:null]));
  return{tops,tiers,ranks,previous};
 }

 function clearPerception(tile){
  tile.dataset.tierTop='false';
  tile.dataset.previousTierTop='';
  tile.style.setProperty('--wb-tier-tilt','0deg');
  tile.style.setProperty('--wb-tier-lift','0px');
  tile.style.setProperty('--wb-tier-origin-x','50%');
  tile.style.setProperty('--wb-tier-origin-y','50%');
 }

 function apply(){
  raf=0;
  const root=studio(),world=stage();
  if(!root||!world)return;
  const zoom=viewZoom();
  const active=window.ristParallax?.isEnabled?.()!==false&&window.ristParallax?.isWorldBuilderActive?.()===true;
  const spatialWeight=active?smoothstep(.5,1,zoom):0;
  const strength=tiltStrength();
  const topology=topologyFor(visuals);
  lastTopology={tops:Object.fromEntries(topology.tops),tiers:[...topology.tiers]};
  root.dataset.projectionRepresentation=representationFor(zoom);
  root.dataset.projectionTruth='tier-layer';
  root.dataset.projectionRule='tier-top-tilt';
  root.style.setProperty('--wb-cartographic-blend',String(1-spatialWeight));
  root.style.setProperty('--wb-perspective-strength',strength.toFixed(3));

  const list=tiles(),stageRect=world.getBoundingClientRect();
  list.forEach((tile,index)=>{
   const visual=visuals[index]||{};
   const tier=tierFor(visual),layer=layerFor(visual),sceneZ=sceneZFor(visual);
   const top=topology.tops.get(tier);
   const rank=topology.ranks.get(tier)??0;
   const previousTier=topology.previous.get(tier);
   const isTop=Number.isFinite(top)&&layer===top;
   const hasPreviousTop=isTop&&previousTier!==null&&previousTier!==undefined;
   const tileRect=tile.getBoundingClientRect();
   const originX=(stageRect.left+(stageRect.width/2))-tileRect.left;
   const originY=stageRect.bottom-tileRect.top;

   // Each successive top surface receives the same relative angular step.
   // Cumulative rank makes tier N visibly tilt against tier N-1 while every
   // ordinary layer remains geometrically flat in the viewer.
   const angle=hasPreviousTop?clamp(-rank*5.25*strength*spatialWeight,-18,0):0;
   const lift=hasPreviousTop?clamp(-rank*9*strength*spatialWeight,-42,0):0;
   const stackZ=1000000+((sceneZ+1000)*1000)+index;

   tile.dataset.sceneZ=String(sceneZ);
   tile.dataset.stackIndex=String(index);
   tile.dataset.tierTop=isTop?'true':'false';
   tile.dataset.previousTierTop=previousTier==null?'':String(previousTier);
   tile.style.setProperty('--wb-stack-z',String(stackZ));
   tile.style.setProperty('--wb-tier-tilt',`${angle.toFixed(3)}deg`);
   tile.style.setProperty('--wb-tier-lift',`${lift.toFixed(3)}px`);
   tile.style.setProperty('--wb-tier-origin-x',`${originX.toFixed(3)}px`);
   tile.style.setProperty('--wb-tier-origin-y',`${originY.toFixed(3)}px`);
   if(!active)clearPerception(tile);
  });
  window.dispatchEvent(new CustomEvent('rist:projection-state',{detail:window.ristProjection?.getState?.()}));
 }

 const schedule=()=>{if(!raf)raf=requestAnimationFrame(apply)};

 window.ristDepth={...(window.ristDepth||{}),set(next){visuals=Array.isArray(next)?next:[];window.dispatchEvent(new CustomEvent('rist-depth-visuals',{detail:visuals}));schedule()}};
 window.ristProjection={
  apply:schedule,
  getState(){
   const zoom=viewZoom();
   return{cellKm:1,cellVolumeKm3:1,zoom,representation:representationFor(zoom),cartographicBlend:1-smoothstep(.5,1,zoom),truth:'tier-layer',rule:'tier-top-tilt',tiltStrength:tiltStrength(),tierTops:{...lastTopology.tops},tiers:[...lastTopology.tiers]};
  }
 };

 const old=document.getElementById('rist-worldbuilder-projection-authority');old?.remove();
 const style=document.createElement('style');
 style.id='rist-worldbuilder-projection-authority';
 style.textContent=`
  .worldbuilder-studio .studio-viewer-canvas .world-stage{perspective:1000px;perspective-origin:50% 78%;transform-style:preserve-3d}
  .worldbuilder-studio .studio-viewer-canvas .world-stage>.tile-cell{z-index:var(--wb-stack-z,1000000)!important;transform-style:preserve-3d!important}
  .worldbuilder-studio .studio-viewer-canvas .world-stage>.tile-cell.wb-selected,
  .worldbuilder-studio .studio-viewer-canvas .world-stage>.tile-cell.wb-moving{z-index:2147483000!important}
  .worldbuilder-studio .studio-viewer-canvas .world-stage>.tile-cell>.tile-image-crop{
   transform:translate3d(var(--wb-motion-x,0px),var(--wb-tier-lift,0px),0) translateY(var(--wb-motion-y,0px)) rotateX(var(--wb-tier-tilt,0deg)) rotate(var(--wb-rotation,0deg))!important;
   transform-origin:var(--wb-tier-origin-x,50%) var(--wb-tier-origin-y,50%)!important;
   transform-style:preserve-3d!important;
   transition:transform 90ms linear!important;
  }
  .worldbuilder-studio .world-stage>.tile-cell.treatment-blend>.tile-image-crop{opacity:.86!important;mix-blend-mode:multiply!important}
  .worldbuilder-studio .world-stage>.tile-cell.treatment-crop>.tile-image-crop{clip-path:inset(1px)!important}
  .worldbuilder-studio.wb-access-reduced .studio-viewer-canvas .world-stage>.tile-cell>.tile-image-crop{transition:none!important}
 `;
 document.head.appendChild(style);

 function start(){
  const root=studio();
  if(!root)return setTimeout(start,100);
  observer=new MutationObserver(schedule);
  observer.observe(root,{subtree:true,childList:true,attributes:true,attributeFilter:['data-zoom','style','class']});
  window.addEventListener('resize',schedule,{passive:true});
  window.addEventListener('pageshow',schedule);
  window.addEventListener('rist-parallax-settings',schedule);
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')schedule()});
  schedule();
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();