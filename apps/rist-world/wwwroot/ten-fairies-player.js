(()=>{
 'use strict';

 const PARTS=[
  'https://d2d6rnm6fnsp89.cloudfront.net/music/ten-fairies/Ten_Fairies_Part_1.mp3',
  'https://d2d6rnm6fnsp89.cloudfront.net/music/ten-fairies/Ten_Fairies_Part_2.mp3'
 ];
 const STYLE_ID='shaelvien-entry-clean-v6';
 const discordMark='<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M20.317 4.3698A19.7913 19.7913 0 0 0 15.432 2.855c-.211.375-.444.864-.608 1.249a18.27 18.27 0 0 0-5.647 0 12.64 12.64 0 0 0-.617-1.249A19.736 19.736 0 0 0 3.677 4.37C.586 8.938-.252 13.39.167 17.779A19.9 19.9 0 0 0 6.154 20.8a14.1 14.1 0 0 0 1.47-2.39 12.8 12.8 0 0 1-2.315-1.11c.194-.142.384-.29.568-.441 4.465 2.067 9.308 2.067 13.72 0 .185.152.375.3.568.441a12.8 12.8 0 0 1-2.319 1.111 14 14 0 0 0 1.47 2.39 19.84 19.84 0 0 0 5.987-3.022c.49-5.088-.837-9.5-4.886-13.41ZM8.02 15.331c-1.34 0-2.44-1.244-2.44-2.774s1.077-2.776 2.44-2.776c1.375 0 2.462 1.256 2.44 2.776 0 1.53-1.077 2.774-2.44 2.774Zm7.975 0c-1.34 0-2.44-1.244-2.44-2.774s1.077-2.776 2.44-2.776c1.375 0 2.462 1.256 2.44 2.776 0 1.53-1.065 2.774-2.44 2.774Z"/></svg>';
 let mediaObserverStarted=false;

 function inferPart(audio){
  const src=audio?.currentSrc||audio?.querySelector('source')?.src||'';
  return /Part_2\.mp3(?:$|[?#])/i.test(src)?1:0;
 }

 function updateMediaSession(part,audio){
  if(!('mediaSession' in navigator)||typeof MediaMetadata==='undefined')return;
  const roman=part===1?'II':'I';
  try{
   navigator.mediaSession.metadata=new MediaMetadata({
    title:`The Ten Fairies — Part ${roman}`,
    artist:'Winthrop · Modern realization by Suno',
    album:'The Ten Fairies (1880s)'
   });
  }catch{}
 }

 function wireMediaSessionAudio(audio){
  if(!audio||audio.dataset.tenFairiesMediaSession==='1')return;
  audio.dataset.tenFairiesMediaSession='1';
  const sync=()=>updateMediaSession(inferPart(audio),audio);
  audio.addEventListener('play',sync);
  audio.addEventListener('loadedmetadata',sync);
  audio.addEventListener('emptied',()=>requestAnimationFrame(sync));
  sync();
 }

 function wireMediaSessionPlayers(root=document){
  root.querySelectorAll?.('.ten-fairies-player audio').forEach(wireMediaSessionAudio);
 }

 function observeMediaSessionPlayers(){
  if(mediaObserverStarted||!document.body)return;
  mediaObserverStarted=true;
  new MutationObserver(records=>{
   records.forEach(record=>record.addedNodes.forEach(node=>{
    if(!(node instanceof Element))return;
    if(node.matches('.ten-fairies-player audio'))wireMediaSessionAudio(node);
    wireMediaSessionPlayers(node);
   }));
  }).observe(document.body,{childList:true,subtree:true});
 }

 function ensureStyles(){
  if(document.getElementById(STYLE_ID))return;
  const style=document.createElement('style');
  style.id=STYLE_ID;
  style.textContent=`
   .sr-only-shaelvien{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}
   [data-rist-play-entry] .artwork,[data-rist-play-entry] .artwork-lock{inset:-4%!important;transform:scale(1.055)!important;background-size:cover!important;background-position:center 47%!important;background-repeat:no-repeat!important;background-color:#05070d!important}
   [data-rist-play-entry]:after{background:linear-gradient(to bottom,rgba(0,0,0,.03) 0%,rgba(0,0,0,.08) 48%,rgba(0,0,0,.82) 100%)!important}
   [data-rist-play-entry] .entry{gap:8px!important;padding-bottom:76px!important;max-width:620px!important}
   [data-rist-play-entry] .tagline{display:block!important;font-size:calc(clamp(12px,2.8vw,17px) - 1px)!important}
   [data-rist-play-entry] .menu{grid-template-columns:1fr 1fr!important;gap:10px!important;max-width:560px!important}
   [data-rist-play-entry] .return-link{display:none!important}
   [data-rist-play-entry] .menu button{display:flex!important;align-items:center!important;justify-content:center!important;gap:9px!important;min-height:52px!important;font-size:clamp(11px,2.8vw,15px)!important;border-color:#718492!important;background:rgba(8,16,25,.88)!important;color:#f4f0e5!important;transition:background .16s ease,border-color .16s ease,color .16s ease,box-shadow .16s ease!important}
   [data-rist-play-entry] .menu button[data-armed="true"]{border-color:#c79a47!important;background:linear-gradient(#6a4a22,#33200f)!important;color:#ffe9ad!important;box-shadow:0 0 0 1px rgba(255,221,145,.16),0 10px 24px #0008!important}
   [data-rist-play-entry] .menu button svg{width:23px;height:23px;flex:0 0 23px}
   [data-rist-play-entry] .ten-fairies-player{display:block!important;position:fixed!important;z-index:2147483550!important;left:50%!important;right:auto!important;top:auto!important;bottom:max(5px,env(safe-area-inset-bottom))!important;transform:translateX(-50%)!important;width:min(760px,calc(100vw - 10px))!important;box-sizing:border-box!important;color:#eee6d2!important;font-family:system-ui,-apple-system,"Segoe UI",sans-serif!important}
   [data-rist-play-entry] .ten-fairies-dock{display:grid!important;grid-template-columns:minmax(112px,.42fr) auto minmax(220px,1.58fr)!important;grid-template-areas:"title parts audio" "ticker ticker ticker"!important;gap:4px 7px!important;align-items:center!important;overflow:hidden!important;padding:5px 7px 4px!important;border:1px solid rgba(183,150,75,.76)!important;border-radius:10px!important;background:rgba(4,10,14,.91)!important;box-shadow:0 9px 25px rgba(0,0,0,.42)!important;backdrop-filter:blur(8px)!important}
   [data-rist-play-entry] .ten-fairies-dock-title{grid-area:title!important;min-width:0!important;display:grid!important;gap:1px!important}
   [data-rist-play-entry] .ten-fairies-dock-title strong{color:#f0d68e!important;font:900 9px/1.05 system-ui!important;letter-spacing:.11em!important}
   [data-rist-play-entry] .ten-fairies-dock-title small{color:#9fb0b7!important;font:750 7px/1.1 system-ui!important;letter-spacing:.06em!important}
   [data-rist-play-entry] .ten-fairies-parts{grid-area:parts!important;display:flex!important;gap:3px!important}
   [data-rist-play-entry] .ten-fairies-part{min-width:28px!important;height:28px!important;border:1px solid rgba(183,150,75,.58)!important;border-radius:6px!important;background:#101820!important;color:#d9c78f!important;font:900 10px/1 system-ui!important;padding:0!important}
   [data-rist-play-entry] .ten-fairies-part[aria-pressed="true"]{background:#5a421d!important;color:#fff0b8!important;border-color:#d0a853!important}
   [data-rist-play-entry] .ten-fairies-audio{grid-area:audio!important;display:block!important;width:100%!important;min-width:0!important;height:30px!important;margin:0!important}
   [data-rist-play-entry] .ten-fairies-ticker{grid-area:ticker!important;min-width:0!important;overflow:hidden!important;white-space:nowrap!important;border-top:1px solid rgba(183,150,75,.2)!important;padding-top:2px!important;color:#b9c4c8!important;font:650 7.5px/1.15 Georgia,"Times New Roman",serif!important}
   [data-rist-play-entry] .ten-fairies-ticker>span{display:inline-block!important;min-width:max-content!important;padding-left:100%!important;animation:ten-fairies-entry-scroll 60s linear infinite!important}
   [data-rist-play-entry] .ten-fairies-ticker em{color:#dbc98f!important}
   @keyframes ten-fairies-entry-scroll{from{transform:translateX(0)}to{transform:translateX(-100%)}}
   @media(max-width:620px){
    [data-rist-play-entry] .entry{padding-bottom:72px!important}
    [data-rist-play-entry] .menu{gap:7px!important}
    [data-rist-play-entry] .menu button{min-height:50px!important;gap:7px!important}
    [data-rist-play-entry] .menu button svg{width:21px;height:21px;flex-basis:21px}
    [data-rist-play-entry] .ten-fairies-dock{grid-template-columns:1fr auto minmax(180px,2fr)!important;grid-template-areas:"title parts audio" "ticker ticker ticker"!important;gap:3px!important;padding:4px 5px 3px!important}
    [data-rist-play-entry] .ten-fairies-dock-title small{display:none!important}
    [data-rist-play-entry] .ten-fairies-part{min-width:26px!important;height:26px!important}
    [data-rist-play-entry] .ten-fairies-audio{height:28px!important}
   }
   @media(max-width:420px){
    [data-rist-play-entry] .artwork,[data-rist-play-entry] .artwork-lock{inset:-2.6%!important;transform:scale(1)!important;background-size:cover!important;background-position:center 47%!important}
   }
   @media(orientation:landscape) and (max-height:560px){
    [data-rist-play-entry] .artwork,[data-rist-play-entry] .artwork-lock{inset:-4%!important;transform:scale(1.055)!important;background-size:cover!important;background-position:center 45%!important}
    [data-rist-play-entry] .entry{padding-bottom:62px!important}
    [data-rist-play-entry] .tagline{font-size:10px!important}
   }
   @media(prefers-reduced-motion:reduce){[data-rist-play-entry] .ten-fairies-ticker{overflow-x:auto!important}[data-rist-play-entry] .ten-fairies-ticker>span{padding-left:0!important;animation:none!important}}
  `;
  document.head.appendChild(style);
 }

 function renderEntryPlayer(host){
  if(!host)return;
  host.dataset.compactAwsPlayer='1';
  host.setAttribute('aria-label','The Ten Fairies modern Suno realization');
  host.innerHTML=`
   <div class="ten-fairies-dock">
    <div class="ten-fairies-dock-title"><strong>THE TEN FAIRIES</strong><small data-ten-fairies-part-label>PART I · SUNO</small></div>
    <div class="ten-fairies-parts" aria-label="Choose The Ten Fairies part">
     <button type="button" class="ten-fairies-part" data-part="0" aria-pressed="true" aria-label="Select Part 1">I</button>
     <button type="button" class="ten-fairies-part" data-part="1" aria-pressed="false" aria-label="Select Part 2">II</button>
    </div>
    <audio class="ten-fairies-audio" controls preload="metadata" playsinline aria-label="Play The Ten Fairies Part 1 modern Suno realization"><source src="${PARTS[0]}" type="audio/mpeg"></audio>
    <div class="ten-fairies-ticker" role="note" aria-label="The Ten Fairies provenance and attribution"><span>Inspired by and dedicated to “Winthrop,” the printed composer credit on the historical <em>The Ten Fairies</em> · Historical source: Library of Congress, <em>Music for the Nation: American Sheet Music, ca. 1870–1885</em> · Modern audio realization: Suno · Not a historical recording · Attribution research associates J. R. Winthrop with James Ramsey Murray (1841–1905), but that identification is not yet conclusively tied to this score.</span></div>
   </div>`;

  const audio=host.querySelector('.ten-fairies-audio');
  const source=audio?.querySelector('source');
  const label=host.querySelector('[data-ten-fairies-part-label]');
  wireMediaSessionAudio(audio);
  updateMediaSession(0,audio);
  host.querySelectorAll('.ten-fairies-part').forEach(button=>button.addEventListener('click',()=>{
   const part=Number(button.dataset.part)||0;
   if(!audio||!source)return;
   audio.pause();
   source.src=PARTS[part];
   audio.setAttribute('aria-label',`Play The Ten Fairies Part ${part+1} modern Suno realization`);
   audio.load();
   updateMediaSession(part,audio);
   host.querySelectorAll('.ten-fairies-part').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
   if(label)label.textContent=`PART ${part===0?'I':'II'} · SUNO`;
  }));
 }

 function installDelayedActions(root){
  const buttons=[root.querySelector('#signin'),root.querySelector('#signup')].filter(Boolean);
  let live=root.querySelector('[data-entry-selection-status]');
  let pendingTimer=0;
  let pendingButton=null;
  if(!live){
   live=document.createElement('span');
   live.className='sr-only-shaelvien';
   live.dataset.entrySelectionStatus='1';
   live.setAttribute('aria-live','polite');
   root.appendChild(live);
  }
  const clearSelection=except=>buttons.forEach(button=>{
   if(button===except)return;
   button.dataset.armed='false';
   button.setAttribute('aria-pressed','false');
  });
  const cancelPending=()=>{
   if(pendingTimer){clearTimeout(pendingTimer);pendingTimer=0;}
   if(pendingButton){pendingButton.dataset.armed='false';pendingButton.setAttribute('aria-pressed','false');pendingButton=null;}
  };
  buttons.forEach(button=>{
   if(button.dataset.delayedActionReady==='1')return;
   button.dataset.delayedActionReady='1';
   button.dataset.armed='false';
   button.setAttribute('aria-pressed','false');
   button.addEventListener('click',event=>{
    if(button.dataset.releaseDelayedAction==='1'){
     button.dataset.releaseDelayedAction='0';
     button.dataset.armed='false';
     button.setAttribute('aria-pressed','false');
     pendingButton=null;
     live.textContent='';
     return;
    }
    event.preventDefault();
    event.stopImmediatePropagation();
    if(pendingButton!==button)cancelPending();
    clearSelection(button);
    button.dataset.armed='true';
    button.setAttribute('aria-pressed','true');
    pendingButton=button;
    const name=(button.textContent||'Action').trim().replace(/\s+/g,' ');
    live.textContent=`${name} selected. Continuing.`;
    if(pendingTimer)clearTimeout(pendingTimer);
    pendingTimer=setTimeout(()=>{
     pendingTimer=0;
     if(pendingButton!==button)return;
     button.dataset.releaseDelayedAction='1';
     button.click();
    },350);
   },true);
  });
 }

 function cleanEntry(){
  const root=document.querySelector('[data-rist-play-entry]');
  if(!root)return;
  ensureStyles();
  const signIn=root.querySelector('#signin');
  const signUp=root.querySelector('#signup');
  const returnLink=root.querySelector('.return-link');
  const provider=root.querySelector('.provider');
  const alpha=root.querySelector('.alpha');
  if(signIn){signIn.innerHTML=`${discordMark}<span>SIGN IN</span>`;signIn.setAttribute('aria-label','Sign in with Discord');}
  if(signUp){signUp.innerHTML=`${discordMark}<span>NEW USER</span>`;signUp.setAttribute('aria-label','Create a new account with Discord');}
  if(returnLink)returnLink.remove();
  if(provider){provider.classList.add('sr-only-shaelvien');provider.textContent='Authentication is provided by Discord.';}
  if(alpha)alpha.classList.add('sr-only-shaelvien');
  installDelayedActions(root);
  const players=[...root.querySelectorAll('.ten-fairies-player')];
  players.slice(1).forEach(player=>player.remove());
  if(players[0])renderEntryPlayer(players[0]);
 }

 function enforceUserControlledPlayback(){
  document.querySelectorAll('.ten-fairies-player audio').forEach(audio=>{audio.autoplay=false;audio.removeAttribute('autoplay');});
 }

 function run(){
  cleanEntry();
  enforceUserControlledPlayback();
  wireMediaSessionPlayers();
  observeMediaSessionPlayers();
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run,{once:true}); else run();
})();