(() => {
'use strict';

const query=new URLSearchParams(location.search);
if(window.parent===window||query.get('live-worldbuilder')!=='1'||String(query.get('mode')||'worldbuilder').toLowerCase()!=='regiondefiner')return;

const ACCESS_MODE=String(query.get('access')||'edit').toLowerCase();
const READ_ONLY=ACCESS_MODE==='view';
const CLAIM_ONLY=ACCESS_MODE==='claim';
const GRID_COLUMNS=300;
const GRID_ROWS=300;
const stage=document.getElementById('stage');
const world=document.getElementById('world');
const live=document.getElementById('live');
if(!stage||!world)return;

let mode='direct';
let panel=null;
let panelStatus=null;
let previewCanvas=null;
let maskImageNode=null;
let activeOverlay=null;
let gesture=null;
let syntheticClick=false;
let suppressNativeClickUntil=0;
let boundaryPath=[];
let boundarySet=new Set();
let boundaryClosed=false;
let shadowCells=new Set();
let shadowShape='hex';
let previewing=false;
let submitting=false;
let previousMask=null;
let lastObservedShape='';
let imageObject=null;
let imagePixels=null;
let imageControls=null;
let imageName='';
const imageTransform={scale:1,rotation:0,offsetX:0,offsetY:0,alpha:24};

const clamp=(value,min,max)=>Math.min(max,Math.max(min,value));
const selectionOverlay=()=>document.querySelector('.region-definition-grid');
const currentShape=()=>String(selectionOverlay()?.dataset.gridShape||'hex').toLowerCase()==='square'?'square':'hex';
const currentRegionState=()=>{
  try{return window.ShaelvienPrototype?.getViewerState?.()?.regionDefinition||null}catch{return null}
};
const coreSelectedCells=()=>new Set((currentRegionState()?.selectedCells||[]).map(Number).filter(Number.isInteger));

function announce(text){
  if(live){live.textContent='';requestAnimationFrame(()=>{live.textContent=String(text||'')})}
  if(panelStatus)panelStatus.textContent=String(text||'');
}

function injectStyle(){
  if(document.getElementById('region-selection-tools-style'))return;
  const style=document.createElement('style');
  style.id='region-selection-tools-style';
  style.textContent=`
.region-selection-tools-panel{position:absolute;z-index:5000;left:50%;top:max(10px,env(safe-area-inset-top));transform:translateX(-50%);width:min(94vw,760px);box-sizing:border-box;padding:8px;border:1px solid rgba(199,229,239,.38);border-radius:12px;background:rgba(5,10,14,.92);backdrop-filter:blur(10px);box-shadow:0 8px 28px rgba(0,0,0,.44);font:600 12px/1.25 system-ui,sans-serif;color:#eef9ff}
.region-selection-tools-panel[hidden]{display:none!important}.region-selection-tools-row{display:flex;flex-wrap:wrap;gap:6px;align-items:center}.region-selection-tools-row+ .region-selection-tools-row{margin-top:7px}.region-selection-tools-panel button,.region-selection-tools-panel input{min-height:40px}.region-selection-tools-panel button{border:1px solid rgba(199,229,239,.34);border-radius:8px;background:#10202a;color:#eef9ff;padding:7px 10px;font-weight:800;letter-spacing:.02em}.region-selection-tools-panel button[aria-pressed="true"]{outline:2px solid #fff;outline-offset:1px;background:#183947}.region-selection-tools-panel button:disabled{opacity:.48}.region-selection-tools-panel label{display:flex;gap:5px;align-items:center}.region-selection-tools-panel input[type="range"]{width:94px}.region-selection-tools-panel input[type="text"]{flex:1;min-width:150px;border:1px solid rgba(199,229,239,.34);border-radius:8px;background:#061018;color:#fff;padding:7px 9px}.region-selection-tools-status{display:block;flex:1;min-width:220px;color:#cde6f1;font-weight:650}.region-selection-tools-file{position:relative;overflow:hidden}.region-selection-tools-file input{position:absolute;inset:0;opacity:0;cursor:pointer}.region-selection-tools-preview{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:140}.region-selection-tools-mask-image{position:absolute;pointer-events:none;z-index:139;opacity:.34;transform-origin:50% 50%;filter:drop-shadow(0 0 2px rgba(255,255,255,.8))}.region-selection-tools-panel .compact-value{min-width:38px;text-align:right;font-variant-numeric:tabular-nums}.region-selection-tools-submit{margin-left:auto}@media(max-width:620px){.region-selection-tools-panel{top:max(6px,env(safe-area-inset-top));padding:6px}.region-selection-tools-panel button{min-height:44px;padding:7px 8px}.region-selection-tools-status{min-width:100%;order:10}.region-selection-tools-panel input[type="range"]{width:76px}}
`;
  document.head.appendChild(style);
}

function makePanel(){
  if(panel?.isConnected)return panel;
  injectStyle();
  panel=document.createElement('section');
  panel.className='region-selection-tools-panel';
  panel.hidden=true;
  panel.setAttribute('role','group');
  panel.setAttribute('aria-label','Region selection tools');
  panel.innerHTML=`
    <div class="region-selection-tools-row" data-mode-row>
      <button type="button" data-mode="direct" aria-pressed="true">DIRECT</button>
      <button type="button" data-mode="boundary" aria-pressed="false">BOUNDARY LOOP</button>
      <button type="button" data-mode="image" aria-pressed="false">IMAGE MASK</button>
      <button type="button" data-action="clear">CLEAR</button>
      <span class="region-selection-tools-status" role="status" aria-live="polite"></span>
    </div>
    <div class="region-selection-tools-row" data-boundary-row hidden>
      <span>Trace the outer hexes with one continuous touch. Closing the circuit fills the inside.</span>
      <button type="button" data-action="reset-boundary">RESET LOOP</button>
    </div>
    <div class="region-selection-tools-row" data-image-row hidden>
      <label class="region-selection-tools-file"><button type="button" tabindex="-1">CHOOSE IMAGE</button><input type="file" accept="image/*" data-image-file aria-label="Choose transparent image mask" /></label>
      <label>Scale <input type="range" min="25" max="300" value="100" step="1" data-image-scale /><span class="compact-value" data-image-scale-value>100%</span></label>
      <label>Rotate <input type="range" min="-180" max="180" value="0" step="1" data-image-rotation /><span class="compact-value" data-image-rotation-value>0°</span></label>
      <label>X <input type="range" min="-100" max="100" value="0" step="1" data-image-x /><span class="compact-value" data-image-x-value>0%</span></label>
      <label>Y <input type="range" min="-100" max="100" value="0" step="1" data-image-y /><span class="compact-value" data-image-y-value>0%</span></label>
      <button type="button" data-action="apply-image" disabled>USE NON-TRANSPARENT AREA</button>
    </div>
    <div class="region-selection-tools-row" data-submit-row hidden>
      <button type="button" data-action="preview">PREVIEW</button>
      <button type="button" data-action="back" hidden>BACK TO SELECT</button>
      <input type="text" maxlength="80" placeholder="Region name" aria-label="Region name" data-region-name />
      <button type="button" class="region-selection-tools-submit" data-action="submit">${CLAIM_ONLY?'REQUEST CLAIM':'SAVE REGION'}</button>
    </div>`;
  stage.appendChild(panel);
  panelStatus=panel.querySelector('.region-selection-tools-status');
  imageControls={
    file:panel.querySelector('[data-image-file]'),
    scale:panel.querySelector('[data-image-scale]'),
    rotation:panel.querySelector('[data-image-rotation]'),
    x:panel.querySelector('[data-image-x]'),
    y:panel.querySelector('[data-image-y]'),
    apply:panel.querySelector('[data-action="apply-image"]')
  };
  panel.querySelectorAll('[data-mode]').forEach(button=>button.addEventListener('click',()=>setMode(button.dataset.mode||'direct')));
  panel.querySelector('[data-action="clear"]')?.addEventListener('click',clearSelection);
  panel.querySelector('[data-action="reset-boundary"]')?.addEventListener('click',()=>resetBoundary(true));
  panel.querySelector('[data-action="preview"]')?.addEventListener('click',previewShadowSelection);
  panel.querySelector('[data-action="back"]')?.addEventListener('click',exitShadowPreview);
  panel.querySelector('[data-action="submit"]')?.addEventListener('click',submitShadowSelection);
  imageControls.file?.addEventListener('change',event=>{const file=event.target.files?.[0];if(file)void loadMaskImage(file);event.target.value=''});
  imageControls.scale?.addEventListener('input',()=>{imageTransform.scale=Number(imageControls.scale.value)/100;panel.querySelector('[data-image-scale-value]').textContent=`${Math.round(imageTransform.scale*100)}%`;updateMaskImagePlacement()});
  imageControls.rotation?.addEventListener('input',()=>{imageTransform.rotation=Number(imageControls.rotation.value)||0;panel.querySelector('[data-image-rotation-value]').textContent=`${Math.round(imageTransform.rotation)}°`;updateMaskImagePlacement()});
  imageControls.x?.addEventListener('input',()=>{imageTransform.offsetX=(Number(imageControls.x.value)||0)/100;panel.querySelector('[data-image-x-value]').textContent=`${Math.round(imageTransform.offsetX*100)}%`;updateMaskImagePlacement()});
  imageControls.y?.addEventListener('input',()=>{imageTransform.offsetY=(Number(imageControls.y.value)||0)/100;panel.querySelector('[data-image-y-value]').textContent=`${Math.round(imageTransform.offsetY*100)}%`;updateMaskImagePlacement()});
  imageControls.apply?.addEventListener('click',applyImageMaskSelection);
  panel.querySelector('[data-region-name]')?.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();void submitShadowSelection()}});
  return panel;
}

