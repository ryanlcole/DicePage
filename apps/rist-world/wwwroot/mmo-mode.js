(()=>{
 const KEY='rist:mmo-mode';
 let mode=localStorage.getItem(KEY)||'local';
 const button=()=>document.querySelector('.header-mmo-button');
 const canAiEdit=()=>button()?.dataset.shaelvienAiAuthority==='true';
 function syncAuthority(){document.body.classList.toggle('rist-shaelvien-ai-owner',mode==='shaelvien'&&canAiEdit())}
 function apply(next,persist=true){
  mode=next==='shaelvien'?'shaelvien':'local';
  if(persist)localStorage.setItem(KEY,mode);
  document.body.classList.toggle('rist-mmo-shaelvien',mode==='shaelvien');
  document.body.classList.toggle('rist-mmo-local',mode==='local');
  const b=button();
  if(b){
   const owner=canAiEdit();
   b.classList.toggle('active',mode==='shaelvien');
   b.classList.toggle('ai-authority',mode==='shaelvien'&&owner);
   b.setAttribute('aria-pressed',String(mode==='shaelvien'));
   b.title=mode==='shaelvien'?(owner?'Shaelvien MMO — AI edit authority':'Shaelvien MMO — published map locked'):'GM local mode — editable personal map';
  }
  syncAuthority();
  document.dispatchEvent(new CustomEvent('rist:mmo-mode',{detail:{mode,canAiEdit:canAiEdit()}}));
 }
 function toggle(){apply(mode==='shaelvien'?'local':'shaelvien')}
 function guard(e){
  if(mode!=='shaelvien')return;
  // Published Shaelvien maps remain manually locked for everyone, including the owner.
  // Owner authority is reserved for AI-mediated edits and future protected AI endpoints.
  if(e.target.closest('.tile-browser,.pallet,.zone-editor,.tile-cell,.piece:not(.pin),.map-lock-button')){e.preventDefault();e.stopImmediatePropagation()}
 }
 document.addEventListener('pointerdown',guard,true);
 const observer=new MutationObserver(()=>syncAuthority());
 observer.observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:['data-shaelvien-ai-authority']});
 window.RistMMO={toggle,setMode:apply,get mode(){return mode},get canAiEdit(){return canAiEdit()}};
 document.addEventListener('DOMContentLoaded',()=>apply(mode,false));
 setTimeout(()=>apply(mode,false),0);
})();