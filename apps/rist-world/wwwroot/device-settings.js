(()=>{
 'use strict';

 const PARALLAX_KEY='rist.parallax.enabled.v1';
 const PARALLAX_ACTIVE_KEY='rist.parallax.worldbuilder.active.v1';
 const AUDIO_KEY='rist.audio.enabled.v1';
 const VIDEO_KEY='rist.video.enabled.v1';
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

 const MIC_SESSION_KEY='rist.microphone.permission.v1';
 const AUDIO_SESSION_KEY='rist.audio.unlock.v1';
 const audioCtor=()=>window.AudioContext||window.webkitAudioContext||null;
 let startAudioContext=null;
 async function unlockAudio(){
  if(read(sessionStorage,AUDIO_SESSION_KEY,'')==='unlocked')return 'unlocked';
  const Ctor=audioCtor();
  if(!Ctor)return 'unsupported';
  try{
   startAudioContext=startAudioContext||new Ctor();
   const resume=startAudioContext.resume?.();
   if(resume&&typeof resume.then==='function')await resume;
   const status=startAudioContext.state==='running'?'unlocked':'blocked';
   if(status==='unlocked')write(sessionStorage,AUDIO_SESSION_KEY,status);
   return status;
  }catch{return 'blocked'}
 }
 async function requestMicrophone(){
  const cached=read(sessionStorage,MIC_SESSION_KEY,'');
  if(cached==='granted'||cached==='denied'||cached==='unsupported')return cached;
  const gum=navigator.mediaDevices?.getUserMedia?.bind(navigator.mediaDevices);
  if(!gum){write(sessionStorage,MIC_SESSION_KEY,'unsupported');return 'unsupported'}
  try{
   const stream=await gum({audio:true,video:false});
   stream?.getTracks?.().forEach(track=>track.stop());
   write(sessionStorage,MIC_SESSION_KEY,'granted');
   return 'granted';
  }catch(error){
   const name=String(error?.name||'');
   const status=name==='NotAllowedError'||name==='SecurityError'?'denied':'unavailable';
   if(status==='denied')write(sessionStorage,MIC_SESSION_KEY,status);
   return status;
  }
 }
 window.ristDeviceCapabilities={
  audioState:()=>read(sessionStorage,AUDIO_SESSION_KEY,'prompt'),
  microphoneState:()=>read(sessionStorage,MIC_SESSION_KEY,navigator.mediaDevices?.getUserMedia?'prompt':'unsupported'),
  async requestAtStart({motion=true,microphone=true,audio=true}={}){
   // Audio must be opened from the user's Start gesture. Browser permission
   // prompts for motion and microphone follow from the same explicit action.
   const audioPromise=audio?unlockAudio():Promise.resolve('disabled');
   let motionStatus='disabled';
   if(motion)try{motionStatus=await window.ristMotionPermission?.request?.()||'unsupported'}catch{motionStatus='denied'}
   let microphoneStatus='disabled';
   if(microphone)microphoneStatus=await requestMicrophone();
   const audioStatus=await audioPromise;
   const detail={audio:audioStatus,motion:motionStatus,microphone:microphoneStatus};
   dispatchEvent(new CustomEvent('rist-device-capabilities',{detail}));
   return detail;
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
 const sessionPrefKey=key=>key+'.session';
 const preferenceExists=key=>{try{return localStorage.getItem(key)!==null}catch{return false}};
 const prefValue=(key,fallback='on')=>{const session=read(sessionStorage,sessionPrefKey(key),'');return session||read(localStorage,key,fallback)};
 const boolPref=(key,fallback=true)=>prefValue(key,fallback?'on':'off')==='on';
 const persistAllowed=()=>{try{return window.ristPrivacy?.allowsOptional?.()===true}catch{return false}};
 const writePreference=(key,value,persist=persistAllowed())=>{
  const text=value?'on':'off';
  if(persist){write(localStorage,key,text);try{sessionStorage.removeItem(sessionPrefKey(key))}catch{}}
  else write(sessionStorage,sessionPrefKey(key),text);
 };
 const mediaState=()=>({audio:boolPref(AUDIO_KEY,true),video:boolPref(VIDEO_KEY,true)});
 const applyMediaState=()=>{
  const state=mediaState();
  document.documentElement.dataset.ristAudio=state.audio?'on':'off';
  document.documentElement.dataset.ristVideo=state.video?'on':'off';
  document.querySelectorAll('audio,video').forEach(node=>{
   if(!state.audio){
    if(!node.muted)node.dataset.ristMutedByPreference='1';
    node.muted=true;
   }else if(node.dataset.ristMutedByPreference==='1'){
    node.muted=false;
    delete node.dataset.ristMutedByPreference;
   }
   if(node.tagName==='VIDEO'){
    if(!state.video){
     if(!node.hidden)node.dataset.ristHiddenByPreference='1';
     node.hidden=true;
     try{node.pause()}catch{}
    }else if(node.dataset.ristHiddenByPreference==='1'){
     node.hidden=false;
     delete node.dataset.ristHiddenByPreference;
    }
   }
  });
  dispatchEvent(new CustomEvent('rist-media-settings',{detail:state}));
  return state;
 };
 window.ristMediaSettings={
  isAudioEnabled:()=>mediaState().audio,
  isVideoEnabled:()=>mediaState().video,
  setAudioEnabled(value){writePreference(AUDIO_KEY,!!value);return applyMediaState().audio},
  setVideoEnabled(value){writePreference(VIDEO_KEY,!!value);return applyMediaState().video},
  settings:mediaState,
  initializeAtStart(persistPreferences=false){
   const persist=!!persistPreferences;
   for(const key of [PARALLAX_KEY,PARALLAX_ACTIVE_KEY,AUDIO_KEY,VIDEO_KEY]){
    if(preferenceExists(key)){try{sessionStorage.removeItem(sessionPrefKey(key))}catch{}}
    else writePreference(key,true,persist);
   }
   const parallax=boolPref(PARALLAX_KEY,true);
   const active=boolPref(PARALLAX_ACTIVE_KEY,true);
   try{window.ristParallax?.setEnabled?.(parallax);window.ristParallax?.setActive?.(active)}catch{}
   const media=applyMediaState();
   return [parallax,media.audio,media.video];
  }
 };
 const observeMedia=()=>{applyMediaState();new MutationObserver(m=>{if(m.some(x=>[...x.addedNodes].some(n=>n.nodeType===1&&(n.matches?.('audio,video')||n.querySelector?.('audio,video')))))applyMediaState()}).observe(document.body,{childList:true,subtree:true})};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',observeMedia,{once:true});else observeMedia();

 if(!window.ristParallax){
  const getEnabled=()=>boolPref(PARALLAX_KEY,false);
  const getActive=()=>boolPref(PARALLAX_ACTIVE_KEY,false);
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
   setEnabled(value){const next=!!value;writePreference(PARALLAX_KEY,next);emit();return next},
   setActive(value){const next=!!value;writePreference(PARALLAX_ACTIVE_KEY,next);emit();return next},
   activateForSession(persist=false){
    writePreference(PARALLAX_KEY,true,!!persist);
    writePreference(PARALLAX_ACTIVE_KEY,true,!!persist);
    emit();
    return true;
   },
   setTiltStrength:setTilt,
   resetTilt:()=>setTilt(DEFAULT_TILT),
   depthForTier:getTilt,
   setTierDepth:(_tier,value)=>setTilt(value),
   getTierDepths:()=>({viewerTilt:getTilt()})
  };
 }

 // Permission is only the browser gate. Once motion events are available this
 // listener remains active continuously; the saved Parallax preference alone
 // decides whether the landing artwork renders the motion.
 const landingRoot=()=>document.querySelector('.rist-game-start');
 const landingEnabled=()=>{
  const root=landingRoot();
  if(!root||root.hidden)return false;
  return typeof window.ristParallax?.isEnabled==='function'
   ? !!window.ristParallax.isEnabled()
   : boolPref(PARALLAX_KEY,false);
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