function coreClearButton(){
  return [...document.querySelectorAll('#keyboardKeys button')].find(button=>String(button.querySelector('strong')?.textContent||'').trim().toUpperCase()==='CLEAR')||null;
}
function clearCoreSelection(){
  const button=coreClearButton();
  if(button&&!button.disabled){button.click();return true}
  return false;
}

function resetShadow(restoreMask=true){
  boundaryPath=[];boundarySet.clear();boundaryClosed=false;shadowCells.clear();
  removeShadowCanvas();
  if(restoreMask)exitShadowPreview();
  updateSubmitRow();
}
function resetBoundary(withAnnouncement=false){
  resetShadow(true);
  shadowShape=currentShape();
  if(withAnnouncement)announce('Boundary loop reset. Trace the outer cells and return to the start to close the circuit.');
}
function clearSelection(){
  if(mode==='direct'){
    if(!clearCoreSelection())announce('Nothing is selected.');
    else announce('Direct selection cleared.');
    return;
  }
  resetShadow(true);
  if(mode==='boundary')announce('Boundary selection cleared.');
  else announce('Image mask selection cleared. The source image remains available for adjustment.');
}

function setMode(next){
  next=['direct','boundary','image'].includes(next)?next:'direct';
  if(mode!==next){
    if(previewing)exitShadowPreview();
    resetShadow(false);
    clearCoreSelection();
  }
  mode=next;
  shadowShape=currentShape();
  panel?.querySelectorAll('[data-mode]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.mode===mode)));
  const boundaryRow=panel?.querySelector('[data-boundary-row]');if(boundaryRow)boundaryRow.hidden=mode!=='boundary';
  const imageRow=panel?.querySelector('[data-image-row]');if(imageRow)imageRow.hidden=mode!=='image';
  updateSubmitRow();
  updateMaskImagePlacement();
  if(mode==='direct')announce('Direct selection. Keep your thumb or pointer down and slide across cells. Start on a selected cell to erase a path.');
  else if(mode==='boundary')announce('Boundary Loop. Trace the outer cells with one continuous touch. When the circuit closes, the enclosed cells fill automatically.');
  else announce(imageObject?`Image Mask ready: ${imageName}. Adjust it, then use the non-transparent area.`:'Image Mask. Choose a transparent image; it stays local and is used only to calculate the region footprint.');
}

function cellFromClient(clientX,clientY,shape=currentShape()){
  const overlay=selectionOverlay();if(!overlay)return null;
  const rect=overlay.getBoundingClientRect();if(!(rect.width>0&&rect.height>0))return null;
  const nx=clamp((clientX-rect.left)/rect.width,0,.999999),ny=clamp((clientY-rect.top)/rect.height,0,.999999);
  const row=clamp(Math.floor(ny*GRID_ROWS),0,GRID_ROWS-1);
  const offset=shape==='hex'&&(row%2)?0.5:0;
  const column=clamp(Math.floor((nx*GRID_COLUMNS)-offset),0,GRID_COLUMNS-1);
  return row*GRID_COLUMNS+column;
}
function cellCenterClient(cell,shape=currentShape()){
  const overlay=selectionOverlay(),rect=overlay?.getBoundingClientRect();if(!overlay||!rect||rect.width<1||rect.height<1)return null;
  const row=Math.floor(cell/GRID_COLUMNS),column=cell%GRID_COLUMNS,offset=shape==='hex'&&(row%2)?0.5:0;
  const nx=clamp((column+0.5+offset)/GRID_COLUMNS,0,.999999),ny=clamp((row+0.5)/GRID_ROWS,0,.999999);
  return{x:rect.left+(nx*rect.width),y:rect.top+(ny*rect.height)};
}
function dispatchCoreToggle(cell){
  const overlay=selectionOverlay(),point=cellCenterClient(cell);if(!overlay||!point)return false;
  syntheticClick=true;
  try{
    overlay.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,clientX:point.x,clientY:point.y,button:0,buttons:0,view:window}));
    return true;
  }finally{syntheticClick=false}
}
function paintDirectCell(cell){
  if(cell===null||gesture?.visited.has(cell))return;
  gesture.visited.add(cell);
  const selected=gesture.coreSet;
  if(!selected)return;
  const has=selected.has(cell);
  if(has===gesture.paintValue)return;
  if(dispatchCoreToggle(cell)){
    if(gesture.paintValue)selected.add(cell);else selected.delete(cell);
  }
}

