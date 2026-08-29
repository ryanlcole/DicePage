(()=>{
 'use strict';
 const subtitleFor=()=>{
  const active=document.querySelector('.character-console .console-bank.board-section-active');
  if(!active)return '';
  const match=[['attributes-bank','Attribute'],['trackers-bank','Tracker'],['limits-bank','Limit'],['skills-bank','Skill'],['flare-bank','Flare']].find(([name])=>active.classList.contains(name));
  return match?.[1]||'';
 };
 function apply(){
  document.querySelectorAll('.card-detail-editor:not([data-subtitle-defaulted="1"])').forEach(editor=>{
   const input=[...editor.querySelectorAll('label')].find(label=>label.textContent.trim().startsWith('Subtitle'))?.querySelector('input');
   if(!input)return;
   editor.dataset.subtitleDefaulted='1';
   if(input.value.trim())return;
   const next=subtitleFor();
   if(next){input.value=next;input.dispatchEvent(new Event('input',{bubbles:true}))}
  });
 }
 document.addEventListener('rist:dom-change',apply);
 apply();
})();
