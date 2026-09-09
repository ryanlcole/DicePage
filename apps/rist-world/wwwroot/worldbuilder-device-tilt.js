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
 const zUnlocked=()=>studio()?.classList.contains('wb-z-unlocked')===true;

 window.ristDepth={
  set(visuals){
   state.visuals=Array.isArray(visuals)?visuals:[];
   schedule();
  }
 };

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

 function depthFor(index){
  const visual=state.visuals[index]||{};
  const tier=Number(visual.tierIndex??visual.TierIndex??0);
  const layer=Number(visual.layerOffset??visual.LayerOffset??0);
  return Math.max(0,(tier*9)+layer);
 }

 function apply(){
  state.raf=0;
  state.x+=(state.targetX-state.x)*0.16;
  state.y+=(state.targetY-state.y)*0.16;

  const list=tiles();
  const depths=list.map((_,index)=>depthFor(index));
  const maxDepth=Math.max(0,...depths);
  const navigating=zUnlocked();

  list.forEach((tile,index)=>{
   const depth=depths[index];
   const elevation=navigating&&maxDepth>0?Math.min(1,depth/Math.max(1,maxDepth)):0;
   const dx=state.x*elevation;
   const dy=state.y*elevation;
   tile.style.translate=`${dx.toFixed(2)}px ${dy.toFixed(2)}px`;
   tile.style.willChange=elevation>0?'translate':'';
   tile.dataset.sceneZ=String(depth);
  });

  const active=Math.abs(state.targetX-state.x)>.05||Math.abs(state.targetY-state.y)>.05;
  if(active)state.raf=requestAnimationFrame(apply);
 }

 function schedule(){if(!state.raf)state.raf=requestAnimationFrame(apply);}

 function onOrientation(event){
  if(!state.enabled||event.beta==null||event.gamma==null)return;
  const adjusted=screenAdjusted(Number(event.beta),Number(event.gamma));
  if(state.baselineBeta==null||state.baselineGamma==null){
   state.baselineBeta=adjusted.beta;
   state.baselineGamma=adjusted.gamma;
  }
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
    if(result==='granted')enable();
    else state.permission='denied';
   }else{
    enable();
   }
  }catch{
   state.permission='denied';
  }finally{
   state.permissionAsked=false;
  }
  return state.permission;
 }

 function resetForOrientationChange(){
  state.baselineBeta=null;
  state.baselineGamma=null;
  state.targetX=0;
  state.targetY=0;
  schedule();
 }

 window.addEventListener('orientationchange',resetForOrientationChange,{passive:true});
 screen.orientation?.addEventListener?.('change',resetForOrientationChange);

 if('DeviceOrientationEvent' in window&&typeof window.DeviceOrientationEvent?.requestPermission!=='function')enable();
 const observer=new MutationObserver(schedule);
 observer.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['class']});
})();