function neighbors(cell,shape=currentShape()){
  const row=Math.floor(cell/GRID_COLUMNS),column=cell%GRID_COLUMNS,result=[];
  const offsets=shape==='hex'
    ?((row&1)?[[0,-1],[0,1],[-1,0],[-1,1],[1,0],[1,1]]:[[0,-1],[0,1],[-1,-1],[-1,0],[1,-1],[1,0]])
    :[[-1,0],[1,0],[0,-1],[0,1]];
  for(const [dr,dc] of offsets){const rr=row+dr,cc=column+dc;if(rr>=0&&rr<GRID_ROWS&&cc>=0&&cc<GRID_COLUMNS)result.push(rr*GRID_COLUMNS+cc)}
  return result;
}
function areNeighbors(a,b,shape=currentShape()){return neighbors(a,shape).includes(b)}

function appendBoundaryCell(cell){
  if(cell===null||boundaryClosed)return;
  if(!boundaryPath.length){boundaryPath=[cell];boundarySet=new Set([cell]);shadowCells=new Set(boundarySet);renderShadowCanvas();updateSubmitRow();return}
  const last=boundaryPath[boundaryPath.length-1];
  if(cell===last)return;
  const first=boundaryPath[0];
  if(cell===first&&boundaryPath.length>=3&&areNeighbors(last,first,shadowShape)){closeBoundaryLoop();return}
  if(boundarySet.has(cell)){
    announce('The boundary crossed itself. Continue around the outside or reset the loop.');
    return;
  }
  if(!areNeighbors(last,cell,shadowShape))return;
  boundaryPath.push(cell);boundarySet.add(cell);shadowCells=new Set(boundarySet);renderShadowCanvas();updateSubmitRow();
}

