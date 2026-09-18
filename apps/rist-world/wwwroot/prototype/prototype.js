(() => {
'use strict';
const ASSET_ROOT='https://d2d6rnm6fnsp89.cloudfront.net/library/terrains/standard/world/whole_maps/geonaph/';
const BASE_WORLD_ASSETS=Object.freeze([
  Object.freeze({key:'surface',file:'geonaph_full_static_canonical_surface_v001.png'}),
  Object.freeze({key:'highlands',file:'geonaph_full_static_highlands_rivers_v001.png'}),
  Object.freeze({key:'mountains',file:'geonaph_full_static_mountain_volcanic_archipelago_v001.png'})
]);
const BASE_LAYER_COUNT=BASE_WORLD_ASSETS.length;
const $=id=>document.getElementById(id);
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
const smoothstep=(a,b,v)=>{const t=clamp((v-a)/(b-a),0,1);return t*t*(3-2*t)};
const reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
const stage=$('stage'),world=$('world'),surface=$('surfacePlane'),highlands=$('highlandsPlane'),mountains=$('mountainPlane'),loading=$('loading'),battle=$('battleInstance'),battleText=$('battleText'),keyboard=$('viewerKeyboard'),keyboardToggle=$('keyboardToggle'),imageUploadToggle=$('imageUploadToggle'),parallaxAdd=$('parallaxAdd'),settingsToggle=$('settingsToggle'),viewerSettingsPanel=$('viewerSettingsPanel'),viewerSettingsClose=$('viewerSettingsClose'),settingsFit=$('settingsFit'),settingsResetTilt=$('settingsResetTilt'),settingsStartMenu=$('settingsStartMenu'),imageUploadPanel=$('imageUploadPanel'),imageUploadClose=$('imageUploadClose'),imageDropzone=$('imageDropzone'),imageBrowse=$('imageBrowse'),imageFile=$('imageFile'),imageX=$('imageX'),imageY=$('imageY'),imageTransparency=$('imageTransparency'),keyboardTabs=$('keyboardTabs'),keyboardKeys=$('keyboardKeys'),live=$('live');
const planeByKey={surface,highlands,mountains};
const layerReady={surface:false,highlands:false,mountains:false};
const pointers=new Map();
let naturalWidth=1,naturalHeight=1,scale=1,minScale=.1,maxScale=12,x=0,y=0,fitX=0,fitY=0,panStart=null,pinchStart=null,keyboardMode='Viewer',toolMode='Inspect',tiltBaseline=null,tiltTargetX=0,tiltTargetY=0,tiltX=0,tiltY=0,tiltFrame=0,selectedImage=null,imageDrag=null,currentParallaxGroup=0,parallaxGapCount=0;
const userLayers=[];
function announce(text){live.textContent='';requestAnimationFrame(()=>{live.textContent=text})}
function updateLayerOrder(){
  userLayers.forEach((item,index)=>{item.layerIndex=index+BASE_LAYER_COUNT;item.node.style.zIndex=String(10+index);item.node.dataset.layer=String(item.layerIndex);item.node.dataset.parallaxGroup=String(item.parallaxGroup)});
}
function groupHasUserLayer(group){return userLayers.some(item=>item.parallaxGroup===group)}
function addParallaxGap(){
  if(currentParallaxGroup>0&&!groupHasUserLayer(currentParallaxGroup)){announce('Parallax gap is already ready. Add an image before creating another gap.');return}
  currentParallaxGroup+=1;parallaxGapCount+=1;parallaxAdd.setAttribute('aria-label',`Add parallax gap. ${parallaxGapCount} gap${parallaxGapCount===1?'':'s'} currently in the stack.`);
  keyboardMode='Layers';renderKeyboardTabs();renderKeyboardKeys();applyParallax();announce(`Parallax gap ${parallaxGapCount} added. New images will be placed at depth group ${currentParallaxGroup}.`);
}
function moveSelectedLayer(delta){
  if(!selectedImage)return;const index=userLayers.indexOf(selectedImage);if(index<0)return;const next=clamp(index+delta,0,userLayers.length-1);if(next===index)return;userLayers.splice(index,1);userLayers.splice(next,0,selectedImage);updateLayerOrder();announce(`Image moved to layer ${selectedImage.layerIndex}.`);renderKeyboardKeys();
}
function moveSelectedDepth(delta){
  if(!selectedImage)return;selectedImage.parallaxGroup=Math.max(0,selectedImage.parallaxGroup+delta);currentParallaxGroup=Math.max(currentParallaxGroup,selectedImage.parallaxGroup);parallaxGapCount=Math.max(parallaxGapCount,currentParallaxGroup);updateLayerOrder();applyParallax();announce(`Image moved to parallax depth ${selectedImage.parallaxGroup}.`);renderKeyboardKeys();
}
function viewerCenterPosition(){
  const r=stage.getBoundingClientRect();
  const wx=((r.width/2)-x)/Math.max(scale,.00001);
  const wy=((r.height/2)-y)/Math.max(scale,.00001);
  return{x:clamp(wx/Math.max(naturalWidth,1),0,1),y:clamp(wy/Math.max(naturalHeight,1),0,1)};
}
function openImageUpload(){
  const point=viewerCenterPosition();
  imageX.value=point.x.toFixed(3);imageY.value=point.y.toFixed(3);
  imageTransparency.checked=true;imageUploadPanel.hidden=false;stage.classList.add('image-upload-open');imageDropzone.focus();
  announce(`Image upload opened. Viewer frozen. The image will become layer ${BASE_LAYER_COUNT+userLayers.length} in parallax depth ${currentParallaxGroup}.`);
}function closeImageUpload(){imageUploadPanel.hidden=true;stage.classList.remove('image-upload-open');imageUploadToggle.focus()}
function fileDataUrl(file){return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result||''));reader.onerror=()=>reject(reader.error);reader.readAsDataURL(file)})}
function loadDataImage(src){return new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>resolve(img);img.onerror=reject;img.src=src})}
async function transparencyCandidate(src){
  const img=await loadDataImage(src),max=2048,ratio=Math.min(1,max/Math.max(img.naturalWidth,img.naturalHeight)),w=Math.max(1,Math.round(img.naturalWidth*ratio)),h=Math.max(1,Math.round(img.naturalHeight*ratio));
  const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.drawImage(img,0,0,w,h);
  const data=ctx.getImageData(0,0,w,h),px=data.data;
  for(let i=3;i<px.length;i+=4)if(px[i]<245)return src;
  const samples=[],step=Math.max(1,Math.floor(Math.min(w,h)/48));
  for(let xx=0;xx<w;xx+=step){samples.push((0*w+xx)*4,((h-1)*w+xx)*4)}
  for(let yy=0;yy<h;yy+=step){samples.push((yy*w)*4,(yy*w+(w-1))*4)}
  let r=0,g=0,b=0;for(const i of samples){r+=px[i];g+=px[i+1];b+=px[i+2]}r/=samples.length;g/=samples.length;b/=samples.length;
  let variance=0;for(const i of samples){variance+=(px[i]-r)**2+(px[i+1]-g)**2+(px[i+2]-b)**2}variance/=samples.length;
  if(variance>1500)return src;
  const threshold=48;
  for(let i=0;i<px.length;i+=4){const d=Math.hypot(px[i]-r,px[i+1]-g,px[i+2]-b);if(d<threshold)px[i+3]=0;else if(d<threshold*1.5)px[i+3]=Math.round(255*(d-threshold)/(threshold*.5))}
  ctx.putImageData(data,0,0);return canvas.toDataURL('image/png');
}
function refreshUserImage(item){
  if(!item?.node)return;
  const desired=item.transparent&&item.transparentSrc?item.transparentSrc:item.originalSrc;
  if(item.renderedSrc!==desired){item.node.src=desired;item.renderedSrc=desired}
  item.node.style.left=`${item.x*naturalWidth}px`;item.node.style.top=`${item.y*naturalHeight}px`;
  item.node.style.opacity=String(item.opacity);
  const px=Number(item.parallaxX)||0,py=Number(item.parallaxY)||0;
  item.node.style.transform=`translate(-50%,-50%) translate3d(${px.toFixed(2)}px,${py.toFixed(2)}px,0) rotate(${item.rotation}deg) scale(${item.size})`;
}function selectUserImage(item){
  selectedImage?.node?.classList.remove('selected');selectedImage=item;item?.node?.classList.add('selected');renderKeyboardKeys();
}
function removeSelectedImage(){if(!selectedImage)return;const index=userLayers.indexOf(selectedImage);selectedImage.node.remove();if(index>=0)userLayers.splice(index,1);selectedImage=null;updateLayerOrder();applyParallax();renderKeyboardKeys();announce('Image removed from the layer stack.')}
function beginImageDrag(event,item){
  event.preventDefault();event.stopPropagation();selectUserImage(item);item.node.setPointerCapture?.(event.pointerId);
  imageDrag={id:event.pointerId,item,startX:event.clientX,startY:event.clientY,x:item.x,y:item.y};
}
function moveImageDrag(event){
  if(!imageDrag||imageDrag.id!==event.pointerId)return;event.preventDefault();event.stopPropagation();
  imageDrag.item.x=clamp(imageDrag.x+(event.clientX-imageDrag.startX)/(Math.max(scale,.00001)*Math.max(naturalWidth,1)),0,1);
  imageDrag.item.y=clamp(imageDrag.y+(event.clientY-imageDrag.startY)/(Math.max(scale,.00001)*Math.max(naturalHeight,1)),0,1);
  refreshUserImage(imageDrag.item);
}
function endImageDrag(event){if(!imageDrag||imageDrag.id!==event.pointerId)return;imageDrag.item.node.releasePointerCapture?.(event.pointerId);imageDrag=null}
async function placeUploadedImage(file){
  if(!file?.type?.startsWith('image/')){announce('Choose an image file.');return}
  const originalSrc=await fileDataUrl(file),transparentSrc=await transparencyCandidate(originalSrc);
  const item={
    id:crypto.randomUUID?.()||String(Date.now()),originalSrc,transparentSrc,transparent:!!imageTransparency.checked,
    x:clamp(Number(imageX.value)||0,0,1),y:clamp(Number(imageY.value)||0,0,1),parallaxGroup:currentParallaxGroup,layerIndex:BASE_LAYER_COUNT+userLayers.length,size:1,rotation:0,opacity:1,node:null
  };
  const node=document.createElement('img');node.className='user-image-placement';node.alt='Placed user image';node.draggable=false;item.node=node;
  node.addEventListener('pointerdown',event=>beginImageDrag(event,item));node.addEventListener('pointermove',moveImageDrag);node.addEventListener('pointerup',endImageDrag);node.addEventListener('pointercancel',endImageDrag);
  userLayers.push(item);world.appendChild(node);updateLayerOrder();refreshUserImage(item);selectUserImage(item);closeImageUpload();keyboardMode='Image';openKeyboard();renderKeyboardTabs();renderKeyboardKeys();applyParallax();
  announce(`Image placed as layer ${item.layerIndex} at parallax depth ${item.parallaxGroup}. Image editing keyboard opened.`);
}
function applyParallax(){
  const dx=x-fitX,dy=y-fitY;
  surface.style.opacity=layerReady.surface?'1':'0';highlands.style.opacity=layerReady.highlands?'1':'0';mountains.style.opacity=layerReady.mountains?'1':'0';
  surface.style.transform='none';highlands.style.transform='none';mountains.style.transform='none';
  for(const item of userLayers){
    const depth=Math.max(0,item.parallaxGroup||0);
    const panStrength=depth*.055,tiltStrength=depth*.78;
    item.parallaxX=((-dx*panStrength)+(tiltX*tiltStrength))/Math.max(scale,.00001);
    item.parallaxY=((-dy*panStrength)+(tiltY*tiltStrength))/Math.max(scale,.00001);
    refreshUserImage(item);
  }
}
function updateReadouts(){
  stage.dataset.layerCount=String(BASE_LAYER_COUNT+userLayers.length);
  stage.dataset.parallaxGaps=String(parallaxGapCount);
  stage.setAttribute('aria-label',`Interactive layered world viewer. ${BASE_LAYER_COUNT+userLayers.length} image layers and ${parallaxGapCount} optional parallax gap${parallaxGapCount===1?'':'s'}.`);
}
function applyTransform(){
  world.style.width=naturalWidth+'px';
  world.style.height=naturalHeight+'px';
  world.style.transform=`translate3d(${x}px,${y}px,0) scale(${scale})`;
  applyParallax();
  updateReadouts();
}
function fitMap(){
  if(!naturalWidth||!naturalHeight)return;
  const r=stage.getBoundingClientRect();
  minScale=Math.min(r.width/naturalWidth,r.height/naturalHeight);
  scale=minScale;
  maxScale=Math.max(minScale*24,8);
  x=fitX=(r.width-naturalWidth*scale)/2;
  y=fitY=0;
  applyTransform();
}
function zoomAt(cx,cy,factor){
  const r=stage.getBoundingClientRect(),sx=cx-r.left,sy=cy-r.top,old=scale,next=clamp(old*factor,minScale*.75,maxScale);
  if(Math.abs(next-old)<.0001)return;
  const wx=(sx-x)/old,wy=(sy-y)/old;
  scale=next;
  x=sx-wx*scale;
  y=sy-wy*scale;
  applyTransform();
}

