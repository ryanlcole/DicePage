(()=>{
 'use strict';
 const q=s=>document.querySelector(s);
 function mode(){return q('.mmo-zone-actions')?.dataset.worldMode||q('.map-shell')?.dataset.worldMode||'mmo'}
 function toggle(){q(mode()==='mmo'?'.mmo-mode-sandbox-action':'.mmo-mode-shaelvien-action')?.click()}
 function sync(){
  const title=q('.release-map-region .map-frame-title');if(!title)return;
  const prefix=title.querySelector('.map-frame-title-prefix');
  const input=title.querySelector('input');
  const m=mode();
  if(prefix)prefix.textContent='';
  if(input){input.value=m==='mmo'?'Shaelvien MMO - AI Map':'RIST Sandbox - Map';input.setAttribute('aria-label','Toggle MMO and Sandbox');}
  title.classList.add('rist-world-mode-title');
  title.setAttribute('role','button');title.setAttribute('tabindex','0');title.setAttribute('aria-label',m==='mmo'?'Shaelvien MMO - AI Map; switch to Sandbox':'RIST Sandbox - Map; switch to MMO');title.setAttribute('aria-pressed',m==='mmo'?'true':'false');
  if(title.dataset.ristModeBound==='1')return;
  title.dataset.ristModeBound='1';
  title.addEventListener('click',e=>{e.preventDefault();toggle()});
  title.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();toggle()}});
 }
 let queued=false;const schedule=()=>{if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;sync()})};
 new MutationObserver(schedule).observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['data-world-mode']});
 setInterval(sync,500);
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',sync,{once:true});else sync();
})();