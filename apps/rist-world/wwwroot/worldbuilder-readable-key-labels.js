(()=>{
 'use strict';
 const VERSION='20260917-readable-keys-1';
 if(window.RistWorldBuilderReadableKeys?.version===VERSION)return;
 let frame=0;
 const keyboard=()=>document.querySelector('.worldbuilder-studio .wb-device-keyboard');
 const labelOf=button=>{
  const strong=button.querySelector(':scope > strong')?.textContent?.trim();
  if(strong)return strong;
  const aria=(button.getAttribute('aria-label')||'').split('.')[0].trim();
  return aria||button.textContent?.trim()||'Key';
 };
 function cleanModeArt(host){
  host.querySelectorAll('.wb-device-mode').forEach(button=>{
   button.classList.add('wb-readable-mode');
   button.style.setProperty('background-image','none','important');
   button.style.setProperty('background-size','auto','important');
  });
 }
 function labelKeys(host){
  host.querySelectorAll('.wb-device-keys .wb-device-key').forEach(button=>{
   if(button.closest('.wb-asset-keyboard')||button.closest('.wb-persistent-dpad'))return;
   const label=labelOf(button);
   let visible=button.querySelector(':scope > .wb-key-readable-label');
   if(!visible){
    visible=document.createElement('span');
    visible.className='wb-key-readable-label';
    visible.setAttribute('aria-hidden','true');
    button.appendChild(visible);
   }
   if(visible.textContent!==label)visible.textContent=label;
   button.classList.add('wb-readable-key');
   button.dataset.readableKey=label;
  });
 }
 function apply(){const host=keyboard();if(!host)return;cleanModeArt(host);labelKeys(host)}
 function schedule(){if(frame)return;frame=requestAnimationFrame(()=>{frame=0;apply()})}
 function start(){
  apply();
  const observer=new MutationObserver(records=>{if(records.some(record=>record.type==='childList'||record.type==='attributes'))schedule()});
  observer.observe(document.getElementById('app')||document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['aria-selected','class','style']});
  document.addEventListener('click',event=>{if(event.target?.closest?.('.wb-device-keyboard'))setTimeout(schedule,0)},true);
  window.addEventListener('rist:viewer-state',schedule);
  window.addEventListener('rist-sprite-playback',schedule);
  window.addEventListener('pageshow',schedule,{passive:true});
 }
 window.RistWorldBuilderReadableKeys={version:VERSION,refresh:schedule};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