function renderState(){applyTransform();renderKeyboardKeys()}
const BASE_KEYBOARD_MODES=['Viewer','Layers','Image','Pixels','Tiles','Sprites','Labels','Litch','CAD','Stylus','Tethers','Metadata','Selected'];
function keyboardModes(){return BASE_KEYBOARD_MODES}
function toolKey(label,sub,fn,disabled=false){const b=document.createElement('button');b.type='button';b.disabled=disabled;b.innerHTML=`<strong>${label}</strong><small>${sub}</small>`;b.setAttribute('aria-label',label==='⛶'?'Fit map to screen':`${label}: ${sub}`);b.addEventListener('click',fn);return b}
function setTool(name){toolMode=name;announce(`${name} tool selected. Prototype tool mode changes controls only; world truth is not altered.`);renderKeyboardKeys()}
function renderKeyboardTabs(){const modes=keyboardModes();if(!modes.includes(keyboardMode))keyboardMode=modes[0];keyboardTabs.replaceChildren();modes.forEach(mode=>{const b=document.createElement('button');b.type='button';b.role='tab';b.textContent=mode;b.classList.toggle('active',mode===keyboardMode);b.setAttribute('aria-selected',String(mode===keyboardMode));b.addEventListener('click',()=>{keyboardMode=mode;renderKeyboardTabs();renderKeyboardKeys();announce(`${mode} keyboard opened.`)});keyboardTabs.append(b)})}
function renderKeyboardKeys(){
  if(!keyboardKeys)return;
  keyboardKeys.replaceChildren();
  if(keyboardMode==='Viewer'){
    keyboardKeys.append(
      toolKey('−','zoom',()=>{const r=stage.getBoundingClientRect();zoomAt(r.left+r.width/2,r.top+r.height/2,1/1.22)}),
      toolKey('+','zoom',()=>{const r=stage.getBoundingClientRect();zoomAt(r.left+r.width/2,r.top+r.height/2,1.22)}),
      toolKey('⛶','camera',fitMap),
      toolKey('⌁','reset tilt',resetTilt)
    );return;
  }
  if(keyboardMode==='Layers'){
    keyboardKeys.append(
      toolKey('▧','add image',openImageUpload),
      toolKey('≋','add parallax gap',addParallaxGap),
      toolKey(String(BASE_LAYER_COUNT+userLayers.length),'layers',()=>{},true),
      toolKey(String(parallaxGapCount),'parallax gaps',()=>{},true)
    );return;
  }
  if(keyboardMode==='Image'){
    if(!selectedImage){keyboardKeys.append(toolKey('▧','add image',openImageUpload));return}
    keyboardKeys.append(
      toolKey('SIZE −','image',()=>{selectedImage.size=clamp(selectedImage.size-.1,.2,5);refreshUserImage(selectedImage)}),
      toolKey('SIZE +','image',()=>{selectedImage.size=clamp(selectedImage.size+.1,.2,5);refreshUserImage(selectedImage)}),
      toolKey('↺','rotate',()=>{selectedImage.rotation-=15;refreshUserImage(selectedImage)}),
      toolKey('↻','rotate',()=>{selectedImage.rotation+=15;refreshUserImage(selectedImage)}),
      toolKey('OP −','opacity',()=>{selectedImage.opacity=clamp(selectedImage.opacity-.1,.1,1);refreshUserImage(selectedImage)}),
      toolKey('OP +','opacity',()=>{selectedImage.opacity=clamp(selectedImage.opacity+.1,.1,1);refreshUserImage(selectedImage)}),
      toolKey(selectedImage.transparent?'TRANS ✓':'TRANS','background',()=>{selectedImage.transparent=!selectedImage.transparent;refreshUserImage(selectedImage);renderKeyboardKeys()}),
      toolKey('BACK','layer order',()=>moveSelectedLayer(-1)),
      toolKey('FRONT','layer order',()=>moveSelectedLayer(1)),
      toolKey('DEPTH −','parallax',()=>moveSelectedDepth(-1),selectedImage.parallaxGroup<=0),
      toolKey('DEPTH +','parallax',()=>moveSelectedDepth(1)),
      toolKey('DELETE','image',removeSelectedImage)
    );return;
  }
  if(keyboardMode==='Selected'){
    keyboardKeys.append(toolKey('IMAGE','edit selected',()=>{keyboardMode='Image';renderKeyboardTabs();renderKeyboardKeys()},!selectedImage),toolKey('INSPECT','viewer',()=>setTool('Inspect')),toolKey('META','viewer',()=>setTool('Metadata')));return;
  }
  const sets={Pixels:['Select','Paint','Erase','Fill'],Tiles:['Library','Place','Rotate','Scale'],Sprites:['Library','Place','Play','Speed'],Labels:['New Label','Style','Anchor','Offset'],Litch:['Light','Shadow','Intensity','Falloff'],CAD:['Line','Shape','Measure','Snap'],Stylus:['Draw','Pressure','Erase','Sample'],Tethers:['Link','Unlink','Anchor','Trace'],Metadata:['Inspect','Identity','Provenance','Relations']};
  (sets[keyboardMode]||['Inspect']).forEach(name=>keyboardKeys.append(toolKey(name,keyboardMode.toLowerCase(),()=>setTool(name))));
}
function openKeyboard(){keyboard.hidden=false;stage.classList.add('keyboard-open');keyboardToggle.setAttribute('aria-expanded','true');keyboardToggle.setAttribute('aria-label','Close World Builder keyboard');renderKeyboardTabs();renderKeyboardKeys();announce(`${keyboardMode} keyboard opened over viewer. Viewer size unchanged.`)}
function closeKeyboard(){keyboard.hidden=true;stage.classList.remove('keyboard-open');keyboardToggle.setAttribute('aria-expanded','false');keyboardToggle.setAttribute('aria-label','Open World Builder keyboard');announce('Keyboard hidden. Viewer unobstructed.')}

