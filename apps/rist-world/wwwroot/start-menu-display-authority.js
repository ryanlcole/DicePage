(()=>{
 'use strict';

 const makeTickerScroll=()=>{
  document.querySelectorAll('.worldbuilder-studio .studio-ticker').forEach(button=>{
   if(button.dataset.ristTickerScroll==='1')return;
   const label=(button.textContent||'WORLD BUILDING').trim()||'WORLD BUILDING';
   button.dataset.ristTickerScroll='1';
   button.setAttribute('title','Open Start Menu');
   button.innerHTML=`<span class="rist-ticker-window"><span class="rist-ticker-track"><span>${label}</span><span aria-hidden="true">${label}</span><span aria-hidden="true">${label}</span></span></span>`;
  });
 };

 const style=document.createElement('style');
 style.id='rist-start-menu-display-authority';
 style.textContent=`
  .worldbuilder-studio .studio-ticker{overflow:hidden!important;position:relative!important;min-width:150px!important;padding:0!important;cursor:pointer!important}
  .worldbuilder-studio .studio-ticker .rist-ticker-window{display:block;width:100%;overflow:hidden;white-space:nowrap;pointer-events:none}
  .worldbuilder-studio .studio-ticker .rist-ticker-track{display:inline-flex;align-items:center;gap:28px;min-width:max-content;will-change:transform;animation:rist-worldbuilding-ticker 9s linear infinite}
  .worldbuilder-studio .studio-ticker .rist-ticker-track>span{display:inline-block;white-space:nowrap;color:#e4c97d;font:900 7px/19px system-ui;letter-spacing:.08em}
  .worldbuilder-studio .studio-ticker:hover .rist-ticker-track,.worldbuilder-studio .studio-ticker:focus-visible .rist-ticker-track{animation-play-state:paused}
  @keyframes rist-worldbuilding-ticker{from{transform:translateX(0)}to{transform:translateX(calc(-33.333% - 9.333px))}}
  @media(prefers-reduced-motion:reduce){.worldbuilder-studio .studio-ticker .rist-ticker-track{animation:none!important}}
 `;
 document.head.appendChild(style);

 window.ristFullscreen={
  state(){
   const supported=!!(document.fullscreenEnabled||document.webkitFullscreenEnabled||document.documentElement.requestFullscreen||document.documentElement.webkitRequestFullscreen);
   const active=!!(document.fullscreenElement||document.webkitFullscreenElement);
   return [active,supported];
  },
  async toggle(){
   const active=document.fullscreenElement||document.webkitFullscreenElement;
   const root=document.documentElement;
   try{
    if(active){
     if(document.exitFullscreen)await document.exitFullscreen();
     else if(document.webkitExitFullscreen)document.webkitExitFullscreen();
    }else{
     if(root.requestFullscreen)await root.requestFullscreen({navigationUI:'hide'}).catch(()=>root.requestFullscreen());
     else if(root.webkitRequestFullscreen)root.webkitRequestFullscreen();
    }
   }catch{}
   return this.state();
  }
 };

 makeTickerScroll();
 const observer=new MutationObserver(makeTickerScroll);
 observer.observe(document.body,{childList:true,subtree:true});
})();
