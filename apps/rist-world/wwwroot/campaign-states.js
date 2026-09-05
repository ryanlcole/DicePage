(()=>{
 'use strict';
 const REGISTRY_KEY='rist.campaign.states.v1';
 const CURRENT_KEY='rist.campaign.current.v1';
 const q=(s,r=document)=>r?.querySelector?.(s)||null;
 const parse=(v,f)=>{try{return v?JSON.parse(v):f}catch{return f}};
 const cleanCode=v=>String(v||'').trim().toUpperCase().replace(/[^A-Z0-9_-]+/g,'-').replace(/^-+|-+$/g,'').slice(0,24);
 const registry=()=>{const rows=parse(localStorage.getItem(REGISTRY_KEY),'');return Array.isArray(rows)?rows:[]};
 const saveRegistry=rows=>localStorage.setItem(REGISTRY_KEY,JSON.stringify(rows));
 const stateLabel=(state,code)=>`${String(state).padStart(3,'0')}-${code}`;
 const kindLabel=kind=>kind==='mmo'?'MMO':kind==='sandbox'?'Sandbox':'Offline';
 const panel=()=>q('.rist-game-start:not([hidden]) [data-start-panel]');
 const status=(message,isError=false)=>{const n=q('[data-campaign-status]',panel());if(n){n.textContent=message||'';n.classList.toggle('error',!!isError)}};
 const waitFor=(test,timeout=7000)=>new Promise(resolve=>{const start=Date.now();const tick=()=>{let value=null;try{value=test()}catch{}if(value)return resolve(value);if(Date.now()-start>=timeout)return resolve(null);setTimeout(tick,60)};tick()});
 function nextOfflineState(){const used=new Set(registry().filter(x=>x.kind==='offline').map(x=>Number(x.state)).filter(Number.isFinite));let n=1;while(used.has(n))n++;return n}
 function remember(record){const rows=registry().filter(x=>x.id!==record.id);rows.push(record);rows.sort((a,b)=>(Number(a.state)||0)-(Number(b.state)||0)||String(a.id).localeCompare(String(b.id)));saveRegistry(rows);return record}
 function setCurrent(record){localStorage.setItem(CURRENT_KEY,record.id);localStorage.setItem('rist.campaign.currentRecord.v1',JSON.stringify(record));document.dispatchEvent(new CustomEvent('rist:campaign-state-changed',{detail:record}))}
 async function applyPrefs(){return await window.RistGameStartScreen?.applyPrefs?.()}
 async function clickAction(selector){const button=await waitFor(()=>q(selector),7000);if(!button)return false;button.click();return true}
 async function begin(record){
  setCurrent(record);status(`Opening ${record.id}…`);
  const prefs=await applyPrefs();
  if(!await clickAction('.mmo-new-campaign-action')){status('Campaign engine is still loading.',true);return}
  await new Promise(r=>setTimeout(r,80));
  await clickAction(record.hosted?'.mmo-save-hosted-campaign-action':'.mmo-save-local-campaign-action');
  sessionStorage.setItem('rist.gameStart.current',JSON.stringify({...prefs,kind:'new',campaign:record}));
  document.dispatchEvent(new CustomEvent('rist:new-campaign',{detail:{...prefs,campaign:record}}));
  document.dispatchEvent(new CustomEvent('rist:game-start',{detail:{...prefs,kind:'new',campaign:record}}));
  window.RistGameStartScreen?.close?.();
 }
 async function load(record){
  setCurrent(record);status(`Loading ${record.id}…`);
  const prefs=await applyPrefs();
  const selector=record.hosted?'.mmo-load-hosted-campaign-action':'.mmo-load-campaign-action';
  if(!await clickAction(selector)){status('Campaign engine is still loading.',true);return}
  sessionStorage.setItem('rist.gameStart.current',JSON.stringify({...prefs,kind:'load',campaign:record}));
  document.dispatchEvent(new CustomEvent('rist:load-campaign',{detail:{...prefs,campaign:record}}));
  document.dispatchEvent(new CustomEvent('rist:game-start',{detail:{...prefs,kind:'load',campaign:record}}));
  window.RistGameStartScreen?.close?.();
 }
 async function tokenInfo(){
  const api=window.RistCampaignAuthority;
  if(!api?.tokenBalance)return{available:null,ready:false};
  try{const value=await api.tokenBalance();return{available:Math.max(0,Number(value)||0),ready:true}}catch{return{available:null,ready:false}}
 }
 async function allocateHosted(kind,userCode){
  const api=window.RistCampaignAuthority;
  if(!api?.allocateState)throw new Error('Hosted campaign token service is not connected yet.');
  const balance=await tokenInfo();
  if(balance.ready&&balance.available<1)throw new Error('A campaign token is required to create a hosted state.');
  const result=await api.allocateState({kind,userCode});
  const state=Number(result?.state);
  if(!Number.isInteger(state)||state<1)throw new Error('No hosted state is currently available.');
  const code=cleanCode(result?.userCode||userCode);
  const id=stateLabel(state,code);
  return remember({id,state,userCode:code,kind,hosted:true,createdAt:new Date().toISOString()});
 }
 function renderNew(){
  const p=panel();if(!p)return;
  p.innerHTML=`<form class="rist-start-card rist-campaign-new" data-campaign-new><h1>New Campaign</h1><p class="rist-start-note">Every campaign is a state. Its code is the state number plus your code.</p><label>Your code<input name="creatorCode" maxlength="24" autocomplete="off" placeholder="DRAGON" required></label><fieldset><legend>Storage</legend><label><input type="radio" name="campaignKind" value="offline" checked><span>Offline · unlimited · this device</span></label><label><input type="radio" name="campaignKind" value="sandbox"><span>Sandbox · hosted · 1 token</span></label><label><input type="radio" name="campaignKind" value="mmo"><span>MMO · hosted · 1 token</span></label></fieldset><p class="rist-start-note" data-token-status>Hosted state numbers are allocated by the server so two players cannot claim the same state.</p><output class="rist-start-note" data-campaign-status aria-live="polite"></output><button type="submit">Create State</button><button type="button" class="rist-start-back" data-campaign-home>Return</button></form>`;
  tokenInfo().then(info=>{const n=q('[data-token-status]',p);if(!n)return;n.textContent=info.ready?`Campaign tokens available: ${info.available}. Offline states never consume tokens.`:'Offline states are available now. Hosted Sandbox/MMO creation waits for the campaign-token authority.'});
  requestAnimationFrame(()=>q('input[name="creatorCode"]',p)?.focus());
 }
 function localRows(){return registry().slice().sort((a,b)=>(Number(a.state)||0)-(Number(b.state)||0)||String(a.id).localeCompare(String(b.id)))}
 async function combinedRows(){
  const local=localRows(),api=window.RistCampaignAuthority;if(!api?.listStates)return local;
  try{
   const remote=await api.listStates();
   if(Array.isArray(remote))for(const r of remote){const state=Number(r.state),code=cleanCode(r.userCode||r.code);if(!Number.isInteger(state)||state<1||!code)continue;const kind=r.kind==='mmo'?'mmo':'sandbox';remember({id:stateLabel(state,code),state,userCode:code,kind,hosted:true,createdAt:r.createdAt||''})}
  }catch{}
  return localRows();
 }
 async function renderLoad(){
  const p=panel();if(!p)return;
  p.innerHTML=`<section class="rist-start-card rist-campaign-load"><h1>Load Campaign</h1><div data-campaign-list><p class="rist-start-note">Loading states…</p></div><button type="button" data-load-local-file>Load Offline File…</button><output class="rist-start-note" data-campaign-status aria-live="polite"></output><button type="button" class="rist-start-back" data-campaign-home>Return</button></section>`;
  const rows=await combinedRows(),host=q('[data-campaign-list]',p);if(!host)return;
  if(!rows.length){host.innerHTML='<p class="rist-start-note">No saved states yet.</p>';return}
  host.innerHTML=rows.map(r=>`<button type="button" class="rist-campaign-state-button" data-load-state="${String(r.id).replace(/"/g,'&quot;')}"><strong>${r.id}</strong><span>${kindLabel(r.kind)}${r.hosted?' · hosted':' · local'}</span></button>`).join('');
 }
 async function openLocalFile(){
  window.RistGameStartScreen?.close?.();
  const loadButton=await waitFor(()=>q('#header-slider [aria-label="Load"]'),5000);if(!loadButton)return;
  loadButton.click();
  const input=await waitFor(()=>q('#header-slider .map-file-load input[type="file"]'),2500);input?.click();
 }
 document.addEventListener('click',event=>{
  const target=event.target instanceof Element?event.target:null;if(!target)return;
  const newButton=target.closest('[data-action="new-campaign"]');
  if(newButton){event.preventDefault();event.stopImmediatePropagation();renderNew();return}
  const loadButton=target.closest('[data-action="load-campaign"]');
  if(loadButton){event.preventDefault();event.stopImmediatePropagation();void renderLoad();return}
  if(target.closest('[data-campaign-home]')){event.preventDefault();window.RistGameStartScreen?.setView?.('home');return}
  if(target.closest('[data-load-local-file]')){event.preventDefault();void openLocalFile();return}
  const stateButton=target.closest('[data-load-state]');if(stateButton){event.preventDefault();const record=registry().find(x=>x.id===stateButton.dataset.loadState);if(record)void load(record)}
 },true);
 document.addEventListener('submit',event=>{
  const form=event.target instanceof Element?event.target.closest('[data-campaign-new]'):null;if(!form)return;
  event.preventDefault();event.stopImmediatePropagation();
  const data=new FormData(form),userCode=cleanCode(data.get('creatorCode')),kind=String(data.get('campaignKind')||'offline');
  if(!userCode){status('Create a short code using letters or numbers.',true);return}
  if(kind==='offline'){
   const state=nextOfflineState(),record=remember({id:stateLabel(state,userCode),state,userCode,kind:'offline',hosted:false,createdAt:new Date().toISOString()});void begin(record);return;
  }
  status('Checking campaign token and finding an available hosted state…');
  allocateHosted(kind==='mmo'?'mmo':'sandbox',userCode).then(begin).catch(error=>status(error?.message||'Hosted state could not be created.',true));
 },true);
 window.RistCampaignStates={registry,current:()=>localStorage.getItem(CURRENT_KEY)||'',renderNew,renderLoad,load,begin,nextOfflineState};
})();
