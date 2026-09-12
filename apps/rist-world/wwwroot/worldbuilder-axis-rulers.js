export function attachAxisRulers(element){
 const studio=element?.closest?.('.worldbuilder-studio');
 if(!studio||!element)return{dispose(){}};

 // Rulers were doing two jobs at once: displaying coordinates and acting as
 // draggable navigation surfaces. That made mobile movement noisy and created a
 // feedback loop between pan updates, ruler style updates and mutation observers.
 // Keep navigation discrete and explicit instead: one compact legend, one cell /
 // layer / tier per arrow press.
 const style=document.createElement('style');
 style.id='rist-worldbuilder-coordinate-legend';
 style.textContent=`
  .worldbuilder-studio .wb-axis-ruler,
  .worldbuilder-studio .wb-z-ruler,
  .worldbuilder-studio .wb-x-ruler,
  .worldbuilder-studio .wb-y-ruler,
  .worldbuilder-studio .rist-coordinate-frame{display:none!important;visibility:hidden!important;pointer-events:none!important}
  .worldbuilder-studio .studio-viewer-canvas{--viewer-frame:2px!important}
  .worldbuilder-studio .studio-viewer-canvas .world-stage{transition:none!important}
  .worldbuilder-studio .wb-coordinate-legend{position:absolute;z-index:2147480;left:8px;top:8px;width:132px;display:grid;gap:3px;padding:5px;border:1px solid rgba(183,151,76,.78);border-radius:8px;background:rgba(5,13,18,.86);box-shadow:0 4px 14px rgba(0,0,0,.4);backdrop-filter:blur(3px);-webkit-backdrop-filter:blur(3px);pointer-events:auto;touch-action:manipulation;user-select:none}
  .worldbuilder-studio .wb-coordinate-row{height:30px;display:grid;grid-template-columns:30px minmax(0,1fr) 30px;align-items:center;gap:3px}
  .worldbuilder-studio .wb-coordinate-row button{box-sizing:border-box;width:30px;height:30px;padding:0;border:1px solid #536873;border-radius:6px;background:#0d1820;color:#f1d98e;font:900 16px/1 system-ui;touch-action:manipulation}
  .worldbuilder-studio .wb-coordinate-row button:disabled{opacity:.32}
  .worldbuilder-studio .wb-coordinate-value{min-width:0;display:grid;grid-template-columns:auto 1fr;align-items:center;gap:5px;color:#dce4e7;font:800 10px/1 system-ui;white-space:nowrap}
  .worldbuilder-studio .wb-coordinate-value small{color:#88a9bc;font:900 7px/1 system-ui;letter-spacing:.06em}
  .worldbuilder-studio .wb-coordinate-value strong{overflow:hidden;text-overflow:ellipsis;text-align:right;color:#f0ddb0;font:900 11px/1 system-ui}
  @media(max-width:760px){.worldbuilder-studio .wb-coordinate-legend{left:6px;top:6px;width:124px;padding:4px}.worldbuilder-studio .wb-coordinate-row{height:28px;grid-template-columns:28px minmax(0,1fr) 28px}.worldbuilder-studio .wb-coordinate-row button{width:28px;height:28px}}
 `;
 document.getElementById(style.id)?.remove();
 document.head.appendChild(style);

 const legend=document.createElement('nav');
 legend.className='wb-coordinate-legend';
 legend.setAttribute('aria-label','World coordinates');
 element.appendChild(legend);

 const rows={};
 const makeRow=(key,label)=>{
  const row=document.createElement('div');
  row.className='wb-coordinate-row';
  const down=document.createElement('button');
  down.type='button';down.textContent='‹';down.setAttribute('aria-label',`${label} decrement`);
  const value=document.createElement('span');value.className='wb-coordinate-value';
  const name=document.createElement('small');name.textContent=label;
  const current=document.createElement('strong');current.textContent='0';
  value.append(name,current);
  const up=document.createElement('button');
  up.type='button';up.textContent='›';up.setAttribute('aria-label',`${label} increment`);
  row.append(down,value,up);legend.appendChild(row);
  rows[key]={row,down,up,current};
 };
 makeRow('x','X');makeRow('y','Y');makeRow('layer','Z-LAYER');makeRow('tier','Z-TIER');

 const command=name=>[...(studio.querySelectorAll('.studio-command-rail button')||[])].find(button=>(button.querySelector('strong')?.textContent||'').trim()===name);
 const locked=()=>localStorage.getItem('rist.world.viewerLocked')!=='false';
 const nextFrame=()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));

 const readDepth=()=>{
  const layerText=command('Layers')?.querySelector('small')?.textContent||'';
  const tierText=command('Tiers')?.querySelector('small')?.textContent||'';
  const layerMatch=layerText.match(/Layer\s+(-?\d+)/i);
  const tierMatch=tierText.match(/Tier\s+(-?\d+)/i);
  return{layer:layerMatch?Number(layerMatch[1]):0,tier:tierMatch?Number(tierMatch[1]):0};
 };

 const render=()=>{
  const navigation=window.ristViewerNavigation?.get?.()||{x:0,y:0};
  const depth=readDepth();
  rows.x.current.textContent=String(Math.round(Number(navigation.x)||0));
  rows.y.current.textContent=String(Math.round(Number(navigation.y)||0));
  rows.layer.current.textContent=String(depth.layer);
  rows.tier.current.textContent=String(depth.tier);
  const isLocked=locked();
  for(const row of Object.values(rows)){row.down.disabled=isLocked;row.up.disabled=isLocked;}
  legend.title=isLocked?'Unlock the map + viewer to move coordinates':'Each arrow moves exactly one increment';
 };

 const nudge=(axis,delta)=>{
  if(locked())return;
  window.ristViewerNavigation?.nudge?.(axis,delta);
  render();
 };

 const stepDepth=async(kind,delta)=>{
  if(locked())return;
  const triggerName=kind==='layer'?'Layers':'Tiers';
  const panelLabel=kind==='layer'?'Layer controls':'Tier controls';
  const actionText=`${kind==='layer'?'Layer':'Tier'} ${delta<0?'Down':'Up'}`;
  let panel=studio.querySelector(`.studio-mini-panel[aria-label="${panelLabel}"]`);
  const wasOpen=!!panel;
  if(!panel){
   command(triggerName)?.click();
   await nextFrame();
   panel=studio.querySelector(`.studio-mini-panel[aria-label="${panelLabel}"]`);
  }
  const action=panel?[...panel.querySelectorAll('button')].find(button=>(button.textContent||'').trim()===actionText):null;
  if(action&&!action.disabled)action.click();
  await nextFrame();
  if(!wasOpen)command(triggerName)?.click();
  await nextFrame();
  render();
 };

 rows.x.down.onclick=()=>nudge('x',-1);rows.x.up.onclick=()=>nudge('x',1);
 rows.y.down.onclick=()=>nudge('y',-1);rows.y.up.onclick=()=>nudge('y',1);
 rows.layer.down.onclick=()=>void stepDepth('layer',-1);rows.layer.up.onclick=()=>void stepDepth('layer',1);
 rows.tier.down.onclick=()=>void stepDepth('tier',-1);rows.tier.up.onclick=()=>void stepDepth('tier',1);

 // Do not let legend taps become map-pan gestures.
 legend.addEventListener('pointerdown',event=>event.stopPropagation(),true);
 legend.addEventListener('pointermove',event=>event.stopPropagation(),true);
 legend.addEventListener('wheel',event=>{event.preventDefault();event.stopPropagation();},{passive:false,capture:true});

 // Blank-canvas drag/pinch/wheel navigation is intentionally disabled here. Tile
 // manipulation remains untouched. Coordinates now move only through the explicit
 // one-step controls, eliminating the previous pan/ruler jitter path.
 const stopGesture=event=>{
  if(event.target?.closest?.('.wb-coordinate-legend,.world-stage .tile-cell,.studio-mini-panel,.studio-load-panel,.studio-command-slider,.studio-top-slider'))return;
  event.preventDefault();event.stopPropagation();event.stopImmediatePropagation();
 };
 element.addEventListener('pointerdown',stopGesture,{capture:true,passive:false});
 element.addEventListener('wheel',stopGesture,{capture:true,passive:false});

 const rail=studio.querySelector('.studio-command-slider');
 let scheduled=false;
 const schedule=()=>{if(scheduled)return;scheduled=true;requestAnimationFrame(()=>{scheduled=false;render();});};
 const observer=new MutationObserver(schedule);
 if(rail)observer.observe(rail,{childList:true,subtree:true,characterData:true});
 window.addEventListener('rist:viewer-pan',render);
 window.addEventListener('storage',render);
 render();

 return{dispose(){observer.disconnect();window.removeEventListener('rist:viewer-pan',render);window.removeEventListener('storage',render);element.removeEventListener('pointerdown',stopGesture,true);element.removeEventListener('wheel',stopGesture,true);legend.remove();style.remove();}};
}