function closedBoundaryFill(boundary,shape){
  const max=GRID_COLUMNS*GRID_ROWS,blocked=new Uint8Array(max),outside=new Uint8Array(max),queue=new Int32Array(max);
  for(const cell of boundary)if(cell>=0&&cell<max)blocked[cell]=1;
  let head=0,tail=0;
  const enqueue=cell=>{if(cell<0||cell>=max||blocked[cell]||outside[cell])return;outside[cell]=1;queue[tail++]=cell};
  for(let col=0;col<GRID_COLUMNS;col++){enqueue(col);enqueue((GRID_ROWS-1)*GRID_COLUMNS+col)}
  for(let row=0;row<GRID_ROWS;row++){enqueue(row*GRID_COLUMNS);enqueue(row*GRID_COLUMNS+GRID_COLUMNS-1)}
  while(head<tail){
    const cell=queue[head++];
    for(const neighbor of neighbors(cell,shape))enqueue(neighbor);
  }
  const result=new Set(boundary);
  for(let cell=0;cell<max;cell++)if(!blocked[cell]&&!outside[cell])result.add(cell);
  return result;
}
function closeBoundaryLoop(){
  if(boundaryClosed||boundaryPath.length<3)return false;
  const first=boundaryPath[0],last=boundaryPath[boundaryPath.length-1];
  if(!areNeighbors(first,last,shadowShape)){announce('The boundary is still open. Continue until the last cell touches the first edge-to-edge.');return false}
  boundaryClosed=true;
  shadowCells=closedBoundaryFill(boundarySet,shadowShape);
  renderShadowCanvas();updateSubmitRow();
  announce(`Boundary closed. ${shadowCells.size} ${shadowShape} cells are inside the claim preview.`);
  return true;
}

