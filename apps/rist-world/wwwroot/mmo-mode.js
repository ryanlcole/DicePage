(()=>{
 'use strict';
 const KEY='rist:mmo-mode';
 let mode=localStorage.getItem(KEY)==='shaelvien'?'shaelvien':'local';
 const button=()=>document.querySelector('.header-mmo-button');
 const canAiEdit=()=>button()?.dataset.shaelvienAiAuthority==='true';
 const ownsCurrentZone=()=>document.body.classList.contains('rist-mmo-owned-zone');
 function render(emit=false){
  const shaelvien=mode==='shaelvien',owner=canAiEdit(),owns=ownsCurrentZone();
  document.body.classList.toggle('rist-mmo-shaelvien',shaelvien);
  document.body.classList.toggle('rist-mmo-local',!shaelvien);
  document.body.classList.toggle('rist-shaelvien-ai-owner',shaelvien&&owner);
  const b=button();
  if(b){
   b.classList.toggle('active',shaelvien);b.classList.toggle('mmo-art-active',shaelvien);b.classList.toggle('ai-authority',shaelvien&&owner);
   b.setAttribute('aria-pressed',String(shaelvien));
   b.title=shaelvien?(owns?'Shaelvien MMO — your editable GM zone':owner?'Shaelvien MMO — AI edit authority':'Shaelvien MMO — published map locked'):'GM local mode — editable personal map';
  }
  if(emit)document.dispatchEvent(new CustomEvent('rist:mmo-mode',{detail:{mode,canAiEdit:owner,ownsCurrentZone:owns}}));
 }
 function apply(next,persist=true){mode=next==='shaelvien'?'shaelvien':'local';if(persist)localStorage.setItem(KEY,mode);render(true)}
 const toggle=()=>apply(mode==='shaelvien'?'local':'shaelvien');
 function guard(e){if(mode!=='shaelvien'||ownsCurrentZone())return;const target=e.target instanceof Element?e.target:null;if(target?.closest('.tile-browser,.pallet,.zone-editor,.tile-cell,.piece:not(.pin),.map-lock-button')){e.preventDefault();e.stopImmediatePropagation()}}
 document.addEventListener('pointerdown',guard,true);
 document.addEventListener('rist:dom-change',()=>render(false));
 document.addEventListener('rist:mmo-build',()=>render(true));
 window.RistMMO={toggle,setMode:apply,get mode(){return mode},get canAiEdit(){return canAiEdit()}};
 render(false);
})();
