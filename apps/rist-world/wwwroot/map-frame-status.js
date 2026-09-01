(()=>{
 'use strict';
 const FRAME_HEIGHT=12;
 const qs=(root,selector)=>root?.querySelector(selector);
 const pinState={mode:'idle',x:.5,y:.5,moving:false};
 let mapEventsBound=false;
 let menuOpen=false;
 let legacyGridMigrated=false;

 const click=(el)=>{if(!el)return false;el.click();return true;};
 const clickHidden=(selector)=>click(document.querySelector(selector));
 const headerButton=(label)=>[...document.querySelectorAll('#header-slider .root-menu-button')].find(b=>(b.querySelector('strong')?.textContent||'').trim().toLowerCase()===label.toLowerCase());
 function sourcePinButton(){return document.querySelector('.public-pin-source,.public-pin-button');}
 function findAxisControl(kind){
  const root=document.querySelector('.release-public-region');
  if(!root)return null;
  return [...root.querySelectorAll('button')].find(el=>new RegExp(`^\\s*${kind}\\b`,'i').test(el.textContent||''));
 }
 function ensureContextMenu(){
  const strip=document.querySelector('.world-context-strip');
  if(!strip)return;
  let menu=strip.querySelector(':scope>.universal-menu-button');
  if(!menu){
   menu=document.createElement('button');menu.type='button';menu.className='world-context-action universal-menu-button';menu.innerHTML='<strong>Menu</strong>';menu.setAttribute('aria-expanded','false');
   menu.addEventListener('click',()=>{menuOpen=!menuOpen;menu.setAttribute('aria-expanded',String(menuOpen));syncContextMenu();});
   strip.prepend(menu);
  }
  let group=strip.querySelector(':scope>.universal-menu-group');
  if(!group){group=document.createElement('div');group.className='universal-menu-group';menu.after(group);}
  const specs=[
   ['mmo','MMO',toggleWorldMode],['gm','GM',()=>click(headerButton((headerButton('GM')?'GM':'RP'))||headerButton('RP'))],['tier','Tier',()=>click(findAxisControl('Tier'))],['layer','Layer',()=>click(findAxisControl('Layer'))],['pin','Pin',pinMenuClick],['grid','Grid',()=>click(headerButton(currentGridLabel()))],['scale','Scale',()=>click(headerButton('Scale'))],['assets','Assets',()=>click(headerButton('Assets'))],['options','Options',()=>click(document.querySelector('#header-slider [aria-label="Settings"]'))],['about','About',()=>{location.href='info.html';}]
  ];
  for(const [key,label,handler] of specs){
   let b=group.querySelector(`[data-universal-menu="${key}"]`);
   if(!b){b=document.createElement('button');b.type='button';b.className='world-context-action universal-menu-item';b.dataset.universalMenu=key;b.innerHTML=`<strong>${label}</strong>`;b.addEventListener('click',handler);group.appendChild(b);}
  }
  let login=strip.querySelector(':scope>.universal-login');
  if(!login){login=document.createElement('button');login.type='button';login.className='world-context-action universal-login';login.addEventListener('click',()=>click(document.querySelector('#header-slider .door-button')));strip.appendChild(login);}
  const source=document.querySelector('#header-slider .door-button strong');login.innerHTML=`<strong>${source?.textContent?.trim()||'Login'}</strong>`;
  syncContextMenu();
 }
 function currentGridLabel(){const source=[...document.querySelectorAll('#header-slider .root-menu-button strong')].find(x=>/^(Square|Hex|No Grid)$/.test((x.textContent||'').trim()));return source?.textContent?.trim()||'No Grid';}
 function syncContextMenu(){
  const group=document.querySelector('.universal-menu-group');if(group)group.hidden=!menuOpen;
  const mmo=document.querySelector('[data-universal-menu="mmo"] strong');const mode=qs(document,'.mmo-zone-actions')?.dataset.worldMode||'mmo';if(mmo)mmo.textContent=mode==='mmo'?'MMO':'RIST';
  const pin=document.querySelector('[data-universal-menu="pin"]');if(pin){pin.classList.toggle('pin-setting',pinState.mode==='placing');pin.classList.toggle('pin-delete',pinState.mode==='selected');const s=pin.querySelector('strong');if(s)s.textContent=pinState.mode==='placing'?'Set':pinState.mode==='selected'?'DEL':'Pin';}
 }
 function toggleWorldMode(){const mode=qs(document,'.mmo-zone-actions')?.dataset.worldMode||'mmo';clickHidden(mode==='mmo'?'.mmo-mode-sandbox-action':'.mmo-mode-shaelvien-action');setTimeout(sync,0);}

 function hideMapOverlayText(){
  document.querySelectorAll('.release-map-region *').forEach(el=>{
   if(el.matches('.map-frame-title,.rist-coordinate-axis,.rist-coordinate-tick,.map-frame-controls,.map-frame-corner-add'))return;
   const own=[...el.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join(' ').replace(/\s+/g,' ').trim();
   const all=(el.textContent||'').replace(/\s+/g,' ').trim();
   if(/SHAELVIEN\s+MMO.*AI\s*MAP/i.test(own)||/SHAELVIEN\s+MMO.*AI\s*MAP/i.test(all)&&el.children.length<=2)el.style.setProperty('display','none','important');
   if(/Temporary Public Zone/i.test(own))el.style.setProperty('display','none','important');
  });
 }
 function setSettingsLabel(){const label=document.querySelector('#header-slider [aria-label="Settings"] strong');if(label)label.textContent='Options';}
 function ensureGhost(){const map=document.querySelector('.release-map-region .map-shell>.map');if(!map)return null;let ghost=map.querySelector(':scope>.rist-pin-placement-ghost');if(!ghost){ghost=document.createElement('div');ghost.className='rist-pin-placement-ghost';ghost.setAttribute('aria-hidden','true');ghost.textContent='●';map.appendChild(ghost);}ghost.style.left=`${pinState.x*100}%`;ghost.style.top=`${pinState.y*100}%`;return ghost;}
 function removeGhost(){document.querySelector('.rist-pin-placement-ghost')?.remove();}
 function setPinFromPoint(map,clientX,clientY){const r=map.getBoundingClientRect();if(r.width<1||r.height<1)return;pinState.x=Math.max(0,Math.min(1,(clientX-r.left)/r.width));pinState.y=Math.max(0,Math.min(1,(clientY-r.top)/r.height));ensureGhost();}
 function beginPinPlacement(){pinState.mode='placing';pinState.x=.5;pinState.y=.5;pinState.moving=false;ensureGhost();syncContextMenu();}
 function cancelPinPlacement(){pinState.mode='idle';pinState.moving=false;removeGhost();syncContextMenu();}
 function commitPinPlacement(){const map=document.querySelector('.release-map-region .map-shell>.map'),source=sourcePinButton();if(!map||!source){cancelPinPlacement();return;}const r=map.getBoundingClientRect(),clientX=r.left+r.width*pinState.x,clientY=r.top+r.height*pinState.y,pointerId=9876;try{source.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,pointerId,clientX,clientY,pointerType:'mouse',isPrimary:true,button:0,buttons:1}));}catch{}setTimeout(()=>{try{source.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,pointerId,clientX,clientY,pointerType:'mouse',isPrimary:true,button:0,buttons:0}));}catch{}},40);pinState.mode='idle';pinState.moving=false;removeGhost();syncContextMenu();}
 function deleteSelectedPin(){clickHidden('.mmo-pin-delete-action');pinState.mode='idle';pinState.moving=false;removeGhost();syncContextMenu();}
 function pinMenuClick(){if(pinState.mode==='selected'){deleteSelectedPin();return;}if(pinState.mode==='placing'){commitPinPlacement();return;}beginPinPlacement();}
 function bindMapPinEvents(){if(mapEventsBound)return;mapEventsBound=true;document.addEventListener('click',event=>{const placed=event.target?.closest?.('.release-map-region .placed-pin');if(placed)setTimeout(()=>{pinState.mode='selected';removeGhost();syncContextMenu();},0);},true);const mapEvent=(event,phase)=>{if(pinState.mode!=='placing')return;const map=document.querySelector('.release-map-region .map-shell>.map');if(!map||!map.contains(event.target)||event.target?.closest?.('.placed-pin'))return;if(phase==='down'){pinState.moving=true;setPinFromPoint(map,event.clientX,event.clientY);}else if(phase==='move'&&pinState.moving)setPinFromPoint(map,event.clientX,event.clientY);else if(phase==='up'){setPinFromPoint(map,event.clientX,event.clientY);pinState.moving=false;}else return;event.preventDefault();event.stopPropagation();};document.addEventListener('pointerdown',e=>mapEvent(e,'down'),true);document.addEventListener('pointermove',e=>mapEvent(e,'move'),true);document.addEventListener('pointerup',e=>mapEvent(e,'up'),true);document.addEventListener('pointercancel',()=>pinState.moving=false,true);}
 function ensureFrameControls(shell){let controls=qs(shell,':scope>.map-frame-controls');if(controls)return controls;controls=document.createElement('div');controls.className='map-frame-controls';controls.innerHTML='<button type="button" class="map-frame-corner-add top-left">+</button><button type="button" class="map-frame-corner-add top-right">+</button><button type="button" class="map-frame-corner-add bottom-left">+</button><button type="button" class="map-frame-corner-add bottom-right">+</button><label class="map-frame-title"><span class="map-frame-title-prefix">Shaelvien:</span><input type="text" maxlength="40" value="Shaelvien" aria-label="World name"></label>';shell.appendChild(controls);const input=qs(controls,'.map-frame-title input'),saved=localStorage.getItem('rist.world.frame-name');if(saved)input.value=saved;input.addEventListener('change',()=>{const v=input.value.trim()||'Shaelvien';input.value=v;localStorage.setItem('rist.world.frame-name',v);});return controls;}
 function ensureViewerGrid(){
  const stage=document.querySelector('.release-map-region .world-stage');if(!stage)return;
  let viewer=stage.querySelector(':scope>.viewer-square-grid');if(!viewer){viewer=document.createElement('div');viewer.className='viewer-square-grid';stage.appendChild(viewer);}
  const role=(headerButton('GM')?'GM':'PC');document.querySelector('.release-map-region .map-shell')?.setAttribute('data-viewer-role',role);
  const movement=stage.querySelector(':scope>.grid');if(movement)movement.classList.add('movement-grid');
  if(!legacyGridMigrated&&currentGridLabel()==='Square'){
   legacyGridMigrated=true;const gridRoot=headerButton('Square');if(gridRoot){gridRoot.click();setTimeout(()=>{const panel=[...document.querySelectorAll('#header-slider .root-menu-panel button')].find(b=>/None/i.test(b.textContent||''));if(panel)panel.click();},0);}
  }
  document.querySelectorAll('#header-slider .root-menu-panel button').forEach(b=>{if(/^\s*Square\s*$/i.test(b.textContent||''))b.style.setProperty('display','none','important');});
 }
 function openCharacterSheet(){const load=headerButton('Load');if(!load)return;load.click();setTimeout(()=>{const b=[...document.querySelectorAll('#header-slider .load-menu button')].find(x=>/Characters/i.test(x.textContent||''));if(b)b.click();},0);}
 function ensureAssetDecks(){
  for(const region of document.querySelectorAll('.release-public-region,.release-private-region')){
   region.classList.add('character-deck-region');let deck=region.querySelector(':scope>.character-sheet-deck');if(!deck){deck=document.createElement('button');deck.type='button';deck.className='character-sheet-deck';deck.setAttribute('aria-label','Open character sheet');deck.innerHTML='<span class="deck-face">Character</span>';deck.addEventListener('click',openCharacterSheet);region.appendChild(deck);}
  }
 }
 function installCircularScroll(){
  if(!window.ristWorld||window.ristWorld.__wrapInstalled)return;window.ristWorld.__wrapInstalled=true;
  window.ristWorld.scrollRail=(selector,direction)=>{const rail=document.querySelector(selector);if(!rail)return;const dir=Number(direction)<0?-1:1;const vertical=rail.classList.contains('tile-browser-slider')||(rail.classList.contains('desktop-arrow-adaptive')&&matchMedia('(orientation: landscape)').matches);const target=[...rail.children].find(el=>el.classList&&!el.classList.contains('rail-scroll-arrow')&&(vertical?el.scrollHeight>el.clientHeight+2:el.scrollWidth>el.clientWidth+2))||rail;const max=vertical?target.scrollHeight-target.clientHeight:target.scrollWidth-target.clientWidth;const pos=vertical?target.scrollTop:target.scrollLeft;if(max<=1)return;if(dir>0&&pos>=max-4){target.scrollTo(vertical?{top:0,behavior:'smooth'}:{left:0,behavior:'smooth'});return;}if(dir<0&&pos<=4){target.scrollTo(vertical?{top:max,behavior:'smooth'}:{left:max,behavior:'smooth'});return;}const amount=Math.max(96,(vertical?target.clientHeight:target.clientWidth)*.78)*dir;target.scrollBy(vertical?{top:amount,behavior:'smooth'}:{left:amount,behavior:'smooth'});};
 }
 function sync(){
  const shell=document.querySelector('.release-map-region .map-shell'),source=shell?.querySelector('.map>.status'),map=shell?.querySelector(':scope>.map');if(!shell||!source||!map)return;
  source.style.setProperty('display','none','important');shell.querySelector(':scope>.map-frame-status')?.remove();shell.querySelector(':scope>.map-frame-corners')?.remove();
  const controls=ensureFrameControls(shell),mode=qs(document,'.mmo-zone-actions')?.dataset.worldMode||'mmo';shell.dataset.worldMode=mode;const prefix=qs(controls,'.map-frame-title-prefix');if(prefix)prefix.textContent=mode==='mmo'?'Shaelvien:':'RIST:';
  ensureContextMenu();bindMapPinEvents();ensureViewerGrid();ensureAssetDecks();installCircularScroll();setSettingsLabel();hideMapOverlayText();syncContextMenu();
 }
 let attempts=0;const quick=setInterval(()=>{attempts++;sync();if(document.querySelector('.map-frame-controls')||attempts>=100)clearInterval(quick);},100);setInterval(sync,900);new MutationObserver(()=>requestAnimationFrame(sync)).observe(document.documentElement,{childList:true,subtree:true});window.addEventListener('resize',()=>requestAnimationFrame(sync));window.addEventListener('orientationchange',()=>setTimeout(sync,150));if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',sync,{once:true});else sync();
})();