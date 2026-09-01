(()=>{
 'use strict';
 const FRAME_HEIGHT=12;
 const qs=(root,selector)=>root?.querySelector(selector);
 function clickHidden(selector){const el=document.querySelector(selector);if(el){el.click();return true;}return false;}
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
    <button type="button" class="map-frame-mode" aria-label="Toggle MMO and Sandbox mode">MMO</button>
    <label class="map-frame-world-name"><span>World</span><input type="text" maxlength="40" aria-label="World name" value="Shaelvien"></label>
   </div>
   <div class="map-frame-meta right-meta" role="group" aria-label="Plane tier and layer navigation">
    <span class="frame-axis"><b>Plane</b><button type="button" data-axis="plane" data-delta="-1">−</button><output data-axis-value="plane">0</output><button type="button" data-axis="plane" data-delta="1">+</button></span>
    <span class="frame-axis"><b>Tier</b><button type="button" data-axis="tier" data-delta="-1">−</button><output data-axis-value="tier">0</output><button type="button" data-axis="tier" data-delta="1">+</button></span>
    <label class="frame-layer"><b>Layer</b><select aria-label="Layer"></select></label>
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
  controls.querySelectorAll('.frame-axis button').forEach(button=>button.addEventListener('click',()=>{
   const axis=button.dataset.axis,delta=Number(button.dataset.delta)||0;
   const label=axis==='plane'?(delta<0?'Plane−':'Plane+'):(delta<0?'Tier−':'Tier+');
   const candidates=[...document.querySelectorAll('.locked-tile-menu button')];
   const target=candidates.find(x=>x.textContent.trim()===label);
   if(target)target.click();
  }));
  const layer=qs(controls,'.frame-layer select');
  layer.addEventListener('change',()=>{
   const target=document.querySelector(`.recursion-layer-button[data-tier="${CSS.escape(layer.value)}"]`);
   if(target)target.click();
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
   Object.assign(frame.style,{position:'absolute',top:'0',left:'0',right:'0',boxSizing:'border-box',minWidth:'0',width:'100%',height:`${FRAME_HEIGHT}px`,minHeight:`${FRAME_HEIGHT}px`,maxHeight:`${FRAME_HEIGHT}px`,display:'flex',alignItems:'center',justifyContent:'center',overflow:'hidden',whiteSpace:'nowrap',textOverflow:'ellipsis',paddingTop:'0',paddingBottom:'0',margin:'0',background:'#071015',color:'#d7be80',font:'800 8px/1 system-ui,-apple-system,sans-serif',letterSpacing:'.04em',pointerEvents:'none',zIndex:'159'});
   shell.prepend(frame);
  }
  frame.style.height=`${FRAME_HEIGHT}px`;frame.style.minHeight=`${FRAME_HEIGHT}px`;frame.style.maxHeight=`${FRAME_HEIGHT}px`;frame.style.paddingTop='0';frame.style.paddingBottom='0';frame.style.font='800 8px/1 system-ui,-apple-system,sans-serif';
  if(frame.textContent!==source.textContent)frame.textContent=source.textContent;
  source.style.setProperty('display','none','important');
  const staleCorners=shell.querySelector(':scope>.map-frame-corners');if(staleCorners)staleCorners.remove();
  const shellRect=shell.getBoundingClientRect(),mapRect=map.getBoundingClientRect();
  const leftFrameWidth=Math.max(0,Math.round(mapRect.left-shellRect.left)),rightFrameWidth=Math.max(0,Math.round(shellRect.right-mapRect.right));
  frame.style.paddingLeft=`${leftFrameWidth}px`;frame.style.paddingRight=`${rightFrameWidth}px`;

  const controls=ensureControls(shell);
  const mode=qs(document,'.mmo-zone-actions')?.dataset.worldMode||'mmo';
  const modeButton=qs(controls,'.map-frame-mode');if(modeButton)modeButton.textContent=mode==='mmo'?'MMO':'RIST';
  const coordinateText=source.textContent||'';
  const plane=coordinateText.match(/Plane\s*(-?\d+)/i)?.[1]??'0';
  const tier=coordinateText.match(/Tier\s*(-?\d+)/i)?.[1]??'0';
  const planeOut=qs(controls,'[data-axis-value="plane"]'),tierOut=qs(controls,'[data-axis-value="tier"]');if(planeOut)planeOut.textContent=plane;if(tierOut)tierOut.textContent=tier;
  const layerSelect=qs(controls,'.frame-layer select');
  if(layerSelect){
   const buttons=[...document.querySelectorAll('.recursion-layer-button[data-tier]')];
   const current=document.querySelector('.recursion-layer-button.active[data-tier]')?.dataset.tier||buttons[0]?.dataset.tier||'WORLD';
   const values=buttons.map(x=>x.dataset.tier).filter(Boolean);
   if(values.join('|')!==layerSelect.dataset.values){layerSelect.replaceChildren(...values.map(value=>{const option=document.createElement('option');option.value=value;option.textContent=value;return option;}));layerSelect.dataset.values=values.join('|');}
   layerSelect.value=current;
  }
 }
 let attempts=0;const quick=setInterval(()=>{attempts++;sync();if(document.querySelector('.map-frame-status')||attempts>=100)clearInterval(quick);},100);
 setInterval(sync,1500);window.addEventListener('resize',()=>requestAnimationFrame(sync));window.addEventListener('orientationchange',()=>setTimeout(sync,150));
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',sync,{once:true});else sync();
})();
