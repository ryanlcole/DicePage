(()=>{
 'use strict';
 const authReturn=()=>{const p=new URLSearchParams(location.search);return p.has('rist_handoff')||location.hash.includes('rist_session')};
 const storedToken=()=>sessionStorage.getItem('rist.session')||'';
 const gameStarted=()=>!!sessionStorage.getItem('rist.gameStart.current');
 let earlyAuthStarted=false,authPollTimer=0,authConfigPromise=null,validationInFlight=null,validatedToken='';
 function app(){return document.getElementById('app')}
 function clearLegacyPreview(){
  sessionStorage.removeItem('rist-public-preview');
  delete document.documentElement.dataset.ristPublicPreview;
  document.querySelector('.rist-preview-badge')?.remove();
  const params=new URLSearchParams(location.search);
  if(params.has('preview')){
   params.delete('preview');
   const clean=params.toString();
   history.replaceState(null,'',location.pathname+(clean?'?'+clean:'')+location.hash);
  }
 }
 function setGameAccess(allowed){
  const host=app();
  document.documentElement.dataset.ristAuthRequired=allowed?'0':'1';
  if(!host)return;
  if(allowed){
   host.style.removeProperty('visibility');
   host.style.removeProperty('pointer-events');
   host.removeAttribute('inert');
   host.removeAttribute('aria-hidden');
  }else{
   host.style.visibility='hidden';
   host.style.pointerEvents='none';
   host.setAttribute('inert','');
   host.setAttribute('aria-hidden','true');
  }
 }
 function openTitle(authenticated=false,view){window.RistGameStartScreen?.open?.(authenticated?{authenticated:true}:{authenticated:false,view})}
 function getAuthConfig(){
  if(authConfigPromise)return authConfigPromise;
  authConfigPromise=fetch('auth-config.json',{cache:'no-store'}).then(r=>r.ok?r.json():null).catch(()=>null).finally(()=>{setTimeout(()=>{authConfigPromise=null},15000)});
  return authConfigPromise;
 }
 function clearInvalidSession(){
  validatedToken='';
  window.ristAuth?.clearSession?.();
  sessionStorage.removeItem('rist.session');
  sessionStorage.removeItem('rist.lastActivity');
  sessionStorage.removeItem('rist.gameStart.current');
 }
 async function validateStoredSession(force=false){
  const token=storedToken();
  if(!token)return false;
  if(!force&&validatedToken===token)return true;
  if(validationInFlight)return validationInFlight;
  validationInFlight=(async()=>{
   const cfg=await getAuthConfig();
   const apiBase=String(cfg?.apiBaseUrl||'').replace(/\/$/,'');
   if(!apiBase)return false;
   try{
    const response=await fetch(apiBase+'/me',{cache:'no-store',headers:{Authorization:'Bearer '+token}});
    if(response.ok){validatedToken=token;return true}
    if(response.status===401||response.status===403)clearInvalidSession();
    return false;
   }catch{return false}
  })().finally(()=>{validationInFlight=null});
  return validationInFlight;
 }
 function finishAuthenticated(){
  clearInterval(authPollTimer);authPollTimer=0;earlyAuthStarted=false;
  clearLegacyPreview();
  setGameAccess(true);
  window.ristAuth?.installIdleExpiry?.();
  if(gameStarted())window.RistGameStartScreen?.close?.();else openTitle(true);
 }
 async function validateAndFinish({force=false,fallback='entry'}={}){
  setGameAccess(false);
  openTitle(false,'authwait');
  if(await validateStoredSession(force)){finishAuthenticated();return true}
  setGameAccess(false);
  if(!storedToken()&&gameStarted())sessionStorage.removeItem('rist.gameStart.current');
  openTitle(false,fallback);
  return false;
 }
 function beginEarlyAuth(force=false){
  if(!authReturn())return;
  if(force)earlyAuthStarted=false;
  if(earlyAuthStarted)return;
  earlyAuthStarted=true;
  setGameAccess(false);
  openTitle(false,'authwait');
  const started=Date.now();
  const waitForAuth=()=>{
   const auth=window.ristAuth;
   if(!auth?.captureSession){
    if(Date.now()-started<8000)setTimeout(waitForAuth,25);else{earlyAuthStarted=false;setGameAccess(false);openTitle(false,'entry')}
    return;
   }
   if(!auth._earlyCaptureWrapped){
    auth._earlyCaptureWrapped=true;
    const original=auth.captureSession.bind(auth);
    let inFlight=null;
    auth.captureSession=apiBase=>{
     if(inFlight)return inFlight;
     inFlight=Promise.resolve(original(apiBase)).finally(()=>{inFlight=null});
     return inFlight;
    };
   }
   getAuthConfig()
    .then(cfg=>cfg?.apiBaseUrl?auth.captureSession(cfg.apiBaseUrl):null)
    .then(async token=>{
     earlyAuthStarted=false;
     if(token||storedToken())await validateAndFinish({force:true,fallback:'entry'});
     else{setGameAccess(false);openTitle(false,'entry')}
    })
    .catch(()=>{earlyAuthStarted=false;setGameAccess(false);openTitle(false,'entry')});
  };
  waitForAuth();
 }
 async function reconcileAuth(){
  clearLegacyPreview();
  setGameAccess(false);
  if(authReturn()){
   beginEarlyAuth(true);
   return;
  }
  if(storedToken()){
   await validateAndFinish({force:true,fallback:'entry'});
   return;
  }
  if(gameStarted())sessionStorage.removeItem('rist.gameStart.current');
  openTitle(false,'entry');
 }
 async function start(){
  clearLegacyPreview();
  setGameAccess(false);
  if(authReturn()){
   openTitle(false,'authwait');beginEarlyAuth();
   let attempts=0;clearInterval(authPollTimer);authPollTimer=setInterval(async()=>{
    if(storedToken()){
     clearInterval(authPollTimer);authPollTimer=0;
     await validateAndFinish({force:true,fallback:'entry'});
    }else if(++attempts>=120){
     clearInterval(authPollTimer);authPollTimer=0;earlyAuthStarted=false;setGameAccess(false);openTitle(false,'entry');
    }
   },100);
   return;
  }
  if(storedToken()){
   await validateAndFinish({force:true,fallback:'entry'});
   return;
  }
  openTitle(false,'splash');
 }
 // Safari/iOS may suspend during Discord or app switching and later restore
 // from BFCache. Revalidate with the server before exposing the game; the
 // presence of a browser token alone is never sufficient authorization.
 addEventListener('pageshow',()=>{setTimeout(reconcileAuth,0);setTimeout(reconcileAuth,180)});
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)setTimeout(reconcileAuth,40)});
 addEventListener('focus',()=>setTimeout(reconcileAuth,40));
 setGameAccess(false);
 beginEarlyAuth();
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.RistAuthGate={reconcile:reconcileAuth,hasSession:()=>validatedToken!==''&&validatedToken===storedToken(),validate:validateStoredSession};
})();
