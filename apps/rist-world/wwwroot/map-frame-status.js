(()=>{
 'use strict';
 const FRAME_HEIGHT=12;
 const qs=(root,selector)=>root?.querySelector(selector);
 const pinState={mode:'idle',x:.5,y:.5,moving:false};
 let mapEventsBound=false;

 function clickHidden(selector){const el=document.querySelector(selector);if(el){el.click();return true;}return false;}
 function sourcePinButton(){return document.querySelector('.public-pin-source,.token-pin-source,.private-pin-source');}
 function findPrivateControl(kind){
  const root=document.querySelector('.release-private-region');
  if(!root)return null;
  const candidates=[...root.querySelectorAll('button,[role="button"]')];
  if(kind==='tier')return candidates.find(el=>/^\s*TIER\b/i.test(el.textContent||''));
  if(kind==='layer')return candidates.find(el=>/^\s*LAYER\b/i.test(el.textContent||''));
  return null;
 }
 function hideMapOverlayText(){
  const root=document.querySelector('.release-map-region');
  if(!root)return;
  [...root.querySelectorAll('*')].forEach(el=>{
   const text=(el.textContent||'').replace(/\s+/g,' ').trim();
   if(!text||text.length>180)return;
   const target=/Temporary Public Zone/i.test(text)||/SHAELVIEN\s+MMO.*AI\s*MAP/i.test(text);
   if(!target)return;
   if(el.matches('.map-frame-title,.rist-coordinate-axis,.rist-coordinate-tick,.map-frame-controls'))return;
   if(el.children.length>4)return;
   el.style.setProperty('display','none','important');
  });
 }
 function setSettingsLabel(){
  const label=document.querySelector('#header-slider [aria-label="Settings"] strong');
  if(label&&label.textContent!=='Settings')label.textContent='Settings';
 }
 function ensureGhost(){
  const map=document.querySelector('.release-map-region .map-shell>.map');
  if(!map)return null;
  let ghost=map.querySelector(':scope>.rist-pin-placement-ghost');
  if(!ghost){
   ghost=document.createElement('div');
   ghost.className='rist-pin-placement-ghost';
   ghost.setAttribute('aria-label','Pin placement cursor');
   ghost.textContent='●';
   map.appendChild(ghost);
  }
  ghost.style.left=`${pinState.x*100}%`;
  ghost.style.top=`${pinState.y*100}%`;
  return ghost;
 }
 function removeGhost(){document.querySelector('.rist-pin-placement-ghost')?.remove();}
 function setPinFromPoint(map,clientX,clientY){
  const r=map.getBoundingClientRect();
  if(r.width<1||r.height<1)return;
  pinState.x=Math.max(0,Math.min(1,(clientX-r.left)/r.width));
  pinState.y=Math.max(0,Math.min(1,(clientY-r.top)/r.height));
  ensureGhost();
 }
 function beginPinPlacement(){
  pinState.mode='placing';pinState.x=.5;pinState.y=.5;pinState.moving=false;
  ensureGhost();syncPinButton();
 }
 function cancelPinPlacement(){pinState.mode='idle';pinState.moving=false;removeGhost();syncPinButton();}
 function commitPinPlacement(){
  const map=document.querySelector('.release-map-region .map-shell>.map');
  const source=sourcePinButton();
  if(!map||!source){cancelPinPlacement();return;}
  const r=map.getBoundingClientRect();
  const clientX=r.left+r.width*pinState.x,clientY=r.top+r.height*pinState.y;
  const pointerId=9876;
  try{source.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,pointerId,clientX,clientY,pointerType:'mouse',isPrimary:true,button:0,buttons:1}));}catch{}
  setTimeout(()=>{
   try{source.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,pointerId,clientX,clientY,pointerType:'mouse',isPrimary:true,button:0,buttons:0}));}catch{}
  },40);
  pinState.mode='idle';pinState.moving=false;removeGhost();syncPinButton();
 }
 function deleteSelectedPin(){
  clickHidden('.mmo-pin-delete-action');
  pinState.mode='idle';pinState.moving=false;removeGhost();syncPinButton();
 }
 function pinMenuClick(){
  if(pinState.mode==='selected'){deleteSelectedPin();return;}
  if(pinState.mode==='placing'){commitPinPlacement();return;}
  beginPinPlacement();
 }
 function bindMapPinEvents(){
  if(mapEventsBound)return;
  mapEventsBound=true;
  document.addEventListener('click',event=>{
   const placed=event.target?.closest?.('.release-map-region .placed-pin');
   if(!placed)return;
   setTimeout(()=>{pinState.mode='selected';pinState.moving=false;removeGhost();syncPinButton();},0);
  },true);
  const mapEvent=(event,phase)=>{
   if(pinState.mode!=='placing')return;
   const map=event.target?.closest?.('.release-map-region .map-shell>.map')||document.querySelector('.release-map-region .map-shell>.map');
   if(!map||!map.contains(event.target))return;
   if(event.target?.closest?.('.placed-pin'))return;
   if(phase==='down'){pinState.moving=true;setPinFromPoint(map,event.clientX,event.clientY);}
   else if(phase==='move'&&pinState.moving)setPinFromPoint(map,event.clientX,event.clientY);
   else if(phase==='up'){setPinFromPoint(map,event.clientX,event.clientY);pinState.moving=false;}
   else return;
   event.preventDefault();event.stopPropagation();
  };
  document.addEventListener('pointerdown',e=>mapEvent(e,'down'),true);
  document.addEventListener('pointermove',e=>mapEvent(e,'move'),true);
  document.addEventListener('pointerup',e=>mapEvent(e,'up'),true);
  document.addEventListener('pointercancel',()=>{pinState.moving=false;},true);
 }
 function syncPinButton(){
  const button=document.querySelector('#header-slider .map-menu-control-pin');
  if(!button)return;
  const strong=button.querySelector('strong');
  button.classList.toggle('pin-setting',pinState.mode==='placing');
  button.classList.toggle('pin-delete',pinState.mode==='selected');
  if(strong)strong.textContent=pinState.mode==='placing'?'Set':pinState.mode==='selected'?'DEL':'Pin';
  button.setAttribute('aria-label',pinState.mode==='placing'?'Set map pin':pinState.mode==='selected'?'Delete selected map pin':'Place map pin');
 }
 function closeAxisOverlay(){document.querySelector('.rist-axis-menu-overlay')?.remove();}
 function openAxisMenu(kind){
  closeAxisOverlay();
  const source=findPrivateControl(kind);
  if(!source)return;
  source.click();
  setTimeout(()=>{
   const picker=source.closest('.z-axis-picker');
   const originals=[...(picker?.querySelectorAll('.z-axis-options>button')||[])];
   const overlay=document.createElement('div');overlay.className='rist-axis-menu-overlay';overlay.setAttribute('role','dialog');overlay.setAttribute('aria-label',`${kind} options`);
   const title=document.createElement('strong');title.textContent=kind==='tier'?'Tier':'Layer';overlay.appendChild(title);
   if(originals.length===0){const current=document.createElement('span');current.textContent=(source.textContent||'').replace(/\s+/g,' ').trim();overlay.appendChild(current);}
   for(const original of originals){const clone=document.createElement('button');clone.type='button';clone.textContent=(original.textContent||'').replace(/\s+/g,' ').trim();clone.className=original.className;clone.addEventListener('click',()=>{original.click();closeAxisOverlay();});overlay.appendChild(clone);}
   const close=document.createElement('button');close.type='button';close.textContent='×';close.className='axis-overlay-close';close.addEventListener('click',closeAxisOverlay);overlay.appendChild(close);
   document.body.appendChild(overlay);
  },60);
 }
 function ensureMenuControls(){
  const track=document.querySelector('#header-slider .release-root-track');
  if(!track)return;
  const specs=[['mmo','MMO'],['pin','Pin'],['tier','Tier'],['layer','Layer']];
  let anchor=track.firstElementChild;
  for(const [kind,label] of specs){
   let button=track.querySelector(`.map-menu-control[data-map-menu-control="${kind}"]`);
   if(!button){
    button=document.createElement('button');
    button.type='button';
    button.className=`root-menu-button map-menu-control map-menu-control-${kind}`;
    button.dataset.mapMenuControl=kind;
    button.setAttribute('aria-label',label);
    button.innerHTML=`<strong>${label}</strong>`;
    if(kind==='mmo')button.addEventListener('click',()=>{
     const mode=qs(document,'.mmo-zone-actions')?.dataset.worldMode||'mmo';
     clickHidden(mode==='mmo'?'.mmo-mode-sandbox-action':'.mmo-mode-shaelvien-action');
     setTimeout(sync,0);
    });
    else if(kind==='pin')button.addEventListener('click',pinMenuClick);
    else button.addEventListener('click',()=>openAxisMenu(kind));
   }
   if(button!==anchor)track.insertBefore(button,anchor);
   anchor=button.nextElementSibling;
  }
  syncPinButton();
 }
 function ensureControls(shell){
  let controls=qs(shell,':scope>.map-frame-controls');
  if(controls)return controls;
  controls=document.createElement('div');
  controls.className='map-frame-controls';
  controls.innerHTML=`
   <button type="button" class="map-frame-corner-add top-left" data-frame-add="nw" aria-label="Add world">+</button>
   <div class="map-frame-title" role="toolbar" aria-label="World mode, name, and role">
    <button type="button" class="map-frame-mode-toggle" aria-label="Switch to Sandbox">MMO</button>
    <span class="map-frame-world-name" aria-label="World name">Shaelvien</span>
    <span class="map-frame-role-slot" aria-hidden="true"></span>
   </div>`;
  shell.appendChild(controls);
  controls.querySelector('[data-frame-add]')?.addEventListener('click',event=>{
   event.stopPropagation();
   const direction=event.currentTarget.dataset.frameAdd||'nw';
   const open=()=>window.RistMmoBuild?.open?.(direction);
   if(window.RistMmoBuild?.open){open();return;}
   document.addEventListener('rist:mmo-build-ready',open,{once:true});
   document.dispatchEvent(new CustomEvent('rist:need-interaction'));
  });
  return controls;
 }
 function sync(){
  const shell=document.querySelector('.release-map-region .map-shell');
  const source=shell?.querySelector('.map>.status');
  const map=shell?.querySelector(':scope>.map');
  if(!shell||!source||!map)return;
  let frame=shell.querySelector(':scope>.map-frame-status');
  if(!frame){
   frame=document.createElement('div');frame.className='map-frame-status';frame.setAttribute('aria-hidden','true');
   Object.assign(frame.style,{position:'absolute',top:'0',left:'12px',right:'12px',boxSizing:'border-box',height:`${FRAME_HEIGHT}px`,minHeight:`${FRAME_HEIGHT}px`,maxHeight:`${FRAME_HEIGHT}px`,display:'block',overflow:'hidden',padding:'0',margin:'0',background:'#071015',pointerEvents:'none',zIndex:'159'});
   shell.prepend(frame);
  }
  frame.textContent='';source.style.setProperty('display','none','important');
  shell.querySelector(':scope>.map-frame-corners')?.remove();
  const controls=ensureControls(shell);
  ensureMenuControls();bindMapPinEvents();setSettingsLabel();hideMapOverlayText();
  const mode=qs(document,'.mmo-zone-actions')?.dataset.worldMode||'mmo';
  shell.dataset.worldMode=mode;
  const roleLabel=document.querySelector('#header-slider button[aria-label="Role"] strong')?.textContent||'RP';
  shell.dataset.worldRole=/^GM$/i.test(roleLabel.trim())?'gamemaster':'roleplayer';
  const worldName=qs(controls,'.map-frame-world-name');
  if(worldName)worldName.textContent=map.dataset.worldName||'Shaelvien';
  const frameMode=qs(controls,'.map-frame-mode-toggle');
  if(frameMode)frameMode.textContent=mode==='mmo'?'MMO':'Sandbox';
  const modeButton=document.querySelector('#header-slider .map-menu-control-mmo');
  if(modeButton){modeButton.querySelector('strong').textContent=mode==='mmo'?'MMO':'RIST';modeButton.dataset.mode=mode;}
  for(const kind of ['tier','layer']){
   const sourceControl=findPrivateControl(kind);if(sourceControl)sourceControl.classList.add('map-control-source-relocated');
  }
  const publicLead=document.querySelector('.release-public-region .public-assets-lead-controls');if(publicLead)publicLead.setAttribute('aria-hidden','true');
 }
 let attempts=0;const quick=setInterval(()=>{attempts++;sync();if(document.querySelector('.map-frame-controls')||attempts>=100)clearInterval(quick);},100);
 setInterval(sync,700);
 new MutationObserver(()=>requestAnimationFrame(sync)).observe(document.documentElement,{childList:true,subtree:true});
 window.addEventListener('resize',()=>requestAnimationFrame(sync));window.addEventListener('orientationchange',()=>setTimeout(sync,150));
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',sync,{once:true});else sync();
})();
