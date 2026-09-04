(()=>{
 'use strict';
 const LOCK_LABELS=new Set(['settings','chat','add files','add file','load','save','library']);
 const norm=s=>(s||'').replace(/\s+/g,' ').trim().toLowerCase();
 const isLockedControl=el=>LOCK_LABELS.has(norm(el.getAttribute?.('aria-label')||el.getAttribute?.('title')||el.textContent));
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
 function start(){
  const params=new URLSearchParams(location.search);
  const alreadyPreview=params.get('preview')==='1'||sessionStorage.getItem('rist-public-preview')==='1';
  if(alreadyPreview){lockPreview();window.RistGameStartScreen?.close?.();observe();return}
  if(sessionStorage.getItem('rist.session')){openTitle(true);observe();return}
  if(params.has('rist_handoff')||location.hash.includes('rist_session')){
   openTitle(false,'authwait');
   let attempts=0;const timer=setInterval(()=>{if(sessionStorage.getItem('rist.session')){clearInterval(timer);openTitle(true)}else if(++attempts>=100){clearInterval(timer);openTitle(false,'entry')}},100);
   observe();return;
  }
  openTitle(false,'splash');observe();
 }
 function observe(){new MutationObserver(()=>requestAnimationFrame(scanLocks)).observe(document.getElementById('app')||document.body,{childList:true,subtree:true})}
 document.addEventListener('click',blockLocked,true);
 document.addEventListener('pointerdown',blockLocked,true);
 document.addEventListener('rist:preview-request',()=>{lockPreview();requestAnimationFrame(scanLocks)});
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
