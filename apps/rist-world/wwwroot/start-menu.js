(()=>{
 'use strict';
 function range(label,value){return row(label,`<input type="range" min="0" max="100" value="${value}" aria-label="${label}">`)}
 function row(label,control){return `<label class="rist-setting-row"><span>${label}</span><span>${control}</span></label>`}
 function select(options){return `<select>${options.map(option=>`<option>${option}</option>`).join('')}</select>`}
 const sections={
  World:`<h2>World</h2><p class="rist-start-note">Edit shared world context and display time.</p>${row('Stars','<button type="button" data-world-context="stars">Edit</button>')}${row('Sky','<button type="button" data-world-context="sky">Edit</button>')}${row('Calendar','<button type="button" data-world-context="cal">Edit</button>')}${row('UGC','<button type="button" data-world-context="ugc">Edit</button>')}${row('Clock','<button type="button" data-world-clock>Edit</button>')}`,
  Video:`<h2>Video</h2>${row('Picture Mode',select(['Standard','Cinema','Game','Vivid','Custom']))}${range('Brightness',50)}${range('Contrast',50)}${range('Gamma',50)}${range('Motion',50)}${row('Aspect',select(['Auto','16:9','4:3','Fit','Fill']))}`,
  Picture:`<h2>Picture</h2>${range('Exposure',50)}${range('Highlights',50)}${range('Shadows',50)}${range('Saturation',50)}${range('Temperature',50)}${range('Sharpness',50)}${range('Opacity',100)}`,
  Sound:`<h2>Sound</h2><p class="rist-start-note">Mixing-board foundation. Shaelvien tileset controls and external sound-app integrations can plug into these channels.</p>${range('Master',75)}${range('Music',70)}${range('Effects',80)}${range('Voice',80)}${range('Ambient',75)}${range('UI',65)}${row('Sound Apps','<button type="button" disabled>Future integrations</button>')}`,
  Effects:`<h2>Effects</h2>${range('Particles',75)}${range('Weather',80)}${range('Lighting',75)}${range('Parallax / 3D',75)}${range('Animation',100)}`,
  'Manage Storage':`<h2>Manage Storage</h2>${row('Cloud Usage','<button type="button">View usage</button>')}${row('Import Campaign','<button type="button">Import</button>')}${row('Export Campaign','<button type="button">Export</button>')}${row('Request Help','<button type="button">Request Help</button>')}`,
  Account:`<h2>Account</h2><div class="rist-account-profile"><div class="rist-account-avatar"></div><div><strong>Profile</strong><div class="rist-start-note">Player image, alias and personal account details</div></div></div>${row('Player Alias','<input type="text" placeholder="Alias">')}<div class="rist-discord-id-row rist-setting-row"><span>Discord ID</span><span class="rist-discord-id">Loading…</span></div>${row('Personal Details','<button type="button">Manage</button>')}${row('Parental Controls','<button type="button">Manage</button>')}${row('Email Preferences','<button type="button">Manage emails</button>')}${row('Linked Accounts','<button type="button">Manage accounts</button>')}${row('Help','<button type="button">Help</button>')}`
 };
 let overlay=null,panel=null;
 function pause(open){document.body.classList.toggle('rist-start-open',open);document.dispatchEvent(new CustomEvent(open?'rist:pause':'rist:resume',{detail:{source:'start-menu'}}))}
 function showHome(){panel.innerHTML=`<h1 class="rist-start-title">START</h1><div class="rist-start-grid">${Object.keys(sections).map(name=>`<button type="button" class="rist-start-button" data-start-section="${name}">${name}</button>`).join('')}</div><button type="button" class="rist-start-exit" data-start-exit>Exit</button>`}
 async function hydrateAccount(){const out=panel?.querySelector('.rist-discord-id');if(!out)return;try{const config=await fetch('auth-config.json',{cache:'no-store'}).then(response=>response.ok?response.json():null);const token=sessionStorage.getItem('rist.session');if(!config?.apiBaseUrl||!token){out.textContent='Log in with Discord';return}const response=await fetch(config.apiBaseUrl.replace(/\/$/,'')+'/me',{headers:{Authorization:'Bearer '+token},cache:'no-store'});if(!response.ok){out.textContent='Unavailable';return}const profile=await response.json();out.textContent=profile.userId||profile.UserId||'Unavailable'}catch{out.textContent='Unavailable'}}
 function showSection(name){panel.innerHTML=`<section class="rist-start-sub">${sections[name]}<button type="button" class="rist-start-back" data-start-back>Back</button><button type="button" class="rist-start-exit" data-start-exit>Exit</button></section>`;if(name==='Account')void hydrateAccount()}
 function ensure(){
  if(overlay&&document.body.contains(overlay))return;
  overlay=document.querySelector('.rist-start-overlay');
  if(!overlay){overlay=document.createElement('div');overlay.className='rist-start-overlay';overlay.hidden=true;overlay.innerHTML='<div class="rist-start-panel" role="dialog" aria-modal="true" aria-label="Start menu"></div>';document.body.appendChild(overlay)}
  panel=overlay.querySelector('.rist-start-panel');showHome();
  if(overlay.dataset.wired==='1')return;overlay.dataset.wired='1';
  overlay.addEventListener('click',e=>{const target=e.target instanceof Element?e.target:null;if(!target)return;const context=target.closest('[data-world-context]');if(context){window.RistWorldContext?.edit?.(context.dataset.worldContext);return}if(target.closest('[data-world-clock]')){window.RistWorldContext?.openClock?.();return}const section=target.closest('[data-start-section]');if(section){showSection(section.dataset.startSection);return}if(target.closest('[data-start-back]')){showHome();return}if(target.closest('[data-start-exit]'))close()});
 }
 function open(){ensure();showHome();overlay.hidden=false;pause(true)}
 function close(){if(!overlay)return;overlay.hidden=true;pause(false)}
 window.RistStartMenu={open,close};
 addEventListener('keydown',e=>{if(e.key==='Escape'&&overlay&&!overlay.hidden)close()});
 ensure();
})();