function processGesturePoint(clientX,clientY){
  const cell=cellFromClient(clientX,clientY,shadowShape);if(cell===null)return;
  if(mode==='direct')paintDirectCell(cell);else if(mode==='boundary')appendBoundaryCell(cell);
}
function interpolateGesture(fromX,fromY,toX,toY){
  const distance=Math.hypot(toX-fromX,toY-fromY),steps=Math.max(1,Math.ceil(distance/4));
  for(let i=1;i<=steps;i++){const t=i/steps;processGesturePoint(fromX+(toX-fromX)*t,fromY+(toY-fromY)*t)}
}
function pointerDown(event){
  const overlay=selectionOverlay();
  if(READ_ONLY||!overlay||!overlay.classList.contains('active')||(mode!=='direct'&&mode!=='boundary'))return;
  if(event.pointerType==='mouse'&&event.button!==0)return;
  event.preventDefault();event.stopImmediatePropagation();
  try{overlay.setPointerCapture(event.pointerId)}catch{}
  shadowShape=currentShape();
  if(mode==='boundary'&&boundaryClosed)resetBoundary(false);
  gesture={id:event.pointerId,lastX:event.clientX,lastY:event.clientY,visited:new Set(),coreSet:mode==='direct'?coreSelectedCells():null,paintValue:null};
  if(mode==='direct'){
    const first=cellFromClient(event.clientX,event.clientY,shadowShape);
    gesture.paintValue=first===null?true:!gesture.coreSet.has(first);
  }
  processGesturePoint(event.clientX,event.clientY);
}
function pointerMove(event){
  if(!gesture||gesture.id!==event.pointerId)return;
  event.preventDefault();event.stopImmediatePropagation();
  interpolateGesture(gesture.lastX,gesture.lastY,event.clientX,event.clientY);
  gesture.lastX=event.clientX;gesture.lastY=event.clientY;
}
function pointerEnd(event){
  if(!gesture||gesture.id!==event.pointerId)return;
  event.preventDefault();event.stopImmediatePropagation();
  interpolateGesture(gesture.lastX,gesture.lastY,event.clientX,event.clientY);
  if(mode==='boundary'&&!boundaryClosed&&boundaryPath.length>=3)closeBoundaryLoop();
  const overlay=selectionOverlay();
  try{if(overlay?.hasPointerCapture?.(event.pointerId))overlay.releasePointerCapture(event.pointerId)}catch{}
  gesture=null;suppressNativeClickUntil=performance.now()+500;
  if(mode==='direct')announce(`${coreSelectedCells().size} region cells selected. Keep your thumb down to continue painting.`);
}
function clickCapture(event){
  if(syntheticClick)return;
  if(performance.now()<suppressNativeClickUntil){event.preventDefault();event.stopImmediatePropagation()}
}
function bindOverlay(overlay){
  if(!overlay||overlay.dataset.regionSelectionToolsBound==='true')return;
  overlay.dataset.regionSelectionToolsBound='true';
  overlay.addEventListener('pointerdown',pointerDown,true);
  overlay.addEventListener('pointermove',pointerMove,true);
  overlay.addEventListener('pointerup',pointerEnd,true);
  overlay.addEventListener('pointercancel',pointerEnd,true);
  overlay.addEventListener('click',clickCapture,true);
}

function removeShadowCanvas(){previewCanvas?.remove();previewCanvas=null}
function ensureShadowCanvas(){
  if(previewCanvas?.isConnected)return previewCanvas;
  const canvas=document.createElement('canvas');canvas.className='region-selection-tools-preview';canvas.width=1200;canvas.height=1200;canvas.setAttribute('aria-hidden','true');
  world.appendChild(canvas);previewCanvas=canvas;return canvas;
}
function drawCellPath(ctx,cell,shape,width,height){
  const row=Math.floor(cell/GRID_COLUMNS),column=cell%GRID_COLUMNS,cw=width/GRID_COLUMNS,ch=height/GRID_ROWS,offset=shape==='hex'&&(row%2)?0.5:0;
  const x=(column+offset)*cw,y=row*ch;
  ctx.beginPath();
  if(shape==='square'){ctx.rect(x,y,cw,ch);return}
  const cx=x+cw/2,cy=y+ch/2,hh=ch*(4/3),top=cy-hh/2,bottom=cy+hh/2,left=cx-cw/2,right=cx+cw/2;
  ctx.moveTo(cx,top);ctx.lineTo(right,top+hh*.25);ctx.lineTo(right,top+hh*.75);ctx.lineTo(cx,bottom);ctx.lineTo(left,top+hh*.75);ctx.lineTo(left,top+hh*.25);ctx.closePath();
}
function renderShadowCanvas(){
  if(mode==='direct'||(!shadowCells.size&&!boundaryPath.length)){removeShadowCanvas();return}
  const canvas=ensureShadowCanvas(),ctx=canvas.getContext('2d');if(!ctx)return;
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.fillStyle='rgba(63,194,238,.28)';ctx.strokeStyle='rgba(199,241,255,.32)';ctx.lineWidth=1;
  for(const cell of shadowCells){drawCellPath(ctx,cell,shadowShape,canvas.width,canvas.height);ctx.fill()}
  if(boundaryPath.length){
    ctx.strokeStyle=boundaryClosed?'rgba(255,240,163,.95)':'rgba(255,255,255,.9)';ctx.lineWidth=3;
    for(const cell of boundarySet){drawCellPath(ctx,cell,shadowShape,canvas.width,canvas.height);ctx.stroke()}
  }
}

