(()=>{
 'use strict';
 const ALIAS_KEY='rist.playerAlias.v1';
 let queued=false;
 const q=(s,r=document)=>r?.querySelector?.(s)||null;
 const qa=(s,r=document)=>[...(r?.querySelectorAll?.(s)||[])];
 const text=el=>(el?.textContent||'').replace(/\s+/g,' ').trim();
 const startPanel=()=>q('.rist-start-overlay:not([hidden]) .rist-start-panel');

 function announce(message){
  let live=q('#rist-control-status');
  if(!live){live=document.createElement('div');live.id='rist-control-status';live.className='rist-control-status';live.setAttribute('role','status');live.setAttribute('aria-live','polite');live.hidden=true;document.body.appendChild(live)}
  live.textContent='';requestAnimationFrame(()=>{live.textContent=message});
 }
 function clickHeader(label){
  const button=qa('#header-slider .root-menu-button').find(b=>text(b).toLowerCase()===label.toLowerCase()||(b.getAttribute('aria-label')||'').toLowerCase().startsWith(label.toLowerCase()));
  if(!button)return false;
  window.RistStartMenu?.close?.();
  requestAnimationFrame(()=>button.click());
  return true;
 }
 function hydrateDice(panel){
  const button=q('[data-dice-sum-toggle]',panel),note=q('[data-dice-gm-note]',panel);
  if(!button)return;
  const api=window.RistDicePrivacy,state=api?.state?.();
  if(!api||!state){button.textContent='Unavailable';button.disabled=true;if(note)note.textContent='Dice controls are still loading.';return}
  if(!state.gm){button.textContent=state.sumEnabled?'On':'Off';button.disabled=true;if(note)note.textContent='Only the GameMaster can change SUM visibility.';return}
  button.disabled=false;button.textContent=state.sumEnabled?'On':'Off';button.setAttribute('aria-pressed',String(!!state.sumEnabled));
  if(note)note.textContent='Controls whether the running dice total is shown.';
 }
 function disableUnimplemented(panel,heading){
  if(!['Video','Picture','Effects'].includes(heading))return;
  qa('input,select,textarea,button',panel).forEach(control=>{
   if(control.matches('[data-start-back],[data-start-exit]'))return;
   control.disabled=true;
   control.setAttribute('aria-disabled','true');
   control.title='Not active in this build';
  });
  if(!q('.rist-control-unavailable',panel)){
   const note=document.createElement('p');note.className='rist-start-note rist-control-unavailable';note.textContent=`${heading} processing is not active in this build yet.`;
   q('h2',panel)?.insertAdjacentElement('afterend',note);
  }
 }
 function hydrateStorage(panel){
  if(text(q('h2',panel))!=='Manage Storage')return;
  qa('button',panel).forEach(button=>{
   const label=text(button);
   if(label==='View usage'){
    button.disabled=true;button.setAttribute('aria-disabled','true');button.title='Cloud usage reporting is not active yet';
   }else if(label==='Import'){
    button.dataset.controlImport='1';button.title='Open the existing Load controls';
   }else if(label==='Export'){
    button.dataset.controlExport='1';button.title='Open the existing Save / Export controls';
   }
  });
 }
 function hydrateAccount(panel){
  if(text(q('h2',panel))!=='Account')return;
  const input=q('input[type="text"]',panel);if(!input)return;
  input.dataset.playerAlias='1';input.value=localStorage.getItem(ALIAS_KEY)||input.value||'';input.setAttribute('aria-label','Player alias');
 }
 function hydrateCurrentFolder(){
  qa('.library-deck-folder.active[aria-label^="Current folder "]').forEach(button=>{
   button.disabled=true;button.setAttribute('aria-current','page');button.title='Current folder';
  });
 }
 function hydrate(){
  const panel=startPanel();
  if(panel){
   const heading=text(q('h2',panel));
   if(heading==='Dice')hydrateDice(panel);
   disableUnimplemented(panel,heading);
   hydrateStorage(panel);
   hydrateAccount(panel);
  }
  hydrateCurrentFolder();
 }
 function queue(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;hydrate()})}

 document.addEventListener('click',event=>{
  const target=event.target instanceof Element?event.target:null;if(!target)return;
  const context=target.closest('[data-world-context]');
  if(context&&context.closest('.rist-start-overlay')){
   event.preventDefault();event.stopPropagation();
   const key=context.dataset.worldContext;
   if(window.RistWorldContext?.edit){window.RistWorldContext.edit(key);announce(`Opened ${key} world context controls.`)}
   else announce('World context controls are not ready yet.');
   return;
  }
  if(target.closest('[data-world-clock]')?.closest('.rist-start-overlay')){
   event.preventDefault();event.stopPropagation();
   if(window.RistWorldContext?.openClock){window.RistWorldContext.openClock();announce('Opened clock controls.')}else announce('Clock controls are not ready yet.');
   return;
  }
  const sum=target.closest('[data-dice-sum-toggle]');
  if(sum&&sum.closest('.rist-start-overlay')){
   event.preventDefault();event.stopPropagation();
   const api=window.RistDicePrivacy,state=api?.state?.();if(!api||!state||!state.gm)return;
   api.setSumEnabled(!state.sumEnabled);setTimeout(queue,0);announce(`Dice SUM ${state.sumEnabled?'hidden':'shown'}.`);return;
  }
  if(target.closest('[data-control-import]')){event.preventDefault();event.stopPropagation();if(!clickHeader('Load'))announce('Load controls are unavailable.');return}
  if(target.closest('[data-control-export]')){event.preventDefault();event.stopPropagation();if(!clickHeader('Save'))announce('Save controls are unavailable.');return}
 },true);
 document.addEventListener('change',event=>{
  const input=event.target instanceof Element?event.target.closest('[data-player-alias]'):null;if(!input)return;
  const value=String(input.value||'').trim().slice(0,64);input.value=value;localStorage.setItem(ALIAS_KEY,value);document.dispatchEvent(new CustomEvent('rist:player-alias-changed',{detail:{alias:value}}));announce('Player alias saved on this device.');
 },true);
 document.addEventListener('rist:new-campaign',()=>setTimeout(()=>{q('.mmo-new-campaign-action')?.click();announce('New campaign ready.')},0));
 document.addEventListener('rist:load-campaign',()=>setTimeout(()=>{q('.mmo-load-campaign-action')?.click();announce('Saved campaign loaded.')},0));
 document.addEventListener('rist:dice-sum-setting-changed',queue);
 document.addEventListener('rist:dom-change',queue);
 new MutationObserver(queue).observe(document.documentElement,{childList:true,subtree:true});
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',hydrate,{once:true});else hydrate();
 window.RistControlIntegrity={refresh:hydrate};
 Promise.resolve(window.RistPLC?.ensureGroup?.('shell')).finally(()=>setTimeout(queue,0));
})();
