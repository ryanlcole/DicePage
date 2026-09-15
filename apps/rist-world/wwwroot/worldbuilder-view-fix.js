let bridge=null;
let observer=null;
let style=null;
let pointers=new Map();
let panX=0;
let panY=0;
let navigationMode=true;
let requestedNavigationMode=true;
let syncQueued=false;
let lastLayerFrame=null;
let lastSceneZ=0;

function studio(){return document.querySelector('.worldbuilder-studio');}
function viewer(){return studio()?.querySelector('.studio-viewer-canvas');}
function stage(){return studio()?.querySelector('.world-stage');}
function tileList(){return [...(stage()?.querySelectorAll(':scope > .tile-cell')||[])];}
function pieceList(){return [...(stage()?.querySelectorAll(':scope > .piece')||[])];}

function queueSync(){
 if(syncQueued)return;
 syncQueued=true;
 requestAnimationFrame(()=>{
  syncQueued=false;
  syncMode();
  if(lastLayerFrame)applyZPlane(lastLayerFrame,lastSceneZ);
 });
}

function ensureStyle(){
 if(style)return;
 style=document.createElement('style');
 style.id='rist-worldbuilder-view-fix';
 style.textContent=`
  .worldbuilder-studio.wb-z-unlocked .tile-edit-overlay{display:none!important}
  .worldbuilder-studio .studio-viewer-grid{visibility:hidden!important;opacity:0!important;pointer-events:none!important}
  .worldbuilder-studio.wb-grid-visible .studio-viewer-canvas .world-stage::after{
   content:"";
   position:absolute;
   inset:var(--viewer-frame);
   z-index:20;
   pointer-events:none;
   box-sizing:border-box;
   border:1px solid rgba(215,199,145,.64);
   background-color:transparent;
   background-image:
    linear-gradient(to right,rgba(215,199,145,.52) 1px,transparent 1px),
    linear-gradient(to bottom,rgba(215,199,145,.52) 1px,transparent 1px);
   background-size:calc((100cqw - (2 * var(--viewer-frame))) / 30) calc((100cqw - (2 * var(--viewer-frame))) / 30);
   background-position:0 0;
   background-repeat:repeat;
  }
  .worldbuilder-studio .studio-viewer-canvas .world-stage .tile-cell{
   pointer-events:none!important;
   cursor:default!important;
   -webkit-user-select:none!important;
   user-select:none!important;
   -webkit-touch-callout:none!important;
  }
  .worldbuilder-studio .studio-viewer-canvas .world-stage .tile-cell::after{
   box-shadow:none!important;border:0!important;outline:0!important
  }
  .worldbuilder-studio .studio-viewer-canvas .world-stage .tile-cell img,
  .worldbuilder-studio .studio-viewer-canvas .world-stage .tile-cell .tile-image-crop{
   pointer-events:none!important;
   -webkit-user-select:none!important;
   user-select:none!important;
   -webkit-user-drag:none!important;
   -webkit-touch-callout:none!important;
  }
  .worldbuilder-studio .world-stage .tile-cell.wb-layer-lower{z-index:10!important}
  .worldbuilder-studio .world-stage .tile-cell.wb-layer-current{z-index:30!important}
  .worldbuilder-studio .world-stage .tile-cell.wb-layer-higher{display:none!important}
  .worldbuilder-studio .world-stage .piece.wb-layer-lower{z-index:11!important}
  .worldbuilder-studio .world-stage .piece.wb-layer-current{z-index:31!important}
  .worldbuilder-studio .world-stage .piece.wb-layer-higher{display:none!important}
  .worldbuilder-studio .world-stage .tile-cell.wb-selected{
   outline:3px solid #f2cf72!important;
   outline-offset:-3px!important;
   box-shadow:inset 0 0 0 2px rgba(12,30,40,.85)!important;
  }
  .worldbuilder-studio .world-stage .tile-cell.wb-layer-lower.wb-selected{z-index:12!important}
  .worldbuilder-studio .world-stage .tile-cell.wb-layer-current.wb-selected{z-index:32!important}
  .worldbuilder-studio .studio-command-rail .wb-grid-control{order:-2!important}
  .wb-quick-drag-ghost{transform:translate(calc(-50% + var(--wb-thumb-side,70px)),calc(-50% - 88px)) scale(1.06)!important}
 `;
 document.head.appendChild(style);
 document.querySelectorAll('[data-wb-select="true"]').forEach(node=>node.remove());
}

