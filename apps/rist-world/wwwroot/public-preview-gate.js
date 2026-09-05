(()=>{
 'use strict';
 const LOCK_LABELS=new Set(['settings','chat','add files','add file','load','save','library']);
 const norm=s=>(s||'').replace(/\s+/g,' ').trim().toLowerCase();
 const isLockedControl=el=>LOCK_LABELS.has(norm(el.getAttribute?.('aria-label')||el.getAttribute?.('title')||el.textContent));
 const authReturn=()=>{const p=new URLSearchParams(location.search);return p.has('rist_handoff')||location.hash.includes('rist_session')};
 const hasSession=()=>!!sessionStorage.getItem('rist.session');
 const gameStarted=()=>!!sessionStorage.getItem('rist.gameStart.current');
 let earlyAuthStarted=false,authPollTimer=0,observerStarted=false;
 function lockPreview(){
  document.documentElement.dataset.ristPublicPreview='1';
  sessionStorage.setItem('rist-public-preview','1');
  if(!document.querySelector('.rist-preview-badge')){const b=document.createElement('div');b.className='rist-preview-badge';b.textContent='PUBLIC PREVIEW';document.body.append(b)}
  scanLocks();
 }
 function scanLocks(){
  if(document.documentElement.dataset.ristPublicPreview!=='1')return;
  document.querySelectorAll('button,a,[role="button"],[role="menuitem"],[role="tab"],label').forEach(el=>{if(el.closest('.rist-game-start'))return;if(isLockedControl(el)){el.dataset.previewLocked='1';el.setAttribute('aria-disabled','true');el.title='Locked in public preview'}});
  document.querySelectorAll('input[type="file"]').forEach(el=>{el.dataset.previewLocked='1';el.disabled=true});
  document.querySelectorAll('[contenteditable="true"],input,textarea,select').forEach(el=>{const host=el.closest('[class*="character" i],[id*="character" i],[class*="sheet" i],[id*="sheet" i]');if(host){el.dataset.previewLocked='1';if('readOnly' in el)el.readOnly=true;if('disabled' in el&&el.tagName==='SELECT')el.disabled=true;el.setAttribute('aria-readonly','true')}});
 }
 function blockLocked(event){
  if(document.documentElement.dataset.ristPublicPreview!=='1')return;
  const target=event.target instanceof Element?event.target.closest('button,a,[role="button"],[role="menuitem"],[role="tab"],label,input,textarea,select,[contenteditable]'):null;
  if(!target||target.closest('.rist-game-start'))return;
  if(target.dataset.previewLocked==='1'||isLockedControl(target)){event.preventDefault();event.stopPropagation();event.stopImmediatePropagation()}
 }
 function openTitle(authenticated=false,view){window.RistGameStartScreen?.open?.(authenticated?{authenticated:true}:{authenticated:false,view})}
 function finishAuthenticated(){
  clearInterval(authPollTimer);authPollTimer=0;earlyAuthStarted=false;
  if(gameStarted())window.RistGameStartScreen?.close?.();else openTitle(true);
 }
 function beginEarlyAuth(force=false){
  if(!authReturn())return;
  if(force)earlyAuthStarted=false;
  if(earlyAuthStarted)return;
  earlyAuthStarted=true;
  openTitle(false,'authwait');
  const started=Date.now();
  const waitForAuth=()=>{
   if(hasSession()){finishAuthenticated();return}
   const auth=window.ristAuth;
   if(!auth?.captureSession){
    if(Date.now()-started<8000)setTimeout(waitForAuth,25);else{earlyAuthStarted=false;openTitle(false,'entry')}
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
    .then(token=>{if(token||hasSession())finishAuthenticated();else{earlyAuthStarted=false;openTitle(false,'entry')}})
    .catch(()=>{earlyAuthStarted=false;if(hasSession())finishAuthenticated();else openTitle(false,'entry')});
  };
  waitForAuth();
 }
 function reconcileAuth(){
  if(document.documentElement.dataset.ristPublicPreview==='1')return;
  if(hasSession()){
   finishAuthenticated();
   window.ristAuth?.installIdleExpiry?.();
   return;
  }
  if(authReturn()){
   beginEarlyAuth(true);
   return;
  }
  // A suspended iOS tab can restore with the start overlay hidden while the
  // bearer session has been discarded. Never leave that as a black screen.
  if(gameStarted())sessionStorage.removeItem('rist.gameStart.current');
  openTitle(false,'entry');
 }
 function start(){
  const params=new URLSearchParams(location.search);
  const alreadyPreview=params.get('preview')==='1'||sessionStorage.getItem('rist-public-preview')==='1';
  if(alreadyPreview){lockPreview();window.RistGameStartScreen?.close?.();observe();return}
  if(hasSession()){finishAuthenticated();observe();return}
  if(authReturn()){
   openTitle(false,'authwait');beginEarlyAuth();
   let attempts=0;clearInterval(authPollTimer);authPollTimer=setInterval(()=>{if(hasSession()){finishAuthenticated()}else if(++attempts>=120){clearInterval(authPollTimer);authPollTimer=0;earlyAuthStarted=false;openTitle(false,'entry')}},100);
   observe();return;
  }
  openTitle(false,'splash');observe();
 }
 function observe(){if(observerStarted)return;observerStarted=true;new MutationObserver(()=>requestAnimationFrame(scanLocks)).observe(document.getElementById('app')||document.body,{childList:true,subtree:true})}
 document.addEventListener('click',blockLocked,true);
 document.addEventListener('pointerdown',blockLocked,true);
 document.addEventListener('rist:preview-request',()=>{lockPreview();requestAnimationFrame(scanLocks)});
 // Safari/iOS may suspend this page during Discord or app switching and later
 // restore it from BFCache. Reconcile from persisted storage every time it
 // becomes active instead of trusting stale in-memory auth/start-screen state.
 addEventListener('pageshow',()=>{setTimeout(reconcileAuth,0);setTimeout(reconcileAuth,180)});
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)setTimeout(reconcileAuth,40)});
 addEventListener('focus',()=>setTimeout(reconcileAuth,40));
 beginEarlyAuth();
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
