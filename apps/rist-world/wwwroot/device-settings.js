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
})();