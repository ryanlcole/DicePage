let bridge=null;
let observer=null;
let style=null;
let pointers=new Map();
let panX=0;
let panY=0;
let navigationMode=true;
let requestedNavigationMode=true;
let selectMode=false;
let syncQueued=false;

function studio(){return document.querySelector('.worldbuilder-studio');}
function viewer(){return studio()?.querySelector('.studio-viewer-canvas');}
function stage(){return studio()?.querySelector('.world-stage');}
function zLockButton(){
 const root=studio();
 if(!root)return null;
 return [...root.querySelectorAll('.studio-command-rail button')]
  .find(node=>node.querySelector('strong')?.textContent?.trim()==='Z-Lock')||null;
}

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
  .worldbuilder-studio.wb-z-unlocked .world-stage .tile-cell{pointer-events:none!important;cursor:default!important}
  .worldbuilder-studio.wb-z-unlocked .tile-edit-overlay{display:none!important}
  .worldbuilder-studio.wb-select-mode .world-stage .tile-cell{pointer-events:auto!important;cursor:pointer!important;touch-action:none!important}
  .worldbuilder-studio.wb-select-mode .world-stage .tile-cell img,
  .worldbuilder-studio.wb-select-mode .world-stage .tile-cell .tile-image-crop{-webkit-user-select:none!important;user-select:none!important;-webkit-user-drag:none!important;-webkit-touch-callout:none!important;touch-action:none!important}
  .worldbuilder-studio .studio-command-rail .wb-select-command{box-sizing:border-box;flex:0 0 auto;height:48px;min-width:104px;padding:4px 12px;display:grid;place-items:center;gap:2px;border:1px solid #4b5f69;border-radius:9px;background:#0d171e;color:#d4dde1;touch-action:manipulation}
  .worldbuilder-studio .studio-command-rail .wb-select-command strong{font:900 12px/1 system-ui;color:#f0ddb0}
  .worldbuilder-studio .studio-command-rail .wb-select-command small{font:800 7px/1 system-ui;letter-spacing:.06em;text-transform:uppercase;color:#8fa5b0}
  .worldbuilder-studio .studio-command-rail .wb-select-command.active{border-color:#d0aa56;background:#201b10;box-shadow:inset 0 0 0 1px rgba(242,207,114,.35)}
  .wb-underlay-host{position:absolute;inset:0;z-index:1;pointer-events:none;overflow:hidden}
  .wb-underlay-tile{position:absolute;box-sizing:border-box;overflow:hidden;pointer-events:none;border:0;outline:0}
  .wb-underlay-tile>.wb-underlay-crop{position:absolute;inset:0;display:block;overflow:hidden;line-height:0}
  .wb-underlay-tile img{position:absolute;display:block;max-width:none;max-height:none;border:0;outline:0;transform-origin:center center}
  .wb-quick-drag-ghost{transform:translate(calc(-50% + var(--wb-thumb-side,70px)),calc(-50% - 88px)) scale(1.06)!important}
  @media(max-width:760px){.worldbuilder-studio .studio-command-rail .wb-select-command{height:44px;min-width:94px;padding:4px 9px}}
 `;
 document.head.appendChild(style);
}

function ensureSelectButton(){
 const root=studio();
 const rail=root?.querySelector('.studio-command-rail');
 if(!rail)return null;
 let button=rail.querySelector('[data-wb-select="true"]');
 if(button)return button;
 button=document.createElement('button');
 button.type='button';
 button.className='wb-select-command';
 button.dataset.wbSelect='true';
 button.setAttribute('aria-pressed','false');
 button.innerHTML='<strong>Select</strong><small>Tap to Edit</small>';
 button.addEventListener('click',event=>{
  event.preventDefault();
  event.stopPropagation();
  selectMode=!selectMode;
  pointers.clear();
  syncMode();
 });
 const library=rail.querySelector('button');
 if(library)library.insertAdjacentElement('afterend',button);else rail.prepend(button);
 return button;
}

function syncMode(){
 // Select is a user-owned edit latch. External Z/navigation synchronization may
 // request navigation, but it cannot silently cancel an active tile-edit session.
 navigationMode=selectMode?false:requestedNavigationMode;
 const root=studio();
 if(!root)return;
 root.classList.toggle('wb-z-unlocked',navigationMode);
 root.classList.toggle('wb-select-mode',selectMode);
 const select=ensureSelectButton();
 select?.classList.toggle('active',selectMode);
 if(select){
  select.setAttribute('aria-pressed',String(selectMode));
  const small=select.querySelector('small');
  const next=selectMode?'Editing Tiles':'Tap to Edit';
  if(small&&small.textContent!==next)small.textContent=next;
 }
 const s=stage();
 if(s){
  s.style.setProperty('--wb-pan-x',`${panX}px`);
  s.style.setProperty('--wb-pan-y',`${panY}px`);
 }
}

export function setNavigationMode(enabled){
 requestedNavigationMode=!!enabled;
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
 observer=new MutationObserver(queueSync);
 observer.observe(document.body,{childList:true,subtree:true});
 return true;
}

export function dispose(){
 document.removeEventListener('pointerdown',onPointerDown,true);
 document.removeEventListener('pointermove',onPointerMove,true);
 document.removeEventListener('pointerup',release,true);
 document.removeEventListener('pointercancel',release,true);
 document.removeEventListener('wheel',onWheel,true);
 observer?.disconnect();observer=null;pointers.clear();syncQueued=false;
 document.querySelectorAll('.wb-underlay-host').forEach(node=>node.remove());
 document.querySelector('.worldbuilder-studio')?.classList.remove('wb-z-unlocked','wb-select-mode');
 style?.remove();style=null;bridge=null;requestedNavigationMode=true;selectMode=false;navigationMode=true;
}