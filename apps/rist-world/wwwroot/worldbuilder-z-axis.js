import * as core from './worldbuilder-z-axis-core.js';
import './worldbuilder-controls.js';
import './worldbuilder-controls-state.js';

export const viewerPoint=core.viewerPoint;
export const viewerGridPoint=core.viewerGridPoint;
export const beginQuickPointerDrop=core.beginQuickPointerDrop;

export function attach(element,dotnet){
 if(!element)return core.attach(element,dotnet);
 const studio=element.closest('.worldbuilder-studio');
 let active=null;
 let disposed=false;
 let viewerLocked=true;
 let depthState={sceneZ:0,tierIndex:0,layerOffset:0,viewerLocked:true};
 let uiObserver=null;
 let autoSaveTimer=null;

 const style=document.createElement('style');
 style.id='rist-worldbuilder-mahjong-picking';
 style.textContent=`
  @import url('./css/worldbuilder-control-rework.css?v=20260910-controls-1');
  .worldbuilder-studio .world-stage .tile-cell,
  .worldbuilder-studio .world-stage .tile-cell *{-webkit-touch-callout:none!important;-webkit-user-select:none!important;user-select:none!important;-webkit-user-drag:none!important;touch-action:none!important}
  .worldbuilder-studio .world-stage .tile-cell.wb-selected{outline:3px solid #f2cf72!important;outline-offset:-3px!important;box-shadow:inset 0 0 0 2px rgba(12,30,40,.85)!important;z-index:214748!important}
  .worldbuilder-studio .studio-command-rail [data-wb-hidden="true"]{display:none!important}
 `;
 document.head.appendChild(style);

 const stage=()=>studio?.querySelector('.world-stage');
 const tiles=()=>studio?[...studio.querySelectorAll('.world-stage .tile-cell')]:[];
 const rail=()=>studio?.querySelector('.studio-command-rail');
 const buttonByText=text=>[...(rail()?.querySelectorAll('button')||[])].find(b=>(b.querySelector('strong')?.textContent||'').trim()===text);
 const isBlocked=target=>!!target?.closest?.('.studio-mini-panel,.studio-load-panel,.studio-library-shade,.recursion-cockpit,.desktop-map-zoom,.locked-tile-menu,.recursive-region-actions,.wb-modal,.wb-z-ruler');

 const tileAtPoint=(x,y)=>{
  const list=tiles();
  for(let i=list.length-1;i>=0;i--){const r=list[i].getBoundingClientRect();if(x>=r.left&&x<=r.right&&y>=r.top&&y<=r.bottom)return list[i];}
  return null;
 };
 const worldPoint=(x,y)=>{
  const s=stage();if(!s)return null;
  const r=s.getBoundingClientRect();if(r.width<1||r.height<1)return null;
  const px=(x-r.left)/r.width,py=(y-r.top)/r.height;
  if(px<0||px>1||py<0||py>1)return null;
  return [px,py];
 };
 const syncButtons=selected=>{
  const set=new Set((selected||[]).map(Number));
  tiles().forEach((tile,index)=>tile.classList.toggle('wb-selected',set.has(index)));
  for(const name of ['rotate','remove']){const button=studio?.querySelector(`[data-wb-command="${name}"]`);if(button)button.disabled=set.size<1;}
  const remove=studio?.querySelector('[data-wb-command="remove"] small');if(remove)remove.textContent=`${set.size} Selected`;
  return [...set];
 };
 const pick=async(x,y,additive)=>{
  const p=worldPoint(x,y);if(!p)return [];
  try{return syncButtons(await dotnet.invokeMethodAsync('SelectPlacedTileAtWorldPoint',p[0],p[1],!!additive)||[]);}catch{return [];}
 };

 const clearModal=()=>studio?.querySelectorAll('.wb-modal').forEach(x=>x.remove());
 const modal=(title,bodyBuilder)=>{
  clearModal();
  const host=document.createElement('section');host.className='wb-modal';host.setAttribute('role','dialog');host.setAttribute('aria-modal','true');
  const header=document.createElement('header');const strong=document.createElement('strong');strong.textContent=title;const close=document.createElement('button');close.type='button';close.textContent='×';close.onclick=()=>host.remove();header.append(strong,close);host.appendChild(header);
  bodyBuilder(host,()=>host.remove());
  element.appendChild(host);return host;
 };
 const actionButton=(label,onClick,cls='')=>{const b=document.createElement('button');b.type='button';b.textContent=label;if(cls)b.className=cls;b.addEventListener('click',onClick);return b;};

 const openCustomTileSize=async()=>{
  let value=1;try{value=Number(await dotnet.invokeMethodAsync('GetTileSizeKmAtOriginFromJs'))||1;}catch{}
  modal('Tile Size at (0,0)',(host,close)=>{
   const label=document.createElement('label');label.textContent='Kilometers per tile';
   const input=document.createElement('input');input.type='number';input.min='0.001';input.max='1000000';input.step='any';input.value=String(value);label.appendChild(input);host.appendChild(label);
   const small=document.createElement('small');small.textContent='This is world math only. Travel-distance rules remain a game-system decision.';host.appendChild(small);
   host.appendChild(actionButton('Apply',async()=>{const km=Number(input.value);if(Number.isFinite(km)&&km>0){try{await dotnet.invokeMethodAsync('SetTileSizeKmAtOriginFromJs',km);localStorage.setItem('rist.world.tileSizeKmAtOrigin',String(km));}catch{}close();syncUi();}}));
   host.appendChild(actionButton('Cancel',close));
  });
 };

 const openSaveMenu=()=>{
  modal('Save',(host,close)=>{
   const row=document.createElement('label');const cb=document.createElement('input');cb.type='checkbox';cb.checked=localStorage.getItem('rist.world.autosave')!=='false';row.append(cb,document.createTextNode('Autosave'));host.appendChild(row);
   cb.addEventListener('change',()=>{localStorage.setItem('rist.world.autosave',String(cb.checked));dotnet.invokeMethodAsync('SetAutoSaveFromJs',cb.checked).catch(()=>{});});
   host.appendChild(actionButton('Save',async()=>{try{await dotnet.invokeMethodAsync('SaveWorldFromJs');}catch{}close();}));
   host.appendChild(actionButton('Export',async()=>{try{await dotnet.invokeMethodAsync('SaveWorldFromJs');}catch{}window.ristWorld?.exportCurrentWorld?.();close();}));
   host.appendChild(actionButton('Cancel',close));
  });
 };
 const openLoadMenu=()=>{
  modal('Load',(host,close)=>{
   host.appendChild(actionButton('Load',async()=>{try{await dotnet.invokeMethodAsync('LoadWorldFromJs');}catch{}close();}));
   host.appendChild(actionButton('Import',()=>{window.ristWorld?.importCurrentWorld?.();close();}));
   host.appendChild(actionButton('Cancel',close));
  });
 };
 const publishState=()=>window.ristWorld?.readPublishState?.()||{published:false,owner:'self',active:['self'],saved:[]};
 const writePublish=state=>window.ristWorld?.writePublishState?.(state);
 const openPublishMenu=()=>{
  modal('Publish',(host,close)=>{
   host.appendChild(actionButton('Publish',async()=>{
    const state=publishState();state.published=true;state.active=[state.owner,...(state.saved||[]).filter(x=>x!==state.owner)];writePublish(state);try{await dotnet.invokeMethodAsync('SetPublishModeFromJs',true);}catch{}close();
   }));
   host.appendChild(actionButton('Unpublish',async()=>{
    const state=publishState();state.published=false;state.saved=[...(state.active||[])].filter(x=>x!==state.owner);state.active=[state.owner];writePublish(state);try{await dotnet.invokeMethodAsync('SetPublishModeFromJs',false);}catch{}close();
   },'danger'));
  });
 };

 const ensureRuler=()=>{
  let ruler=element.querySelector('.wb-z-ruler');
  if(!ruler){
   ruler=document.createElement('button');ruler.type='button';ruler.className='wb-z-ruler';ruler.setAttribute('aria-label','Z axis ruler');
   const marker=document.createElement('span');marker.className='wb-z-ruler-current';ruler.appendChild(marker);
   ruler.addEventListener('click',e=>{
    const rect=ruler.getBoundingClientRect();const t=Math.max(0,Math.min(1,(e.clientY-rect.top)/rect.height));const approx=Math.round(50-(t*100));
    modal('Z Location',(host,close)=>{
     const label=document.createElement('label');label.textContent='Approximate Z';const input=document.createElement('input');input.type='number';input.step='1';input.value=String(approx);label.appendChild(input);host.appendChild(label);
     host.appendChild(actionButton('Add Tier',async()=>{const z=Math.round(Number(input.value)||0);try{depthState=await dotnet.invokeMethodAsync('AddTierAtSceneZFromJs',z);}catch{}close();updateRuler();}));
     host.appendChild(actionButton('Add Layer',async()=>{const z=Math.round(Number(input.value)||0);try{depthState=await dotnet.invokeMethodAsync('AddLayerAtSceneZFromJs',z);}catch{}close();updateRuler();}));
     host.appendChild(actionButton('Cancel',close));
    });
   });
   element.appendChild(ruler);
  }
  return ruler;
 };
 const updateRuler=async()=>{
  try{depthState=await dotnet.invokeMethodAsync('GetWorldBuilderDepthState');viewerLocked=!!(depthState.viewerLocked??depthState.ViewerLocked);}catch{}
  const ruler=ensureRuler();const marker=ruler.querySelector('.wb-z-ruler-current');const scene=Number(depthState.sceneZ??depthState.SceneZ??0);const pct=Math.max(0,Math.min(100,50-scene));if(marker)marker.style.top=`${pct}%`;
  studio?.classList.toggle('viewer-locked',viewerLocked);
 };

 const wireStaticButton=(button,handler)=>{
  if(!button||button.dataset.wbRewired==='1')return;
  button.dataset.wbRewired='1';
  button.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();handler();},{capture:true});
 };
 const syncUi=async()=>{
  if(disposed||!studio)return;
  const r=rail();if(!r)return;
  const placement=r.querySelector('[data-wb-command="placement"]');if(placement)placement.dataset.wbHidden='true';
  const resize=r.querySelector('[data-wb-command="resize"]');if(resize)resize.dataset.wbHidden='true';
  for(const name of ['Layers','Tiers']){const b=buttonByText(name);if(b)b.dataset.wbHidden='true';}

  const size=r.querySelector('.tile-size-button');
  if(size){
   const preset=Number(size.dataset.footprint||1);try{await dotnet.invokeMethodAsync('SetTileSizeKmAtOriginFromJs',preset);}catch{}
   let strong=size.querySelector('strong');if(strong)strong.textContent='Tile Size';let small=size.querySelector('small');if(!small){small=document.createElement('small');size.appendChild(small);}small.textContent=`${preset:g} km/tile`.replace(':g','');
  }
  let custom=r.querySelector('[data-wb-command="custom-size"]');
  if(!custom&&size){custom=document.createElement('button');custom.type='button';custom.className='wb-injected-command';custom.dataset.wbCommand='custom-size';custom.innerHTML='<strong>Custom Size</strong><small>at (0,0)</small>';custom.addEventListener('click',openCustomTileSize);size.insertAdjacentElement('afterend',custom);}

  const lock=buttonByText('Z-Lock')||buttonByText('Lock')||buttonByText('Unlock');
  if(lock){
   wireStaticButton(lock,async()=>{try{viewerLocked=await dotnet.invokeMethodAsync('ToggleViewerLockFromJs');}catch{viewerLocked=!viewerLocked;}syncUi();});
   const strong=lock.querySelector('strong');if(strong)strong.textContent=viewerLocked?'Unlock':'Lock';const small=lock.querySelector('small');if(small)small.textContent=viewerLocked?'Viewer Locked':'Viewer Unlocked';lock.classList.toggle('active',viewerLocked);
  }
  const rotate=r.querySelector('[data-wb-command="rotate"]');if(lock&&rotate&&lock.nextElementSibling!==rotate)r.insertBefore(lock,rotate);
  const view=buttonByText('View');const undo=r.querySelector('[data-wb-command="undo"]');const remove=r.querySelector('[data-wb-command="remove"]');if(view){if(undo)r.insertBefore(undo,view);if(remove)r.insertBefore(remove,view);}

  wireStaticButton(buttonByText('Save'),openSaveMenu);
  wireStaticButton(buttonByText('Load'),openLoadMenu);
  wireStaticButton(buttonByText('Publish'),openPublishMenu);
  await updateRuler();
 };

 const onPointerDown=e=>{
  if(disposed||!studio||isBlocked(e.target))return;
  const s=stage();if(!s||(!s.contains(e.target)&&!element.contains(e.target)))return;
  const tile=tileAtPoint(e.clientX,e.clientY);
  if(tile){
   const rect=tile.getBoundingClientRect();const additive=!!(e.shiftKey||e.ctrlKey||e.metaKey);
   active={id:e.pointerId,tile,startX:e.clientX,startY:e.clientY,lastX:e.clientX,lastY:e.clientY,grabX:e.clientX-rect.left,grabY:e.clientY-rect.top,moved:false,index:-1,pickPromise:null};
   active.pickPromise=pick(e.clientX,e.clientY,additive).then(selected=>{if(active&&active.id===e.pointerId)active.index=selected.length?selected[selected.length-1]:-1;return selected;});
   e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();return;
  }
  if(viewerLocked){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();}
 };
 const onPointerMove=e=>{
  if(active&&e.pointerId===active.id){const distance=Math.abs(e.clientX-active.startX)+Math.abs(e.clientY-active.startY);active.lastX=e.clientX;active.lastY=e.clientY;if(distance>8){active.moved=true;active.tile.classList.add('wb-moving');}e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();return;}
  if(viewerLocked&&element.contains(e.target)){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();}
 };
 const finish=async(e,cancel)=>{
  if(!active||e.pointerId!==active.id)return;
  const current=active;active=null;current.tile.classList.remove('wb-moving');e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();if(cancel)return;
  const selected=await current.pickPromise;const index=current.index>=0?current.index:(selected?.length?selected[selected.length-1]:-1);
  if(current.moved&&index>=0){try{syncButtons(await dotnet.invokeMethodAsync('MovePlacedTileFromJs',index,e.clientX-current.grabX+.5,e.clientY-current.grabY+.5)||[]);}catch{}}
 };
 const onPointerUp=e=>{if(active&&e.pointerId===active.id){void finish(e,false);return;}if(viewerLocked&&element.contains(e.target)){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();}};
 const onPointerCancel=e=>{if(active&&e.pointerId===active.id){void finish(e,true);return;}if(viewerLocked&&element.contains(e.target)){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();}};
 const onWheel=e=>{if(viewerLocked&&element.contains(e.target)){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();}};
 const onContextMenu=e=>{const s=stage();if(!s)return;if(tileAtPoint(e.clientX,e.clientY)){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();}};
 const onDragStart=e=>{if(e.target?.closest?.('.world-stage .tile-cell')){e.preventDefault();e.stopPropagation();}};

 document.addEventListener('pointerdown',onPointerDown,{capture:true,passive:false});
 document.addEventListener('pointermove',onPointerMove,{capture:true,passive:false});
 document.addEventListener('pointerup',onPointerUp,{capture:true,passive:false});
 document.addEventListener('pointercancel',onPointerCancel,{capture:true,passive:false});
 document.addEventListener('contextmenu',onContextMenu,true);
 document.addEventListener('dragstart',onDragStart,true);
 element.addEventListener('wheel',onWheel,{capture:true,passive:false});

 const coreBinding=core.attach(element,dotnet);
 uiObserver=new MutationObserver(()=>queueMicrotask(syncUi));uiObserver.observe(studio,{childList:true,subtree:true});
 try{viewerLocked=localStorage.getItem('rist.world.viewerLocked')!=='false';dotnet.invokeMethodAsync('SetViewerLockFromJs',viewerLocked).catch(()=>{});}catch{}
 syncUi();
 autoSaveTimer=setInterval(()=>{if(localStorage.getItem('rist.world.autosave')!=='false')dotnet.invokeMethodAsync('SaveWorldFromJs').catch(()=>{});},30000);

 return {dispose(){
  disposed=true;active=null;clearInterval(autoSaveTimer);uiObserver?.disconnect();
  document.removeEventListener('pointerdown',onPointerDown,true);document.removeEventListener('pointermove',onPointerMove,true);document.removeEventListener('pointerup',onPointerUp,true);document.removeEventListener('pointercancel',onPointerCancel,true);document.removeEventListener('contextmenu',onContextMenu,true);document.removeEventListener('dragstart',onDragStart,true);element.removeEventListener('wheel',onWheel,true);
  style.remove();element.querySelector('.wb-z-ruler')?.remove();clearModal();try{coreBinding?.dispose?.();}catch{}
 }};
}
