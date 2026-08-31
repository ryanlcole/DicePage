(()=>{
 'use strict';

 let mode='shaelvien';
 const button=()=>document.querySelector('[aria-label="Toggle Sandbox and MMO"]');
 const stateNode=()=>document.querySelector('.mmo-zone-actions[data-world-mode]');
 const canAiEdit=()=>button()?.dataset.shaelvienAiAuthority==='true';
 const ownsCurrentZone=()=>document.body.classList.contains('rist-mmo-owned-zone');
 const authenticated=()=>!!document.querySelector('.rist.auth-ready');

 function savedMode(){
  return stateNode()?.dataset.worldMode==='sandbox'?'local':'shaelvien';
 }

 function render(emit=false){
  const shaelvien=mode==='shaelvien',owner=canAiEdit(),owns=ownsCurrentZone();
  document.body.classList.toggle('rist-mmo-shaelvien',shaelvien);
  document.body.classList.toggle('rist-mmo-local',!shaelvien);
  document.body.classList.toggle('rist-shaelvien-ai-owner',shaelvien&&owner);
  const b=button();
  if(b){
   b.classList.add('header-mmo-button');
   b.classList.toggle('active',shaelvien);
   b.classList.toggle('mmo-art-active',shaelvien);
   b.classList.toggle('ai-authority',shaelvien&&owner);
   b.setAttribute('aria-pressed',String(shaelvien));
   b.querySelector('strong')?.replaceChildren(document.createTextNode(shaelvien?'MMO':'Sandbox'));
   b.title=shaelvien?(owns?'MMO — your editable GM zone':owner?'MMO — AI edit authority':'MMO — published map locked'):'Sandbox — editable personal world';
  }
  if(emit)document.dispatchEvent(new CustomEvent('rist:mmo-mode',{detail:{mode,canAiEdit:owner,ownsCurrentZone:owns}}));
 }

 function sync(){
  const next=savedMode();
  if(next===mode)return;
  mode=next;
  render(true);
 }

 function apply(next){
  const target=next==='local'?'local':'shaelvien';
  if(!authenticated()){
   mode='shaelvien';
   render(false);
   return;
  }
  if(target===mode)return;
  mode=target;
  render(true);
  document.querySelector(target==='local'?'.mmo-mode-sandbox-action':'.mmo-mode-shaelvien-action')?.click();
 }

 const toggle=()=>apply(mode==='shaelvien'?'local':'shaelvien');
 function guard(e){
  if(mode!=='shaelvien'||ownsCurrentZone())return;
  const target=e.target instanceof Element?e.target:null;
  if(target?.closest('.tile-browser,.pallet,.zone-editor,.tile-cell,.piece:not(.pin),.map-lock-button')){
   e.preventDefault();e.stopImmediatePropagation();
  }
 }

 document.addEventListener('pointerdown',guard,true);
 document.addEventListener('rist:dom-change',sync);
 document.addEventListener('rist:mmo-build',()=>render(true));
 window.RistMMO={toggle,setMode:apply,get mode(){return mode},get canAiEdit(){return canAiEdit()}};
 mode=savedMode();
 render(false);
})();
