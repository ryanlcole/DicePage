(()=>{
 'use strict';

 const state={
  enabled:false,
  permissionAsked:false,
  permission:'unknown',
  baselineBeta:null,
  baselineGamma:null,
  targetX:0,
  targetY:0,
  x:0,
  y:0,
  raf:0,
  visuals:[]
 };

 const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
 const studio=()=>document.querySelector('.worldbuilder-studio');
 const tiles=()=>studio()?[...studio().querySelectorAll('.world-stage .tile-cell')]:[];
 const landing=()=>document.querySelector('.launcher-hub');
 const userParallaxEnabled=()=>window.ristParallax?.isEnabled?.()!==false;
 const worldBuilderParallaxActive=()=>window.ristParallax?.isWorldBuilderActive?.()===true;

 const acceptVisuals=visuals=>{state.visuals=Array.isArray(visuals)?visuals:[];schedule();};
 window.addEventListener('rist-depth-visuals',event=>acceptVisuals(event.detail));
 window.ristDepth=window.ristDepth||{};
 window.ristDepth.set=visuals=>{acceptVisuals(visuals);window.dispatchEvent(new CustomEvent('rist-depth-visuals',{detail:state.visuals}));};

 window.ristMotionPermission={
  state(){return state.permission;},
  async request(){return await requestPermission();}
 };

 function screenAdjusted(beta,gamma){
  const angle=(screen.orientation?.angle ?? window.orientation ?? 0);
  if(angle===90)return {beta:-gamma,gamma:beta};
  if(angle===-90||angle===270)return {beta:gamma,gamma:-beta};
  if(Math.abs(angle)===180)return {beta:-beta,gamma:-gamma};
  return {beta,gamma};
 }

 function visualFor(index){return state.visuals[index]||{};}
 function tierFor(index){
  const visual=visualFor(index);
  return Math.max(0,Number(visual.tierIndex??visual.TierIndex??0));
 }
 function layerFor(index){
  const visual=visualFor(index);
  return Math.max(0,Number(visual.layerOffset??visual.LayerOffset??0));
 }
 function depthFor(index){
  const tier=tierFor(index);
  const layer=layerFor(index);
  const strength=Number(window.ristParallax?.depthForTier?.(tier)??1);
  return Math.max(0,(tier+(layer/10))*Math.max(0,strength));
 }

 function clearLandingParallax(root){
  if(!root)return;
  for(const selector of ['.launcher-hero','.launcher-primary','.launcher-secondary','.launcher-footer']){
   const node=root.querySelector(selector);if(node){node.style.translate='';node.style.willChange='';}
  }
 }

 function applyLandingParallax(){
  const root=landing();
  if(!root)return;
  if(!userParallaxEnabled()){clearLandingParallax(root);return;}

  const hero=root.querySelector('.launcher-hero');
  const primary=root.querySelector('.launcher-primary');
  const secondary=root.querySelector('.launcher-secondary');
  const footer=root.querySelector('.launcher-footer');

  if(hero){hero.style.translate=`${(state.x*1.15).toFixed(2)}px ${(state.y*1.15).toFixed(2)}px`;hero.style.willChange='translate';}
  if(primary){primary.style.translate=`${(state.x*.42).toFixed(2)}px ${(state.y*.42).toFixed(2)}px`;primary.style.willChange='translate';}
  if(secondary){secondary.style.translate=`${(state.x*.24).toFixed(2)}px ${(state.y*.24).toFixed(2)}px`;secondary.style.willChange='translate';}
  if(footer){footer.style.translate=`${(state.x*.10).toFixed(2)}px ${(state.y*.10).toFixed(2)}px`;footer.style.willChange='translate';}
 }

 function clearWorldBuilderParallax(){
  const root=studio();if(!root)return;
  root.querySelectorAll('.world-stage .tile-cell').forEach(tile=>{tile.style.translate='';tile.style.willChange='';});
 }

 function applyWorldBuilderParallax(){
  if(!userParallaxEnabled()||!worldBuilderParallaxActive()){clearWorldBuilderParallax();return;}
  const list=tiles();
  if(list.length===0)return;
  const depths=list.map((_,index)=>depthFor(index));
  const maxDepth=Math.max(0,...depths);
  list.forEach((tile,index)=>{
   const depth=depths[index];
   const elevation=maxDepth>0?Math.min(1,depth/maxDepth):0;
   const dx=state.x*elevation;
   const dy=state.y*elevation;
   tile.style.translate=`${dx.toFixed(2)}px ${dy.toFixed(2)}px`;
   tile.style.willChange=elevation>0?'translate':'';
   tile.dataset.parallaxDepth=String(depth);
  });
 }

 function apply(){
  state.raf=0;
  state.x+=(state.targetX-state.x)*0.16;
  state.y+=(state.targetY-state.y)*0.16;
  applyLandingParallax();
  applyWorldBuilderParallax();
  const active=Math.abs(state.targetX-state.x)>.05||Math.abs(state.targetY-state.y)>.05;
  if(active)state.raf=requestAnimationFrame(apply);
 }

 function schedule(){if(!state.raf)state.raf=requestAnimationFrame(apply);}

 function onOrientation(event){
  if(!state.enabled||event.beta==null||event.gamma==null)return;
  const adjusted=screenAdjusted(Number(event.beta),Number(event.gamma));
  if(state.baselineBeta==null||state.baselineGamma==null){state.baselineBeta=adjusted.beta;state.baselineGamma=adjusted.gamma;}
  const beta=clamp(adjusted.beta-state.baselineBeta,-24,24);
  const gamma=clamp(adjusted.gamma-state.baselineGamma,-24,24);
  state.targetX=clamp(gamma*.62,-15,15);
  state.targetY=clamp(beta*.46,-12,12);
  schedule();
 }

 function enable(){
  if(state.enabled)return;
  state.enabled=true;
  state.permission='granted';
  state.baselineBeta=null;
  state.baselineGamma=null;
  window.addEventListener('deviceorientation',onOrientation,true);
  schedule();
 }

 async function requestPermission(){
  if(state.enabled)return state.permission;
  if(state.permissionAsked)return state.permission;
  state.permissionAsked=true;
  try{
   const Orientation=window.DeviceOrientationEvent;
   if(!Orientation){state.permission='unsupported';return state.permission;}
   if(typeof Orientation.requestPermission==='function'){
    const result=await Orientation.requestPermission();
    if(result==='granted')enable();else state.permission='denied';
   }else enable();
  }catch{state.permission='denied';}
  finally{state.permissionAsked=false;}
  return state.permission;
 }

 function resetForOrientationChange(){state.baselineBeta=null;state.baselineGamma=null;state.targetX=0;state.targetY=0;schedule();}

 function onPointerMove(event){
  const canvas=event.target?.closest?.('.worldbuilder-studio .studio-viewer-canvas');
  if(!canvas||!worldBuilderParallaxActive()||!userParallaxEnabled())return;
  const rect=canvas.getBoundingClientRect();if(rect.width<1||rect.height<1)return;
  state.targetX=clamp(((event.clientX-rect.left)/rect.width-.5)*18,-9,9);
  state.targetY=clamp(((event.clientY-rect.top)/rect.height-.5)*14,-7,7);
  schedule();
 }
 function onPointerOut(event){if(event.target?.closest?.('.studio-viewer-canvas')&&!event.relatedTarget?.closest?.('.studio-viewer-canvas')){state.targetX=0;state.targetY=0;schedule();}}

 window.addEventListener('orientationchange',resetForOrientationChange,{passive:true});
 screen.orientation?.addEventListener?.('change',resetForOrientationChange);
 window.addEventListener('rist-parallax-settings',schedule);
 document.addEventListener('pointermove',onPointerMove,{passive:true});
 document.addEventListener('pointerout',onPointerOut,{passive:true});

 if('DeviceOrientationEvent' in window&&typeof window.DeviceOrientationEvent?.requestPermission!=='function')enable();
 const observer=new MutationObserver(schedule);
 observer.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['class']});
})();