function worldPixelSize(){return{width:Math.max(1,world.offsetWidth||Number.parseFloat(world.style.width)||1),height:Math.max(1,world.offsetHeight||Number.parseFloat(world.style.height)||1)}}
function imageDisplayGeometry(){
  if(!imageObject)return null;
  const {width,height}=worldPixelSize(),imageAspect=imageObject.naturalWidth/Math.max(1,imageObject.naturalHeight),worldAspect=width/height;
  let baseWidth=width,baseHeight=height;
  if(imageAspect>=worldAspect)baseHeight=baseWidth/imageAspect;else baseWidth=baseHeight*imageAspect;
  return{worldWidth:width,worldHeight:height,width:baseWidth*imageTransform.scale,height:baseHeight*imageTransform.scale,centerX:(.5+imageTransform.offsetX)*width,centerY:(.5+imageTransform.offsetY)*height};
}
function ensureMaskImageNode(){
  if(maskImageNode?.isConnected)return maskImageNode;
  const img=document.createElement('img');img.className='region-selection-tools-mask-image';img.alt='';img.setAttribute('aria-hidden','true');img.draggable=false;world.appendChild(img);maskImageNode=img;return img;
}
function updateMaskImagePlacement(){
  if(!imageObject||mode!=='image'||previewing){maskImageNode?.remove();maskImageNode=null;return}
  const geometry=imageDisplayGeometry();if(!geometry)return;
  const node=ensureMaskImageNode();node.src=imageObject.src;
  node.style.left=`${(geometry.centerX/geometry.worldWidth)*100}%`;node.style.top=`${(geometry.centerY/geometry.worldHeight)*100}%`;
  node.style.width=`${(geometry.width/geometry.worldWidth)*100}%`;node.style.height=`${(geometry.height/geometry.worldHeight)*100}%`;
  node.style.transform=`translate(-50%,-50%) rotate(${imageTransform.rotation}deg)`;
}
async function loadMaskImage(file){
  if(!file?.type?.startsWith('image/')){announce('Choose an image file for the mask.');return}
  const url=URL.createObjectURL(file),img=new Image();
  try{
    await new Promise((resolve,reject)=>{img.onload=resolve;img.onerror=()=>reject(new Error('Image could not be read'));img.src=url});
    if(imageObject?.src?.startsWith('blob:'))URL.revokeObjectURL(imageObject.src);
    imageObject=img;imageName=String(file.name||'mask image');
    const maxSide=1024,ratio=Math.min(1,maxSide/Math.max(img.naturalWidth,img.naturalHeight));
    const canvas=document.createElement('canvas');canvas.width=Math.max(1,Math.round(img.naturalWidth*ratio));canvas.height=Math.max(1,Math.round(img.naturalHeight*ratio));
    const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.clearRect(0,0,canvas.width,canvas.height);ctx.drawImage(img,0,0,canvas.width,canvas.height);
    imagePixels={width:canvas.width,height:canvas.height,data:ctx.getImageData(0,0,canvas.width,canvas.height).data};
    if(imageControls?.apply)imageControls.apply.disabled=false;
    resetShadow(true);updateMaskImagePlacement();
    announce(`${imageName} loaded locally. Adjust scale, rotation, X, or Y, then use its non-transparent area as the selection.`);
  }catch(error){URL.revokeObjectURL(url);announce(String(error?.message||'Image mask could not be loaded.'))}
}
function alphaAt(u,v){
  if(!imagePixels||u<0||u>1||v<0||v>1)return 0;
  const x=clamp(Math.floor(u*(imagePixels.width-1)),0,imagePixels.width-1),y=clamp(Math.floor(v*(imagePixels.height-1)),0,imagePixels.height-1);
  return imagePixels.data[((y*imagePixels.width+x)*4)+3]||0;
}
function imageUvForWorld(nx,ny,geometry){
  const px=(nx*geometry.worldWidth)-geometry.centerX,py=(ny*geometry.worldHeight)-geometry.centerY,angle=-imageTransform.rotation*Math.PI/180,cos=Math.cos(angle),sin=Math.sin(angle);
  const rx=(px*cos)-(py*sin),ry=(px*sin)+(py*cos);
  return{u:(rx/geometry.width)+.5,v:(ry/geometry.height)+.5};
}
function cellCoveredByImage(cell,shape,geometry){
  const row=Math.floor(cell/GRID_COLUMNS),column=cell%GRID_COLUMNS,offset=shape==='hex'&&(row%2)?0.5:0;
  const cx=clamp((column+.5+offset)/GRID_COLUMNS,0,1),cy=clamp((row+.5)/GRID_ROWS,0,1),dx=.24/GRID_COLUMNS,dy=.24/GRID_ROWS;
  for(const [ox,oy] of [[0,0],[-dx,0],[dx,0],[0,-dy],[0,dy]]){const uv=imageUvForWorld(cx+ox,cy+oy,geometry);if(alphaAt(uv.u,uv.v)>imageTransform.alpha)return true}
  return false;
}
function applyImageMaskSelection(){
  if(!imageObject||!imagePixels){announce('Choose an image first.');return}
  exitShadowPreview();shadowShape=currentShape();const geometry=imageDisplayGeometry();if(!geometry)return;
  const cells=new Set(),max=GRID_COLUMNS*GRID_ROWS;
  for(let cell=0;cell<max;cell++)if(cellCoveredByImage(cell,shadowShape,geometry))cells.add(cell);
  shadowCells=cells;boundaryPath=[];boundarySet.clear();boundaryClosed=false;renderShadowCanvas();updateSubmitRow();
  announce(cells.size?`${cells.size} ${shadowShape} cells selected from the non-transparent image footprint.`:'No non-transparent image area overlaps the map. Adjust the image and try again.');
}

