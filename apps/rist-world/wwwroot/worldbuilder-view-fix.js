let bridge=null;
let observer=null;
let style=null;
let pointers=new Map();
let panX=0;
let panY=0;
let navigationMode=false;
let explicitMode=null;

function studio(){return document.querySelector('.worldbuilder-studio');}
function viewer(){return studio()?.querySelector('.studio-viewer-canvas');}
function stage(){return studio()?.querySelector('.world-stage');}
function uiNavigationMode(){
 const root=studio();
 if(!root)return false;
 const button=[...root.querySelectorAll('.studio-command-rail button')]
  .find(node=>node.querySelector('strong')?.textContent?.trim()==='Z-Lock');
 return button?.querySelector('small')?.textContent?.trim()==='Unlocked';
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
  .worldbuilder-studio.wb-z-unlocked .world-stage .tile-cell{pointer-events:none!important;cursor:default!important}
  .worldbuilder-studio.wb-z-unlocked .tile-edit-overlay{display:none!important}
  .wb-underlay-host{position:absolute;inset:0;z-index:1;pointer-events:none;overflow:hidden}
  .wb-underlay-tile{position:absolute;box-sizing:border-box;overflow:hidden;pointer-events:none;border:0;outline:0}
  .wb-underlay-tile>.wb-underlay-crop{position:absolute;inset:0;display:block;overflow:hidden;line-height:0}
  .wb-underlay-tile img{position:absolute;display:block;max-width:none;max-height:none;border:0;outline:0;transform-origin:center center}
  .wb-quick-drag-ghost{transform:translate(calc(-50% + var(--wb-thumb-side,70px)),calc(-50% - 88px)) scale(1.06)!important}
 `;
 document.head.appendChild(style);
}

function syncMode(){
 navigationMode=explicitMode??uiNavigationMode();
 const root=studio();
 if(!root)return;
 root.classList.toggle('wb-z-unlocked',navigationMode);
 const s=stage();
 if(s){
  s.style.setProperty('--wb-pan-x',`${panX}px`);
  s.style.setProperty('--wb-pan-y',`${panY}px`);
 }
}

export function setNavigationMode(enabled){
 explicitMode=!!enabled;
 navigationMode=explicitMode;
 if(!navigationMode)pointers.clear();
 syncMode();
}

function shouldHandle(event){
 const v=viewer();
 if(!v||!navigationMode)return false;
 if(!v.contains(event.target))return false;
 if(event.target?.closest?.('.studio-mini-panel,.studio-load-panel,.studio-library-shade,.recursion-cockpit'))return false;
 return true;
}

function onPointerDown(event){
 syncMode();
 if(!shouldHandle(event))return;
 pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
 event.preventDefault();
 event.stopPropagation();
}

function onPointerMove(event){
 const ghost=document.querySelector('.wb-quick-drag-ghost');
 if(ghost)ghost.style.setProperty('--wb-thumb-side',event.clientX<window.innerWidth/2?'70px':'-70px');
 if(!pointers.has(event.pointerId)||!navigationMode)return;
 const before=pointers.get(event.pointerId);
 pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
 if(pointers.size===1){
  panX+=event.clientX-before.x;
  panY+=event.clientY-before.y;
  syncMode();
 }
 event.preventDefault();
 event.stopPropagation();
}

function release(event){
 if(!pointers.has(event.pointerId))return;
 pointers.delete(event.pointerId);
 if(navigationMode){event.preventDefault();event.stopPropagation();}
}

function onWheel(event){
 syncMode();
 if(!shouldHandle(event))return;
 // worldbuilder-z-axis owns continuous scale and layer-boundary traversal.
 // This only keeps the legacy map wheel handler from also zooming.
 event.stopPropagation();
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
 document.addEventListener('pointercancel',release,true);
 document.addEventListener('wheel',onWheel,{capture:true,passive:false});
 observer=new MutationObserver(syncMode);observer.observe(document.body,{childList:true,subtree:true,characterData:true});
 return true;
}

export function dispose(){
 document.removeEventListener('pointerdown',onPointerDown,true);
 document.removeEventListener('pointermove',onPointerMove,true);
 document.removeEventListener('pointerup',release,true);
 document.removeEventListener('pointercancel',release,true);
 document.removeEventListener('wheel',onWheel,true);
 observer?.disconnect();observer=null;pointers.clear();
 document.querySelectorAll('.wb-underlay-host').forEach(node=>node.remove());
 document.querySelector('.worldbuilder-studio')?.classList.remove('wb-z-unlocked');
 style?.remove();style=null;bridge=null;explicitMode=null;
}