BASE_WORLD_ASSETS.forEach(asset=>{
  const node=planeByKey[asset.key];
  node.addEventListener('load',()=>{
    layerReady[asset.key]=true;
    if(asset.key==='surface'){
      naturalWidth=node.naturalWidth||1;
      naturalHeight=node.naturalHeight||1;
      loading.hidden=true;
      fitMap();
    }else renderState();
  });
  node.addEventListener('error',()=>{
    layerReady[asset.key]=false;
    if(asset.key==='surface'){loading.hidden=false;loading.textContent='WORLD MAP ASSET UNAVAILABLE'}
    renderState();
  });
  node.src=ASSET_ROOT+asset.file;
});

function screenAdjusted(beta,gamma){
  const raw=Number(screen.orientation?.angle??window.orientation??0);
  const angle=((raw%360)+360)%360;
  if(angle===90)return{x:beta,y:-gamma};
  if(angle===270)return{x:-beta,y:gamma};
  if(angle===180)return{x:-gamma,y:-beta};
  return{x:gamma,y:beta};
}
function renderTilt(){
  tiltFrame=0;
  tiltX+=(tiltTargetX-tiltX)*.22;
  tiltY+=(tiltTargetY-tiltY)*.22;
  applyParallax();
  if(Math.abs(tiltTargetX-tiltX)>.03||Math.abs(tiltTargetY-tiltY)>.03)tiltFrame=requestAnimationFrame(renderTilt);
}
function scheduleTilt(){if(!tiltFrame)tiltFrame=requestAnimationFrame(renderTilt)}
function resetTilt(){
  tiltBaseline=null;
  tiltTargetX=0;
  tiltTargetY=0;
  scheduleTilt();
}
addEventListener('deviceorientation',event=>{
  const beta=Number(event.beta),gamma=Number(event.gamma);
  if(!Number.isFinite(beta)||!Number.isFinite(gamma))return;
  const axes=screenAdjusted(beta,gamma);
  if(!tiltBaseline){tiltBaseline={x:axes.x,y:axes.y};return;}
  tiltTargetX=clamp((axes.x-tiltBaseline.x)/20,-1,1)*22;
  tiltTargetY=clamp((axes.y-tiltBaseline.y)/20,-1,1)*16;
  scheduleTilt();
},{passive:true});
addEventListener('orientationchange',resetTilt,{passive:true});
screen.orientation?.addEventListener?.('change',resetTilt);
function openViewerSettings(){viewerSettingsPanel.hidden=false;viewerSettingsClose.focus()}
function closeViewerSettings(){viewerSettingsPanel.hidden=true;settingsToggle.focus()}
function openStartMenu(){if(window.top&&window.top!==window)window.top.location.href='/Game/index.html';else location.href='/Game/index.html'}

