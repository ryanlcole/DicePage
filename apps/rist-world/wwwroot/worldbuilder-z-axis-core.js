let quickDropCleanup=null;

export function viewerPoint(element,clientX,clientY){
 if(!element)return null;
 const rect=element.getBoundingClientRect();
 if(rect.width<1||rect.height<1)return null;
 const x=(clientX-rect.left)/rect.width,y=(clientY-rect.top)/rect.height;
 return x<0||x>1||y<0||y>1?null:[x,y];
}

export function viewerGridPoint(element,clientX,clientY){
 if(!element)return null;
 const target=element.querySelector('.world-stage')||element.querySelector('.studio-viewer-grid')||element;
 const rect=target.getBoundingClientRect();
 if(rect.width<1||rect.height<1)return null;
 const x=(clientX-rect.left)/rect.width,y=(clientY-rect.top)/rect.height;
 return x<0||x>1||y<0||y>1?null:[x,y];
}

export function beginQuickPointerDrop(dotnet,pointerId){
 if(quickDropCleanup)quickDropCleanup();
 const finish=()=>{document.removeEventListener('pointerup',up,true);document.removeEventListener('pointercancel',cancel,true);quickDropCleanup=null};
 const up=e=>{if(e.pointerId!==pointerId)return;finish();dotnet?.invokeMethodAsync('QuickPointerDrop',e.clientX,e.clientY).catch(()=>{})};
 const cancel=e=>{if(e.pointerId!==pointerId)return;finish()};
 document.addEventListener('pointerup',up,true);document.addEventListener('pointercancel',cancel,true);quickDropCleanup=finish;
}