function markGridControl(){
 const root=studio();
 if(!root)return;
 root.querySelectorAll('.studio-command-rail button').forEach(button=>{
  const label=button.querySelector(':scope > strong')?.textContent?.trim();
  button.classList.toggle('wb-grid-control',label==='View');
 });
}

function syncGridVisibility(){
 const root=studio();
 if(!root)return;
 const legacyGrid=root.querySelector('.studio-viewer-grid');
 const visible=!legacyGrid||!legacyGrid.classList.contains('off');
 root.classList.toggle('wb-grid-visible',visible);
}

function syncMode(){
 navigationMode=requestedNavigationMode;
 const root=studio();
 if(!root)return;
 root.classList.toggle('wb-z-unlocked',navigationMode);
 root.classList.remove('wb-select-mode');
 root.querySelectorAll('[data-wb-select="true"]').forEach(node=>node.remove());
 syncGridVisibility();
 markGridControl();
 const s=stage();
 if(s){
  s.style.setProperty('--wb-pan-x',`${panX}px`);
  s.style.setProperty('--wb-pan-y',`${panY}px`);
 }
}

export function setNavigationMode(enabled){
 requestedNavigationMode=!!enabled;
 if(!requestedNavigationMode)pointers.clear();
 syncMode();
}

function blockedTarget(target){
 return !!target?.closest?.('.studio-mini-panel,.studio-load-panel,.studio-library-shade,.recursion-cockpit,.desktop-map-zoom');
}

function viewerPoint(clientX,clientY){
 const s=stage();
 if(!s)return null;
 const rect=s.getBoundingClientRect();
 if(rect.width<1||rect.height<1)return null;
 const x=(clientX-rect.left)/rect.width;
 const y=(clientY-rect.top)/rect.height;
 if(x<0||x>1||y<0||y>1)return null;
 return [x,y];
}

function applySelection(selected){
 const set=new Set((selected||[]).map(Number));
 tileList().forEach((tile,index)=>tile.classList.toggle('wb-selected',set.has(index)));
 const root=studio();
 if(!root)return;
 for(const name of ['rotate','resize','remove']){
  const button=root.querySelector(`[data-wb-command="${name}"]`);
  if(button)button.disabled=set.size<1;
 }
 const remove=root.querySelector('[data-wb-command="remove"] small');
 if(remove)remove.textContent=`${set.size} Selected`;
}

async function pickAt(clientX,clientY,additive=false){
 if(!bridge)return;
 const point=viewerPoint(clientX,clientY);
 if(!point){
  if(!additive)applySelection([]);
  return;
 }
 try{
  const selected=await bridge.invokeMethodAsync('SelectPlacedTileAtWorldPoint',point[0],point[1],!!additive);
  applySelection(selected||[]);
 }catch{}
}

function onPointerDown(event){
 syncMode();
 const v=viewer();
 if(!v||!v.contains(event.target)||blockedTarget(event.target))return;
 pointers.set(event.pointerId,{
  x:event.clientX,y:event.clientY,
  startX:event.clientX,startY:event.clientY,
  moved:false,
  additive:!!(event.shiftKey||event.ctrlKey||event.metaKey)
 });
 if(navigationMode){
  event.preventDefault();
  event.stopPropagation();
 }
}

function onPointerMove(event){
 const ghost=document.querySelector('.wb-quick-drag-ghost');
 if(ghost)ghost.style.setProperty('--wb-thumb-side',event.clientX<window.innerWidth/2?'70px':'-70px');
 const current=pointers.get(event.pointerId);
 if(!current)return;
 const dx=event.clientX-current.x;
 const dy=event.clientY-current.y;
 current.x=event.clientX;current.y=event.clientY;
 if(Math.abs(event.clientX-current.startX)+Math.abs(event.clientY-current.startY)>8)current.moved=true;
 if(navigationMode&&pointers.size===1&&current.moved){
  panX+=dx;panY+=dy;syncMode();
  event.preventDefault();
  event.stopPropagation();
 }
}

function release(event){
 const current=pointers.get(event.pointerId);
 if(!current)return;
 pointers.delete(event.pointerId);
 if(!current.moved){
  event.preventDefault();
  event.stopPropagation();
  event.stopImmediatePropagation();
  void pickAt(event.clientX,event.clientY,current.additive);
  return;
 }
 if(navigationMode){event.preventDefault();event.stopPropagation();}
}

