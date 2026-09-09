let quickDropCleanup=null;

export function viewerPoint(element,clientX,clientY){
 if(!element)return null;
 const rect=element.getBoundingClientRect();
 if(rect.width<1||rect.height<1)return null;
 const x=(clientX-rect.left)/rect.width;
 const y=(clientY-rect.top)/rect.height;
 if(x<0||x>1||y<0||y>1)return null;
 return [x,y];
}

export function viewerGridPoint(element,clientX,clientY){
 if(!element)return null;
 const grid=element.querySelector('.studio-viewer-grid');
 const rect=(grid||element).getBoundingClientRect();
 if(rect.width<1||rect.height<1)return null;
 const x=(clientX-rect.left)/rect.width;
 const y=(clientY-rect.top)/rect.height;
 if(x<0||x>1||y<0||y>1)return null;
 return [x,y];
}

export function beginQuickPointerDrop(dotnet,pointerId){
 if(quickDropCleanup)quickDropCleanup();
 const finish=()=>{
  document.removeEventListener('pointerup',onUp,true);
  document.removeEventListener('pointercancel',onCancel,true);
  quickDropCleanup=null;
 };
 const onUp=e=>{
  if(e.pointerId!==pointerId)return;
  finish();
  dotnet?.invokeMethodAsync('QuickPointerDrop',e.clientX,e.clientY).catch(()=>{});
 };
 const onCancel=e=>{
  if(e.pointerId!==pointerId)return;
  finish();
 };
 document.addEventListener('pointerup',onUp,true);
 document.addEventListener('pointercancel',onCancel,true);
 quickDropCleanup=finish;
}

