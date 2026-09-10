let bridge=null;
let observer=null;
let style=null;
let pointers=new Map();
let panX=0;
let panY=0;
let navigationMode=true;
let requestedNavigationMode=true;
let syncQueued=false;

function studio(){return document.querySelector('.worldbuilder-studio');}
function viewer(){return studio()?.querySelector('.studio-viewer-canvas');}
function stage(){return studio()?.querySelector('.world-stage');}
function tileList(){return [...(stage()?.querySelectorAll(':scope > .tile-cell')||[])];}

function queueSync(){
 if(syncQueued)return;
 syncQueued=true;
 requestAnimationFrame(()=>{syncQueued=false;syncMode();});
}

function ensureStyle(){
 if(style)return;
 style=document.createElement('style');
 style.id='rist-worldbuilder-view-fix';
 style.textContent=`
  .worldbuilder-studio.wb-z-unlocked .studio-viewer-canvas .world-stage{
   transform:translate(var(--wb-pan-x,0px),var(--wb-pan-y,0px)) scale(var(--wb-z-scale,1))!important;
   transform-origin:center center!important;
  }
  .worldbuilder-studio.wb-z-unlocked .tile-edit-overlay{display:none!important}
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
  .worldbuilder-studio .world-stage .tile-cell.wb-selected{
   outline:3px solid #f2cf72!important;
   outline-offset:-3px!important;
   box-shadow:inset 0 0 0 2px rgba(12,30,40,.85)!important;
   z-index:214748!important;
  }
  .wb-underlay-host{position:absolute;inset:0;z-index:1;pointer-events:none;overflow:hidden}
  .wb-underlay-tile{position:absolute;box-sizing:border-box;overflow:hidden;pointer-events:none;border:0;outline:0}
  .wb-underlay-tile>.wb-underlay-crop{position:absolute;inset:0;display:block;overflow:hidden;line-height:0}
  .wb-underlay-tile img{position:absolute;display:block;max-width:none;max-height:none;border:0;outline:0;transform-origin:center center;pointer-events:none;-webkit-user-drag:none;-webkit-touch-callout:none}
  .wb-quick-drag-ghost{transform:translate(calc(-50% + var(--wb-thumb-side,70px)),calc(-50% - 88px)) scale(1.06)!important}
 `;
 document.head.appendChild(style);
 document.querySelectorAll('[data-wb-select="true"]').forEach(node=>node.remove());
}

function syncMode(){
 navigationMode=requestedNavigationMode;
 const root=studio();
 if(!root)return;
 root.classList.toggle('wb-z-unlocked',navigationMode);
 root.classList.remove('wb-select-mode');
 root.querySelectorAll('[data-wb-select="true"]').forEach(node=>node.remove());
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

function cropStyle(tile){
 const sourceWidth=Number(tile.sourceWidth??tile.SourceWidth??0);
 const sourceHeight=Number(tile.sourceHeight??tile.SourceHeight??0);
 const cropX=Number(tile.cropX??tile.CropX??0);
 const cropY=Number(tile.cropY??tile.CropY??0);
 const cropWidth=Number(tile.cropWidth??tile.CropWidth??0);
 const cropHeight=Number(tile.cropHeight??tile.CropHeight??0);
 if(sourceWidth<=0||sourceHeight<=0||cropWidth<=0||cropHeight<=0)return null;
 return {width:`${sourceWidth*100/cropWidth}%`,height:`${sourceHeight*100/cropHeight}%`,left:`${-cropX*100/cropWidth}%`,top:`${-cropY*100/cropHeight}%`};
}

export function renderUnderlay(tiles,currentSceneZ){
 ensureStyle();
 syncMode();
 const s=stage();
 if(!s)return;
 s.querySelector(':scope > .wb-underlay-host')?.remove();
 if(!navigationMode||!Array.isArray(tiles)||tiles.length===0)return;
 const host=document.createElement('div');
 host.className='wb-underlay-host';
 host.setAttribute('aria-hidden','true');
 const current=Number(currentSceneZ||0);
 for(const tile of tiles){
  const zoom=Math.max(Number(tile.placementZoom??tile.PlacementZoom??1),1/300);
  const cell=document.createElement('div');
  cell.className='wb-underlay-tile';
  cell.style.left=`${Number(tile.x??tile.X??0)*100}%`;
  cell.style.top=`${Number(tile.y??tile.Y??0)*100}%`;
  cell.style.width=`${100/30/zoom}%`;
  cell.style.height=`${100/30/zoom}%`;
  const sceneZ=Number(tile.sceneZ??tile.SceneZ??0);
  const depth=Math.max(1,current-sceneZ);
  cell.style.opacity=String(Math.max(.42,.94-Math.min(depth,14)*.03));
  const crop=document.createElement('span');crop.className='wb-underlay-crop';
  const img=document.createElement('img');img.src=tile.image??tile.Image??'';img.alt='';
  const css=cropStyle(tile);if(css)Object.assign(img.style,css);else{img.style.width='100%';img.style.height='100%';}
  const turns=Number(tile.rotationQuarterTurns??tile.RotationQuarterTurns??0);img.style.transform=`rotate(${turns*90}deg)`;
  crop.appendChild(img);cell.appendChild(crop);host.appendChild(cell);
 }
 const firstCurrent=s.querySelector(':scope > .tile-cell');
 if(firstCurrent)s.insertBefore(host,firstCurrent);else s.appendChild(host);
}

export function attach(dotnet){
 bridge=dotnet;ensureStyle();syncMode();
 document.addEventListener('pointerdown',onPointerDown,true);
 document.addEventListener('pointermove',onPointerMove,true);
 document.addEventListener('pointerup',release,true);
 document.addEventListener('pointercancel',cancel,true);
 document.addEventListener('wheel',onWheel,{capture:true,passive:false});
 document.addEventListener('contextmenu',onContextMenu,true);
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
 observer?.disconnect();observer=null;pointers.clear();syncQueued=false;
 document.querySelectorAll('.wb-underlay-host,[data-wb-select="true"]').forEach(node=>node.remove());
 document.querySelector('.worldbuilder-studio')?.classList.remove('wb-z-unlocked','wb-select-mode');
 style?.remove();style=null;bridge=null;requestedNavigationMode=true;navigationMode=true;
}