function cancel(event){pointers.delete(event.pointerId);}

function onWheel(event){
 const v=viewer();
 if(!v||!navigationMode||!v.contains(event.target)||blockedTarget(event.target))return;
 event.stopPropagation();
}

function onContextMenu(event){
 const v=viewer();
 if(!v||!v.contains(event.target))return;
 event.preventDefault();
 event.stopPropagation();
 event.stopImmediatePropagation();
}

function onClick(event){
 const button=event.target?.closest?.('.studio-command-rail button');
 if(button?.querySelector(':scope > strong')?.textContent?.trim()==='View'){
  requestAnimationFrame(()=>{syncGridVisibility();if(lastLayerFrame)applyZPlane(lastLayerFrame,lastSceneZ);});
 }
}

function layerItems(frame,key){
 return frame?.[key]??frame?.[key[0].toUpperCase()+key.slice(1)]??[];
}

function layerValue(item,key,fallback){
 const value=item?.[key]??item?.[key[0].toUpperCase()+key.slice(1)];
 const number=Number(value);
 return Number.isFinite(number)?number:fallback;
}

function classifyLayer(node,sceneZ,currentSceneZ){
 node.classList.remove('wb-layer-lower','wb-layer-current','wb-layer-higher');
 if(sceneZ<currentSceneZ)node.classList.add('wb-layer-lower');
 else if(sceneZ>currentSceneZ)node.classList.add('wb-layer-higher');
 else node.classList.add('wb-layer-current');
}

function applyZPlane(frame,currentSceneZ){
 syncGridVisibility();
 const current=Number(currentSceneZ||0);
 const tiles=layerItems(frame,'tiles');
 const pieces=layerItems(frame,'pieces');
 const tileDepth=new Map(tiles.map((item,index)=>[layerValue(item,'index',index),layerValue(item,'sceneZ',current)]));
 const pieceDepth=new Map(pieces.map((item,index)=>[layerValue(item,'index',index),layerValue(item,'sceneZ',current)]));

 tileList().forEach((node,index)=>classifyLayer(node,tileDepth.get(index)??current,current));
 pieceList().forEach((node,index)=>classifyLayer(node,pieceDepth.get(index)??current,current));
}

export function renderZPlane(frame,currentSceneZ){
 ensureStyle();
 lastLayerFrame=frame??null;
 lastSceneZ=Number(currentSceneZ||0);
 syncMode();
 if(lastLayerFrame)applyZPlane(lastLayerFrame,lastSceneZ);
}

export function attach(dotnet){
 if(dotnet)bridge=dotnet;
 ensureStyle();
 syncMode();
 document.addEventListener('pointerdown',onPointerDown,true);
 document.addEventListener('pointermove',onPointerMove,true);
 document.addEventListener('pointerup',release,true);
 document.addEventListener('pointercancel',cancel,true);
 document.addEventListener('wheel',onWheel,{capture:true,passive:false});
 document.addEventListener('contextmenu',onContextMenu,true);
 document.addEventListener('click',onClick,true);
 observer=new MutationObserver(queueSync);
 observer.observe(document.body,{childList:true,subtree:true});
 return true;
}

export function dispose(){
 document.removeEventListener('pointerdown',onPointerDown,true);
 document.removeEventListener('pointermove',onPointerMove,true);
 document.removeEventListener('pointerup',release,true);
 document.removeEventListener('pointercancel',cancel,true);
 document.removeEventListener('wheel',onWheel,true);
 document.removeEventListener('contextmenu',onContextMenu,true);
 document.removeEventListener('click',onClick,true);
 observer?.disconnect();observer=null;pointers.clear();syncQueued=false;
 document.querySelectorAll('[data-wb-select="true"]').forEach(node=>node.remove());
 document.querySelector('.worldbuilder-studio')?.classList.remove('wb-z-unlocked','wb-select-mode','wb-grid-visible');
 tileList().forEach(node=>node.classList.remove('wb-layer-lower','wb-layer-current','wb-layer-higher','wb-selected'));
 pieceList().forEach(node=>node.classList.remove('wb-layer-lower','wb-layer-current','wb-layer-higher'));
 style?.remove();style=null;bridge=null;requestedNavigationMode=true;navigationMode=true;lastLayerFrame=null;lastSceneZ=0;
}
