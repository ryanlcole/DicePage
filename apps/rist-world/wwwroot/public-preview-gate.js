(()=>{
 'use strict';
 const SESSION_KEY='rist.session';
 const GAME_KEY='rist.gameStart.current';
 let capturePromise=null;
 let configPromise=null;
 let reconcileTimer=0;
 const hasSession=()=>!!sessionStorage.getItem(SESSION_KEY);
 const authReturn=()=>{const p=new URLSearchParams(location.search);return p.has('rist_handoff')||location.hash.includes('rist_session')};
 const app=()=>document.getElementById('app');
 const sleep=ms=>new Promise(r=>setTimeout(r,ms));
 function showApp(){const host=app();if(!host)return;host.style.removeProperty('visibility');host.style.removeProperty('display');host.style.removeProperty('pointer-events');host.removeAttribute('inert');host.removeAttribute('aria-hidden');document.documentElement.dataset.ristAuthRequired='0'}
 function hideApp(){const host=app();if(!host)return;host.style.visibility='hidden';host.style.pointerEvents='none';host.setAttribute('inert','');host.setAttribute('aria-hidden','true');document.documentElement.dataset.ristAuthRequired='1'}
 function openTitle(view='entry'){window.RistGameStartScreen?.open?.({authenticated:false,view})}
 function closeTitle(){window.RistGameStartScreen?.close?.()}
 function clearLegacyPreview(){sessionStorage.removeItem('rist-public-preview');delete document.documentElement.dataset.ristPublicPreview;document.querySelector('.rist-preview-badge')?.remove();const p=new URLSearchParams(location.search);if(p.has('preview')){p.delete('preview');history.replaceState(null,'',location.pathname+(p.toString()?'?'+p:'')+location.hash)}}
 async function getConfig(){if(configPromise)return configPromise;configPromise=fetch('auth-config.json',{cache:'no-store'}).then(r=>r.ok?r.json():null).catch(()=>null);return configPromise}
 async function waitForAuthApi(timeout=8000){const start=Date.now();while(Date.now()-start<timeout){if(window.ristAuth?.captureSession)return window.ristAuth;await sleep(40)}return null}
 async function captureReturn(){
  if(hasSession())return sessionStorage.getItem(SESSION_KEY);
  if(!authReturn())return null;
  if(capturePromise)return capturePromise;
  capturePromise=(async()=>{const [auth,cfg]=await Promise.all([waitForAuthApi(),getConfig()]);if(!auth?.captureSession||!cfg?.apiBaseUrl)return null;try{return await auth.captureSession(cfg.apiBaseUrl)}catch{return null}})().finally(()=>{capturePromise=null});
  return capturePromise;
 }
 async function forceDefaultGame(){
  try{localStorage.setItem('rist.gameStart.selection.v2',JSON.stringify({role:'Roleplayer',domain:'Shaelvien MMO'}));localStorage.setItem('rist.topFrame.userRole','Roleplayer');localStorage.setItem('rist.topFrame.domain','Shaelvien MMO')}catch{}
  const start=Date.now();
  while(Date.now()-start<7000){const mode=document.querySelector('.mmo-zone-actions[data-world-mode]')?.dataset.worldMode||document.querySelector('.map-shell[data-world-mode]')?.dataset.worldMode||'';const role=document.querySelector('.mmo-zone-actions[data-world-role]')?.dataset.worldRole||'';if(mode==='mmo'&&role==='PC')break;if(mode!=='mmo')document.querySelector('.mmo-mode-shaelvien-action')?.click();if(role!=='PC')document.querySelector('.mmo-role-player-action')?.click();await sleep(100)}
 }
 async function enterGame(){showApp();closeTitle();document.body.classList.remove('rist-game-start-open');await forceDefaultGame();sessionStorage.setItem(GAME_KEY,JSON.stringify({role:'Roleplayer',domain:'Shaelvien MMO',kind:'direct'}));document.dispatchEvent(new CustomEvent('rist:game-start',{detail:{role:'Roleplayer',domain:'Shaelvien MMO',kind:'direct'}}));requestAnimationFrame(()=>{showApp();window.dispatchEvent(new Event('resize'));document.dispatchEvent(new CustomEvent('rist:resume'))})}
 async function reconcile(){clearLegacyPreview();if(hasSession()){window.ristAuth?.installIdleExpiry?.();await enterGame();return}hideApp();if(authReturn()){openTitle('authwait');const token=await captureReturn();if(token){window.ristAuth?.installIdleExpiry?.();await enterGame();return}if(authReturn()){openTitle('authwait');return}}sessionStorage.removeItem(GAME_KEY);openTitle('entry')}
 function queueReconcile(delay=0){clearTimeout(reconcileTimer);reconcileTimer=setTimeout(()=>void reconcile(),delay)}
 function start(){clearLegacyPreview();if(hasSession()){void enterGame();return}hideApp();if(authReturn()){openTitle('authwait');void captureReturn().then(token=>{if(token)void enterGame();else queueReconcile(250)});return}openTitle('entry')}
 addEventListener('pageshow',()=>{queueReconcile(0);setTimeout(()=>queueReconcile(0),180)});
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)queueReconcile(30)});
 addEventListener('focus',()=>queueReconcile(60));
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.RistAuthGate={reconcile,hasSession,captureReturn};
})();