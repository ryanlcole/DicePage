(()=>{
 'use strict';
 const q=s=>document.querySelector(s);
 function mode(){return q('.mmo-zone-actions')?.dataset.worldMode||q('.map-shell')?.dataset.worldMode||'mmo'}
 function toggle(){q(mode()==='mmo'?'.mmo-mode-sandbox-action':'.mmo-mode-shaelvien-action')?.click()}
 function sync(){
  const button=q('.release-map-region .map-frame-mode-toggle');if(!button)return;
  const m=mode();
  button.textContent=m==='mmo'?'MMO':'Sandbox';
  button.setAttribute('aria-label',m==='mmo'?'Switch to Sandbox':'Switch to MMO');
  button.setAttribute('aria-pressed',m==='mmo'?'true':'false');
  if(button.dataset.ristModeBound==='1')return;
  button.dataset.ristModeBound='1';
  button.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();toggle()});
 }
 let queued=false;const schedule=()=>{if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;sync()})};
 new MutationObserver(schedule).observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['data-world-mode']});
 setInterval(sync,500);
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',sync,{once:true});else sync();
})();