export function attach(element,dotnet){
 if(!element)return{dispose(){}};
 const studio=element.closest('.worldbuilder-studio');
 let quickPointer=null,quickDragIndex=-1,quickGhost=null,commandObserver=null,syncing=false,disposed=false;
 const styleId='rist-worldbuilder-placement-interactions';
 window.RistWorldBuilderStudioDotNet=dotnet;
 try{window.dispatchEvent(new CustomEvent('rist:worldbuilder-dotnet-ready',{detail:{dotnet}}))}catch{}
 let style=document.getElementById(styleId);
 if(!style){
  style=document.createElement('style');style.id=styleId;style.textContent=`
   .worldbuilder-studio .quick-slot.filled,.worldbuilder-studio .quick-slot.filled *{-webkit-user-select:none!important;user-select:none!important;-webkit-touch-callout:none!important;touch-action:none!important}
   .worldbuilder-studio .quick-slot.filled.wb-grabbing{transform:scale(.96);opacity:.72;border-color:#f2cf72!important}
   .wb-quick-drag-ghost{position:fixed!important;z-index:2147483000!important;pointer-events:none!important;width:84px;height:64px;border:2px solid #f2cf72;border-radius:10px;overflow:hidden;background:#0d171e;box-shadow:0 10px 28px #000b;transform:translate(-50%,-50%) scale(1.06)}
   .wb-quick-drag-ghost img{width:100%;height:100%;object-fit:cover;display:block}.wb-quick-drag-ghost span{position:absolute;left:0;right:0;bottom:0;padding:4px;background:#000c;color:#fff1bd;font:800 9px/1 system-ui;text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
   .worldbuilder-studio .studio-command-rail .wb-injected-command{box-sizing:border-box;flex:0 0 auto;height:48px;min-width:104px;padding:4px 12px;display:grid;place-items:center;gap:2px;border:1px solid #4b5f69;border-radius:9px;background:#0d171e;color:#d4dde1;touch-action:manipulation}
   .worldbuilder-studio .studio-command-rail .wb-injected-command strong{font:900 12px/1 system-ui;color:#f0ddb0}.worldbuilder-studio .studio-command-rail .wb-injected-command small{font:800 7px/1 system-ui;letter-spacing:.06em;text-transform:uppercase;color:#8fa5b0}.worldbuilder-studio .studio-command-rail .wb-injected-command:disabled{opacity:.38}
   .worldbuilder-studio .studio-command-rail .tile-size-button small{display:block;font:800 7px/1 system-ui;letter-spacing:.06em;text-transform:uppercase;color:#8fa5b0}
   @media(max-width:760px){.worldbuilder-studio .studio-command-rail .wb-injected-command{height:44px;min-width:94px;padding:4px 9px}}
  `;document.head.appendChild(style);
 }
 const tiles=()=>studio?[...studio.querySelectorAll('.world-stage .tile-cell')]:[];
 const tileIndex=(tile,fallback)=>{const value=Number(tile?.dataset?.wbIndex);return Number.isInteger(value)&&value>=0?value:fallback};
 const applySelection=selected=>{const set=new Set((selected||[]).map(Number));tiles().forEach((tile,index)=>tile.classList.toggle('wb-selected',set.has(tileIndex(tile,index))));return[...set]};
 const applyVisuals=async()=>{try{const visuals=await dotnet.invokeMethodAsync('GetWorldBuilderTileVisuals');const rotations=new Map((visuals||[]).map(v=>[Number(v.index??v.Index),Number(v.rotationQuarterTurns??v.RotationQuarterTurns??0)]));tiles().forEach((tile,index)=>{const sessionIndex=tileIndex(tile,index);tile.style.setProperty('--wb-rotation',`${((rotations.get(sessionIndex)||0)%4+4)%4*90}deg`)})}catch{}};
 const rail=()=>studio?.querySelector('.studio-command-rail');
 async function syncCommands(){
  if(disposed||syncing)return;syncing=true;
  try{
   const host=rail();if(!host)return;
   const size=host.querySelector('.tile-size-button');if(size&&!size.querySelector('small')){const small=document.createElement('small');small.textContent='Tile Size';size.appendChild(small)}
   let state={canUndo:false,selectedCount:0};try{state=await dotnet.invokeMethodAsync('GetWorldBuilderCommandState')}catch{}
   const make=(name,title,small,after,action)=>{let b=host.querySelector(`[data-wb-command="${name}"]`);if(!b){b=document.createElement('button');b.type='button';b.className='wb-injected-command';b.dataset.wbCommand=name;b.innerHTML=`<strong>${title}</strong><small>${small}</small>`;b.addEventListener('click',action);if(after)after.insertAdjacentElement('afterend',b);else host.appendChild(b)}return b};
   const undo=make('undo','Undo','Last Action',size,async()=>{try{await dotnet.invokeMethodAsync('UndoWorldBuilderFromJs');applySelection([]);await applyVisuals();await syncCommands()}catch{}});
   const rotate=make('rotate','Rotate 90°','Selected',undo,async()=>{try{applySelection(await dotnet.invokeMethodAsync('RotateSelectedTilesFromJs')||[]);await applyVisuals();await syncCommands()}catch{}});
   const resize=make('resize','Resize','To Tile Size',rotate,async()=>{try{applySelection(await dotnet.invokeMethodAsync('ResizeSelectedTilesFromJs')||[]);await applyVisuals();await syncCommands()}catch{}});
   const remove=make('remove','Remove Tile','0 Selected',resize,async()=>{try{applySelection(await dotnet.invokeMethodAsync('RemoveSelectedTilesFromJs')||[]);await applyVisuals();await syncCommands()}catch{}});
   const count=Number(state.selectedCount??state.SelectedCount??0);undo.disabled=!(state.canUndo??state.CanUndo??false);rotate.disabled=count<1;resize.disabled=count<1;remove.disabled=count<1;remove.querySelector('small').textContent=`${count} Selected`;
   await applyVisuals();
  }finally{syncing=false}
 }
 const queueSync=()=>queueMicrotask(syncCommands);
 commandObserver=new MutationObserver(queueSync);if(studio)commandObserver.observe(studio,{childList:true,subtree:true});queueSync();

 const quickIndexFor=button=>{const value=button?.dataset?.quickIndex;if(value==null||value==='')return -1;const index=Number(value);return Number.isInteger(index)&&index>=0?index:-1;};
 const placeQuick=async(index,x,y)=>{if(index<0)return;try{if(await dotnet.invokeMethodAsync('PlaceQuickTileFromJs',index,x,y)){applySelection([]);await applyVisuals();await syncCommands()}}catch{}};
 const removeGhost=()=>{quickGhost?.remove();quickGhost=null};
 const createGhost=(button,x,y)=>{removeGhost();quickGhost=document.createElement('div');quickGhost.className='wb-quick-drag-ghost';const img=button.querySelector('img'),label=button.querySelector('span');if(img){const copy=document.createElement('img');copy.src=img.src;copy.alt='';quickGhost.appendChild(copy)}if(label){const text=document.createElement('span');text.textContent=label.textContent||'';quickGhost.appendChild(text)}quickGhost.style.left=`${x}px`;quickGhost.style.top=`${y}px`;document.body.appendChild(quickGhost)};
 const onNativeDragStart=e=>{const b=e.target?.closest?.('.worldbuilder-studio .quick-slot.filled');if(b)quickDragIndex=quickIndexFor(b)};
 const onNativeDrop=e=>{if(quickDragIndex<0)return;const view=e.target?.closest?.('.worldbuilder-studio .studio-viewer-canvas');if(!view)return;e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();const i=quickDragIndex;quickDragIndex=-1;void placeQuick(i,e.clientX,e.clientY)};
 const onNativeDragEnd=()=>{quickDragIndex=-1};
 const onQuickDown=e=>{if(e.pointerType==='mouse')return;const b=e.target?.closest?.('.worldbuilder-studio .quick-slot.filled');if(!b)return;const index=quickIndexFor(b);if(index<0)return;e.preventDefault();e.stopPropagation();b.setPointerCapture?.(e.pointerId);b.classList.add('wb-grabbing');quickPointer={id:e.pointerId,startX:e.clientX,startY:e.clientY,moved:false,button:b,index}};
 const onQuickMove=e=>{if(!quickPointer||e.pointerId!==quickPointer.id)return;const d=Math.abs(e.clientX-quickPointer.startX)+Math.abs(e.clientY-quickPointer.startY);if(!quickPointer.moved&&d>6){quickPointer.moved=true;createGhost(quickPointer.button,e.clientX,e.clientY)}if(quickPointer.moved){quickGhost.style.left=`${e.clientX}px`;quickGhost.style.top=`${e.clientY}px`}e.preventDefault();e.stopPropagation()};
 const finishQuick=(e,place)=>{if(!quickPointer||e.pointerId!==quickPointer.id)return;const q=quickPointer;quickPointer=null;q.button.classList.remove('wb-grabbing');q.button.releasePointerCapture?.(e.pointerId);removeGhost();if(place&&q.moved)void placeQuick(q.index,e.clientX,e.clientY)};
 const onQuickUp=e=>{if(!quickPointer||e.pointerId!==quickPointer.id)return;e.preventDefault();e.stopPropagation();finishQuick(e,true)};
 const onQuickCancel=e=>finishQuick(e,false);
 document.addEventListener('dragstart',onNativeDragStart,true);document.addEventListener('drop',onNativeDrop,true);document.addEventListener('dragend',onNativeDragEnd,true);
 document.addEventListener('pointerdown',onQuickDown,{capture:true,passive:false});document.addEventListener('pointermove',onQuickMove,{capture:true,passive:false});document.addEventListener('pointerup',onQuickUp,{capture:true,passive:false});document.addEventListener('pointercancel',onQuickCancel,true);

 return{dispose(){disposed=true;commandObserver?.disconnect();document.removeEventListener('dragstart',onNativeDragStart,true);document.removeEventListener('drop',onNativeDrop,true);document.removeEventListener('dragend',onNativeDragEnd,true);document.removeEventListener('pointerdown',onQuickDown,true);document.removeEventListener('pointermove',onQuickMove,true);document.removeEventListener('pointerup',onQuickUp,true);document.removeEventListener('pointercancel',onQuickCancel,true);quickPointer=null;quickDragIndex=-1;removeGhost();if(quickDropCleanup)quickDropCleanup();if(window.RistWorldBuilderStudioDotNet===dotnet)window.RistWorldBuilderStudioDotNet=null;document.getElementById(styleId)?.remove()}};
}
