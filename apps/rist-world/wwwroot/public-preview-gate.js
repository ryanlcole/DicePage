(()=>{
 'use strict';
 const LOCK_LABELS=new Set(['settings','chat','add files','add file','load','save','library']);
 const norm=s=>(s||'').replace(/\s+/g,' ').trim().toLowerCase();
 const isLockedControl=el=>{
  const label=norm(el.getAttribute?.('aria-label')||el.getAttribute?.('title')||el.textContent);
  return LOCK_LABELS.has(label);
 };
 function lockPreview(){
  document.documentElement.dataset.ristPublicPreview='1';
  sessionStorage.setItem('rist-public-preview','1');
  if(!document.querySelector('.rist-preview-badge')){
   const b=document.createElement('div');b.className='rist-preview-badge';b.textContent='PUBLIC PREVIEW';document.body.append(b);
  }
  scanLocks();
 }
 function scanLocks(){
  if(document.documentElement.dataset.ristPublicPreview!=='1')return;
 document.querySelectorAll('button,a,[role="button"],[role="menuitem"],[role="tab"],label').forEach(el=>{
   if(el.closest('.rist-game-start'))return;
   if(isLockedControl(el)){
    el.dataset.previewLocked='1';el.setAttribute('aria-disabled','true');el.title='Locked in public preview';
   }
  });
  document.querySelectorAll('input[type="file"]').forEach(el=>{el.dataset.previewLocked='1';el.disabled=true});
  document.querySelectorAll('[contenteditable="true"],input,textarea,select').forEach(el=>{
   const host=el.closest('[class*="character" i],[id*="character" i],[class*="sheet" i],[id*="sheet" i]');
   if(host){el.dataset.previewLocked='1';if('readOnly' in el)el.readOnly=true;if('disabled' in el&&el.tagName==='SELECT')el.disabled=true;el.setAttribute('aria-readonly','true')}
  });
 }
 function blockLocked(event){
  if(document.documentElement.dataset.ristPublicPreview!=='1')return;
  const target=event.target instanceof Element?event.target.closest('button,a,[role="button"],[role="menuitem"],[role="tab"],label,input,textarea,select,[contenteditable]'):null;
  if(!target)return;
  if(target.closest('.rist-game-start'))return;
  if(target.dataset.previewLocked==='1'||isLockedControl(target)){
   event.preventDefault();event.stopPropagation();event.stopImmediatePropagation();
  }
 }
 async function auth(mode){
 sessionStorage.removeItem('rist-public-preview');
  delete document.documentElement.dataset.ristPublicPreview;
  localStorage.setItem('rist.auth.intent',mode);
  try{
   const cfg=await fetch('auth-config.json',{cache:'no-store'}).then(r=>r.json());
   if(cfg?.apiBaseUrl){
    const next=encodeURIComponent(location.href.split('#')[0]);
    const loginPath=String(cfg.loginPath||'/auth/login').startsWith('/')?String(cfg.loginPath||'/auth/login'):`/${cfg.loginPath}`;
    location.href=`${cfg.apiBaseUrl.replace(/\/$/,'')}${loginPath}?next=${next}&intent=${encodeURIComponent(mode)}`;
    return;
   }
  }catch{}
  // Fallback to any rendered auth control if the endpoint contract changes.
  const tryClick=()=>{
   const candidates=[...document.querySelectorAll('button,a,[role="button"]')];
   const found=candidates.find(el=>/discord|log\s*in|sign\s*up/i.test(el.textContent||el.getAttribute('aria-label')||''));
   if(found){found.click();return true}return false;
  };
  if(!tryClick()){let n=0;const t=setInterval(()=>{if(tryClick()||++n>40)clearInterval(t)},100)}
 }
 function gate(){
  if(document.querySelector('.rist-entry-gate'))return;
  const wrap=document.createElement('div');wrap.className='rist-entry-gate';wrap.setAttribute('role','dialog');wrap.setAttribute('aria-modal','true');wrap.setAttribute('aria-labelledby','rist-entry-title');
  wrap.innerHTML='<div class="rist-entry-dialog"><h2 id="rist-entry-title">Enter Shaelvien</h2><p>Log in to play, create an account, or look around in a read-only public preview.</p><div class="rist-entry-actions"><button type="button" data-entry="login">Log In</button><button type="button" data-entry="signup">Sign Up</button><button type="button" class="preview" data-entry="preview">Preview</button></div></div>';
  wrap.addEventListener('click',e=>{const b=e.target.closest?.('[data-entry]');if(!b)return;const action=b.dataset.entry;if(action==='preview'){lockPreview();wrap.remove();window.RistGameStartScreen?.open?.({preview:true})}else auth(action)});
  document.body.append(wrap);setTimeout(()=>wrap.querySelector('button')?.focus(),0);
 }
 document.addEventListener('click',blockLocked,true);
 document.addEventListener('pointerdown',blockLocked,true);
 const observe=()=>new MutationObserver(()=>requestAnimationFrame(scanLocks)).observe(document.getElementById('app')||document.body,{childList:true,subtree:true});
 function start(){
  const params=new URLSearchParams(location.search);
  const preview=params.get('preview')==='1'||sessionStorage.getItem('rist-public-preview')==='1';
  if(preview){lockPreview();window.RistGameStartScreen?.open?.({preview:true})}
  else if(sessionStorage.getItem('rist.session'))window.RistGameStartScreen?.open?.({preview:false});
  else if(params.has('rist_handoff')||location.hash.includes('rist_session')){
   let attempts=0;const timer=setInterval(()=>{if(sessionStorage.getItem('rist.session')){clearInterval(timer);window.RistGameStartScreen?.open?.({preview:false})}else if(++attempts>=100){clearInterval(timer);gate()}},100);
  }
  else gate();
  observe();
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
