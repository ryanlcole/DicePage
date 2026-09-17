import * as core from './worldbuilder-z-axis-core.js?v=20260915-completion-1';
import './worldbuilder-controls.js?v=20260912-pangea-sprites-1';
import './worldbuilder-controls-state.js';
import './worldbuilder-drag-preview.js';

export const viewerPoint=core.viewerPoint;
export const viewerGridPoint=core.viewerGridPoint;
export const beginQuickPointerDrop=core.beginQuickPointerDrop;

export function attach(element,dotnet){
 if(!element)return core.attach(element,dotnet);
 const studio=element.closest('.worldbuilder-studio');
 let active=null,disposed=false,viewerLocked=true,syncingUi=false,uiObserver=null,autoSaveTimer=null;
 let depthState={sceneZ:0,tierIndex:0,layerOffset:0,viewerLocked:true};
 let tierShortcuts=[];
 let customMapScale=Number(localStorage.getItem('rist.world.customMapScalePerSquare'))||1;

 const style=document.createElement('style');style.id='rist-worldbuilder-spatial-editor';style.textContent=`@import url('./css/worldbuilder-control-rework.css?v=20260910-controls-3');
 .worldbuilder-studio .world-stage .tile-cell,.worldbuilder-studio .world-stage .tile-cell *{-webkit-touch-callout:none!important;-webkit-user-select:none!important;user-select:none!important;-webkit-user-drag:none!important;touch-action:none!important}
 .worldbuilder-studio .world-stage .tile-cell{cursor:grab!important}.worldbuilder-studio .world-stage .tile-cell.wb-moving{opacity:.72!important;cursor:grabbing!important;z-index:214749!important}
 .worldbuilder-studio .world-stage .tile-cell.wb-selected{outline:3px solid #f2cf72!important;outline-offset:-3px!important;box-shadow:inset 0 0 0 2px rgba(12,30,40,.85)!important;z-index:214748!important}
 .worldbuilder-studio .world-stage .tile-cell>.tile-image-crop{transform:rotate(var(--wb-rotation,0deg));transform-origin:center center}
 .worldbuilder-studio .studio-command-rail [data-wb-hidden="true"]{display:none!important}`;document.head.appendChild(style);

 const stage=()=>studio?.querySelector('.world-stage');
 const tiles=()=>studio?[...studio.querySelectorAll('.world-stage .tile-cell')]:[];
 const rail=()=>studio?.querySelector('.studio-command-rail');
 const byText=text=>[...(rail()?.querySelectorAll('button')||[])].find(b=>(b.querySelector('strong')?.textContent||'').trim()===text);
 const blocked=t=>!!t?.closest?.('.studio-mini-panel,.studio-load-panel,.studio-library-shade,.recursion-cockpit,.locked-tile-menu,.recursive-region-actions,.wb-modal,.asset-preview-stage,.wb-context-keyboard,.wb-keyboard-launcher,.wb-tier-shortcut-hud');
 const tileAt=(x,y)=>{const list=tiles();for(let i=list.length-1;i>=0;i--){const r=list[i].getBoundingClientRect();if(x>=r.left&&x<=r.right&&y>=r.top&&y<=r.bottom)return list[i]}return null};
 const point=(x,y)=>{const s=stage();if(!s)return null;const r=s.getBoundingClientRect();if(r.width<1||r.height<1)return null;const px=(x-r.left)/r.width,py=(y-r.top)/r.height;return px<0||px>1||py<0||py>1?null:[px,py]};
 const cellsFor=tile=>{const s=stage(),sr=s?.getBoundingClientRect(),tr=tile?.getBoundingClientRect();if(!sr||!tr||sr.width<1)return 1;return Math.max(1,Math.min(30,Math.round(tr.width/(sr.width/30))))};
 const applySelection=selected=>{const set=new Set((selected||[]).map(Number));tiles().forEach((t,i)=>t.classList.toggle('wb-selected',set.has(i)));for(const n of ['rotate','remove']){const b=studio?.querySelector(`[data-wb-command="${n}"]`);if(b)b.disabled=set.size<1}const small=studio?.querySelector('[data-wb-command="remove"] small');if(small)small.textContent=`${set.size} Selected`;return[...set]};
 const pick=async(x,y,additive)=>{const p=point(x,y);if(!p)return[];try{return applySelection(await dotnet.invokeMethodAsync('SelectPlacedTileAtWorldPoint',p[0],p[1],!!additive)||[])}catch{return[]}};
 const stop=e=>{e.preventDefault();e.stopPropagation();e.stopImmediatePropagation()};

 const clearModal=()=>studio?.querySelectorAll('.wb-modal').forEach(x=>x.remove());
 const button=(label,fn,cls='')=>{const b=document.createElement('button');b.type='button';b.textContent=label;if(cls)b.className=cls;b.onclick=fn;return b};
 const modal=(title,build)=>{clearModal();const host=document.createElement('section');host.className='wb-modal';host.setAttribute('role','dialog');host.setAttribute('aria-modal','true');const h=document.createElement('header'),s=document.createElement('strong');s.textContent=title;h.append(s,button('×',()=>host.remove()));host.append(h);build(host,()=>host.remove());element.append(host);return host};
 const setCustomScale=value=>{if(!Number.isFinite(value)||value<=0)return;customMapScale=Math.min(1_000_000,Math.max(.001,value));localStorage.setItem('rist.world.customMapScalePerSquare',String(customMapScale));scheduleUi()};
 const openCustomSize=()=>modal('Custom map scale',(host,close)=>{const label=document.createElement('label'),input=document.createElement('input');label.append(document.createTextNode('Distance per square'));input.type='number';input.min='0.001';input.max='1000000';input.step='any';input.value=String(customMapScale);label.append(input);host.append(label);const note=document.createElement('small');note.textContent='Optional cartographer scale for this map view. Tile Size still defines the exact grid footprint of placed assets.';host.append(note,button('Apply',()=>{setCustomScale(Number(input.value));close()}),button('Cancel',close))});
 const perform=async(host,close,action)=>{if(host.dataset.busy==='true')return;host.dataset.busy='true';try{await action();close()}catch{let error=host.querySelector('[role="alert"]');if(!error){error=document.createElement('p');error.setAttribute('role','alert');host.append(error)}error.textContent='Could not complete this action. Your current world is still open. Check your connection and try again.'}finally{host.dataset.busy='false'}};
 const openSave=()=>modal('Save',(host,close)=>{const row=document.createElement('label'),cb=document.createElement('input');cb.type='checkbox';cb.checked=localStorage.getItem('rist.world.autosave')!=='false';row.append(cb,document.createTextNode('Autosave'));host.append(row);cb.onchange=()=>{localStorage.setItem('rist.world.autosave',String(cb.checked));dotnet.invokeMethodAsync('SetAutoSaveFromJs',cb.checked).catch(()=>{})};host.append(button('Save',()=>perform(host,close,()=>dotnet.invokeMethodAsync('SaveWorldFromJs'))),button('Export',()=>perform(host,close,async()=>{await dotnet.invokeMethodAsync('SaveWorldFromJs');window.ristWorld?.exportCurrentWorld?.()})),button('Cancel',close))});
 const openLoad=()=>modal('Load',(host,close)=>host.append(button('Load',()=>perform(host,close,()=>dotnet.invokeMethodAsync('LoadWorldFromJs'))),button('Import',()=>{window.ristWorld?.importCurrentWorld?.();close()}),button('Cancel',close)));
 const openPublish=()=>modal('Publish',(host,close)=>host.append(button('Publish',()=>perform(host,close,()=>dotnet.invokeMethodAsync('SetPublishModeFromJs',true))),button('Unpublish',()=>perform(host,close,()=>dotnet.invokeMethodAsync('SetPublishModeFromJs',false)))));
 const wire=(b,fn)=>{if(!b||b.dataset.wbRewired==='1')return;b.dataset.wbRewired='1';b.addEventListener('click',e=>{stop(e);fn()},{capture:true})};
 const publishDepth=()=>{
  if(!studio)return;
  studio.dataset.wbSceneZ=String(depthState.sceneZ??0);
  studio.dataset.wbTierIndex=String(depthState.tierIndex??0);
  studio.dataset.wbViewerLocked=viewerLocked?'true':'false';
  window.dispatchEvent(new CustomEvent('rist:worldbuilder-depth',{detail:{...depthState,shortcuts:tierShortcuts.map(x=>({...x}))}}));
 };
 const updateDepth=async()=>{
  try{
   depthState=await dotnet.invokeMethodAsync('GetWorldBuilderDepthState');
   viewerLocked=!!(depthState.viewerLocked??depthState.ViewerLocked);
   if(!tierShortcuts.length)tierShortcuts=await dotnet.invokeMethodAsync('GetWorldBuilderTierShortcuts')||[];
  }catch{}
  studio?.classList.toggle('viewer-locked',viewerLocked);
  studio?.classList.toggle('viewer-unlocked',!viewerLocked);
  publishDepth();
  return depthState;
 };
 const applyDepth=state=>{if(state)depthState=state;viewerLocked=!!(depthState.viewerLocked??depthState.ViewerLocked??viewerLocked);studio?.classList.toggle('viewer-locked',viewerLocked);studio?.classList.toggle('viewer-unlocked',!viewerLocked);publishDepth();scheduleUi();return depthState};
 const depthApi={
  state:()=>({...depthState}),
  shortcuts:()=>tierShortcuts.map(x=>({...x})),
  refresh:updateDepth,
  async moveSceneZ(delta){if(viewerLocked)return{...depthState};try{return applyDepth(await dotnet.invokeMethodAsync('MoveViewerSceneZFromJs',Number(delta)||0))}catch{return{...depthState}}},
  async setSceneZ(sceneZ){if(viewerLocked)return{...depthState};try{return applyDepth(await dotnet.invokeMethodAsync('SetViewerSceneZFromJs',Number(sceneZ)||0))}catch{return{...depthState}}},
  async setTier(tierIndex){if(viewerLocked)return{...depthState};try{return applyDepth(await dotnet.invokeMethodAsync('SetViewerTierFromJs',Number(tierIndex)||0))}catch{return{...depthState}}}
 };
 window.ristWorldBuilderDepth=depthApi;

 async function syncUi(){
  if(disposed||syncingUi)return;syncingUi=true;
  try{
   const r=rail();if(!r)return;
   for(const n of ['Layers','Tiers']){const b=byText(n);if(b)b.dataset.wbHidden='true'}
   const resize=r.querySelector('[data-wb-command="resize"]');if(resize)resize.dataset.wbHidden='true';
   const size=r.querySelector('.tile-size-button');if(size){let small=size.querySelector('small');if(!small){small=document.createElement('small');size.append(small)}small.textContent='Tile Size'}
   let custom=r.querySelector('[data-wb-command="custom-size"]');if(!custom&&size){custom=document.createElement('button');custom.type='button';custom.className='wb-injected-command';custom.dataset.wbCommand='custom-size';custom.innerHTML=`<strong>Custom</strong><small>${customMapScale} / square</small>`;custom.onclick=openCustomSize;size.insertAdjacentElement('afterend',custom)}else if(custom)custom.querySelector('small').textContent=`${customMapScale} / square`;
   await updateDepth();
   const lock=byText('Z-Lock')||byText('Lock')||byText('Unlock');if(lock){wire(lock,async()=>{try{viewerLocked=await dotnet.invokeMethodAsync('ToggleViewerLockFromJs');localStorage.setItem('rist.world.viewerLocked',String(viewerLocked));window.ristViewerNavigation?.resync?.();await updateDepth()}catch{viewerLocked=!viewerLocked;publishDepth()}scheduleUi()});const strong=lock.querySelector('strong'),small=lock.querySelector('small');if(strong)strong.textContent=viewerLocked?'Unlock':'Lock';if(small)small.textContent=viewerLocked?'Viewer Locked':'Viewer Unlocked';lock.classList.toggle('active',viewerLocked);lock.setAttribute('aria-pressed',viewerLocked?'true':'false')}
   const rotate=r.querySelector('[data-wb-command="rotate"]');if(lock&&rotate&&lock.nextElementSibling!==rotate)r.insertBefore(lock,rotate);
   const view=byText('View'),undo=r.querySelector('[data-wb-command="undo"]'),remove=r.querySelector('[data-wb-command="remove"]');if(view){if(undo)r.insertBefore(undo,view);if(remove)r.insertBefore(remove,view)}
   wire(byText('Save'),openSave);wire(byText('Load'),openLoad);wire(byText('Publish'),openPublish);
  }finally{syncingUi=false}
 }
 const scheduleUi=()=>queueMicrotask(syncUi);
 const movePoint=(cur,e)=>({x:e.clientX-cur.grabX+.5,y:e.clientY-cur.grabY+.5});
 const down=e=>{
  if(disposed||blocked(e.target))return;
  const s=stage();if(!s||(!s.contains(e.target)&&!element.contains(e.target)))return;
  const tile=tileAt(e.clientX,e.clientY);if(!tile)return;
  const r=tile.getBoundingClientRect(),additive=!!(e.shiftKey||e.ctrlKey||e.metaKey);
  active={id:e.pointerId,tile,startX:e.clientX,startY:e.clientY,grabX:e.clientX-r.left,grabY:e.clientY-r.top,moved:false,index:-1,cells:cellsFor(tile),preview:false,pickPromise:null};
  active.pickPromise=pick(e.clientX,e.clientY,additive).then(sel=>{if(active&&active.id===e.pointerId)active.index=sel.length?sel[sel.length-1]:-1;return sel});stop(e);
 };
 const move=e=>{if(!active||e.pointerId!==active.id)return;if(Math.abs(e.clientX-active.startX)+Math.abs(e.clientY-active.startY)>8){active.moved=true;active.tile.classList.add('wb-moving');const p=movePoint(active,e);if(!active.preview){active.preview=true;window.ristMovePlacement?.begin?.(active.tile,p.x,p.y,active.cells)}else window.ristMovePlacement?.update?.(p.x,p.y,active.cells,active.tile)}stop(e)};
 const finish=async(e,cancel)=>{if(!active||e.pointerId!==active.id)return;const cur=active;active=null;cur.tile.classList.remove('wb-moving');stop(e);if(cancel){window.ristMovePlacement?.cancel?.();return}const sel=await cur.pickPromise,index=cur.index>=0?cur.index:(sel?.length?sel[sel.length-1]:-1);if(cur.moved&&index>=0){const p=movePoint(cur,e);let choice={upperLayer:false,upperTier:false,treatment:'normal'};try{choice=await window.ristMovePlacement?.choose?.(p.x,p.y,cur.cells,cur.tile)??choice}catch{choice=null}if(choice){try{applySelection(await dotnet.invokeMethodAsync('MovePlacedTileWithPlacementFromJs',index,p.x,p.y,!!choice.upperLayer,!!choice.upperTier,choice.treatment||'normal')||[])}catch{}}}else window.ristMovePlacement?.cancel?.()};
 const up=e=>{if(active&&e.pointerId===active.id)void finish(e,false)};
 const cancel=e=>{if(active&&e.pointerId===active.id)void finish(e,true)};
 const context=e=>{if(tileAt(e.clientX,e.clientY))stop(e)};
 const dragstart=e=>{if(e.target?.closest?.('.world-stage .tile-cell')){e.preventDefault();e.stopPropagation()}};
 document.addEventListener('pointerdown',down,{capture:true,passive:false});document.addEventListener('pointermove',move,{capture:true,passive:false});document.addEventListener('pointerup',up,{capture:true,passive:false});document.addEventListener('pointercancel',cancel,{capture:true,passive:false});document.addEventListener('contextmenu',context,true);document.addEventListener('dragstart',dragstart,true);
 const coreBinding=core.attach(element,dotnet);uiObserver=new MutationObserver(scheduleUi);uiObserver.observe(studio,{childList:true,subtree:true});
 try{viewerLocked=localStorage.getItem('rist.world.viewerLocked')!=='false';dotnet.invokeMethodAsync('SetViewerLockFromJs',viewerLocked).catch(()=>{})}catch{}
 scheduleUi();autoSaveTimer=setInterval(()=>{if(localStorage.getItem('rist.world.autosave')!=='false')dotnet.invokeMethodAsync('SaveWorldFromJs').catch(()=>{})},30000);
 return{dispose(){disposed=true;active=null;window.ristMovePlacement?.cancel?.();clearInterval(autoSaveTimer);uiObserver?.disconnect();document.removeEventListener('pointerdown',down,true);document.removeEventListener('pointermove',move,true);document.removeEventListener('pointerup',up,true);document.removeEventListener('pointercancel',cancel,true);document.removeEventListener('contextmenu',context,true);document.removeEventListener('dragstart',dragstart,true);style.remove();clearModal();if(window.ristWorldBuilderDepth===depthApi)delete window.ristWorldBuilderDepth;try{coreBinding?.dispose?.()}catch{}}};
}