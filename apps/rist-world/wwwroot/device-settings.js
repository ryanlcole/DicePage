(()=>{
 'use strict';

 const PARALLAX_KEY='rist.parallax.enabled.v1';
 const PARALLAX_ACTIVE_KEY='rist.parallax.worldbuilder.active.v1';
 const TILT_KEY='rist.parallax.tilt-strength.v2';
 const MOTION_SESSION_KEY='rist.motion.permission.v1';
 const DEFAULT_TILT=.65;
 const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
 const read=(store,key,fallback)=>{try{return store.getItem(key)??fallback}catch{return fallback}};
 const write=(store,key,value)=>{try{store.setItem(key,String(value))}catch{}};

 const orientationCtor=()=>typeof window.DeviceOrientationEvent==='undefined'?null:window.DeviceOrientationEvent;
 const motionCtor=()=>typeof window.DeviceMotionEvent==='undefined'?null:window.DeviceMotionEvent;
 const motionAvailable=()=>!!(orientationCtor()||motionCtor());
 const permissionRequester=()=>{
  const orientation=orientationCtor();
  if(orientation&&typeof orientation.requestPermission==='function')return ()=>orientation.requestPermission();
  const motion=motionCtor();
  if(motion&&typeof motion.requestPermission==='function')return ()=>motion.requestPermission();
  return null;
 };
 const rememberMotion=status=>{if(status==='granted'||status==='denied')write(sessionStorage,MOTION_SESSION_KEY,status);return status};

 window.ristMotionPermission={
  state(){
   if(!motionAvailable())return 'unsupported';
   const cached=read(sessionStorage,MOTION_SESSION_KEY,'');
   if(cached==='granted'||cached==='denied')return cached;
   return permissionRequester()?'prompt':'granted';
  },
  async request(){
   if(!motionAvailable())return 'unsupported';
   const requester=permissionRequester();
   if(!requester)return rememberMotion('granted');
   try{
    const result=await requester();
    return rememberMotion(result==='granted'?'granted':'denied');
   }catch{
    return rememberMotion('denied');
   }
  }
 };

 const fullscreenElement=()=>document.fullscreenElement||document.webkitFullscreenElement||null;
 const fullscreenRequest=()=>{
  const el=document.documentElement;
  if(typeof el.requestFullscreen==='function')return ()=>el.requestFullscreen();
  if(typeof el.webkitRequestFullscreen==='function')return ()=>el.webkitRequestFullscreen();
  return null;
 };
 const fullscreenExit=()=>{
  if(typeof document.exitFullscreen==='function')return ()=>document.exitFullscreen();
  if(typeof document.webkitExitFullscreen==='function')return ()=>document.webkitExitFullscreen();
  return null;
 };
 const fullscreenSupported=()=>!!fullscreenRequest();
 window.ristFullscreen={
  state:()=>[!!fullscreenElement(),fullscreenSupported()],
  async toggle(){
   try{
    if(fullscreenElement()){
     const exit=fullscreenExit();
     if(exit)await exit();
    }else{
     const request=fullscreenRequest();
     if(request)await request();
    }
   }catch{}
   return [!!fullscreenElement(),fullscreenSupported()];
  }
 };

 // Base-runtime preference bridge. parallax-mode.js replaces this with the
 // full Worldbuilder controller when that workspace loads, using the same keys.
 if(!window.ristParallax){
  const getEnabled=()=>read(localStorage,PARALLAX_KEY,'off')==='on';
  const getActive=()=>read(localStorage,PARALLAX_ACTIVE_KEY,'off')==='on';
  const getTilt=()=>{
   const value=Number(read(localStorage,TILT_KEY,String(DEFAULT_TILT)));
   return Number.isFinite(value)?clamp(value,0,1):DEFAULT_TILT;
  };
  const emit=()=>window.dispatchEvent(new CustomEvent('rist-parallax-settings',{detail:{enabled:getEnabled(),active:getActive(),tiltStrength:getTilt(),truth:'tier-layer',projection:'top-layer-transition'}}));
  const setTilt=value=>{const next=clamp(Number(value)||0,0,1);write(localStorage,TILT_KEY,next.toFixed(3));emit();return next};
  window.ristParallax={
   isEnabled:getEnabled,
   isWorldBuilderActive:getActive,
   tiltStrength:getTilt,
   settings:()=>({enabled:getEnabled(),active:getActive(),tiltStrength:getTilt()}),
   setEnabled(value){const next=!!value;write(localStorage,PARALLAX_KEY,next?'on':'off');emit();return next},
   setActive(value){const next=!!value;write(localStorage,PARALLAX_ACTIVE_KEY,next?'on':'off');emit();return next},
   setTiltStrength:setTilt,
   resetTilt:()=>setTilt(DEFAULT_TILT),
   depthForTier:getTilt,
   setTierDepth:(_tier,value)=>setTilt(value),
   getTierDepths:()=>({viewerTilt:getTilt()})
  };
 }

 // The landing image is always listening for tilt. iOS permission is only the
 // one-time browser gate; after events are available, this stays continuously
 // reactive while the landing screen is visible and Parallax is On.
 const landingRoot=()=>document.querySelector('.rist-game-start');
 const landingEnabled=()=>{
  const root=landingRoot();
  if(!root||root.hidden)return false;
  if(window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches)return false;
  return typeof window.ristParallax?.isEnabled==='function'
   ? !!window.ristParallax.isEnabled()
   : read(localStorage,PARALLAX_KEY,'off')==='on';
 };
 const screenAxes=(beta,gamma)=>{
  const raw=Number(window.screen?.orientation?.angle??window.orientation??0);
  const angle=((raw%360)+360)%360;
  if(angle===90)return{x:beta,y:-gamma};
  if(angle===270)return{x:-beta,y:gamma};
  if(angle===180)return{x:-gamma,y:-beta};
  return{x:gamma,y:beta};
 };
 let baseline=null;
 let currentX=0,currentY=0,targetX=0,targetY=0,frame=0;
 const renderLandingTilt=()=>{
  frame=0;
  const root=landingRoot();
  if(!root)return;
  currentX+=(targetX-currentX)*.28;
  currentY+=(targetY-currentY)*.28;
  root.style.setProperty('--rist-landing-tilt-x',`${currentX.toFixed(2)}px`);
  root.style.setProperty('--rist-landing-tilt-y',`${currentY.toFixed(2)}px`);
  if(Math.abs(targetX-currentX)>.04||Math.abs(targetY-currentY)>.04)frame=requestAnimationFrame(renderLandingTilt);
 };
 const scheduleLandingTilt=()=>{if(!frame)frame=requestAnimationFrame(renderLandingTilt)};
 const resetLandingTilt=()=>{
  baseline=null;
  targetX=0;
  targetY=0;
  scheduleLandingTilt();
 };
 addEventListener('deviceorientation',event=>{
  if(!landingEnabled()){
   if(targetX||targetY||currentX||currentY)resetLandingTilt();
   return;
  }
  const beta=Number(event.beta),gamma=Number(event.gamma);
  if(!Number.isFinite(beta)||!Number.isFinite(gamma))return;
  const axes=screenAxes(beta,gamma);
  if(!baseline){baseline={x:axes.x,y:axes.y};return;}
  const strength=clamp(Number(window.ristParallax?.tiltStrength?.()??DEFAULT_TILT),0,1);
  targetX=clamp((axes.x-baseline.x)/22,-1,1)*30*strength;
  targetY=clamp((axes.y-baseline.y)/22,-1,1)*22*strength;
  scheduleLandingTilt();
 },{passive:true});
 addEventListener('orientationchange',resetLandingTilt,{passive:true});
 addEventListener('rist:landing-parallax-changed',resetLandingTilt);
 addEventListener('rist-parallax-settings',resetLandingTilt);
})();