$('fit').addEventListener('click',fitMap);
$('zoomIn').addEventListener('click',()=>{const r=stage.getBoundingClientRect();zoomAt(r.left+r.width/2,r.top+r.height/2,1.22)});
$('zoomOut').addEventListener('click',()=>{const r=stage.getBoundingClientRect();zoomAt(r.left+r.width/2,r.top+r.height/2,1/1.22)});
$('back').addEventListener('click',openStartMenu);
keyboardToggle.addEventListener('click',()=>keyboard.hidden?openKeyboard():closeKeyboard());
settingsToggle.addEventListener('click',openViewerSettings);
viewerSettingsClose.addEventListener('click',closeViewerSettings);
settingsFit.addEventListener('click',()=>{fitMap();closeViewerSettings()});
settingsResetTilt.addEventListener('click',()=>{resetTilt();closeViewerSettings();announce('Viewer tilt reset.')});
settingsStartMenu.addEventListener('click',openStartMenu);
imageUploadToggle.addEventListener('click',openImageUpload);
parallaxAdd.addEventListener('click',addParallaxGap);
imageUploadClose.addEventListener('click',closeImageUpload);
imageBrowse.addEventListener('click',()=>imageFile.click());
imageFile.addEventListener('change',()=>{const file=imageFile.files?.[0];if(file)void placeUploadedImage(file);imageFile.value=''});
imageDropzone.addEventListener('click',event=>{if(event.target===imageDropzone)imageFile.click()});
imageDropzone.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();imageFile.click()}});
for(const type of ['dragenter','dragover'])imageDropzone.addEventListener(type,event=>{event.preventDefault();event.stopPropagation();imageDropzone.classList.add('dragover')});
for(const type of ['dragleave','drop'])imageDropzone.addEventListener(type,event=>{event.preventDefault();event.stopPropagation();imageDropzone.classList.remove('dragover')});
imageDropzone.addEventListener('drop',event=>{const file=[...(event.dataTransfer?.files||[])].find(f=>f.type.startsWith('image/'));if(file)void placeUploadedImage(file)});
$('keyboardClose').addEventListener('click',closeKeyboard);

