(()=>{
 'use strict';

 const PARTS=[
  {
   label:'Part 1 of 2',
   url:'https://drive.google.com/uc?export=download&id=1bwcsUkSJ8BQ9jyMhMaDadCah76B-zHv-'
  },
  {
   label:'Part 2 of 2',
   url:'https://drive.google.com/uc?export=download&id=1fsB9MRkDgWRSBfqC8rHxCKBq0DdJq1tB'
  }
 ];
 const STYLE_ID='ten-fairies-two-part-style';
 const START_SURFACES='.rist-auth-shell,.rist-auth-start,.launcher-hub,[data-rist-play-entry]';

 function ensureStyle(){
  if(document.getElementById(STYLE_ID))return;
  const style=document.createElement('style');
  style.id=STYLE_ID;
  style.textContent=`
   .ten-fairies-player{
    top:auto!important;
    right:auto!important;
    bottom:max(8px,env(safe-area-inset-bottom))!important;
    left:50%!important;
    transform:translateX(-50%)!important;
    width:min(760px,calc(100vw - 16px))!important;
    max-width:none!important;
    z-index:2147483550!important;
    box-sizing:border-box!important;
    color:#eee6d2!important;
    font-family:system-ui,-apple-system,"Segoe UI",sans-serif!important;
    text-align:left!important;
   }
   [data-rist-play-entry] .ten-fairies-player{display:block!important}
   .ten-fairies-player .ten-fairies-dock{
    display:grid;
    grid-template-columns:minmax(128px,.55fr) minmax(220px,1.45fr);
    grid-template-areas:"title audio" "note note";
    gap:5px 10px;
    align-items:center;
    overflow:hidden;
    padding:8px 10px 7px;
    border:1px solid rgba(183,150,75,.78);
    border-radius:12px;
    background:rgba(4,10,14,.92);
    box-shadow:0 12px 34px rgba(0,0,0,.46);
    backdrop-filter:blur(8px);
   }
   .ten-fairies-player .ten-fairies-dock-title{grid-area:title;min-width:0;display:grid;gap:2px}
   .ten-fairies-player .ten-fairies-dock-title strong{color:#f0d68e;font:900 10px/1.05 system-ui;letter-spacing:.12em}
   .ten-fairies-player .ten-fairies-dock-title small{color:#c2ccd0;font:750 9px/1.15 system-ui;letter-spacing:.05em}
   .ten-fairies-player audio{grid-area:audio;display:block;width:100%!important;height:34px!important;margin:0!important}
   .ten-fairies-player .ten-fairies-dedication{grid-area:note;margin:0!important;color:#d5c7a0;font:650 9px/1.3 Georgia,"Times New Roman",serif;text-align:center}
   .ten-fairies-player .ten-fairies-dedication em{color:#f0d68e}
   .ten-fairies-player .ten-fairies-modern-note{display:block;margin-top:1px;color:#93a5ad;font:600 8px/1.2 system-ui;letter-spacing:.02em}
   body:has([data-rist-play-entry]) .entry{padding-bottom:clamp(96px,14vh,120px)!important}
   @media(max-width:620px){
    .ten-fairies-player{width:min(520px,calc(100vw - 12px))!important;bottom:max(6px,env(safe-area-inset-bottom))!important}
    .ten-fairies-player .ten-fairies-dock{grid-template-columns:1fr;grid-template-areas:"title" "audio" "note";gap:4px;padding:7px 8px 6px}
    .ten-fairies-player .ten-fairies-dock-title{text-align:center}
    .ten-fairies-player audio{height:32px!important}
    body:has([data-rist-play-entry]) .entry{padding-bottom:clamp(132px,22vh,160px)!important}
   }
   @media(prefers-reduced-transparency:reduce){.ten-fairies-player .ten-fairies-dock{background:#040a0e;backdrop-filter:none}}
  `;
  document.head.appendChild(style);
 }

 function visible(host){
  if(!host||!host.isConnected)return false;
  if(!document.querySelector(START_SURFACES))return false;
  const s=getComputedStyle(host);
  return s.display!=='none'&&s.visibility!=='hidden';
 }

 function render(host){
  if(host.dataset.tenFairiesTwoPart==='1')return;
  host.dataset.tenFairiesTwoPart='1';
  host.setAttribute('aria-label','The Ten Fairies two-part music player');
  host.innerHTML=`
   <div class="ten-fairies-dock">
    <div class="ten-fairies-dock-title">
     <strong>THE TEN FAIRIES</strong>
     <small data-ten-fairies-part>Part 1 of 2 · modern interpretation</small>
    </div>
    <audio controls preload="auto" playsinline data-ten-fairies-audio aria-label="Play The Ten Fairies two-part modern interpretation">
     Your browser does not support audio playback.
    </audio>
    <p class="ten-fairies-dedication">Inspired by and dedicated to <strong>“Winthrop”</strong>, the composer credited on the original 1882 publication, <em>The Ten Fairies</em>.
     <span class="ten-fairies-modern-note">Modern two-part interpretation · not a historical recording.</span>
    </p>
   </div>`;

  const audio=host.querySelector('[data-ten-fairies-audio]');
  const label=host.querySelector('[data-ten-fairies-part]');
  let current=0;
  let initialStarted=false;

  function setPart(index,play){
   current=index;
   audio.dataset.part=String(index+1);
   label.textContent=`${PARTS[index].label} · modern interpretation`;
   if(audio.src!==PARTS[index].url){
    audio.src=PARTS[index].url;
    audio.load();
   }
   if(play)void attemptPlay();
  }

  async function attemptPlay(){
   if(!visible(host)||!audio.paused||audio.ended)return false;
   try{
    await audio.play();
    initialStarted=true;
    return true;
   }catch{
    return false;
   }
  }

  audio.addEventListener('play',()=>{initialStarted=true});
  audio.addEventListener('ended',()=>{
   if(current===0)setPart(1,true);
  });

  const unlock=()=>{
   if(!initialStarted&&visible(host))void attemptPlay();
  };
  document.addEventListener('pointerdown',unlock,{capture:true,passive:true});
  document.addEventListener('touchstart',unlock,{capture:true,passive:true});
  document.addEventListener('keydown',unlock,{capture:true});

  setPart(0,false);
  requestAnimationFrame(()=>requestAnimationFrame(()=>void attemptPlay()));
 }

 function scan(){
  ensureStyle();
  document.querySelectorAll('.ten-fairies-player').forEach(render);
 }

 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',scan,{once:true});
 else scan();
 const observer=new MutationObserver(scan);
 observer.observe(document.documentElement,{subtree:true,childList:true});
})();
