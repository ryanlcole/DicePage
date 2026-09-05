(()=>{
 'use strict';
 const hasSession=()=>!!sessionStorage.getItem('rist.session');
 const gameStarted=()=>!!sessionStorage.getItem('rist.gameStart.current');
 const authReturn=()=>{const p=new URLSearchParams(location.search);return p.has('rist_handoff')||location.hash.includes('rist_session')};
 let authTimer=0;
 function app(){return document.getElementById('app')}
 function showApp(){const host=app();if(!host)return;host.style.removeProperty('visibility');host.style.removeProperty('display');host.style.removeProperty('pointer-events');host.removeAttribute('inert');host.removeAttribute('aria-hidden');document.documentElement.dataset.ristAuthRequired='0'}
 function hideApp(){const host=app();if(!host)return;host.style.visibility='hidden';host.style.pointerEvents='none';host.setAttribute('inert','');host.setAttribute('aria-hidden','true');document.documentElement.dataset.ristAuthRequired='1'}
 function clearPreview(){sessionStorage.removeItem('rist-public-preview');delete document.documentElement.dataset.ristPublicPreview;document.querySelector('.rist-preview-badge')?.remove();const p=new URLSearchParams(location.search);if(p.has('preview')){p.delete('preview');history.replaceState(null,'',location.pathname+(p.toString()?'?'+p:'')+location.hash)}}
 function openTitle(authenticated=false,view){window.RistGameStartScreen?.open?.(authenticated?{authenticated:true}:{authenticated:false,view})}
 function recoverGame(){showApp();document.body.classList.remove('rist-game-start-open');window.RistGameStartScreen?.close?.();requestAnimationFrame(()=>{showApp();window.dispatchEvent(new Event('resize'));document.dispatchEvent(new CustomEvent('rist:resume'))})}
 function waitForSession(){clearInterval(authTimer);let attempts=0;authTimer=setInterval(()=>{if(hasSession()){clearInterval(authTimer);authTimer=0;gameStarted()?recoverGame():(showApp(),openTitle(true));return}if(++attempts>=120){clearInterval(authTimer);authTimer=0;hideApp();openTitle(false,'entry')}},100)}
 function reconcile(){clearPreview();if(hasSession()){if(gameStarted())recoverGame();else{showApp();openTitle(true)}window.ristAuth?.installIdleExpiry?.();return}hideApp();if(authReturn()){openTitle(false,'authwait');waitForSession();return}sessionStorage.removeItem('rist.gameStart.current');openTitle(false,'entry')}
 function start(){clearPreview();if(hasSession()){gameStarted()?recoverGame():(showApp(),openTitle(true));return}hideApp();if(authReturn()){openTitle(false,'authwait');waitForSession();return}openTitle(false,'entry')}
 addEventListener('pageshow',()=>{setTimeout(reconcile,0);setTimeout(reconcile,180)});
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)setTimeout(reconcile,40)});
 addEventListener('focus',()=>setTimeout(reconcile,60));
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.RistAuthGate={reconcile,hasSession};
})();
