(()=>{
 'use strict';
 const FRAME_HEIGHT=12;
 const qs=(root,selector)=>root?.querySelector(selector);
 function clickHidden(selector){const el=document.querySelector(selector);if(el){el.click();return true;}return false;}
 function hideLegacyMapBadge(shell){
  [...shell.querySelectorAll('*')].forEach(el=>{
   if(el.children.length)return;
   const text=(el.textContent||'').trim();
   if(/SHAELVIEN\s+MMO.*AI\s*MAP/i.test(text)){
    const badge=el.closest('button,[role="button"],.badge,.map-badge,.world-badge,.mmo-badge')||el;
    badge.style.setProperty('display','none','important');
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
 function ensureHeaderControls(){
  const track=document.querySelector('#header-slider .release-root-track');
  if(!track)return;
  const specs=[['pin','Pin'],['tier','Tier'],['layer','Layer']];
  specs.forEach(([kind,label])=>{
   let proxy=track.querySelector(`.map-control-relocated[data-map-control="${kind}"]`);
   const source=findPrivateControl(kind);
   if(!source)return;
   if(!proxy){
    proxy=document.createElement('button');
    proxy.type='button';
    proxy.className=`root-menu-button map-control-relocated map-control-${kind}`;
    proxy.dataset.mapControl=kind;
    proxy.setAttribute('aria-label',label);
    proxy.innerHTML=kind==='pin'?'<span class="header-icon icon-pin map-pin-icon" aria-hidden="true"></span>':`<strong>${label}</strong>`;
    proxy.addEventListener('click',()=>{
     const current=findPrivateControl(kind);
     if(current)current.click();
    });
    const load=[...track.children].find(el=>/^\s*Load\s*$/i.test(el.textContent||''));
    if(load)load.after(proxy);else track.appendChild(proxy);
   }
   source.classList.add('map-control-source-relocated');
  });
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
   <div class="map-frame-meta left-meta" role="group" aria-label="World mode and name">
    <button type="button" class="map-frame-mode" aria-label="Toggle MMO and RIST mode">MMO</button>
    <label class="map-frame-world-name"><span>World</span><input type="text" maxlength="40" aria-label="World name" value="Shaelvien"></label>
   </div>`;
  shell.appendChild(controls);
  controls.querySelectorAll('[data-frame-add]').forEach(button=>button.addEventListener('click',()=>{
   shell.dispatchEvent(new CustomEvent('rist:map-frame-add',{bubbles:true,detail:{corner:button.dataset.frameAdd}}));
  }));
  qs(controls,'.map-frame-mode').addEventListener('click',()=>{
   const mode=qs(document,'.mmo-zone-actions')?.dataset.worldMode||'mmo';
   clickHidden(mode==='mmo'?'.mmo-mode-sandbox-action':'.mmo-mode-shaelvien-action');
   setTimeout(sync,0);
  });
  const nameInput=qs(controls,'.map-frame-world-name input');
  const savedName=localStorage.getItem('rist.world.frame-name');
  if(savedName)nameInput.value=savedName;
  nameInput.addEventListener('change',()=>{const value=nameInput.value.trim()||'Shaelvien';nameInput.value=value;localStorage.setItem('rist.world.frame-name',value);});
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
   Object.assign(frame.style,{position:'absolute',top:'0',left:'0',right:'0',boxSizing:'border-box',minWidth:'0',width:'100%',height:`${FRAME_HEIGHT}px`,minHeight:`${FRAME_HEIGHT}px`,maxHeight:`${FRAME_HEIGHT}px`,display:'block',overflow:'hidden',padding:'0',margin:'0',background:'#071015',pointerEvents:'none',zIndex:'159'});
   shell.prepend(frame);
  }
  frame.textContent='';
  source.style.setProperty('display','none','important');
  const staleCorners=shell.querySelector(':scope>.map-frame-corners');if(staleCorners)staleCorners.remove();
  hideLegacyMapBadge(shell);
  ensureControls(shell);
  ensureHeaderControls();
  const mode=qs(document,'.mmo-zone-actions')?.dataset.worldMode||'mmo';
  const modeButton=qs(shell,'.map-frame-mode');if(modeButton){modeButton.textContent=mode==='mmo'?'MMO':'RIST';modeButton.dataset.mode=mode;}
 }
 let attempts=0;const quick=setInterval(()=>{attempts++;sync();if(document.querySelector('.map-frame-controls')||attempts>=100)clearInterval(quick);},100);
 setInterval(sync,1200);
 new MutationObserver(()=>requestAnimationFrame(sync)).observe(document.documentElement,{childList:true,subtree:true});
 window.addEventListener('resize',()=>requestAnimationFrame(sync));
 window.addEventListener('orientationchange',()=>setTimeout(sync,150));
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',sync,{once:true});else sync();
})();
