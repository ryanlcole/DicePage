(()=>{
 'use strict';
 const authReturn=()=>{const p=new URLSearchParams(location.search);return p.has('rist_handoff')||location.hash.includes('rist_session')};
 const hasSession=()=>!!sessionStorage.getItem('rist.session');
 const gameStarted=()=>!!sessionStorage.getItem('rist.gameStart.current');
 let earlyAuthStarted=false,authPollTimer=0;
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
 function finishAuthenticated(){
  clearInterval(authPollTimer);authPollTimer=0;earlyAuthStarted=false;
  clearLegacyPreview();
  setGameAccess(true);
  if(gameStarted())window.RistGameStartScreen?.close?.();else openTitle(true);
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
   if(hasSession()){finishAuthenticated();return}
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
     if(hasSession())return Promise.resolve(sessionStorage.getItem('rist.session'));
     if(inFlight)return inFlight;
     inFlight=Promise.resolve(original(apiBase)).finally(()=>{inFlight=null});
     return inFlight;
    };
   }
   fetch('auth-config.json',{cache:'no-store'})
    .then(r=>r.ok?r.json():null)
    .then(cfg=>cfg?.apiBaseUrl?auth.captureSession(cfg.apiBaseUrl):null)
    .then(token=>{if(token||hasSession())finishAuthenticated();else{earlyAuthStarted=false;setGameAccess(false);openTitle(false,'entry')}})
    .catch(()=>{earlyAuthStarted=false;if(hasSession())finishAuthenticated();else{setGameAccess(false);openTitle(false,'entry')}});
  };
  waitForAuth();
 }
 function reconcileAuth(){
  clearLegacyPreview();
  if(hasSession()){
   finishAuthenticated();
   window.ristAuth?.installIdleExpiry?.();
   return;
  }
  setGameAccess(false);
  if(authReturn()){
   beginEarlyAuth(true);
   return;
  }
  if(gameStarted())sessionStorage.removeItem('rist.gameStart.current');
  openTitle(false,'entry');
 }
 function start(){
  clearLegacyPreview();
  setGameAccess(hasSession());
  if(hasSession()){finishAuthenticated();return}
  if(authReturn()){
   openTitle(false,'authwait');beginEarlyAuth();
   let attempts=0;clearInterval(authPollTimer);authPollTimer=setInterval(()=>{if(hasSession()){finishAuthenticated()}else if(++attempts>=120){clearInterval(authPollTimer);authPollTimer=0;earlyAuthStarted=false;setGameAccess(false);openTitle(false,'entry')}},100);
   return;
  }
  setGameAccess(false);
  openTitle(false,'splash');
 }
 // Safari/iOS may suspend during Discord or app switching and later restore
 // from BFCache. Always re-check the bearer session before exposing the game.
 addEventListener('pageshow',()=>{setTimeout(reconcileAuth,0);setTimeout(reconcileAuth,180)});
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)setTimeout(reconcileAuth,40)});
 addEventListener('focus',()=>setTimeout(reconcileAuth,40));
 beginEarlyAuth();
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.RistAuthGate={reconcile:reconcileAuth,hasSession};
})();