export function attach(element,dotnet){
 if(!element)return {dispose(){}};
 const pointers=new Map();
 let pinchDistance=0;
 let wheelAccumulator=0;
 let quickPointer=null;
 let quickDragIndex=-1;
 let selectionPointer=null;
 let commandObserver=null;
 let quickGhost=null;

 const studio=element.closest('.worldbuilder-studio');

 const styleId='rist-worldbuilder-single-grid-authority';
 let gridAuthority=document.getElementById(styleId);
 if(!gridAuthority){
  gridAuthority=document.createElement('style');
  gridAuthority.id=styleId;
  gridAuthority.textContent=`
   .worldbuilder-studio .studio-viewer-canvas .map [class*="grid"]{
    display:none!important;visibility:hidden!important;background:none!important;
    background-image:none!important;border:0!important;outline:0!important;
   }
   .worldbuilder-studio .studio-viewer-canvas .map::before,
   .worldbuilder-studio .studio-viewer-canvas .map::after,
   .worldbuilder-studio .studio-viewer-canvas .world-stage::before,
   .worldbuilder-studio .studio-viewer-canvas .world-stage::after{
    content:none!important;display:none!important;background:none!important;background-image:none!important;
   }
   .worldbuilder-studio .studio-viewer-canvas .coordinate-system,
   .worldbuilder-studio .studio-viewer-canvas .grid-coordinates,
   .worldbuilder-studio .studio-viewer-canvas .coordinate-grid,
   .worldbuilder-studio .studio-viewer-canvas .map-grid,
   .worldbuilder-studio .studio-viewer-canvas .grid-overlay{
    display:none!important;visibility:hidden!important;
   }
   .worldbuilder-studio .quick-slot.filled,
   .worldbuilder-studio .quick-slot.filled *{
    -webkit-user-select:none!important;user-select:none!important;
    -webkit-touch-callout:none!important;touch-action:none!important;
   }
   .worldbuilder-studio .quick-slot.filled.wb-grabbing{
    transform:scale(.96);opacity:.72;border-color:#f2cf72!important;
   }
   .wb-quick-drag-ghost{
    position:fixed!important;z-index:2147483000!important;pointer-events:none!important;
    width:84px;height:64px;border:2px solid #f2cf72;border-radius:10px;overflow:hidden;
    background:#0d171e;box-shadow:0 10px 28px #000b;transform:translate(-50%,-50%) scale(1.06);
   }
   .wb-quick-drag-ghost img{width:100%;height:100%;object-fit:cover;display:block}
   .wb-quick-drag-ghost span{position:absolute;left:0;right:0;bottom:0;padding:4px;background:#000c;color:#fff1bd;font:800 9px/1 system-ui;text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
   .worldbuilder-studio .world-stage .tile-cell.wb-selected{
    outline:3px solid #f2cf72!important;outline-offset:-3px!important;
    box-shadow:inset 0 0 0 2px rgba(12,30,40,.85)!important;
    z-index:25!important;
   }
   .worldbuilder-studio .studio-command-rail .wb-injected-command{
    box-sizing:border-box;flex:0 0 auto;height:48px;min-width:104px;padding:4px 12px;
    display:grid;place-items:center;gap:2px;border:1px solid #4b5f69;border-radius:9px;
    background:#0d171e;color:#d4dde1;touch-action:manipulation;
   }
   .worldbuilder-studio .studio-command-rail .wb-injected-command strong{font:900 12px/1 system-ui;color:#f0ddb0}
   .worldbuilder-studio .studio-command-rail .wb-injected-command small{font:800 7px/1 system-ui;letter-spacing:.06em;text-transform:uppercase;color:#8fa5b0}
   .worldbuilder-studio .studio-command-rail .wb-injected-command.active{border-color:#d0aa56;background:#201b10}
   .worldbuilder-studio .studio-command-rail .wb-injected-command:disabled{opacity:.38}
   .worldbuilder-studio .studio-command-rail .tile-size-button small{display:block;font:800 7px/1 system-ui;letter-spacing:.06em;text-transform:uppercase;color:#8fa5b0}
   @media(max-width:760px){.worldbuilder-studio .studio-command-rail .wb-injected-command{height:44px;min-width:94px;padding:4px 9px}}
  `;
  document.head.appendChild(gridAuthority);
 }

 const syncCommandControls=async()=>{
  if(!studio)return;
  const rail=studio.querySelector('.studio-command-rail');
  if(!rail)return;

  const sizeButton=rail.querySelector('.tile-size-button');
  if(sizeButton&&!sizeButton.querySelector('small')){
   const small=document.createElement('small');
   small.textContent='Asset Size';
   sizeButton.appendChild(small);
  }

  let state={placementMode:'Single',canUndo:false,selectedCount:0};
  try{state=await dotnet.invokeMethodAsync('GetWorldBuilderCommandState');}catch{}

  let placement=rail.querySelector('[data-wb-command="placement"]');
  if(!placement){
   placement=document.createElement('button');
   placement.type='button';
   placement.className='wb-injected-command';
   placement.dataset.wbCommand='placement';
   placement.innerHTML='<strong>Single</strong><small>Placement</small>';
   placement.addEventListener('click',async()=>{
    try{const mode=await dotnet.invokeMethodAsync('TogglePlacementModeFromJs');placement.querySelector('strong').textContent=mode;placement.classList.toggle('active',mode==='Multi');}catch{}
   });
   sizeButton?.insertAdjacentElement('afterend',placement);
  }
  const mode=state.placementMode||state.PlacementMode||'Single';
  placement.querySelector('strong').textContent=mode;
  placement.classList.toggle('active',mode==='Multi');

  let undo=rail.querySelector('[data-wb-command="undo"]');
  if(!undo){
   undo=document.createElement('button');undo.type='button';undo.className='wb-injected-command';undo.dataset.wbCommand='undo';
   undo.innerHTML='<strong>Undo</strong><small>Last Action</small>';
   undo.addEventListener('click',async()=>{try{await dotnet.invokeMethodAsync('UndoWorldBuilderFromJs');applySelection([]);await syncCommandControls();}catch{}});
   placement.insertAdjacentElement('afterend',undo);
  }
  const canUndo=state.canUndo??state.CanUndo??false;
  undo.disabled=!canUndo;

  let remove=rail.querySelector('[data-wb-command="remove"]');
  if(!remove){
   remove=document.createElement('button');remove.type='button';remove.className='wb-injected-command';remove.dataset.wbCommand='remove';
   remove.innerHTML='<strong>Remove Tile</strong><small>0 Selected</small>';
   remove.addEventListener('click',async()=>{try{const selected=await dotnet.invokeMethodAsync('RemoveSelectedTilesFromJs');applySelection(selected||[]);await syncCommandControls();}catch{}});
   undo.insertAdjacentElement('afterend',remove);
  }
  const selectedCount=state.selectedCount??state.SelectedCount??0;
  remove.disabled=selectedCount<1;
  remove.querySelector('small').textContent=`${selectedCount} Selected`;
 };

 const queueSync=()=>queueMicrotask(()=>syncCommandControls());
 commandObserver=new MutationObserver(queueSync);
 if(studio)commandObserver.observe(studio,{childList:true,subtree:true});
 queueSync();

 const applySelection=selected=>{
  if(!studio)return;
  const set=new Set((selected||[]).map(Number));
  const tiles=[...studio.querySelectorAll('.world-stage .tile-cell')];
  tiles.forEach((tile,index)=>tile.classList.toggle('wb-selected',set.has(index)));
 };

 const step=delta=>{if(!delta)return;dotnet.invokeMethodAsync('StepZ',delta).catch(()=>{});};
 const distance=()=>{const values=[...pointers.values()];if(values.length<2)return 0;const dx=values[0].x-values[1].x;const dy=values[0].y-values[1].y;return Math.hypot(dx,dy)};
 const onWheel=e=>{e.preventDefault();wheelAccumulator+=e.deltaY;if(Math.abs(wheelAccumulator)<70)return;const delta=wheelAccumulator>0?1:-1;wheelAccumulator=0;step(delta);};
 const onPointerDown=e=>{pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});if(pointers.size===2)pinchDistance=distance();};
 const onPointerMove=e=>{if(!pointers.has(e.pointerId))return;pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});if(pointers.size!==2)return;const next=distance();if(!pinchDistance){pinchDistance=next;return;}const ratio=next/pinchDistance;if(ratio>=1.16){step(-1);pinchDistance=next;}else if(ratio<=0.86){step(1);pinchDistance=next;}e.preventDefault();};
 const release=e=>{pointers.delete(e.pointerId);if(pointers.size<2)pinchDistance=0;};

 const quickIndexFor=button=>{
  if(!studio||!button)return -1;
  return [...studio.querySelectorAll('.quick-slot.filled')].indexOf(button);
 };

 const placeQuick=async(index,clientX,clientY)=>{
  if(index<0)return;
  try{const placed=await dotnet.invokeMethodAsync('PlaceQuickTileFromJs',index,clientX,clientY);if(placed){applySelection([]);await syncCommandControls();}}catch{}
 };

 const removeGhost=()=>{
  if(quickGhost){quickGhost.remove();quickGhost=null;}
 };
 const createGhost=(button,x,y)=>{
  removeGhost();
  quickGhost=document.createElement('div');
  quickGhost.className='wb-quick-drag-ghost';
  const img=button.querySelector('img');
  const label=button.querySelector('span');
  if(img){const ghostImg=document.createElement('img');ghostImg.src=img.src;ghostImg.alt='';quickGhost.appendChild(ghostImg);}
  if(label){const ghostLabel=document.createElement('span');ghostLabel.textContent=label.textContent||'';quickGhost.appendChild(ghostLabel);}
  quickGhost.style.left=`${x}px`;quickGhost.style.top=`${y}px`;
  document.body.appendChild(quickGhost);
 };
 const moveGhost=(x,y)=>{if(quickGhost){quickGhost.style.left=`${x}px`;quickGhost.style.top=`${y}px`;}};

 const onNativeDragStart=e=>{
  const button=e.target?.closest?.('.worldbuilder-studio .quick-slot.filled');
  if(!button)return;
  quickDragIndex=quickIndexFor(button);
 };
 const onNativeDrop=e=>{
  if(quickDragIndex<0)return;
  const viewer=e.target?.closest?.('.worldbuilder-studio .studio-viewer-canvas');
  if(!viewer)return;
  e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();
  const index=quickDragIndex;quickDragIndex=-1;
  placeQuick(index,e.clientX,e.clientY);
 };
 const onNativeDragEnd=()=>{quickDragIndex=-1;};

 const onQuickPointerDown=e=>{
  if(e.pointerType==='mouse')return;
  const button=e.target?.closest?.('.worldbuilder-studio .quick-slot.filled');
  if(!button)return;
  const index=quickIndexFor(button);
  if(index<0)return;
  e.preventDefault();e.stopPropagation();
  button.setPointerCapture?.(e.pointerId);
  button.classList.add('wb-grabbing');
  quickPointer={id:e.pointerId,startX:e.clientX,startY:e.clientY,moved:false,button,index};
 };
 const onQuickPointerMove=e=>{
  if(!quickPointer||e.pointerId!==quickPointer.id)return;
  const distance=Math.abs(e.clientX-quickPointer.startX)+Math.abs(e.clientY-quickPointer.startY);
  if(!quickPointer.moved&&distance>6){
   quickPointer.moved=true;
   createGhost(quickPointer.button,e.clientX,e.clientY);
  }
  if(quickPointer.moved)moveGhost(e.clientX,e.clientY);
  e.preventDefault();e.stopPropagation();
 };
 const finishQuickPointer=(e,place)=>{
  if(!quickPointer||e.pointerId!==quickPointer.id)return;
  const current=quickPointer;quickPointer=null;
  current.button.classList.remove('wb-grabbing');
  current.button.releasePointerCapture?.(e.pointerId);
  removeGhost();
  if(place&&current.moved)placeQuick(current.index,e.clientX,e.clientY);
 };
 const onQuickPointerUp=e=>{
  if(!quickPointer||e.pointerId!==quickPointer.id)return;
  e.preventDefault();e.stopPropagation();
  finishQuickPointer(e,true);
 };
 const onQuickPointerCancel=e=>finishQuickPointer(e,false);

 const onSelectPointerDown=e=>{
  const tile=e.target?.closest?.('.worldbuilder-studio .world-stage .tile-cell');
  if(!tile)return;
  selectionPointer={id:e.pointerId,x:e.clientX,y:e.clientY,tile};
 };
 const onSelectPointerUp=async e=>{
  if(!selectionPointer||e.pointerId!==selectionPointer.id)return;
  const current=selectionPointer;selectionPointer=null;
  if(Math.abs(e.clientX-current.x)+Math.abs(e.clientY-current.y)>8)return;
  const tiles=[...studio.querySelectorAll('.world-stage .tile-cell')];
  const index=tiles.indexOf(current.tile);if(index<0)return;
  try{
   const additive=!!(e.shiftKey||e.ctrlKey||e.metaKey);
   const selected=await dotnet.invokeMethodAsync('TogglePlacedTileSelection',index,additive);
   applySelection(selected||[]);
   await syncCommandControls();
  }catch{}
 };

 element.addEventListener('wheel',onWheel,{passive:false});
 element.addEventListener('pointerdown',onPointerDown,{passive:true});
 element.addEventListener('pointermove',onPointerMove,{passive:false});
 element.addEventListener('pointerup',release,{passive:true});
 element.addEventListener('pointercancel',release,{passive:true});
 document.addEventListener('dragstart',onNativeDragStart,true);
 document.addEventListener('drop',onNativeDrop,true);
 document.addEventListener('dragend',onNativeDragEnd,true);
 document.addEventListener('pointerdown',onQuickPointerDown,{capture:true,passive:false});
 document.addEventListener('pointermove',onQuickPointerMove,{capture:true,passive:false});
 document.addEventListener('pointerup',onQuickPointerUp,{capture:true,passive:false});
 document.addEventListener('pointercancel',onQuickPointerCancel,true);
 document.addEventListener('pointerdown',onSelectPointerDown,true);
 document.addEventListener('pointerup',onSelectPointerUp,true);

 return {dispose(){
  element.removeEventListener('wheel',onWheel);
  element.removeEventListener('pointerdown',onPointerDown);
  element.removeEventListener('pointermove',onPointerMove);
  element.removeEventListener('pointerup',release);
  element.removeEventListener('pointercancel',release);
  document.removeEventListener('dragstart',onNativeDragStart,true);
  document.removeEventListener('drop',onNativeDrop,true);
  document.removeEventListener('dragend',onNativeDragEnd,true);
  document.removeEventListener('pointerdown',onQuickPointerDown,true);
  document.removeEventListener('pointermove',onQuickPointerMove,true);
  document.removeEventListener('pointerup',onQuickPointerUp,true);
  document.removeEventListener('pointercancel',onQuickPointerCancel,true);
  document.removeEventListener('pointerdown',onSelectPointerDown,true);
  document.removeEventListener('pointerup',onSelectPointerUp,true);
  commandObserver?.disconnect();
  pointers.clear();quickPointer=null;selectionPointer=null;quickDragIndex=-1;
  removeGhost();
  if(quickDropCleanup)quickDropCleanup();
  const style=document.getElementById(styleId);if(style)style.remove();
 }};
}
