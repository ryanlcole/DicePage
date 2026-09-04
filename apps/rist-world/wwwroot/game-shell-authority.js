(()=>{
 'use strict';
 const PREF_KEY='rist.gameStart.selection.v2',IMG_KEY='rist.profile.image.v1';
 const parse=(v,f)=>{try{return v?JSON.parse(v):f}catch{return f}};
 const prefs=()=>{const p=parse(localStorage.getItem(PREF_KEY),{});return{role:p.role==='GameMaster'?'GameMaster':'Roleplayer',domain:p.domain==='RIST'?'RIST':'Shaelvien MMO'}};
 function loggedIn(){
  if(sessionStorage.getItem('rist.session'))return true;
  if(document.querySelector('.rist.release-world.auth-ready'))return true;
  const account=document.querySelector('.world-context-login,#header-slider .door-button');
  return /log\s*out/i.test(`${account?.textContent||''} ${account?.getAttribute?.('aria-label')||''}`);
 }
 function profileImage(){
  const local=localStorage.getItem(IMG_KEY)||window.RistProfileImage?.current?.()||'';
  if(local)return local;
  const img=document.querySelector('.rist-account-avatar img,.rist-profile-preview img,[data-profile-name] img');
  return img?.src||'';
 }
 function actualRole(){const raw=document.querySelector('.mmo-zone-actions[data-world-role]')?.dataset.worldRole;return raw==='GM'?'GameMaster':raw==='PC'?'Roleplayer':prefs().role}
 function isLocked(){const b=document.querySelector('.map-lock-button');if(!b)return true;const title=(b.getAttribute('title')||'').toLowerCase();return title.includes('unlock')||b.getAttribute('aria-pressed')==='false'}
 const setAttr=(el,name,value)=>{if(el&&el.getAttribute(name)!==String(value))el.setAttribute(name,String(value))};
 const setText=(el,value)=>{if(el&&el.textContent!==value)el.textContent=value};
 function ensureProfile(){
  let b=document.querySelector('.rist-game-profile-launcher');
  if(!loggedIn()){b?.remove();return}
  if(!b){
   b=document.createElement('button');b.type='button';b.className='rist-game-profile-launcher';b.setAttribute('aria-label','Open Shaelvien start menu');
   b.addEventListener('click',()=>window.RistGameStartScreen?.open?.({authenticated:true,fromGame:true,view:'home'}));document.body.appendChild(b);
  }
  const src=profileImage();
  if(src){
   let img=b.querySelector('img');if(!img){b.replaceChildren();img=document.createElement('img');img.alt='';b.appendChild(img)}
   if(img.getAttribute('src')!==src)img.src=src;
  }else if(!b.querySelector('.rist-profile-fallback')){
   b.replaceChildren();const span=document.createElement('span');span.className='rist-profile-fallback';span.textContent='●';span.setAttribute('aria-hidden','true');b.appendChild(span);
  }
 }
 function ensureLock(){
  const shell=document.querySelector('.release-map-region .map-shell');let b=document.querySelector('.rist-gm-layer-lock');const gm=actualRole()==='GameMaster';
  if(!shell||!gm){b?.remove();return}
  if(!b){b=document.createElement('button');b.type='button';b.className='rist-gm-layer-lock';b.addEventListener('click',()=>{document.querySelector('.map-lock-button')?.click();setTimeout(sync,60)});shell.appendChild(b)}
  const locked=isLocked(),state=locked?'1':'0',label=locked?'Unlock current tier and layer for editing':'Lock current tier and layer';
  if(b.dataset.locked!==state)b.dataset.locked=state;setAttr(b,'aria-label',label);setAttr(b,'aria-pressed',locked?'false':'true');
  const src=`assets/ui/${locked?'lock-closed':'lock-open'}.svg`;let img=b.querySelector('img');if(!img){b.replaceChildren();img=document.createElement('img');img.alt='';img.setAttribute('aria-hidden','true');b.appendChild(img)}if(img.getAttribute('src')!==src)img.src=src;
 }
 function gateTools(){
  const gm=actualRole()==='GameMaster',locked=isLocked(),role=gm?'gm':'roleplayer',lock=locked?'1':'0';
  if(document.documentElement.dataset.ristGameRole!==role)document.documentElement.dataset.ristGameRole=role;
  if(document.documentElement.dataset.ristLayerLocked!==lock)document.documentElement.dataset.ristLayerLocked=lock;
  document.querySelectorAll('#header-slider .assets-root-panel button').forEach(b=>{const t=(b.textContent||'').trim().toLowerCase();if(['terrain','tiles','all'].includes(t)&&b.dataset.gmEditOnly!=='1')b.dataset.gmEditOnly='1'});
  document.querySelectorAll('#header-slider .root-menu-panel[aria-label="Choose table mode"] button').forEach(b=>{const t=(b.textContent||'').trim().toLowerCase();if(['worldbuilder','forge'].includes(t)&&b.dataset.gmEditOnly!=='1')b.dataset.gmEditOnly='1'});
 }
 function makeFrameReadOnly(){
  const p=prefs();const mode=document.querySelector('.map-frame-mode-toggle');
  if(mode){setText(mode,p.domain==='RIST'?'RIST':'MMO');if(!mode.disabled)mode.disabled=true;setAttr(mode,'aria-disabled','true');setAttr(mode,'aria-label',`Current domain: ${p.domain}`);setAttr(mode,'tabindex','-1');if(mode.style.pointerEvents!=='none')mode.style.pointerEvents='none'}
  const role=document.querySelector('.map-frame-role-slot');if(role){const r=actualRole();role.removeAttribute('aria-hidden');setText(role,r);setAttr(role,'aria-label',`Current role: ${r}`)}
 }
 function sync(){ensureProfile();ensureLock();gateTools();makeFrameReadOnly()}
 ['rist:profile-image-changed','rist:start-settings-changed','rist:start-settings-applied','rist:game-start'].forEach(name=>document.addEventListener(name,()=>setTimeout(sync,30)));
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)sync()});
 setInterval(sync,900);
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>{sync();setTimeout(sync,400);setTimeout(sync,1500)},{once:true});else{sync();setTimeout(sync,400);setTimeout(sync,1500)}
 window.RistGameShell={sync};
})();
