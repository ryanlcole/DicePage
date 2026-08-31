(()=>{
 'use strict';
 const audiences=['Roleplay','OOC','GM','Private'];
 const gameFriendsStorageKey='rist.game.friends.v1';
 let audience='Roleplay';
 let activeTab='Roleplay';
 let privateRecipient='';
 let scriptWindow=null;
 let patching=false;

 const esc=v=>String(v??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot',"'":'&#39;'}[ch]));
 const displayName=()=>document.querySelector('.footer-character-button strong,.rist-account-profile strong,#header-slider .header-user-name')?.textContent?.trim()||'Player';
 const normalizeFriend=value=>{
  if(typeof value==='string')return {id:value,name:value};
  const id=String(value?.id??value?.accountId??value?.userId??value?.name??'').trim();
  const name=String(value?.name??value?.alias??value?.playerAlias??id).trim();
  return id&&name?{id,name}:null;
 };
 function storedGameFriends(){
  try{
   const rows=JSON.parse(localStorage.getItem(gameFriendsStorageKey)||'[]');
   return Array.isArray(rows)?rows.map(normalizeFriend).filter(Boolean):[];
  }catch{return []}
 }
 function gameFriends(){
  let rows=[];
  try{
   const external=window.RistFriends?.list?.();
   if(Array.isArray(external))rows=external.map(normalizeFriend).filter(Boolean);
  }catch{}
  if(!rows.length)rows=storedGameFriends();
  const seen=new Set();
  return rows.filter(x=>{const key=x.id.toLowerCase();if(seen.has(key))return false;seen.add(key);return true});
 }
 function setStoredGameFriends(rows){
  const clean=(Array.isArray(rows)?rows:[]).map(normalizeFriend).filter(Boolean);
  try{localStorage.setItem(gameFriendsStorageKey,JSON.stringify(clean))}catch{}
  document.dispatchEvent(new CustomEvent('rist:friends-changed',{detail:{friends:clean}}));
  return clean;
 }

 function installFilterArrows(header){
  if(!header||header.querySelector('.asset-filter-arrow'))return;
  const tabs=header.querySelector('.asset-type-tabs');
  if(!tabs)return;
  const make=(dir,cls)=>{const b=document.createElement('button');b.type='button';b.className=`asset-filter-arrow ${cls}`;b.textContent=dir<0?'‹':'›';b.setAttribute('aria-label',dir<0?'Scroll filters left':'Scroll filters right');b.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();tabs.scrollBy({left:dir*Math.max(120,tabs.clientWidth*.55),behavior:'smooth'})});return b};
  header.append(make(-1,'prev'),make(1,'next'));
 }

 function currentRpLanguage(){
  const button=document.querySelector('.release-footer-stack .roleplay-language-toggle');
  const internal=button?.dataset.dialectInternal||button?.textContent?.replace(/^(?:Dialect|RP-Language):\s*/i,'').trim()||'Common';
  return /^common$/i.test(internal)?'Universal':internal;
 }
 function syncComposeContext(){
  const input=document.querySelector('.home-chat-compose textarea,.chat-compose-rail textarea');
  if(input)input.placeholder=`${audience} · ${currentRpLanguage()}`;
 }
 function decorateDialect(button){
  if(!button)return;
  const alreadyDecorated=!!button.querySelector('.chat-blue-value');
  const internal=alreadyDecorated
   ? (button.dataset.dialectInternal||'Common')
   : (button.textContent?.replace(/^(?:Dialect|RP-Language):\s*/i,'').trim()||'Common');
  const display=/^common$/i.test(internal)?'Universal':internal;
  const currentDisplay=button.querySelector('.chat-blue-value')?.textContent?.trim();
  if(!alreadyDecorated||currentDisplay!==display||!button.textContent?.startsWith('RP-Language:')){
   button.dataset.dialectInternal=internal;
   const value=document.createElement('span');value.className='chat-blue-value';value.textContent=display;
   button.replaceChildren(document.createTextNode('RP-Language: '),value);
  }
  button.setAttribute('aria-label',`RP-Language ${display}. Tap to change language.`);
  button.title='Change roleplay language';
  syncComposeContext();
 }

 function ensurePrivateFriendSelect(){
  const compose=document.querySelector('.release-footer-stack .chat-compose-rail,.release-footer-stack .home-chat-compose');
  if(!compose)return;
  let select=compose.querySelector('.private-friend-select');
  if(!select){
   select=document.createElement('select');
   select.className='private-friend-select';
   select.setAttribute('aria-label','Private chat friend');
   const send=compose.querySelector('.home-chat-send,button[type="submit"],button');
   send?.before(select);
   select.addEventListener('change',()=>{privateRecipient=select.value;syncComposeContext()});
  }
  const friends=gameFriends();
  const prior=privateRecipient||select.value;
  select.replaceChildren();
  const prompt=document.createElement('option');
  prompt.value='';
  prompt.textContent=friends.length?'Friends':'No Friends';
  select.appendChild(prompt);
  friends.forEach(friend=>{const option=document.createElement('option');option.value=friend.id;option.textContent=friend.name;select.appendChild(option)});
  if(friends.some(x=>x.id===prior)){select.value=prior;privateRecipient=prior}else{select.value='';privateRecipient=''}
  select.hidden=audience!=='Private';
 }

 function ensureChatControls(){
  const rail=document.querySelector('.release-footer-stack .chat-mode-rail');
  if(!rail)return;
  const scripts=rail.querySelector('.chat-history-toggle');
  const dialect=rail.querySelector('.roleplay-language-toggle');
  if(scripts){
   if(scripts.textContent!=='Scripts')scripts.textContent='Scripts';
   scripts.title='Open chat scripts';
   scripts.setAttribute('aria-label','Open chat scripts');
   if(!scripts.dataset.scriptBound){
    scripts.dataset.scriptBound='1';
    scripts.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();openScripts()},true);
   }
  }
  let audienceButton=rail.querySelector('.chat-audience-toggle');
  if(!audienceButton){
   audienceButton=document.createElement('button');
   audienceButton.type='button';
   audienceButton.className='chat-audience-toggle';
   audienceButton.addEventListener('click',()=>{audience=audiences[(audiences.indexOf(audience)+1)%audiences.length];syncAudience(audienceButton)});
   dialect?.before(audienceButton);
  }
  syncAudience(audienceButton);
  decorateDialect(dialect);
  ensurePrivateFriendSelect();
  syncComposeContext();
 }
 function syncAudience(button){
  if(!button)return;
  const current=button.querySelector('.chat-blue-value')?.textContent?.trim();
  if(current!==audience){
   const value=document.createElement('span');value.className='chat-blue-value';value.textContent=audience;
   button.replaceChildren(document.createTextNode('Audience: '),value);
  }
  button.title='Change message audience';
  button.setAttribute('aria-label',`Audience ${audience}. Tap to change.`);
  document.querySelector('.home-inline-chat')?.setAttribute('data-chat-audience',audience.toLowerCase());
  ensurePrivateFriendSelect();
  syncComposeContext();
 }

 function privateNames(){return gameFriends().map(x=>x.name)}
 function ensureScriptWindow(){
  const map=document.querySelector('.release-map-region');
  if(!map)return null;
  if(scriptWindow?.isConnected)return scriptWindow;
  scriptWindow=document.createElement('section');
  scriptWindow.className='rist-script-window';
  scriptWindow.hidden=true;
  scriptWindow.setAttribute('role','dialog');
  scriptWindow.setAttribute('aria-label','Chat scripts');
  scriptWindow.innerHTML='<nav class="rist-script-tabs" aria-label="Script channels"></nav><div class="rist-script-log" aria-live="polite"></div><form class="rist-script-compose"><input type="text" maxlength="1200" autocomplete="off" aria-label="Script message"><button type="submit">Send</button></form>';
  map.appendChild(scriptWindow);
  scriptWindow.querySelector('form').addEventListener('submit',e=>{e.preventDefault();sendFromScripts()});
  rebuildTabs();
  return scriptWindow;
 }
 function rebuildTabs(){
  const win=scriptWindow;if(!win)return;
  const tabs=win.querySelector('.rist-script-tabs');
  const names=['Roleplay','Out of Character','GameMaster',...privateNames()];
  tabs.replaceChildren();
  names.forEach(name=>{const b=document.createElement('button');b.type='button';b.textContent=name;b.classList.toggle('active',name===activeTab);b.addEventListener('click',()=>{activeTab=name;audience=name==='Out of Character'?'OOC':name==='GameMaster'?'GM':name==='Roleplay'?'Roleplay':'Private';if(audience==='Private'){const friend=gameFriends().find(x=>x.name===name);privateRecipient=friend?.id||''}ensureChatControls();rebuildTabs();renderScript()});tabs.appendChild(b)});
  const close=document.createElement('button');close.type='button';close.className='script-close';close.textContent='×';close.setAttribute('aria-label','Close scripts');close.addEventListener('click',closeScripts);tabs.appendChild(close);
 }
 function renderScript(){
  const win=ensureScriptWindow();if(!win)return;
  const log=win.querySelector('.rist-script-log');
  let entries=[];
  if(activeTab==='Out of Character'){
   try{entries=window.RistOocChat?.state?.().history||[]}catch{}
  }else if(activeTab==='Roleplay'){
   const output=document.querySelector('.inline-chat-output');
   if(output){const speaker=output.querySelector('.dialogue-copy strong')?.childNodes?.[0]?.textContent?.trim()||'Roleplay';const text=output.querySelector('.dialogue-copy p,.chat-output-placeholder')?.textContent?.trim();if(text)entries=[{name:speaker,text,time:Date.now()}]}
  }
  if(!entries.length){
   const note=activeTab==='GameMaster'?'GameMaster script will populate from GM-directed messages.':activeTab==='Roleplay'?'Roleplay script appears here as dialogue is produced.':activeTab==='Out of Character'?'OOC messages appear here.':'Private script appears here when that conversation has messages.';
   log.innerHTML=`<p class="rist-script-empty">${esc(note)}</p>`;
  }else log.innerHTML=entries.slice(-150).map(m=>`<article class="rist-script-entry"><strong>${esc(m.name||'Player')}</strong> ${esc(m.text||'')}</article>`).join('');
  log.scrollTop=log.scrollHeight;
  const input=win.querySelector('input');input.placeholder=activeTab==='Out of Character'?'Out of character…':activeTab==='GameMaster'?'Message GameMaster…':activeTab==='Roleplay'?'Roleplay…':`Message ${activeTab}…`;
 }
 function openScripts(){const win=ensureScriptWindow();if(!win)return;win.hidden=false;rebuildTabs();renderScript();setTimeout(()=>win.querySelector('input')?.focus(),0)}
 function closeScripts(){if(scriptWindow)scriptWindow.hidden=true}
 function sendFromScripts(){
  const win=ensureScriptWindow();if(!win)return;
  const input=win.querySelector('input');const text=input.value.trim();if(!text)return;
  if(activeTab==='Out of Character'&&window.RistOocChat?.receive){
   window.RistOocChat.receive({id:crypto.randomUUID?.()||String(Date.now()),name:displayName(),text,time:Date.now()},false);input.value='';renderScript();return;
  }
  const base=document.querySelector('.home-chat-compose textarea');const send=document.querySelector('.home-chat-send');
  if(activeTab==='Roleplay'&&base&&send){
   const setter=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value')?.set;setter?.call(base,text);base.dispatchEvent(new Event('input',{bubbles:true}));input.value='';send.click();setTimeout(renderScript,40);return;
  }
  document.dispatchEvent(new CustomEvent('rist:script-send',{detail:{audience,tab:activeTab,recipientId:privateRecipient||null,text,name:displayName(),time:Date.now()}}));
  input.value='';
 }

 function patch(){
  if(patching)return;patching=true;
  try{
   document.querySelectorAll('.asset-rail-header').forEach(installFilterArrows);
   ensureChatControls();
   if(scriptWindow&&!scriptWindow.isConnected)scriptWindow=null;
  }finally{patching=false}
 }
 const observer=new MutationObserver(()=>queueMicrotask(patch));
 function start(){patch();observer.observe(document.body,{childList:true,subtree:true});document.addEventListener('rist:ooc-received',()=>{if(activeTab==='Out of Character'&&!scriptWindow?.hidden)renderScript()});document.addEventListener('rist:friends-changed',()=>{ensurePrivateFriendSelect();if(scriptWindow&&!scriptWindow.hidden){rebuildTabs();renderScript()}});document.addEventListener('keydown',e=>{if(e.key==='Escape'&&scriptWindow&&!scriptWindow.hidden)closeScripts()})}
 window.RistFriends=window.RistFriends||{};
 if(typeof window.RistFriends.list!=='function')window.RistFriends.list=storedGameFriends;
 if(typeof window.RistFriends.setAccepted!=='function')window.RistFriends.setAccepted=setStoredGameFriends;
 window.RistChatScripts={open:openScripts,close:closeScripts,getAudience:()=>audience,getPrivateRecipient:()=>privateRecipient,setAudience:value=>{if(audiences.includes(value)){audience=value;patch()}},refresh:renderScript};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
