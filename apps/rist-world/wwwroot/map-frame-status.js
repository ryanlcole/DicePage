(()=>{
 'use strict';
 const FRAME_HEIGHT=12;
 const qs=(root,selector)=>root?.querySelector(selector);
 function clickHidden(selector){const el=document.querySelector(selector);if(el){el.click();return true;}return false;}
 function hideLegacyMapBadge(shell){
  [...shell.querySelectorAll('*')].forEach(el=>{
   const text=(el.textContent||'').trim();
   if(!/SHAELVIEN\s+MMO.*AI\s*MAP/i.test(text))return;
   let node=el;
   while(node&&node!==shell){
    node.style?.setProperty('display','none','important');
    if(node.matches?.('button,[role="button"],.badge,.map-badge,.world-badge,.mmo-badge,[class*="badge"],[class*="mmo"]'))break;
    node=node.parentElement;
   }
  });
 }
 function findPrivateControl(kind){
  const root=document.querySelector('.release-private-region');
  if(!root)return null;
  const candidates=[...root.querySelectorAll('button,[role="button"]')];
  if(kind==='tier')return candidates.find(el=>/^\s*TIER\b/i.test(el.textContent||''));
  if(kind==='layer')return candidates.find(el=>/^\s*LAYER\b/i.test(el.textContent||''));
  return candidates.find(el=>/pin/i.test(`${el.getAttribute('aria-label')||''} ${el.getAttribute('title')||''}`))
   || candidates.find(el=>el.querySelector('.icon-pin,.map-pin-icon,[class*="pin"]'));
 }
 function ensureMenuControls(){
  const track=document.querySelector('#header-slider .release-root-track');
  if(!track)return;
  const specs=[['mmo','MMO'],['pin','Map Pin'],['tier','Tier'],['layer','Layer']];
  let anchor=track.firstElementChild;
  for(const [kind,label] of specs){
   let button=track.querySelector(`.map-menu-control[data-map-menu-control="${kind}"]`);
   if(!button){
    button=document.createElement('button');
    button.type='button';
    button.className=`root-menu-button map-menu-control map-menu-control-${kind}`;
    button.dataset.mapMenuControl=kind;
    button.setAttribute('aria-label',label);
    button.innerHTML=kind==='pin'?'<span class="header-icon icon-pin map-pin-icon" aria-hidden="true"></span><strong>Pin</strong>':`<strong>${label}</strong>`;
    if(kind==='mmo')button.addEventListener('click',()=>{
     const mode=qs(document,'.mmo-zone-actions')?.dataset.worldMode||'mmo';
     clickHidden(mode==='mmo'?'.mmo-mode-sandbox-action':'.mmo-mode-shaelvien-action');
     setTimeout(sync,0);
    });
    else button.addEventListener('click',()=>{const source=findPrivateControl(kind);if(source)source.click();});
   }
   if(button!==anchor)track.insertBefore(button,anchor);
   anchor=button.nextElementSibling;
  }
 }
 function ensureControls(shell){
  let controls=qs(shell,':scope>.map-frame-controls');
  if(controls)return controls;
  controls=document.createElement('div');
  controls.className='map-frame-controls';
  controls.innerHTML=`
   <button type="button" class="map-frame-corner-add top-left" data-frame-add="top-left" aria-label="Add from top left">+</button>
   <button type="button" class="map-frame-corner-add top-right" data-frame-add="top-right" aria-label="Add from top right">+</button>
   <button type="button" class="map-frame-corner-add bottom-left" data-frame-add="bottom-left" aria-label="Add from bottom left">+</button>
   <button type="button" class="map-frame-corner-add bottom-right" data-frame-add="bottom-right" aria-label="Add from bottom right">+</button>
   <label class="map-frame-title" aria-label="World name">
    <span class="map-frame-title-prefix">Shaelvien:</span>
    <input type="text" maxlength="40" aria-label="World name" value="Shaelvien">
   </label>`;
  shell.appendChild(controls);
  controls.querySelectorAll('[data-frame-add]').forEach(button=>button.addEventListener('click',()=>{
   shell.dispatchEvent(new CustomEvent('rist:map-frame-add',{bubbles:true,detail:{corner:button.dataset.frameAdd}}));
  }));
  const nameInput=qs(controls,'.map-frame-title input');
  const savedName=localStorage.getItem('rist.world.frame-name');
  if(savedName)nameInput.value=savedName;
  nameInput.addEventListener('change',()=>{
   const value=nameInput.value.trim()||'Shaelvien';
   nameInput.value=value;
   localStorage.setItem('rist.world.frame-name',value);
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
   frame=document.createElement('div');
   frame.className='map-frame-status';
   frame.setAttribute('aria-hidden','true');
   Object.assign(frame.style,{position:'absolute',top:'0',left:'12px',right:'12px',boxSizing:'border-box',height:`${FRAME_HEIGHT}px`,minHeight:`${FRAME_HEIGHT}px`,maxHeight:`${FRAME_HEIGHT}px`,display:'block',overflow:'hidden',padding:'0',margin:'0',background:'#071015',pointerEvents:'none',zIndex:'159'});
   shell.prepend(frame);
  }
  frame.textContent='';
  source.style.setProperty('display','none','important');
  const staleCorners=shell.querySelector(':scope>.map-frame-corners');if(staleCorners)staleCorners.remove();
  hideLegacyMapBadge(shell);
  const controls=ensureControls(shell);
  ensureMenuControls();
  const mode=qs(document,'.mmo-zone-actions')?.dataset.worldMode||'mmo';
  const titlePrefix=qs(controls,'.map-frame-title-prefix');
  if(titlePrefix)titlePrefix.textContent=mode==='mmo'?'Shaelvien:':'RIST:';
  const modeButton=document.querySelector('#header-slider .map-menu-control-mmo');
  if(modeButton){modeButton.querySelector('strong').textContent=mode==='mmo'?'MMO':'RIST';modeButton.dataset.mode=mode;}
  for(const kind of ['pin','tier','layer']){
   const sourceControl=findPrivateControl(kind);
   if(sourceControl)sourceControl.classList.add('map-control-source-relocated');
   const menuButton=document.querySelector(`#header-slider .map-menu-control-${kind}`);
   if(menuButton&&sourceControl&&kind!=='pin')menuButton.querySelector('strong').textContent=(sourceControl.textContent||kind).trim().replace(/\s+/g,' ');
  }
 }
 let attempts=0;const quick=setInterval(()=>{attempts++;sync();if(document.querySelector('.map-frame-controls')||attempts>=100)clearInterval(quick);},100);
 setInterval(sync,1200);
 new MutationObserver(()=>requestAnimationFrame(sync)).observe(document.documentElement,{childList:true,subtree:true});
 window.addEventListener('resize',()=>requestAnimationFrame(sync));window.addEventListener('orientationchange',()=>setTimeout(sync,150));
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',sync,{once:true});else sync();
})();
