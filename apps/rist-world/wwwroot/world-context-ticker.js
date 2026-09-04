(()=>{
 'use strict';
 let timer=0;
 const pad=value=>String(value).padStart(2,'0');
 function tick(){
  const now=new Date();
  const date=document.querySelector('.world-context-date time');
  const utc=document.querySelector('.world-context-utc time');
  if(date){const value=`${pad(now.getMonth()+1)}/${pad(now.getDate())}/${now.getFullYear()}`;if(date.textContent!==value)date.textContent=value;}
  if(utc){const value=`${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())}:${pad(now.getUTCSeconds())}`;if(utc.textContent!==value)utc.textContent=value;}
 }
 function start(){tick();if(!timer)timer=setInterval(tick,1000)}
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)tick()});
 document.addEventListener('rist:game-start',tick);
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.RistWorldTicker={tick};
})();