function saveMaskStyles(){
  if(previousMask)return;
  previousMask={maskImage:world.style.maskImage,webkitMaskImage:world.style.webkitMaskImage,maskSize:world.style.maskSize,webkitMaskSize:world.style.webkitMaskSize,maskRepeat:world.style.maskRepeat,webkitMaskRepeat:world.style.webkitMaskRepeat};
}
function restoreMaskStyles(){
  if(!previousMask)return;
  Object.assign(world.style,previousMask);previousMask=null;
}
function makeSelectionMaskUrl(){
  const canvas=document.createElement('canvas');canvas.width=1200;canvas.height=1200;const ctx=canvas.getContext('2d');if(!ctx)return '';
  ctx.clearRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#fff';
  for(const cell of shadowCells){drawCellPath(ctx,cell,shadowShape,canvas.width,canvas.height);ctx.fill()}
  return `url("${canvas.toDataURL('image/png')}")`;
}
function previewShadowSelection(){
  if(mode==='direct'){announce('Direct selection already uses the built-in crop preview. Use CROP below when ready.');return}
  if(!shadowCells.size){announce('Create a boundary or image-mask selection first.');return}
  const mask=makeSelectionMaskUrl();if(!mask)return;
  saveMaskStyles();world.style.maskImage=mask;world.style.webkitMaskImage=mask;world.style.maskSize='100% 100%';world.style.webkitMaskSize='100% 100%';world.style.maskRepeat='no-repeat';world.style.webkitMaskRepeat='no-repeat';
  previewing=true;removeShadowCanvas();maskImageNode?.remove();maskImageNode=null;updateSubmitRow();
  announce(`Previewing ${shadowCells.size} selected cells. Name the region and ${CLAIM_ONLY?'request the claim':'save the region'}, or go back to adjust it.`);
}
function exitShadowPreview(){
  if(previewing)restoreMaskStyles();
  previewing=false;renderShadowCanvas();updateMaskImagePlacement();updateSubmitRow();
}
function updateSubmitRow(){
  if(!panel)return;
  const row=panel.querySelector('[data-submit-row]');if(!row)return;
  row.hidden=mode==='direct'||!shadowCells.size;
  const preview=panel.querySelector('[data-action="preview"]'),back=panel.querySelector('[data-action="back"]'),submit=panel.querySelector('[data-action="submit"]');
  if(preview)preview.hidden=previewing;if(back)back.hidden=!previewing;
  if(submit){submit.disabled=submitting||!shadowCells.size;submit.textContent=submitting?(CLAIM_ONLY?'SENDING…':'SAVING…'):(CLAIM_ONLY?'REQUEST CLAIM':'SAVE REGION')}
}
function postRegion(type,payload={}){
  try{window.parent.postMessage({source:'shaelvien-regiondefiner',type,...payload},location.origin);return true}catch{return false}
}
async function submitShadowSelection(){
  if(mode==='direct'||!shadowCells.size||submitting)return;
  if(!previewing){previewShadowSelection();return}
  const name=String(panel?.querySelector('[data-region-name]')?.value||'').trim();
  if(!name){announce('Name the region before saving or requesting it.');panel?.querySelector('[data-region-name]')?.focus();return}
  const state=currentRegionState();if(!state){announce('Region state is still loading.');return}
  const visible=Array.isArray(state.visibleWorldLayers)?state.visibleWorldLayers:[];
  const sourceLayerOffsets=visible.length?visible.map(value=>clamp(Math.trunc(Number(value)||1)-1,0,9)):Array.from({length:10},(_,index)=>index);
  const payload={name,cells:[...shadowCells].sort((a,b)=>a-b),tierIndex:clamp(Math.trunc(Number(state.tierIndex)||0),0,99),sourceLayerOffsets:[...new Set(sourceLayerOffsets)].sort((a,b)=>a-b),gridShape:shadowShape};
  submitting=true;updateSubmitRow();
  const sent=postRegion(CLAIM_ONLY?'request-claim':'create-region',payload);
  if(!sent){submitting=false;updateSubmitRow();announce('Region persistence bridge is unavailable.');return}
  announce(CLAIM_ONLY?'Sending the closed selection to the GM for authority review.':'Saving the selected region. The selection is still only a request until the authoritative save succeeds.');
}

