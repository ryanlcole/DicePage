(()=>{
 'use strict';
 const PREF_KEY='rist.gameStart.selection.v2';
 const CAMPAIGN_CODE_KEY='rist.campaign.pendingCode.v1';
 const q=(s,r=document)=>r?.querySelector?.(s)||null;
 const clean=v=>String(v||'').trim().toUpperCase().replace(/[^A-Z0-9_-]+/g,'-').replace(/^-+|-+$/g,'').slice(0,24);
 const panel=()=>q('.rist-game-start:not([hidden]) [data-start-panel]');
 function removePreview(){document.querySelectorAll('.rist-game-start [data-action="preview"]').forEach(el=>el.remove())}
 function renderNew(){
  const host=panel();if(!host)return;
  host.innerHTML=`<form class="rist-start-card rist-campaign-new-clean" data-clean-new-campaign>
   <h1>New Campaign</h1>
   <label>Campaign Code<input name="creatorCode" maxlength="24" autocomplete="off" placeholder="DRAGON" required></label>
   <fieldset><legend>World</legend>
    <label><input type="radio" name="campaignKind" value="mmo" checked><span>MMO</span></label>
    <label><input type="radio" name="campaignKind" value="sandbox"><span>Sandbox</span></label>
   </fieldset>
   <p class="rist-start-note">Hosted campaign · 1 token</p>
   <output class="rist-start-note" data-clean-campaign-status aria-live="polite"></output>
   <button type="submit">Create Campaign</button>
   <button type="button" class="rist-start-back" data-clean-campaign-return>Return</button>
  </form>`;
  requestAnimationFrame(()=>q('input[name="creatorCode"]',host)?.focus());
 }
 function setStatus(message){const el=q('[data-clean-campaign-status]',panel());if(el)el.textContent=message||''}
 async function launch(kind,code){
  const prefsRaw=(()=>{try{return JSON.parse(localStorage.getItem(PREF_KEY)||'{}')}catch{return{}}})();
  const prefs={role:prefsRaw.role==='GameMaster'?'GameMaster':'Roleplayer',domain:kind==='sandbox'?'RIST':'Shaelvien MMO'};
  localStorage.setItem(PREF_KEY,JSON.stringify(prefs));
  localStorage.setItem('rist.topFrame.userRole',prefs.role);
  localStorage.setItem('rist.topFrame.domain',prefs.domain);
  localStorage.setItem(CAMPAIGN_CODE_KEY,code);
  document.dispatchEvent(new CustomEvent('rist:start-settings-changed',{detail:prefs}));
  setStatus('Opening campaign…');
  await window.RistGameStartScreen?.applyPrefs?.();
  const campaign={userCode:code,kind,hosted:true};
  sessionStorage.setItem('rist.gameStart.current',JSON.stringify({...prefs,kind:'new',campaign}));
  document.dispatchEvent(new CustomEvent('rist:new-campaign',{detail:{...prefs,campaign}}));
  document.dispatchEvent(new CustomEvent('rist:game-start',{detail:{...prefs,kind:'new',campaign}}));
  window.RistGameStartScreen?.close?.();
 }
 document.addEventListener('click',event=>{
  const target=event.target instanceof Element?event.target:null;if(!target)return;
  const newButton=target.closest('[data-action="new-campaign"]');
  if(newButton){event.preventDefault();event.stopImmediatePropagation();renderNew();return}
  if(target.closest('[data-clean-campaign-return]')){event.preventDefault();event.stopImmediatePropagation();window.RistGameStartScreen?.setView?.('home');return}
 },true);
 document.addEventListener('submit',event=>{
  const form=event.target instanceof Element?event.target.closest('[data-clean-new-campaign]'):null;if(!form)return;
  event.preventDefault();event.stopImmediatePropagation();
  const data=new FormData(form);const code=clean(data.get('creatorCode'));const kind=String(data.get('campaignKind')||'mmo')==='sandbox'?'sandbox':'mmo';
  if(!code){setStatus('Enter a campaign code.');return}
  void launch(kind,code);
 },true);
 const observer=new MutationObserver(removePreview);observer.observe(document.documentElement,{childList:true,subtree:true});removePreview();
 window.RistCampaignStartClean={renderNew};
})();