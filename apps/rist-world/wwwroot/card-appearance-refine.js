(()=>{
  function refine(){
    document.querySelectorAll('.ccs-theme-modal').forEach(modal=>{
      modal.querySelector('.ccs-theme-wheel-large')?.remove();
      const discard=modal.querySelector('.ccs-theme-cancel');
      if(discard){
        discard.textContent='Discard changes';
        discard.setAttribute('aria-label','Discard appearance changes');
      }
      const apply=modal.querySelector('.ccs-theme-apply');
      if(apply){
        apply.textContent='Apply';
        apply.setAttribute('aria-label','Apply appearance changes');
      }
    });
  }
  const observer=new MutationObserver(refine);
  observer.observe(document.body,{childList:true,subtree:true});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',refine,{once:true});else refine();
})();
