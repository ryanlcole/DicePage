(()=>{
 'use strict';
 const SELECTION_KEY='rist.gameStart.selection.v1',SETTINGS_KEY='rist.gameStart.settings.v1';
 let root=null,status=null,settingsPanel=null;
 const parse=(value,fallback)=>{try{return value?JSON.parse(value):fallback}catch{return fallback}};
 const clean=value=>String(value||'').trim().slice(0,64);
 const waitFor=(test,timeout=5000)=>new Promise(resolve=>{const started=Date.now();const poll=()=>{let value=null;try{value=test()}catch{}if(value)return resolve(value);if(Date.now()-started>=timeout)return resolve(null);setTimeout(poll,80)};poll()});
 function markup(){return `<img class="rist-game-start-art" src="assets/branding/shaelvien-dragon-creation-startup-screen.png" alt="Primordial dragons forming the infinite Light and Unlit lands of Shaelvien with their breath weapons."><div class="rist-game-start-shade" aria-hidden="true"></div><div class="rist-game-start-brand" aria-hidden="true"><strong>SHAELVIEN</strong><span>RIST MMO/Sandbox</span></div><form class="rist-game-start-panel" data-game-start-form><div class="rist-game-start-grid"><fieldset><legend>User Role</legend><div class="rist-game-start-segments"><label><input type="radio" name="role" value="GameMaster"><span>GameMaster</span></label><label><input type="radio" name="role" value="Roleplayer"><span>Roleplayer</span></label></div></fieldset><fieldset><legend>Domain</legend><div class="rist-game-start-segments"><label><input type="radio" name="domain" value="Shaelvien"><span>Shaelvien</span></label><label><input type="radio" name="domain" value="Sandbox"><span>Sandbox</span></label></div></fieldset><label class="rist-game-start-invite"><span>Invite Code</span><input name="inviteCode" maxlength="64" autocomplete="off" placeholder="Enter campaign code"></label><button class="rist-game-start-settings-button" type="button" data-game-start-settings>⚙ Settings</button><button class="rist-game-start-submit" type="submit">Start</button></div><p class="rist-game-start-status" data-game-start-status role="status" aria-live="polite"></p><section class="rist-game-start-options" data-game-start-options hidden><div class="rist-game-start-options-head"><h2>Settings</h2><button class="rist-game-start-options-close" type="button" data-game-start-settings-close aria-label="Close settings">×</button></div><label class="rist-game-start-setting"><span>Reduce motion</span><input type="checkbox" data-game-start-motion></label><label class="rist-game-start-setting"><span>High contrast</span><input type="checkbox" data-game-start-contrast></label><div class="rist-game-start-options-actions"><button class="rist-game-start-cancel" type="button" data-game-start-settings-close>Cancel</button><button class="rist-game-start-save" type="button" data-game-start-settings-save>Save</button></div></section></form>`}
 function ensure(){
  if(root&&document.body.contains(root))return;
  root=document.createElement('section');root.className='rist-game-start';root.hidden=true;root.setAttribute('role','dialog');root.setAttribute('aria-modal','true');root.setAttribute('aria-label','Start Shaelvien');root.innerHTML=markup();document.body.appendChild(root);
  status=root.querySelector('[data-game-start-status]');settingsPanel=root.querySelector('[data-game-start-options]');
  root.addEventListener('click',event=>{const target=event.target.closest?.('button');if(!target)return;if(target.matches('[data-game-start-settings]'))toggleSettings(true);if(target.matches('[data-game-start-settings-close]'))toggleSettings(false);if(target.matches('[data-game-start-settings-save]'))saveSettings()});
  root.querySelector('[data-game-start-form]').addEventListener('submit',startGame);
 }
 function setRadio(name,value){root.querySelectorAll(`input[name="${name}"]`).forEach(input=>input.checked=input.value===value)}
 function selection(){const data=new FormData(root.querySelector('[data-game-start-form]'));return{role:String(data.get('role')||'Roleplayer'),domain:String(data.get('domain')||'Shaelvien'),inviteCode:clean(data.get('inviteCode')),preview:document.documentElement.dataset.ristPublicPreview==='1'}}
 function persist(value){
  localStorage.setItem(SELECTION_KEY,JSON.stringify(value));sessionStorage.setItem('rist.gameStart.current',JSON.stringify(value));
  localStorage.setItem('rist.topFrame.userRole',value.role);localStorage.setItem('rist.topFrame.domain',value.domain);localStorage.setItem('rist.topFrame.inviteCode',value.inviteCode);
 }
 function showStatus(message,error=false){if(!status)return;status.textContent=message;status.classList.toggle('error',error)}
 function toggleSettings(open){settingsPanel.hidden=!open;if(open)root.querySelector('[data-game-start-motion]')?.focus();else root.querySelector('[data-game-start-settings]')?.focus()}
 function settings(){return{reduceMotion:root.querySelector('[data-game-start-motion]').checked,highContrast:root.querySelector('[data-game-start-contrast]').checked}}
 function applySettings(value){root.dataset.highContrast=value.highContrast?'1':'0';document.body.classList.toggle('rist-reduce-motion',Boolean(value.reduceMotion));root.querySelector('[data-game-start-motion]').checked=Boolean(value.reduceMotion);root.querySelector('[data-game-start-contrast]').checked=Boolean(value.highContrast)}
 function saveSettings(){const value=settings();localStorage.setItem(SETTINGS_KEY,JSON.stringify(value));applySettings(value);toggleSettings(false);showStatus('Settings saved.')}
 async function selectDomain(domain){
  const wanted=domain==='Sandbox'?'sandbox':'mmo';
  const state=()=>document.querySelector('.mmo-zone-actions[data-world-mode]')?.dataset.worldMode||document.querySelector('.map-shell[data-world-mode]')?.dataset.worldMode;
  if(state()===wanted)return true;
  const action=await waitFor(()=>document.querySelector(wanted==='sandbox'?'.mmo-mode-sandbox-action':'.mmo-mode-shaelvien-action'));
  if(!action)return false;action.click();return Boolean(await waitFor(()=>state()===wanted,2500));
 }
 async function selectRole(role){
  const wanted=role==='GameMaster'?'gamemaster':'roleplayer';
  const state=()=>document.querySelector('.map-shell[data-world-role]')?.dataset.worldRole;
  if(state()===wanted)return true;
  const opener=await waitFor(()=>document.querySelector('#header-slider .root-menu-button[aria-label="Role"]'));
  if(!opener)return false;opener.click();
  const choice=await waitFor(()=>[...document.querySelectorAll('.root-menu-panel[aria-label="Choose role"] button')].find(button=>button.textContent.trim().toLowerCase()===(role==='GameMaster'?'gamemaster':'roleplayer')),1800);
  if(!choice)return false;choice.click();return Boolean(await waitFor(()=>state()===wanted,2500));
 }
 async function startGame(event){
  event.preventDefault();const value=selection(),button=root.querySelector('.rist-game-start-submit');button.disabled=true;showStatus('Preparing the world…');
  const worldReady=await waitFor(()=>document.querySelector('.rist.release-world'),9000);if(!worldReady){button.disabled=false;showStatus('The world is still loading. Please try Start again.',true);return}
  const domainReady=await selectDomain(value.domain);const roleReady=domainReady&&await selectRole(value.role);
  if(!domainReady||!roleReady){button.disabled=false;showStatus(value.role==='GameMaster'?'GameMaster access is not available for this map.':'The selected world could not be opened yet. Please try again.',true);return}
  persist(value);document.dispatchEvent(new CustomEvent('rist:game-start',{detail:value}));root.hidden=true;document.body.classList.remove('rist-game-start-open');showStatus('');
  document.querySelector('.release-map-region .map-frame-mode-toggle')?.focus();
 }
 function open(options={}){
  ensure();const preview=Boolean(options.preview);const saved=parse(localStorage.getItem(SELECTION_KEY),{});const value=preview?{role:'Roleplayer',domain:'Sandbox',inviteCode:'Geonaph'}:{role:saved.role||'Roleplayer',domain:saved.domain||'Shaelvien',inviteCode:saved.inviteCode||''};
  setRadio('role',value.role);setRadio('domain',value.domain);root.querySelector('[name="inviteCode"]').value=value.inviteCode;applySettings(parse(localStorage.getItem(SETTINGS_KEY),{}));settingsPanel.hidden=true;showStatus('');root.hidden=false;document.body.classList.add('rist-game-start-open');setTimeout(()=>root.querySelector('input:checked')?.focus(),0);
 }
 function close(){if(!root)return;root.hidden=true;document.body.classList.remove('rist-game-start-open')}
 addEventListener('keydown',event=>{if(event.key==='Escape'&&root&&!root.hidden&&!settingsPanel.hidden){event.preventDefault();toggleSettings(false)}});
 window.RistGameStartScreen={open,close,getSelection:selection};
})();
