(()=>{
 'use strict';
 let timer=0;
 const pad=value=>String(value).padStart(2,'0');
 const cfg=()=>window.RistTickerSettings?.load?.()||{visible:{stars:true,sky:true,cal:true,ugc:true,date:true,utc:true,start:true},custom:[]};
 function openStartMenu(event){event?.preventDefault?.();event?.stopPropagation?.();event?.stopImmediatePropagation?.();window.RistStartMenu?.open?.()}
 function ensureTrack(){
  const track=document.querySelector('.world-context-track');if(!track)return null;
  track.setAttribute('role','button');track.setAttribute('tabindex','0');track.setAttribute('aria-label','Open Start Menu');
  if(track.dataset.startMenuBound!=='1'){
   track.dataset.startMenuBound='1';track.addEventListener('click',openStartMenu,true);track.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' ')openStartMenu(e)},true);
  }
  track.querySelectorAll('.world-context-action,.world-context-utc').forEach(el=>{el.setAttribute('tabindex','-1');el.setAttribute('aria-hidden','true');el.style.pointerEvents='none'});
  let start=track.querySelector('.world-context-start-menu');const utc=track.querySelector('.world-context-utc');
  if(!start&&utc){start=document.createElement('span');start.className='world-context-readout world-context-start-menu';start.textContent='Start Menu';start.setAttribute('aria-hidden','true');utc.insertAdjacentElement('afterend',start)}
  return track;
 }
 function builtIns(track,c){const map={stars:track.querySelector('[data-context="stars"]'),sky:track.querySelector('[data-context="sky"]'),cal:track.querySelector('[data-context="cal"]'),ugc:track.querySelector('[data-context="ugc"]'),date:track.querySelector('.world-context-date'),utc:track.querySelector('.world-context-utc'),start:track.querySelector('.world-context-start-menu')};Object.entries(map).forEach(([k,el])=>{if(el)el.style.display=c.visible?.[k]===false?'none':''})}
 function calendarText(x){const months=Math.max(1,Number(x.monthsPerYear)||12),days=Math.max(1,Number(x.daysPerMonth)||30);const elapsed=Math.floor((Date.now()-(Number(x.startedAt)||Date.now()))/86400000);let y=Number(x.currentYear)||1,m=Math.max(1,Number(x.currentMonth)||1),d=Math.max(1,Number(x.currentDay)||1)+elapsed;while(d>days){d-=days;m++;if(m>months){m=1;y++}}const mn=Array.isArray(x.monthNames)&&x.monthNames[m-1]?x.monthNames[m-1]:String(m).padStart(2,'0');return `${x.label||'Custom Calendar'}: ${mn}/${String(d).padStart(2,'0')}/${y}${x.era?' '+x.era:''}`}
 function clockText(x){const hpd=Math.max(1,Number(x.hoursPerDay)||24),mph=Math.max(1,Number(x.minutesPerHour)||60),spm=Math.max(1,Number(x.secondsPerMinute)||60);const elapsed=Math.floor((Date.now()-(Number(x.startedAt)||Date.now()))/1000);let total=(Number(x.currentHour)||0)*mph*spm+(Number(x.currentMinute)||0)*spm+elapsed;const day=hpd*mph*spm;total=((total%day)+day)%day;const h=Math.floor(total/(mph*spm)),m=Math.floor((total%(mph*spm))/spm);return `${x.label||'Custom Clock'}: ${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}${x.periodLabel?' '+x.periodLabel:''}`}
 function customText(x){if(x.type==='calendar')return calendarText(x);if(x.type==='clock')return clockText(x);if(x.type==='currency')return `${x.label||'Currency'}: ${x.value||0}${x.unit?' '+x.unit:''}`;if(x.type==='number')return `${x.label||'Number'}: ${x.value||0}`;return x.text||''}
 function renderCustom(track,c){let host=track.querySelector('.world-context-custom-host');if(!host){host=document.createElement('span');host.className='world-context-custom-host';track.appendChild(host)}host.replaceChildren(...c.custom.filter(x=>x&&x.visible!==false).map(x=>{const s=document.createElement('span');s.className='world-context-readout world-context-custom';s.textContent=customText(x);s.setAttribute('aria-hidden','true');return s}))}
 function tick(){const now=new Date(),date=document.querySelector('.world-context-date time'),utc=document.querySelector('.world-context-utc time');if(date)date.textContent=`${pad(now.getMonth()+1)}/${pad(now.getDate())}/${now.getFullYear()}`;if(utc)utc.textContent=`${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())}:${pad(now.getUTCSeconds())}`;const track=ensureTrack();if(!track)return;const c=cfg();builtIns(track,c);renderCustom(track,c)}
 function start(){tick();if(!timer)timer=setInterval(tick,1000)}
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)tick()});document.addEventListener('rist:game-start',tick);document.addEventListener('rist:ticker-config-changed',tick);if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();window.RistWorldTicker={tick};
})();