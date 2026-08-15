(()=>{
 const subtitleFor=()=>{
   const active=document.querySelector('.character-console .console-bank.board-section-active');
   if(!active)return '';
   if(active.classList.contains('attributes-bank'))return 'Attribute';
   if(active.classList.contains('trackers-bank'))return 'Tracker';
   if(active.classList.contains('limits-bank'))return 'Limit';
   if(active.classList.contains('skills-bank'))return 'Skill';
   if(active.classList.contains('flare-bank'))return 'Flare';
   return '';
 };
 const apply=()=>{
   const editor=document.querySelector('.card-detail-editor');
   if(!editor||editor.dataset.subtitleDefaulted==='1')return;
   const input=[...editor.querySelectorAll('label')].find(x=>x.textContent.trim().startsWith('Subtitle'))?.querySelector('input');
   if(!input)return;
   editor.dataset.subtitleDefaulted='1';
   if(!input.value.trim()){
     const next=subtitleFor();
     if(next){input.value=next;input.dispatchEvent(new Event('input',{bubbles:true}));}
   }
 };
 new MutationObserver(apply).observe(document.documentElement,{childList:true,subtree:true});
 apply();
})();