import * as core from './worldbuilder-z-axis-core.js';
import './worldbuilder-controls.js';
import './worldbuilder-controls-state.js';

export const viewerPoint=core.viewerPoint;
export const viewerGridPoint=core.viewerGridPoint;
export const beginQuickPointerDrop=core.beginQuickPointerDrop;

export function attach(element,dotnet){
 if(!element)return core.attach(element,dotnet);
 const studio=element.closest('.worldbuilder-studio');
 let active=null,disposed=false,viewerLocked=true,syncingUi=false;
 let depthState={sceneZ:0,tierIndex:0,layerOffset:0,viewerLocked:true};
 let uiObserver=null,autoSaveTimer=null;
 let tileSizeKm=Number(localStorage.getItem('rist.world.tileSizeKmAtOrigin'))||1;

 const style=document.createElement('style');
 style.id='rist-worldbuilder-mahjong-picking';
 style.textContent=`@import url('./css/worldbuilder-control-rework.css?v=20260910-controls-3');
 .worldbuilder-studio .world-stage .tile-cell,.worldbuilder-studio .world-stage .tile-cell *{-webkit-touch-callout:none!important;-webkit-user-select:none!important;user-select:none!important;-webkit-user-drag:none!important;touch-action:none!important}
 .worldbuilder-studio .world-stage .tile-cell.wb-selected{outline:3px solid #f2cf72!important;outline-offset:-3px!important;box-shadow:inset 0 0 0 2px rgba(12,30,40,.85)!important;z-index:214748!important}
 .worldbuilder-studio .studio-command-rail [data-wb-hidden="true"]{display:none!important}`;
 document.head.appendChild(style);

 const stage=()=>studio?.querySelector('.world-stage');
 const tiles=()=>studio?[...studio.querySelectorAll('.world-stage .tile-cell')]:[];
 const rail=()=>studio?.querySelector('.studio-command-rail');
 const byText=text=>[...(rail()?.querySelectorAll('button')||[])].find(b=>(b.querySelector('strong')?.textContent||'').trim()===text);
 const blocked=t=>!!t?.closest?.('.studio-mini-panel,.studio-load-panel,.studio-library-shade,.recursion-cockpit,.desktop-map-zoom,.locked-tile-menu,.recursive-region-actions,.wb-modal,.wb-z-ruler');
 const tileAt=(x,y)=>{const list=tiles();for(let i=list.length-1;i>=0;i--){const r=list[i].getBoundingClientRect();if(x>=r.left&&x<=r.right&&y>=r.top&&y<=r.bottom)return list[i];}return null;};
 const point=(x,y)=>{const s=stage();if(!s)return null;const r=s.getBoundingClientRect();if(r.width<1||r.height<1)return null;const px=(x-r.left)/r.width,py=(y-r.top)/r.height;return px<0||px>1||py<0||py>1?null:[px,py];};
 const applySelection=selected=>{const set=new Set((selected||[]).map(Number));tiles().forEach((t,i)=>t.classList.toggle('wb-selected',set.has(i)));for(const n of ['rotate','remove']){const b=studio?.querySelector(`[data-wb-command="${n}"]`);if(b)b.disabled=set.size<1;}const small=studio?.querySelector('[data-wb-command="remove"] small');if(small)small.textContent=`${set.size} Selected`;return [...set];};
 const pick=async(x,y,additive)=>{const p=point(x,y);if(!p)return[];try{return applySelection(await dotnet.invokeMethodAsync('SelectPlacedTileAtWorldPoint',p[0],p[1],!!additive)||[]);}catch{return[];}};

 const clearModal=()=>studio?.querySelectorAll('.wb-modal').forEach(x=>x.remove());
 const button=(label,fn,cls='')=>{const b=document.createElement('button');b.type='button';b.textContent=label;if(cls)b.className=cls;b.onclick=fn;return b;};
 const modal=(title,build)=>{clearModal();const host=document.createElement('section');host.className='wb-modal';host.setAttribute('role','dialog');host.setAttribute('aria-modal','true');const h=document.createElement('header');const s=document.createElement('strong');s.textContent=title;const x=button('×',()=>host.remove());h.append(s,x);host.append(h);build(host,()=>host.remove());element.append(host);return host;};
 const setTileSize=async km=>{if(!Number.isFinite(km)||km<=0)return;tileSizeKm=Math.min(1_000_000,Math.max(.001,km));localStorage.setItem('rist.world.tileSizeKmAtOrigin',String(tileSizeKm));try{await dotnet.invokeMethodAsync('SetTileSizeKmAtOriginFromJs',tileSizeKm);}catch{}scheduleUi();};
 const cycleTileSize=()=>{const presets=[.25,.5,1,2,4,8,16,30,100,1000];const next=presets.find(v=>v>tileSizeKm+1e-9)??presets[0];setTileSize(next);};

 const openCustomSize=()=>modal('Tile Size at (0,0)',(host,close)=>{const label=document.createElement('label');label.append(document.createTextNode('Kilometers per tile'));const input=document.createElement('input');input.type='number';input.min='0.001';input.max='1000000';input.step='any';input.value=String(tileSizeKm);label.append(input);host.append(label);const note=document.createElement('small');note.textContent='World math only; travel distance remains a game-system decision.';host.append(note);host.append(button('Apply',async()=>{await setTileSize(Number(input.value));close();}),button('Cancel',close));});
 const openSave=()=>modal('Save',(host,close)=>{const row=document.createElement('label');const cb=document.createElement('input');cb.type='checkbox';cb.checked=localStorage.getItem('rist.world.autosave')!=='false';row.append(cb,document.createTextNode('Autosave'));host.append(row);cb.onchange=()=>{localStorage.setItem('rist.world.autosave',String(cb.checked));dotnet.invokeMethodAsync('SetAutoSaveFromJs',cb.checked).catch(()=>{});};host.append(button('Save',async()=>{try{await dotnet.invokeMethodAsync('SaveWorldFromJs');}catch{}close();}),button('Export',async()=>{try{await dotnet.invokeMethodAsync('SaveWorldFromJs');}catch{}window.ristWorld?.exportCurrentWorld?.();close();}),button('Cancel',close));});
 const openLoad=()=>modal('Load',(host,close)=>host.append(button('Load',async()=>{try{await dotnet.invokeMethodAsync('LoadWorldFromJs');}catch{}close();}),button('Import',()=>{window.ristWorld?.importCurrentWorld?.();close();}),button('Cancel',close)));
 const openPublish=()=>modal('Publish',(host,close)=>{host.append(button('Publish',async()=>{const st=window.ristWorld?.readPublishState?.()||{owner:'self',active:['self'],saved:[]};st.published=true;st.active=[st.owner,...(st.saved||[]).filter(x=>x!==st.owner)];window.ristWorld?.writePublishState?.(st);try{await dotnet.invokeMethodAsync('SetPublishModeFromJs',true);}catch{}close();}),button('Unpublish',async()=>{const st=window.ristWorld?.readPublishState?.()||{owner:'self',active:['self'],saved:[]};st.published=false;st.saved=[...(st.active||[])].filter(x=>x!==st.owner);st.active=[st.owner];window.ristWorld?.writePublishState?.(st);try{await dotnet.invokeMethodAsync('SetPublishModeFromJs',false);}catch{}close();},'danger'));});

 const ensureRuler=()=>{let r=element.querySelector('.wb-z-ruler');if(r)return r;r=document.createElement('button');r.type='button';r.className='wb-z-ruler';r.setAttribute('aria-label','Z axis ruler');const m=document.createElement('span');m.className='wb-z-ruler-current';r.append(m);r.onclick=e=>{const rr=r.getBoundingClientRect(),t=Math.max(0,Math.min(1,(e.clientY-rr.top)/rr.height)),approx=Math.round(50-t*100);modal('Z Location',(host,close)=>{const label=document.createElement('label');label.append(document.createTextNode('Approximate Z'));const input=document.createElement('input');input.type='number';input.step='1';input.value=String(approx);label.append(input);host.append(label);host.append(button('Add Tier',async()=>{try{depthState=await dotnet.invokeMethodAsync('AddTierAtSceneZFromJs',Math.round(Number(input.value)||0));}catch{}close();updateRuler();}),button('Add Layer',async()=>{try{depthState=await dotnet.invokeMethodAsync('AddLayerAtSceneZFromJs',Math.round(Number(input.value)||0));}catch{}close();updateRuler();}),button('Cancel',close));});};element.append(r);return r;};
 const updateRuler=async()=>{try{depthState=await dotnet.invokeMethodAsync('GetWorldBuilderDepthState');viewerLocked=!!(depthState.viewerLocked??depthState.ViewerLocked);}catch{}const r=ensureRuler(),m=r.querySelector('.wb-z-ruler-current'),scene=Number(depthState.sceneZ??depthState.SceneZ??0);if(m)m.style.top=`${Math.max(0,Math.min(100,50-scene))}%`;studio?.classList.toggle('viewer-locked',viewerLocked);};
 const wire=(b,fn)=>{if(!b||b.dataset.wbRewired==='1')return;b.dataset.wbRewired='1';b.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();fn();},{capture:true});};

 async function syncUi(){
  if(disposed||syncingUi)return;syncingUi=true;
  try{
   const r=rail();if(!r)return;
   const placement=r.querySelector('[data-wb-command="placement"]');if(placement)placement.dataset.wbHidden='true';
   const resize=r.querySelector('[data-wb-command="resize"]');if(resize)resize.dataset.wbHidden='true';
   for(const n of ['Layers','Tiers']){const b=byText(n);if(b)b.dataset.wbHidden='true';}
   const size=r.querySelector('.tile-size-button');
   if(size){wire(size,cycleTileSize);const s=size.querySelector('strong');if(s&&s.textContent!=='Tile Size')s.textContent='Tile Size';let small=size.querySelector('small');if(!small){small=document.createElement('small');size.append(small);}const txt=`${tileSizeKm} km/tile`;if(small.textContent!==txt)small.textContent=txt;}
   let custom=r.querySelector('[data-wb-command="custom-size"]');if(!custom&&size){custom=document.createElement('button');custom.type='button';custom.className='wb-injected-command';custom.dataset.wbCommand='custom-size';custom.innerHTML='<strong>Custom Size</strong><small>at (0,0)</small>';custom.onclick=openCustomSize;size.insertAdjacentElement('afterend',custom);}
   const lock=byText('Z-Lock')||byText('Lock')||byText('Unlock');if(lock){wire(lock,async()=>{try{viewerLocked=await dotnet.invokeMethodAsync('ToggleViewerLockFromJs');localStorage.setItem('rist.world.viewerLocked',String(viewerLocked));}catch{viewerLocked=!viewerLocked;}scheduleUi();});const s=lock.querySelector('strong'),sm=lock.querySelector('small'),label=viewerLocked?'Unlock':'Lock',sub=viewerLocked?'Viewer Locked':'Viewer Unlocked';if(s&&s.textContent!==label)s.textContent=label;if(sm&&sm.textContent!==sub)sm.textContent=sub;lock.classList.toggle('active',viewerLocked);}
   const rotate=r.querySelector('[data-wb-command="rotate"]');if(lock&&rotate&&lock.nextElementSibling!==rotate)r.insertBefore(lock,rotate);
   const view=byText('View'),undo=r.querySelector('[data-wb-command="undo"]'),remove=r.querySelector('[data-wb-command="remove"]');if(view){if(undo)r.insertBefore(undo,view);if(remove)r.insertBefore(remove,view);}
   wire(byText('Save'),openSave);wire(byText('Load'),openLoad);wire(byText('Publish'),openPublish);
   await updateRuler();
  }finally{syncingUi=false;}
 }
 const scheduleUi=()=>queueMicrotask(syncUi);

 const down=e=>{if(disposed||!studio||blocked(e.target))return;const s=stage();if(!s||(!s.contains(e.target)&&!element.contains(e.target)))return;const tile=tileAt(e.clientX,e.clientY);if(tile){const r=tile.getBoundingClientRect(),additive=!!(e.shiftKey||e.ctrlKey||e.metaKey);active={id:e.pointerId,tile,startX:e.clientX,startY:e.clientY,grabX:e.clientX-r.left,grabY:e.clientY-r.top,moved:false,index:-1,pickPromise:null};active.pickPromise=pick(e.clientX,e.clientY,additive).then(sel=>{if(active&&active.id===e.pointerId)active.index=sel.length?sel[sel.length-1]:-1;return sel;});e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();return;}if(viewerLocked){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();}};
 const move=e=>{if(active&&e.pointerId===active.id){if(Math.abs(e.clientX-active.startX)+Math.abs(e.clientY-active.startY)>8){active.moved=true;active.tile.classList.add('wb-moving');}e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();return;}if(viewerLocked&&element.contains(e.target)){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();}};
 const finish=async(e,cancel)=>{if(!active||e.pointerId!==active.id)return;const cur=active;active=null;cur.tile.classList.remove('wb-moving');e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();if(cancel)return;const sel=await cur.pickPromise,index=cur.index>=0?cur.index:(sel?.length?sel[sel.length-1]:-1);if(cur.moved&&index>=0){try{applySelection(await dotnet.invokeMethodAsync('MovePlacedTileFromJs',index,e.clientX-cur.grabX+.5,e.clientY-cur.grabY+.5)||[]);}catch{}}};
 const up=e=>{if(active&&e.pointerId===active.id){void finish(e,false);return;}if(viewerLocked&&element.contains(e.target)){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();}};
 const cancel=e=>{if(active&&e.pointerId===active.id){void finish(e,true);return;}if(viewerLocked&&element.contains(e.target)){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();}};
 const wheel=e=>{if(viewerLocked&&element.contains(e.target)){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();}};
 const context=e=>{if(tileAt(e.clientX,e.clientY)){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();}};
 const dragstart=e=>{if(e.target?.closest?.('.world-stage .tile-cell')){e.preventDefault();e.stopPropagation();}};
 document.addEventListener('pointerdown',down,{capture:true,passive:false});document.addEventListener('pointermove',move,{capture:true,passive:false});document.addEventListener('pointerup',up,{capture:true,passive:false});document.addEventListener('pointercancel',cancel,{capture:true,passive:false});document.addEventListener('contextmenu',context,true);document.addEventListener('dragstart',dragstart,true);element.addEventListener('wheel',wheel,{capture:true,passive:false});
 const coreBinding=core.attach(element,dotnet);
 uiObserver=new MutationObserver(scheduleUi);uiObserver.observe(studio,{childList:true,subtree:true});
 try{viewerLocked=localStorage.getItem('rist.world.viewerLocked')!=='false';dotnet.invokeMethodAsync('SetViewerLockFromJs',viewerLocked).catch(()=>{});dotnet.invokeMethodAsync('SetTileSizeKmAtOriginFromJs',tileSizeKm).catch(()=>{});}catch{}
 scheduleUi();autoSaveTimer=setInterval(()=>{if(localStorage.getItem('rist.world.autosave')!=='false')dotnet.invokeMethodAsync('SaveWorldFromJs').catch(()=>{});},30000);
 return{dispose(){disposed=true;active=null;clearInterval(autoSaveTimer);uiObserver?.disconnect();document.removeEventListener('pointerdown',down,true);document.removeEventListener('pointermove',move,true);document.removeEventListener('pointerup',up,true);document.removeEventListener('pointercancel',cancel,true);document.removeEventListener('contextmenu',context,true);document.removeEventListener('dragstart',dragstart,true);element.removeEventListener('wheel',wheel,true);style.remove();element.querySelector('.wb-z-ruler')?.remove();clearModal();try{coreBinding?.dispose?.();}catch{}}};
}