function handleHostMessage(event){
  if(event.origin!==location.origin||event.source!==window.parent)return;
  const data=event.data;if(!data||data.source!=='shaelvien-regiondefiner-host')return;
  if(data.type==='region-created'){
    submitting=false;previewing=false;previousMask=null;shadowCells.clear();boundaryPath=[];boundarySet.clear();boundaryClosed=false;removeShadowCanvas();maskImageNode?.remove();maskImageNode=null;updateSubmitRow();
    return;
  }
  if(data.type==='claim-requested'){
    submitting=false;
    if(data.result?.success){restoreMaskStyles();previewing=false;shadowCells.clear();boundaryPath=[];boundarySet.clear();boundaryClosed=false;removeShadowCanvas();updateSubmitRow()}
    else updateSubmitRow();
    return;
  }
  if(data.type==='error'){submitting=false;updateSubmitRow()}
}

function refreshAvailability(){
  const overlay=selectionOverlay();bindOverlay(overlay);
  const shape=currentShape();
  if(lastObservedShape&&shape!==lastObservedShape&&mode!=='direct'&&shadowCells.size){resetShadow(true);announce(`Grid changed to ${shape}. The alternate selection was cleared so cell identity cannot drift.`)}
  lastObservedShape=shape;
  const active=!!overlay?.classList.contains('active')&&!READ_ONLY;
  activeOverlay=active?overlay:null;
  const p=makePanel();p.hidden=!active;
  if(activeOverlay){activeOverlay.style.touchAction=(mode==='direct'||mode==='boundary')?'none':'';activeOverlay.style.userSelect='none'}
  if(!active){gesture=null;if(previewing)exitShadowPreview()}
  updateSubmitRow();updateMaskImagePlacement();
}

window.addEventListener('message',handleHostMessage);
const observer=new MutationObserver(refreshAvailability);
observer.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['class','data-grid-shape','hidden']});
makePanel();refreshAvailability();
window.addEventListener('pagehide',()=>{
  observer.disconnect();
  if(imageObject?.src?.startsWith('blob:'))URL.revokeObjectURL(imageObject.src);
  restoreMaskStyles();
},{once:true});
})();
