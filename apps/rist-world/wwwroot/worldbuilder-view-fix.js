let style=null;
let navigationMode=true;
let requestedNavigationMode=true;

function studio(){return document.querySelector('.worldbuilder-studio');}
function stage(){return studio()?.querySelector('.world-stage');}

function ensureStyle(){
 if(style)return;
 style=document.createElement('style');
 style.id='rist-worldbuilder-view-fix';
 style.textContent=`
  .worldbuilder-studio.wb-z-unlocked .tile-edit-overlay{display:none!important}
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
}

function syncMode(){
 navigationMode=requestedNavigationMode;
 const root=studio();
 if(!root)return;
 root.classList.toggle('wb-z-unlocked',navigationMode);
 root.classList.remove('wb-select-mode');
 root.querySelectorAll('[data-wb-select="true"]').forEach(node=>node.remove());
}

export function setNavigationMode(enabled){
 requestedNavigationMode=!!enabled;
 syncMode();
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
 ensureStyle();syncMode();
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

export function attach(){ensureStyle();syncMode();return true;}

export function sync(){syncMode();return true;}

export function dispose(){
 document.querySelectorAll('.wb-underlay-host,[data-wb-select="true"]').forEach(node=>node.remove());
 document.querySelector('.worldbuilder-studio')?.classList.remove('wb-z-unlocked','wb-select-mode');
 style?.remove();style=null;requestedNavigationMode=true;navigationMode=true;
}