stage.addEventListener('wheel',e=>{if(e.target instanceof Element&&e.target.closest('[data-ui]'))return;e.preventDefault();zoomAt(e.clientX,e.clientY,e.deltaY<0?1.12:1/1.12)},{passive:false});
stage.addEventListener('pointerdown',e=>{
  if(e.target instanceof Element&&e.target.closest('[data-ui]'))return;
  if(e.pointerType==='mouse'&&e.button!==0)return;
  stage.setPointerCapture?.(e.pointerId);
  pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
  stage.classList.add('dragging');
  if(pointers.size===1){panStart={pointerX:e.clientX,pointerY:e.clientY,x,y};pinchStart=null}
  else if(pointers.size===2){
    const[a,b]=[...pointers.values()],r=stage.getBoundingClientRect(),cx=(a.x+b.x)/2-r.left,cy=(a.y+b.y)/2-r.top,d=Math.hypot(a.x-b.x,a.y-b.y)||1;
    pinchStart={distance:d,scale,worldX:(cx-x)/scale,worldY:(cy-y)/scale};
    panStart=null;
  }
});
stage.addEventListener('pointermove',e=>{
  if(!pointers.has(e.pointerId))return;
  pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
  if(pointers.size===1&&panStart){x=panStart.x+(e.clientX-panStart.pointerX);y=panStart.y+(e.clientY-panStart.pointerY);applyTransform();return}
  if(pointers.size===2&&pinchStart){
    const[a,b]=[...pointers.values()],r=stage.getBoundingClientRect(),cx=(a.x+b.x)/2-r.left,cy=(a.y+b.y)/2-r.top,d=Math.hypot(a.x-b.x,a.y-b.y)||1;
    scale=clamp(pinchStart.scale*(d/pinchStart.distance),minScale*.75,maxScale);
    x=cx-pinchStart.worldX*scale;
    y=cy-pinchStart.worldY*scale;
    applyTransform();
  }
});
function release(e){
  pointers.delete(e.pointerId);
  if(!pointers.size){panStart=pinchStart=null;stage.classList.remove('dragging')}
  else if(pointers.size===1){const[r]=[...pointers.values()];panStart={pointerX:r.x,pointerY:r.y,x,y};pinchStart=null}
}
stage.addEventListener('pointerup',release);
stage.addEventListener('pointercancel',release);
window.addEventListener('resize',fitMap,{passive:true});
document.addEventListener('keydown',e=>{if(e.key!=='Escape')return;if(!viewerSettingsPanel.hidden){closeViewerSettings();return}if(!imageUploadPanel.hidden){closeImageUpload();return}if(!keyboard.hidden)closeKeyboard()});

window.ShaelvienPrototype=Object.freeze({
  baseLayers:BASE_WORLD_ASSETS,
  getViewerState:()=>({
    layerCount:BASE_LAYER_COUNT+userLayers.length,
    userLayers:userLayers.map(item=>({id:item.id,layerIndex:item.layerIndex,parallaxGroup:item.parallaxGroup,x:item.x,y:item.y,size:item.size,rotation:item.rotation,opacity:item.opacity,transparent:item.transparent})),
    parallaxGapCount,currentParallaxGroup,keyboardOpen:!keyboard.hidden,keyboardMode,toolMode
  })
});
renderKeyboardTabs();
renderState();
})();