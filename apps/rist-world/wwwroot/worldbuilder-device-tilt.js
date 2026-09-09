(()=>{
 'use strict';

 const state={
  enabled:false,
  permissionAsked:false,
  baselineBeta:null,
  baselineGamma:null,
  targetX:0,
  targetY:0,
  x:0,
  y:0,
  raf:0
 };

 const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
 const studio=()=>document.querySelector('.worldbuilder-studio');
 const viewer=()=>studio()?.querySelector('.studio-viewer-canvas');
 const tiles=()=>studio()?[...studio().querySelectorAll('.world-stage .tile-cell')]:[];

 function currentTier(){
  const buttons=studio()?.querySelectorAll('.studio-command-rail button')||[];
  for(const button of buttons){
   const strong=(button.querySelector('strong')?.textContent||'').trim().toLowerCase();
   if(strong!=='tiers')continue;
   const text=button.querySelector('small')?.textContent||'';
   const match=text.match(/tier\s*(-?\d+)/i);
   if(match)return Number(match[1])||0;
  }
  return 0;
 }

 function screenAdjusted(beta,gamma){
  const angle=(screen.orientation?.angle ?? window.orientation ?? 0);
  if(angle===90)return {beta:-gamma,gamma:beta};
  if(angle===-90||angle===270)return {beta:gamma,gamma:-beta};
  if(Math.abs(angle)===180)return {beta:-beta,gamma:-gamma};
  return {beta,gamma};
 }

 function apply(){
  state.raf=0;
  state.x+=(state.targetX-state.x)*0.16;
  state.y+=(state.targetY-state.y)*0.16;

  const tier=Math.max(0,currentTier());
  const elevation=tier===0?0:Math.min(2.4,0.85+(tier*.28));
  const dx=state.x*elevation;
  const dy=state.y*elevation;

  for(const tile of tiles()){
   tile.style.translate=`${dx.toFixed(2)}px ${dy.toFixed(2)}px`;
   tile.style.willChange='translate';
  }

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

  // The raised surface moves opposite the phone tilt, like looking across a
  // physical stacked board. The grid/ocean stay fixed as the reference plane.
  state.targetX=clamp(gamma*.62,-15,15);
  state.targetY=clamp(beta*.46,-12,12);
  schedule();
 }

 function enable(){
  if(state.enabled)return;
  state.enabled=true;
  state.baselineBeta=null;
  state.baselineGamma=null;
  window.addEventListener('deviceorientation',onOrientation,true);
 }

 async function requestFromGesture(){
  if(state.enabled||state.permissionAsked)return;
  state.permissionAsked=true;
  try{
   const Orientation=window.DeviceOrientationEvent;
   if(Orientation&&typeof Orientation.requestPermission==='function'){
    const result=await Orientation.requestPermission();
    if(result==='granted')enable();
    else state.permissionAsked=false;
   }else if('DeviceOrientationEvent' in window){
    enable();
   }
  }catch{
   state.permissionAsked=false;
  }
 }

 function bindViewer(){
  const target=viewer();
  if(!target||target.dataset.ristTiltBound==='1')return;
  target.dataset.ristTiltBound='1';
  // iOS requires motion permission to originate from a user gesture. The first
  // touch on the map requests it; after approval tilt remains passive.
  target.addEventListener('pointerup',requestFromGesture,{capture:true,passive:true});
  target.addEventListener('touchend',requestFromGesture,{capture:true,passive:true});
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

 bindViewer();
 const observer=new MutationObserver(()=>{bindViewer();if(state.enabled)schedule();});
 observer.observe(document.body,{childList:true,subtree:true});
})();
