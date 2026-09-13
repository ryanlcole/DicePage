(()=>{
 'use strict';

 let syncQueued=false;
 const q=(selector,root=document)=>root?.querySelector(selector);
 const qa=(selector,root=document)=>[...(root?.querySelectorAll(selector)||[])];
 const asNumber=value=>Number.isFinite(Number(value))?Number(value):0;

 function currentNavigation(){
  const state=window.ristViewerNavigation?.get?.();
  if(state)return {x:asNumber(state.x),y:asNumber(state.y)};
  return {x:asNumber(localStorage.getItem('rist.world.viewX')),y:asNumber(localStorage.getItem('rist.world.viewY'))};
 }
 function currentZ(){
  const layerButton=qa('.worldbuilder-studio .studio-command-rail button').find(button=>/^Layers$/i.test((q('strong',button)?.textContent||'').trim()));
  const text=`${q('small',layerButton)?.textContent||''} ${q('.worldbuilder-studio .studio-mini-panel[aria-label="Layer controls"] span')?.textContent||''}`;
  const match=text.match(/\bZ\s*(-?\d+(?:\.\d+)?)/i);
  return match?asNumber(match[1]):0;
 }
 function updateCoordinateReadouts(){
  const nav=q('.worldbuilder-studio .studio-coordinate-nav');
  if(!nav)return;
  const {x,y}=currentNavigation();
  const z=currentZ();
  const coordinates=q('[data-studio-coordinates]',nav);
  const height=q('[data-studio-height]',nav);
  const coordinateText=`${x},${y},${z}`;
  const heightText=`H ${z} / SL 0`;
  if(coordinates&&coordinates.textContent!==coordinateText)coordinates.textContent=coordinateText;
  if(height&&height.textContent!==heightText)height.textContent=heightText;
 }
 function moveAxis(axis,step){
  const authority=window.ristViewerNavigation;
  if(!authority)return;
  const state=authority.get?.();
  if(!state)return;
  if(typeof authority.setPosition==='function'){
   const x=asNumber(state.x)+(axis==='x'?step:0);
   const y=asNumber(state.y)+(axis==='y'?step:0);
   authority.setPosition(x,y,true);
  }else authority.nudge?.(axis,step);
  requestAnimationFrame(updateCoordinateReadouts);
 }
 function moveZ(step){
  const view=q('.worldbuilder-studio .studio-viewer-canvas');
  if(!view)return;
  view.dispatchEvent(new WheelEvent('wheel',{deltaY:step>0?340:-340,bubbles:true,cancelable:true}));
  setTimeout(updateCoordinateReadouts,160);
 }
 function axisGroup(axis,before,after,beforeLabel,afterLabel){
  const group=document.createElement('span');group.className='studio-axis-stepper';group.dataset.axis=axis;
  const first=document.createElement('button');first.type='button';first.textContent=before;first.setAttribute('aria-label',beforeLabel);
  const label=document.createElement('strong');label.textContent=axis;
  const second=document.createElement('button');second.type='button';second.textContent=after;second.setAttribute('aria-label',afterLabel);
  if(axis==='X'){
   first.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();moveAxis('x',-1)});
   second.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();moveAxis('x',1)});
  }else if(axis==='Y'){
   first.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();moveAxis('y',-1)});
   second.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();moveAxis('y',1)});
  }else{
   first.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();moveZ(1)});
   second.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();moveZ(-1)});
  }
  group.append(first,label,second);return group;
 }
 function pipe(){const span=document.createElement('span');span.className='studio-coordinate-pipe';span.textContent='|';span.setAttribute('aria-hidden','true');return span;}
 function ensureCoordinateNavigation(){
  const context=q('.worldbuilder-studio .studio-context-strip');
  if(!context)return;
  let nav=q(':scope>.studio-coordinate-nav',context);
  if(!nav){
   nav=document.createElement('div');nav.className='studio-coordinate-nav';nav.setAttribute('role','toolbar');nav.setAttribute('aria-label','World coordinates and axes');
   const coordinates=document.createElement('output');coordinates.className='studio-coordinate-readout';coordinates.dataset.studioCoordinates='1';coordinates.setAttribute('aria-label','Current X Y Z coordinates');
   const height=document.createElement('output');height.className='studio-height-readout';height.dataset.studioHeight='1';height.setAttribute('aria-label','Current height versus sea level');
   nav.append(
    coordinates,pipe(),
    axisGroup('X','←','→','Move left on X','Move right on X'),pipe(),
    axisGroup('Y','↑','↓','Move up on Y','Move down on Y'),pipe(),
    axisGroup('z','↑','↓','Move up on z','Move down on z'),pipe(),
    height
   );
   context.appendChild(nav);
  }
  updateCoordinateReadouts();
 }

 const labelVerticalControls=()=>{
  const layer=q('.worldbuilder-studio .studio-mini-panel[aria-label="Layer controls"]');
  if(layer){
   const buttons=layer.querySelectorAll('button');
   if(buttons[0]&&buttons[0].textContent!=='Layer ↓'){buttons[0].textContent='Layer ↓';buttons[0].setAttribute('aria-label','Move down one layer');}
   if(buttons[1]&&buttons[1].textContent!=='Layer ↑'){buttons[1].textContent='Layer ↑';buttons[1].setAttribute('aria-label','Move up one layer');}
  }
  const tier=q('.worldbuilder-studio .studio-mini-panel[aria-label="Tier controls"]');
  if(tier){
   const buttons=tier.querySelectorAll('button');
   if(buttons[0]&&buttons[0].textContent!=='Tier ↓'){buttons[0].textContent='Tier ↓';buttons[0].setAttribute('aria-label','Move down one tier');}
   if(buttons[1]&&buttons[1].textContent!=='Tier ↑'){buttons[1].textContent='Tier ↑';buttons[1].setAttribute('aria-label','Move up one tier');}
  }
 };

 const style=document.createElement('style');
 style.id='rist-start-menu-display-authority';
 style.textContent=`
  .worldbuilder-studio .studio-context-strip{overflow:hidden!important}
  .worldbuilder-studio .studio-context-strip>.studio-ticker{display:none!important}
  .worldbuilder-studio .studio-coordinate-nav{box-sizing:border-box;width:100%;height:20px;display:grid;grid-template-columns:auto auto auto auto auto auto auto auto auto;align-items:center;justify-content:space-evenly;gap:1px;padding:0 2px;overflow:hidden;white-space:nowrap;color:#d8c589;font:800 8px/18px system-ui,-apple-system,sans-serif;letter-spacing:.01em}
  .worldbuilder-studio .studio-coordinate-readout,.worldbuilder-studio .studio-height-readout{display:block;min-width:0;margin:0;padding:0 2px;overflow:hidden;text-overflow:clip;color:#d8c589;font:800 7px/18px ui-monospace,SFMono-Regular,Menlo,monospace;white-space:nowrap}
  .worldbuilder-studio .studio-axis-stepper{display:grid;grid-template-columns:18px 10px 18px;align-items:center;justify-items:center;gap:0;height:20px;min-width:46px}
  .worldbuilder-studio .studio-axis-stepper>strong{color:#f0d590;font:900 8px/18px system-ui,-apple-system,sans-serif;text-align:center}
  .worldbuilder-studio .studio-context-strip .studio-axis-stepper>button{box-sizing:border-box!important;width:18px!important;min-width:18px!important;max-width:18px!important;height:18px!important;min-height:18px!important;max-height:18px!important;margin:0!important;padding:0!important;border:0!important;border-radius:3px!important;background:transparent!important;color:#e4c97d!important;font:900 12px/18px system-ui,-apple-system,sans-serif!important;line-height:18px!important;text-align:center!important;touch-action:manipulation!important}
  .worldbuilder-studio .studio-context-strip .studio-axis-stepper>button:active{background:#26313a!important;color:#fff0b7!important}
  .worldbuilder-studio .studio-coordinate-pipe{color:#715b2d;font:700 9px/18px system-ui;opacity:.9}
  .worldbuilder-studio .studio-viewer-canvas .map>.status,.worldbuilder-studio .studio-viewer-canvas .map-frame-status{display:none!important;visibility:hidden!important}
  @media(max-width:430px){
   .worldbuilder-studio .studio-coordinate-nav{padding:0 1px;font-size:7px}
   .worldbuilder-studio .studio-coordinate-readout,.worldbuilder-studio .studio-height-readout{font-size:6px;padding:0 1px}
   .worldbuilder-studio .studio-axis-stepper{grid-template-columns:17px 8px 17px;min-width:42px}
   .worldbuilder-studio .studio-context-strip .studio-axis-stepper>button{width:17px!important;min-width:17px!important;max-width:17px!important}
  }
 `;
 document.getElementById(style.id)?.remove();
 document.head.appendChild(style);

 window.ristFullscreen={
  state(){
   const supported=!!(document.fullscreenEnabled||document.webkitFullscreenEnabled||document.documentElement.requestFullscreen||document.documentElement.webkitRequestFullscreen);
   const active=!!(document.fullscreenElement||document.webkitFullscreenElement);
   return [active,supported];
  },
  async toggle(){
   const active=document.fullscreenElement||document.webkitFullscreenElement;
   const root=document.documentElement;
   try{
    if(active){
     if(document.exitFullscreen)await document.exitFullscreen();
     else if(document.webkitExitFullscreen)document.webkitExitFullscreen();
    }else{
     if(root.requestFullscreen)await root.requestFullscreen({navigationUI:'hide'}).catch(()=>root.requestFullscreen());
     else if(root.webkitRequestFullscreen)root.webkitRequestFullscreen();
    }
   }catch{}
   return this.state();
  }
 };

 function sync(){ensureCoordinateNavigation();labelVerticalControls();updateCoordinateReadouts();}
 function queueSync(){if(syncQueued)return;syncQueued=true;requestAnimationFrame(()=>{syncQueued=false;sync()})}
 sync();
 new MutationObserver(queueSync).observe(document.body,{childList:true,subtree:true});
 window.addEventListener('rist:viewer-pan',queueSync);
 window.addEventListener('pageshow',queueSync);
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)queueSync()});
 setInterval(updateCoordinateReadouts,500);
})();
