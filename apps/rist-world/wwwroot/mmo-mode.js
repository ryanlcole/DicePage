(()=>{
 'use strict';
 const KEY='rist:mmo-mode';
 const saved=localStorage.getItem(KEY);
 // MMO is authoritative for a new/unknown preference. Preserve an explicit
 // Sandbox/local choice made by an existing user.
 let mode=saved==='local'?'local':'shaelvien';
 let syncQueued=false;

 const rail=()=>document.querySelector('#header-slider .release-root-track');
 const mmoButton=()=>document.querySelector('.header-mmo-button');
 const sandboxButton=()=>document.querySelector('.header-sandbox-button');
 const canAiEdit=()=>mmoButton()?.dataset.shaelvienAiAuthority==='true';
 const ownsCurrentZone=()=>document.body.classList.contains('rist-mmo-owned-zone');

 function bind(button,next){
  if(!button||button.dataset.ristWorldModeBound==='1')return;
  button.dataset.ristWorldModeBound='1';
  button.removeAttribute('onclick');
  button.addEventListener('click',()=>apply(next));
 }

 function ensureControls(){
  const track=rail();
  if(!track)return;

  let mmo=mmoButton();
  if(!mmo){
   mmo=track.querySelector('[aria-label="Toggle Sandbox and MMO"]');
   if(!mmo)return;
   mmo.classList.add('header-mmo-button');
   mmo.setAttribute('aria-label','Use MMO world');
   mmo.innerHTML='<strong>MMO</strong>';
  }

  const door=track.querySelector('.door-button');
  if(door&&door.nextElementSibling!==mmo)door.insertAdjacentElement('afterend',mmo);

  let sandbox=sandboxButton();
  if(!sandbox){
   sandbox=document.createElement('button');
   sandbox.type='button';
   sandbox.className='root-menu-button header-sandbox-button';
   sandbox.setAttribute('aria-label','Use Sandbox world');
   sandbox.innerHTML='<strong>Sandbox</strong>';
   mmo.insertAdjacentElement('afterend',sandbox);
  }else if(mmo.nextElementSibling!==sandbox){
   mmo.insertAdjacentElement('afterend',sandbox);
  }

  bind(mmo,'shaelvien');
  bind(sandbox,'local');
 }

 function controlsNeedSync(){
  const track=rail();
  if(!track)return false;
  const mmo=mmoButton(),sandbox=sandboxButton();
  if(!mmo||!sandbox)return true;
  const door=track.querySelector('.door-button');
  return !!(door&&door.nextElementSibling!==mmo)||mmo.nextElementSibling!==sandbox;
 }

 function render(emit=false){
  ensureControls();
  const shaelvien=mode==='shaelvien',owner=canAiEdit(),owns=ownsCurrentZone();
  document.body.classList.toggle('rist-mmo-shaelvien',shaelvien);
  document.body.classList.toggle('rist-mmo-local',!shaelvien);
  document.body.classList.toggle('rist-shaelvien-ai-owner',shaelvien&&owner);

  const mmo=mmoButton(),sandbox=sandboxButton();
  if(mmo){
   mmo.classList.toggle('active',shaelvien);
   mmo.classList.toggle('mmo-art-active',shaelvien);
   mmo.classList.toggle('ai-authority',shaelvien&&owner);
   mmo.setAttribute('aria-pressed',String(shaelvien));
   mmo.title=shaelvien?(owns?'MMO — your editable GM zone':owner?'MMO — AI edit authority':'MMO — published map locked'):'Switch to MMO';
  }
  if(sandbox){
   sandbox.classList.toggle('active',!shaelvien);
   sandbox.setAttribute('aria-pressed',String(!shaelvien));
   sandbox.title=shaelvien?'Switch to Sandbox':'Sandbox — editable personal map';
  }
  if(emit)document.dispatchEvent(new CustomEvent('rist:mmo-mode',{detail:{mode,canAiEdit:owner,ownsCurrentZone:owns}}));
 }

 function scheduleControlSync(){
  // PLC reports every DOM mutation. Only react when Blazor has actually
  // replaced or moved the world-mode controls; never render in response to
  // mutations made by render() itself.
  if(syncQueued||!controlsNeedSync())return;
  syncQueued=true;
  requestAnimationFrame(()=>{
   syncQueued=false;
   if(controlsNeedSync())render(false);
  });
 }

 function apply(next,persist=true){
  mode=next==='local'?'local':'shaelvien';
  if(persist)localStorage.setItem(KEY,mode);
  render(true);
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
 document.addEventListener('rist:dom-change',scheduleControlSync);
 document.addEventListener('rist:mmo-build',()=>render(true));
 window.RistMMO={toggle,setMode:apply,get mode(){return mode},get canAiEdit(){return canAiEdit()}};
 render(false);
})();
