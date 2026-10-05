(()=>{
 'use strict';

 const PART_1='https://d2d6rnm6fnsp89.cloudfront.net/music/ten-fairies/Ten_Fairies_Part_1.mp3';
 const PART_2='https://d2d6rnm6fnsp89.cloudfront.net/music/ten-fairies/Ten_Fairies_Part_2.mp3';
 const STYLE_ID='shaelvien-entry-clean-v3';
 const discordMark='<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M20.317 4.3698A19.7913 19.7913 0 0 0 15.432 2.855c-.211.375-.444.864-.608 1.249a18.27 18.27 0 0 0-5.647 0 12.64 12.64 0 0 0-.617-1.249A19.736 19.736 0 0 0 3.677 4.37C.586 8.938-.252 13.39.167 17.779A19.9 19.9 0 0 0 6.154 20.8a14.1 14.1 0 0 0 1.47-2.39 12.8 12.8 0 0 1-2.315-1.11c.194-.142.384-.29.568-.441 4.465 2.067 9.308 2.067 13.72 0 .185.152.375.3.568.441a12.8 12.8 0 0 1-2.319 1.111 14 14 0 0 0 1.47 2.39 19.84 19.84 0 0 0 5.987-3.022c.49-5.088-.837-9.5-4.886-13.41ZM8.02 15.331c-1.34 0-2.44-1.244-2.44-2.774s1.077-2.776 2.44-2.776c1.375 0 2.462 1.256 2.44 2.776 0 1.53-1.077 2.774-2.44 2.774Zm7.975 0c-1.34 0-2.44-1.244-2.44-2.774s1.077-2.776 2.44-2.776c1.375 0 2.462 1.256 2.44 2.776 0 1.53-1.065 2.774-2.44 2.774Z"/></svg>';

 function ensureStyles(){
  if(document.getElementById(STYLE_ID))return;
  const style=document.createElement('style');
  style.id=STYLE_ID;
  style.textContent=`
   .sr-only-shaelvien{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}
   [data-rist-play-entry] .artwork,[data-rist-play-entry] .artwork-lock{inset:0!important;transform:none!important;background-size:contain!important;background-position:center top!important;background-repeat:no-repeat!important;background-color:#05070d!important}
   [data-rist-play-entry]:after{background:linear-gradient(to bottom,rgba(0,0,0,0) 0 44%,rgba(3,7,11,.15) 62%,rgba(3,7,11,.9) 100%)!important}
   [data-rist-play-entry] .entry{gap:8px!important;padding-bottom:82px!important;max-width:620px!important}
   [data-rist-play-entry] .menu{grid-template-columns:1fr 1fr!important;gap:10px!important;max-width:560px!important}
   [data-rist-play-entry] .return-link{display:none!important}
   [data-rist-play-entry] .menu button{display:flex!important;align-items:center!important;justify-content:center!important;gap:9px!important;min-height:52px!important;font-size:clamp(11px,2.8vw,15px)!important}
   [data-rist-play-entry] .menu button svg{width:23px;height:23px;flex:0 0 23px}
   [data-rist-play-entry] .ten-fairies-player{display:block!important;position:fixed!important;z-index:2147483550!important;left:50%!important;right:auto!important;top:auto!important;bottom:max(5px,env(safe-area-inset-bottom))!important;transform:translateX(-50%)!important;width:min(760px,calc(100vw - 10px))!important;box-sizing:border-box!important;color:#eee6d2!important;font-family:system-ui,-apple-system,"Segoe UI",sans-serif!important}
   [data-rist-play-entry] .ten-fairies-dock{display:grid!important;grid-template-columns:minmax(105px,.36fr) minmax(300px,1.64fr)!important;grid-template-areas:"title tracks" "ticker ticker"!important;gap:4px 7px!important;align-items:center!important;overflow:hidden!important;padding:5px 7px 4px!important;border:1px solid rgba(183,150,75,.76)!important;border-radius:10px!important;background:rgba(4,10,14,.91)!important;box-shadow:0 9px 25px rgba(0,0,0,.42)!important;backdrop-filter:blur(8px)!important}
   [data-rist-play-entry] .ten-fairies-dock-title{grid-area:title!important;min-width:0!important;display:grid!important;gap:1px!important}
   [data-rist-play-entry] .ten-fairies-dock-title strong{color:#f0d68e!important;font:900 9px/1.05 system-ui!important;letter-spacing:.11em!important}
   [data-rist-play-entry] .ten-fairies-dock-title small{color:#9fb0b7!important;font:750 7px/1.1 system-ui!important;letter-spacing:.06em!important}
   [data-rist-play-entry] .ten-fairies-tracks{grid-area:tracks!important;display:grid!important;grid-template-columns:1fr 1fr!important;gap:4px!important;min-width:0!important}
   [data-rist-play-entry] .ten-fairies-track{display:grid!important;grid-template-columns:auto minmax(0,1fr)!important;gap:3px!important;align-items:center!important;min-width:0!important}
   [data-rist-play-entry] .ten-fairies-track>span{color:#f0d68e!important;font:900 8px/1 system-ui!important}
   [data-rist-play-entry] .ten-fairies-track audio{display:block!important;width:100%!important;min-width:0!important;height:28px!important;margin:0!important}
   [data-rist-play-entry] .ten-fairies-ticker{grid-area:ticker!important;min-width:0!important;overflow:hidden!important;white-space:nowrap!important;border-top:1px solid rgba(183,150,75,.2)!important;padding-top:2px!important;color:#b9c4c8!important;font:650 7.5px/1.15 Georgia,"Times New Roman",serif!important}
   [data-rist-play-entry] .ten-fairies-ticker>span{display:inline-block!important;min-width:max-content!important;padding-left:100%!important;animation:ten-fairies-entry-scroll 30s linear infinite!important}
   [data-rist-play-entry] .ten-fairies-ticker em{color:#dbc98f!important}
   @keyframes ten-fairies-entry-scroll{from{transform:translateX(0)}to{transform:translateX(-100%)}}
   @media(max-width:620px){
    [data-rist-play-entry] .entry{padding-bottom:78px!important}
    [data-rist-play-entry] .menu{gap:7px!important}
    [data-rist-play-entry] .menu button{min-height:50px!important;gap:7px!important}
    [data-rist-play-entry] .menu button svg{width:21px;height:21px;flex-basis:21px}
    [data-rist-play-entry] .ten-fairies-dock{grid-template-columns:1fr!important;grid-template-areas:"title" "tracks" "ticker"!important;gap:2px!important;padding:4px 5px 3px!important}
    [data-rist-play-entry] .ten-fairies-dock-title{display:flex!important;align-items:baseline!important;justify-content:center!important;gap:7px!important;text-align:center!important}
   }
   @media(orientation:landscape) and (max-height:560px){
    [data-rist-play-entry] .artwork,[data-rist-play-entry] .artwork-lock{background-size:cover!important;background-position:center 38%!important}
    [data-rist-play-entry] .entry{padding-bottom:64px!important}
   }
   @media(prefers-reduced-motion:reduce){[data-rist-play-entry] .ten-fairies-ticker{overflow-x:auto!important}[data-rist-play-entry] .ten-fairies-ticker>span{padding-left:0!important;animation:none!important}}
  `;
  document.head.appendChild(style);
 }

 function renderEntryPlayer(host){
  if(!host||host.dataset.compactAwsPlayer==='1')return;
  host.dataset.compactAwsPlayer='1';
  host.setAttribute('aria-label','The Ten Fairies modern Suno realizations');
  host.innerHTML=`
   <div class="ten-fairies-dock">
    <div class="ten-fairies-dock-title"><strong>THE TEN FAIRIES</strong><small>SUNO REALIZATION</small></div>
    <div class="ten-fairies-tracks" aria-label="The Ten Fairies audio tracks">
     <label class="ten-fairies-track"><span>I</span><audio controls preload="metadata" playsinline aria-label="Play The Ten Fairies Part 1 modern Suno realization"><source src="${PART_1}" type="audio/mpeg"></audio></label>
     <label class="ten-fairies-track"><span>II</span><audio controls preload="metadata" playsinline aria-label="Play The Ten Fairies Part 2 modern Suno realization"><source src="${PART_2}" type="audio/mpeg"></audio></label>
    </div>
    <div class="ten-fairies-ticker" role="note" aria-label="The Ten Fairies provenance and attribution"><span>Inspired by and dedicated to “Winthrop,” the printed composer credit on the historical <em>The Ten Fairies</em> · Historical source: Library of Congress, <em>Music for the Nation: American Sheet Music, ca. 1870–1885</em> · Modern audio realization: Suno · Not a historical recording · Attribution research associates J. R. Winthrop with James Ramsey Murray (1841–1905), but that identification is not yet conclusively tied to this score.</span></div>
   </div>`;
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
  if(returnLink){returnLink.remove();}
  if(provider){provider.classList.add('sr-only-shaelvien');provider.textContent='Authentication is provided by Discord.';}
  if(alpha){alpha.classList.add('sr-only-shaelvien');}

  root.querySelectorAll('.ten-fairies-player').forEach(renderEntryPlayer);
 }

 function enforceUserControlledPlayback(){
  document.querySelectorAll('.ten-fairies-player audio').forEach(audio=>{
   audio.autoplay=false;
   audio.removeAttribute('autoplay');
  });
 }

 function run(){cleanEntry();enforceUserControlledPlayback();}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run,{once:true});
 else run();
})();
