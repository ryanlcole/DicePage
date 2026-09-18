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
  item.node.src=item.transparent&&item.transparentSrc?item.transparentSrc:item.originalSrc;
  item.node.style.left=`${item.x*naturalWidth}px`;item.node.style.top=`${item.y*naturalHeight}px`;
  item.node.style.opacity=String(item.opacity);
  item.node.style.transform=`translate(-50%,-50%) rotate(${item.rotation}deg) scale(${item.size})`;
}
function selectUserImage(item){
  selectedImage?.node?.classList.remove('selected');selectedImage=item;item?.node?.classList.add('selected');renderKeyboardKeys();
}
function removeSelectedImage(){if(!selectedImage)return;selectedImage.node.remove();selectedImage=null;renderKeyboardKeys();announce('Image removed from the viewer.')}
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
const CELESTIAL_TYPES=Object.freeze([
 {key:'sun',name:'Sun',glyph:'☀'},{key:'moon',name:'Moon',glyph:'◐'},{key:'planet',name:'Planet',glyph:'●'},
 {key:'star',name:'Star',glyph:'✦'},{key:'asteroid',name:'Asteroid',glyph:'◆'},{key:'comet',name:'Comet',glyph:'☄'},
 {key:'satellite',name:'Satellite',glyph:'◇'},{key:'nebula',name:'Nebula',glyph:'✺'}
]);
const WEATHER_TYPES=Object.freeze([
 {key:'cloud',name:'Cloud',glyph:'☁'},{key:'fog',name:'Fog',glyph:'≋'},{key:'rain',name:'Rain',glyph:'☂'},
 {key:'storm',name:'Storm',glyph:'ϟ'},{key:'snow',name:'Snow',glyph:'✣'},{key:'wind',name:'Wind',glyph:'〰'}
]);
function normalizedWorldPoint(clientX,clientY){
  const r=stage.getBoundingClientRect(),wx=(clientX-r.left-x)/Math.max(scale,.00001),wy=(clientY-r.top-y)/Math.max(scale,.00001);
  return{x:clamp(wx/Math.max(naturalWidth,1),0,1),y:clamp(wy/Math.max(naturalHeight,1),0,1)};
}
function refreshFloatingNode(item){
  item.node.style.left=`${item.x*naturalWidth}px`;item.node.style.top=`${item.y*naturalHeight}px`;
}
function selectCelestial(item){
  selectedCelestial?.node?.classList.remove('selected');selectedCelestial=item;item?.node?.classList.add('selected');
  if(item){selectedWeather?.node?.classList.remove('selected');selectedWeather=null}
  renderKeyboardKeys();
}
function celestialType(key){return CELESTIAL_TYPES.find(v=>v.key===key)||CELESTIAL_TYPES[0]}
function placeCelestial(key){
  const type=celestialType(key),p=viewerCenterPosition(),id=crypto.randomUUID?.()||String(Date.now());
  const item={id,type:key,name:type.name,x:p.x,y:p.y,size:1,node:null,pathPoints:[],pathNode:null,worldId:`world:${id}`,meta:{parent:'',radius:'',mass:'',gravity:'',semiMajor:'',eccentricity:'',inclination:'',period:'',rotation:'',tilt:'',albedo:'',atmosphere:'',epoch:'',worldName:`${type.name} World`}};
  const node=document.createElement('button');node.type='button';node.className='celestial-placement';node.textContent=type.glyph;node.setAttribute('aria-label',`${type.name}. Celestial object. Drag to position.`);item.node=node;
  node.addEventListener('click',event=>{event.stopPropagation();selectCelestial(item)});
  node.addEventListener('pointerdown',event=>{event.preventDefault();event.stopPropagation();selectCelestial(item);node.setPointerCapture?.(event.pointerId);celestialDrag={id:event.pointerId,item,startX:event.clientX,startY:event.clientY,x:item.x,y:item.y}});
  node.addEventListener('pointermove',event=>{if(!celestialDrag||celestialDrag.id!==event.pointerId)return;event.preventDefault();const d=normalizedWorldPoint(event.clientX,event.clientY);celestialDrag.item.x=d.x;celestialDrag.item.y=d.y;refreshFloatingNode(celestialDrag.item)});
  const done=event=>{if(celestialDrag?.id!==event.pointerId)return;node.releasePointerCapture?.(event.pointerId);celestialDrag=null};node.addEventListener('pointerup',done);node.addEventListener('pointercancel',done);
  world.appendChild(node);refreshFloatingNode(item);selectCelestial(item);keyboardMode='Sky';renderKeyboardTabs();renderKeyboardKeys();announce(`${type.name} placed in Sky. Drag it, draw a path, or open Advanced details.`);
}
function ensurePathNode(item){
  if(item.pathNode)return item.pathNode;const poly=document.createElementNS('http://www.w3.org/2000/svg','polyline');poly.classList.add('celestial-path');poly.dataset.celestialId=item.id;celestialPathLayer.appendChild(poly);item.pathNode=poly;return poly;
}
function refreshCelestialPath(item){
  if(!item)return;const poly=ensurePathNode(item);poly.setAttribute('points',item.pathPoints.map(p=>`${(p.x*naturalWidth).toFixed(1)},${(p.y*naturalHeight).toFixed(1)}`).join(' '));
}
function beginPathDraw(){
  if(!selectedCelestial){announce('Select a celestial object first.');return}
  selectedCelestial.pathPoints=[];refreshCelestialPath(selectedCelestial);pathDraw={item:selectedCelestial,pointerId:null};stage.classList.add('path-draw');announce('Path drawing active. Draw on the world, then release to finish.');
}
function openCelestialAdvanced(){
  if(!selectedCelestial){announce('Select a celestial object first.');return}
  const m=selectedCelestial.meta;celestialName.value=selectedCelestial.name;celestialParent.value=m.parent;celestialRadius.value=m.radius;celestialMass.value=m.mass;celestialGravity.value=m.gravity;celestialSemiMajor.value=m.semiMajor;celestialEccentricity.value=m.eccentricity;celestialInclination.value=m.inclination;celestialPeriod.value=m.period;celestialRotation.value=m.rotation;celestialTilt.value=m.tilt;celestialAlbedo.value=m.albedo;celestialAtmosphere.value=m.atmosphere;celestialEpoch.value=m.epoch;celestialWorldName.value=m.worldName;
  celestialAdvancedPanel.hidden=false;celestialName.focus();announce('Advanced celestial details opened.');
}
function closeCelestialAdvanced(){celestialAdvancedPanel.hidden=true}
function saveCelestialAdvanced(event){
  event?.preventDefault();if(!selectedCelestial)return;
  const m=selectedCelestial.meta;selectedCelestial.name=String(celestialName.value||celestialType(selectedCelestial.type).name).trim().slice(0,80)||celestialType(selectedCelestial.type).name;
  Object.assign(m,{parent:celestialParent.value.trim(),radius:celestialRadius.value,mass:celestialMass.value.trim(),gravity:celestialGravity.value,semiMajor:celestialSemiMajor.value,eccentricity:celestialEccentricity.value,inclination:celestialInclination.value,period:celestialPeriod.value,rotation:celestialRotation.value,tilt:celestialTilt.value,albedo:celestialAlbedo.value,atmosphere:celestialAtmosphere.value.trim(),epoch:celestialEpoch.value.trim(),worldName:celestialWorldName.value.trim()||`${selectedCelestial.name} World`});
  selectedCelestial.node.setAttribute('aria-label',`${selectedCelestial.name}. Celestial object with own world ${m.worldName}. Drag to position.`);closeCelestialAdvanced();announce(`${selectedCelestial.name} astronomical details saved. Own world: ${m.worldName}.`);
}
function removeCelestial(){
  if(!selectedCelestial)return;selectedCelestial.pathNode?.remove();selectedCelestial.node.remove();selectedCelestial=null;renderKeyboardKeys();announce('Celestial object removed.');
}
function placeWeather(key){
  const type=WEATHER_TYPES.find(v=>v.key===key)||WEATHER_TYPES[0],p=viewerCenterPosition(),depth=splitZ(viewerZ),item={type:key,name:type.name,x:p.x,y:p.y,tier:depth.tierIndex,layer:depth.layerOffset,node:null};
  const node=document.createElement('button');node.type='button';node.className='weather-placement';node.textContent=type.glyph;node.setAttribute('aria-label',`${type.name} weather at altitude tier ${depth.tierIndex}, layer ${depth.layerOffset}. Drag to position.`);item.node=node;
  node.addEventListener('pointerdown',event=>{event.preventDefault();event.stopPropagation();selectedWeather?.node?.classList.remove('selected');selectedWeather=item;selectCelestial(null);item.node.classList.add('selected');node.setPointerCapture?.(event.pointerId);weatherDrag={id:event.pointerId,item};renderKeyboardKeys()});
  node.addEventListener('pointermove',event=>{if(weatherDrag?.id!==event.pointerId)return;event.preventDefault();const d=normalizedWorldPoint(event.clientX,event.clientY);item.x=d.x;item.y=d.y;refreshFloatingNode(item)});
  const done=event=>{if(weatherDrag?.id!==event.pointerId)return;node.releasePointerCapture?.(event.pointerId);weatherDrag=null};node.addEventListener('pointerup',done);node.addEventListener('pointercancel',done);
  world.appendChild(node);refreshFloatingNode(item);selectedWeather=item;item.node.classList.add('selected');announce(`${type.name} placed at ${bandDisplayName(currentTierKey())}, layer ${depth.layerOffset}.`);
}


function splitZ(z){const tierIndex=Math.floor(z/LAYERS_PER_TIER);return{tierIndex,layerOffset:z-tierIndex*LAYERS_PER_TIER}}
function stratumByKey(key){return STRATA.find(s=>s.key===key)||STRATA[0]}
function rootFocus(){return focusPath.find(p=>p.level==='Parallax')||null}
function lockedTier(){
  const root=rootFocus();
  if(parallaxOverride||!root||root.key==='all')return null;
  return splitZ(stratumByKey(root.key).z).tierIndex;
}
function clampToLockedTier(value){
  const tier=lockedTier(),z=Math.trunc(value);
  if(tier===null)return z;
  const low=tier*LAYERS_PER_TIER,high=low+LAYERS_PER_TIER-1;
  return clamp(z,low,high);
}
function registeredLayerWindow(){
  const tier=lockedTier();
  if(tier===null)return MAP_TRUTH.assets;
  return MAP_TRUTH.assets.filter(asset=>{
    const assetTier=splitZ(asset.sceneZ).tierIndex;
    return assetTier>=tier-1&&assetTier<=tier+1;
  });
}
function focusOptions(){
  switch(focusPath.length){
    case 0:return ROOT_OPTIONS.map(s=>({key:s.key,label:s.label,level:'Parallax'}));
    case 1:{const s=focusPath[0];return (s.key==='sea'||s.key==='hills'||s.key==='mountains'||s.key==='all')?SURFACE_CATEGORIES.map(v=>({...v})):[{key:s.key+':all',label:'All '+s.label,level:'Category'}]}
    case 2:return[{key:'region',label:'Region',level:'Region'}];
    case 3:return[{key:'local',label:'Local',level:'Local'}];
    case 4:return[{key:'town',label:'Town',level:'Landmark'},{key:'cave',label:'Cave',level:'Landmark'}];
    case 5:return[{key:'npc',label:'NPC',level:'Entity'},{key:'object',label:'Object',level:'Entity'}];
    default:return[];
  }
}
function nextLevel(){return ['Parallax','Category','Region','Local','Landmark','Entity','Battle Instance'][Math.min(focusPath.length,6)]}
function announce(text){live.textContent='';requestAnimationFrame(()=>{live.textContent=text})}
function selectedOption(){const opts=focusOptions();return opts.find(o=>o.key===focusSelected)||opts[0]||null}
function normalizeFocusSelection(){const opts=focusOptions();if(!opts.some(o=>o.key===focusSelected))focusSelected=opts[0]?.key||''}

// All Parallax is the unrestricted viewer state: every registered plane remains
// eligible and zoom alone determines its perceptual handoff. A named stratum is
// different: selecting it creates a tier scope. Only the previous, selected, and
// next tier are eligible for presentation, and the selected registered layer plus
// one registered layer beneath it form the default locked view. Zoom then magnifies
// that locked representation; it never advances perception above the selected layer.
function allParallaxMix(zoomRatio,rawZoomZ){
  const peakToHighlands=smoothstep(1.00,1.60,zoomRatio);
  const highlandsToSurface=smoothstep(1.45,2.75,zoomRatio);
  return{
    zoomRatio,
    zoomZ:rawZoomZ,
    surface:layerReady.surface?1:0,
    highlands:layerReady.highlands?clamp(1-highlandsToSurface,0,1):0,
    mountains:layerReady.mountains?clamp(.82*(1-peakToHighlands),0,1):0
  };
}
function scopedParallaxMix(zoomRatio,rawZoomZ){
  const visible=registeredLayerWindow().filter(asset=>layerReady[asset.key]).sort((a,b)=>a.sceneZ-b.sceneZ);
  const atOrBelow=visible.filter(asset=>asset.sceneZ<=viewerZ);
  const selected=atOrBelow.at(-1)||visible[0]||null;
  const selectedIndex=selected?visible.indexOf(selected):-1;
  const below=selectedIndex>0?visible[selectedIndex-1]:null;
  const belowFade=1-smoothstep(1.25,3.10,zoomRatio);
  const alpha={surface:0,highlands:0,mountains:0};
  if(selected)alpha[selected.key]=1;
  if(below)alpha[below.key]=clamp(.82*belowFade,0,1);
  const selectedLayer=splitZ(viewerZ).layerOffset;
  return{
    zoomRatio,
    zoomZ:Math.min(rawZoomZ,selectedLayer),
    surface:alpha.surface,
    highlands:alpha.highlands,
    mountains:alpha.mountains
  };
}
function parallaxMix(){
  const zoomRatio=Math.max(.01,scale/Math.max(minScale,.00001));
  const rawZoomZ=Math.max(0,Math.log2(zoomRatio)*LAYERS_PER_TIER);
  parallaxOverride=true;
  return allParallaxMix(zoomRatio,rawZoomZ);
}
function applyParallax(mix=parallaxMix()){
  const dx=x-fitX,dy=y-fitY;
  const layers=[
    {node:surface,sceneZ:0,alpha:mix.surface},
    {node:highlands,sceneZ:10,alpha:mix.highlands},
    {node:mountains,sceneZ:20,alpha:mix.mountains}
  ];
  for(const layer of layers){
    const depth=layer.sceneZ/LAYERS_PER_TIER;
    const panStrength=depth*.055;
    const tiltStrength=.42+(depth*.78);
    const localX=((-dx*panStrength)+(tiltX*tiltStrength))/Math.max(scale,.00001);
    const localY=((-dy*panStrength)+(tiltY*tiltStrength))/Math.max(scale,.00001);
    layer.node.style.opacity=clamp(Number(layer.alpha)||0,0,1).toFixed(3);
    layer.node.style.transform=`translate3d(${localX.toFixed(2)}px,${localY.toFixed(2)}px,0)`;
  }
  lastMix=mix;
}
function updateReadouts(){
  const band=currentBand(),depth=splitZ(viewerZ);
  stage.dataset.viewerZ=String(viewerZ);
  stage.dataset.altitudeBand=band.key;
  stage.setAttribute('aria-label',`Interactive world viewer. All parallax layers visible. Editing position ${bandDisplayName(band.key)}, ${bandRangeText(band)}, layer ${depth.layerOffset}.`);
}
function applyTransform(){
  world.style.width=naturalWidth+'px';
  world.style.height=naturalHeight+'px';
  world.style.transform=`translate3d(${x}px,${y}px,0) scale(${scale})`;
  celestialPathLayer.setAttribute('viewBox',`0 0 ${naturalWidth} ${naturalHeight}`);celestialPathLayer.style.width=naturalWidth+'px';celestialPathLayer.style.height=naturalHeight+'px';
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

function setViewerZ(value,reason){
  viewerZ=Math.trunc(value);
  parallaxOverride=true;
  renderState();
  announce(`${reason}. Viewer Z ${viewerZ}. All Parallax remains visible.`);
}
function jumpStratum(key){
  if(key==='all'){
    parallaxOverride=true;activeStratum='sea';viewerZ=0;focusPath=[];focusSelected='all';if(keyboardMode==='Sky')keyboardMode='Viewer';renderKeyboardTabs();renderState();announce('All Parallax viewer mode. Sea Level through Sky are available and zoom controls their perceptual handoff.');return;
  }
  const s=stratumByKey(key);
  parallaxOverride=false;activeStratum=s.key;viewerZ=s.z;focusPath=[{level:'Parallax',key:s.key,label:bandDisplayName(s.key)}];
  focusSelected=focusOptions()[0]?.key||'';if(s.key==='sky')keyboardMode='Sky';else if(keyboardMode==='Sky')keyboardMode='Viewer';renderKeyboardTabs();
  renderState();announce(`${bandDisplayName(s.key)} selected. ${bandRangeText(s)}. Editing is locked to this physical altitude band.`);
}
function selectFocus(key){
  const match=focusOptions().find(o=>o.key===key);if(!match)return;
  if(focusPath.length===0){
    jumpStratum(match.key);
    return;
  }
  focusPath.push({level:match.level,key:match.key,label:match.label});
  focusSelected=focusOptions()[0]?.key||'';
  renderState();
  announce(match.level==='Entity'?`${match.label} selected. Battle Instance revealed.`:`${match.label} selected and locked automatically. ${nextLevel()} revealed.`);
}
function unlockFocus(){
  if(!focusPath.length)return;
  const removed=focusPath.pop();
  if(!focusPath.length){jumpStratum('all');announce(`Returned from ${removed.label} to All Parallax.`);return}
  const root=rootFocus();
  if(root&&root.key!=='all'){const s=stratumByKey(root.key);activeStratum=s.key;parallaxOverride=false;viewerZ=clampToLockedTier(viewerZ)}
  const opts=focusOptions();focusSelected=opts[0]?.key||'';
  renderState();announce(`Returned from ${removed.label} to ${nextLevel()}.`);
}
function rewindFocus(index){
  while(focusPath.length>index+1)focusPath.pop();
  const root=rootFocus();
  if(!root){jumpStratum('all');return}
  const s=stratumByKey(root.key);activeStratum=s.key;parallaxOverride=false;viewerZ=clampToLockedTier(viewerZ);
  focusSelected=focusOptions()[0]?.key||'';renderState();announce(`Focus returned to ${focusPath[index]?.label||'All Parallax'}.`);
}
function resetFocus(){jumpStratum('all')}
function resetFocus(){focusPath=[];focusSelected='all';parallaxOverride=true;renderState()}
function renderFocus(){
  const entityLocked=focusPath.some(p=>p.level==='Entity');
  battle.hidden=!entityLocked;
  if(entityLocked){const e=focusPath.find(p=>p.level==='Entity');battleText.textContent=`${e?.label||'Entity'} focus · tactical viewer representation. Canonical XYZ identity remains unchanged.`}
}
function renderState(){
  parallaxOverride=true;
  stage.dataset.parallaxScope='all';
  stage.dataset.editTier='';
  stage.dataset.viewerZ=String(viewerZ);
  renderFocus();applyTransform();renderKeyboardKeys()
}
const BASE_KEYBOARD_MODES=['Viewer','Weather','Sky','Image','Pixels','Tiles','Sprites','Labels','Litch','CAD','Stylus','Tethers','Metadata','Selected'];
function keyboardModes(){return BASE_KEYBOARD_MODES}
function toolKey(label,sub,fn,disabled=false){const b=document.createElement('button');b.type='button';b.disabled=disabled;b.innerHTML=`<strong>${label}</strong><small>${sub}</small>`;b.setAttribute('aria-label',label==='⛶'?'Fit map to screen':`${label}: ${sub}`);b.addEventListener('click',fn);return b}
function setTool(name){toolMode=name;announce(`${name} tool selected. Prototype tool mode changes controls only; world truth is not altered.`);renderKeyboardKeys()}
function renderKeyboardTabs(){const modes=keyboardModes();if(!modes.includes(keyboardMode))keyboardMode=modes[0];keyboardTabs.replaceChildren();modes.forEach(mode=>{const b=document.createElement('button');b.type='button';b.role='tab';b.textContent=mode;b.classList.toggle('active',mode===keyboardMode);b.setAttribute('aria-selected',String(mode===keyboardMode));b.addEventListener('click',()=>{keyboardMode=mode;renderKeyboardTabs();renderKeyboardKeys();announce(`${mode} keyboard opened.`)});keyboardTabs.append(b)})}
function renderKeyboardKeys(){
  if(!keyboardKeys)return;
  keyboardKeys.replaceChildren();
  const z=splitZ(viewerZ);
  if(keyboardMode==='Viewer'){
    keyboardKeys.append(
      toolKey('Z −','layer',()=>setViewerZ(viewerZ-1,'Editing plane moved down one layer')),
      toolKey('Z +','layer',()=>setViewerZ(viewerZ+1,'Editing plane moved up one layer')),
      toolKey('−','zoom',()=>{const r=stage.getBoundingClientRect();zoomAt(r.left+r.width/2,r.top+r.height/2,1/1.22)}),
      toolKey('+','zoom',()=>{const r=stage.getBoundingClientRect();zoomAt(r.left+r.width/2,r.top+r.height/2,1.22)}),
      toolKey('⛶','camera',fitMap)
    );
    const band=currentBand(),read=toolKey(`L${splitZ(viewerZ).layerOffset}`,bandDisplayName(band.key),()=>{},true);read.classList.add('readout');keyboardKeys.append(read);return;
  }
  if(keyboardMode==='Sky'){
    for(const type of CELESTIAL_TYPES)keyboardKeys.append(toolKey(type.glyph,type.name,()=>placeCelestial(type.key)));
    keyboardKeys.append(toolKey('PATH','draw orbit / route',beginPathDraw,!selectedCelestial),toolKey('ADV','astronomy',openCelestialAdvanced,!selectedCelestial),toolKey('DELETE','celestial',removeCelestial,!selectedCelestial));
    return;
  }
  if(keyboardMode==='Weather'){
    for(const type of WEATHER_TYPES)keyboardKeys.append(toolKey(type.glyph,type.name,()=>placeWeather(type.key)));
    return;
  }
  if(keyboardMode==='Image'){
    if(!selectedImage){keyboardKeys.append(toolKey('ADD','image',openImageUpload));return}
    keyboardKeys.append(
      toolKey('SIZE −','image',()=>{selectedImage.size=clamp(selectedImage.size-.1,.2,5);refreshUserImage(selectedImage)}),
      toolKey('SIZE +','image',()=>{selectedImage.size=clamp(selectedImage.size+.1,.2,5);refreshUserImage(selectedImage)}),
      toolKey('↺','rotate',()=>{selectedImage.rotation-=15;refreshUserImage(selectedImage)}),
      toolKey('↻','rotate',()=>{selectedImage.rotation+=15;refreshUserImage(selectedImage)}),
      toolKey('OP −','opacity',()=>{selectedImage.opacity=clamp(selectedImage.opacity-.1,.1,1);refreshUserImage(selectedImage)}),
      toolKey('OP +','opacity',()=>{selectedImage.opacity=clamp(selectedImage.opacity+.1,.1,1);refreshUserImage(selectedImage)}),
      toolKey(selectedImage.transparent?'TRANS ✓':'TRANS','background',()=>{selectedImage.transparent=!selectedImage.transparent;refreshUserImage(selectedImage);renderKeyboardKeys()}),
      toolKey('DELETE','image',removeSelectedImage)
    );return;
  }
  if(keyboardMode==='Selected'){
    keyboardKeys.append(toolKey('BACK','focus',unlockFocus,!focusPath.length),toolKey('HOME','All Parallax',resetFocus),toolKey('INSPECT','viewer',()=>setTool('Inspect')),toolKey('META','viewer',()=>setTool('Metadata')));return;
  }
  const sets={Pixels:['Select','Paint','Erase','Fill'],Tiles:['Library','Place','Rotate','Scale'],Sprites:['Library','Place','Play','Speed'],Labels:['New Label','Style','Anchor','Offset'],Litch:['Light','Shadow','Intensity','Falloff'],CAD:['Line','Shape','Measure','Snap'],Stylus:['Draw','Pressure','Erase','Sample'],Tethers:['Link','Unlink','Anchor','Trace'],Metadata:['Inspect','Identity','Provenance','Relations']};
  (sets[keyboardMode]||['Inspect']).forEach(name=>keyboardKeys.append(toolKey(name,keyboardMode.toLowerCase(),()=>setTool(name))));
}
function openKeyboard(){keyboard.hidden=false;stage.classList.add('keyboard-open');keyboardToggle.setAttribute('aria-expanded','true');keyboardToggle.setAttribute('aria-label','Close World Builder keyboard');renderKeyboardTabs();renderKeyboardKeys();announce(`${keyboardMode} keyboard opened over viewer. Viewer size unchanged.`)}
function closeKeyboard(){keyboard.hidden=true;stage.classList.remove('keyboard-open');keyboardToggle.setAttribute('aria-expanded','false');keyboardToggle.setAttribute('aria-label','Open World Builder keyboard');announce('Keyboard hidden. Viewer unobstructed.')}

MAP_TRUTH.assets.forEach(asset=>{
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
imageUploadClose.addEventListener('click',closeImageUpload);
imageBrowse.addEventListener('click',()=>imageFile.click());
imageFile.addEventListener('change',()=>{const file=imageFile.files?.[0];if(file)void placeUploadedImage(file);imageFile.value=''});
imageDropzone.addEventListener('click',event=>{if(event.target===imageDropzone)imageFile.click()});
imageDropzone.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();imageFile.click()}});
for(const type of ['dragenter','dragover'])imageDropzone.addEventListener(type,event=>{event.preventDefault();event.stopPropagation();imageDropzone.classList.add('dragover')});
for(const type of ['dragleave','drop'])imageDropzone.addEventListener(type,event=>{event.preventDefault();event.stopPropagation();imageDropzone.classList.remove('dragover')});
imageDropzone.addEventListener('drop',event=>{const file=[...(event.dataTransfer?.files||[])].find(f=>f.type.startsWith('image/'));if(file)void placeUploadedImage(file)});
celestialAdvancedClose.addEventListener('click',closeCelestialAdvanced);
celestialAdvancedForm.addEventListener('submit',saveCelestialAdvanced);
$('keyboardClose').addEventListener('click',closeKeyboard);

stage.addEventListener('wheel',e=>{if(e.target instanceof Element&&e.target.closest('[data-ui]'))return;e.preventDefault();zoomAt(e.clientX,e.clientY,e.deltaY<0?1.12:1/1.12)},{passive:false});
stage.addEventListener('pointerdown',e=>{
  if(e.target instanceof Element&&e.target.closest('[data-ui]'))return;
  if(pathDraw?.item){e.preventDefault();const p=normalizedWorldPoint(e.clientX,e.clientY);pathDraw.pointerId=e.pointerId;pathDraw.item.pathPoints=[p];refreshCelestialPath(pathDraw.item);stage.setPointerCapture?.(e.pointerId);return}
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
  if(pathDraw?.pointerId===e.pointerId){e.preventDefault();const p=normalizedWorldPoint(e.clientX,e.clientY),last=pathDraw.item.pathPoints.at(-1);if(!last||Math.hypot(p.x-last.x,p.y-last.y)>.004){pathDraw.item.pathPoints.push(p);refreshCelestialPath(pathDraw.item)}return}
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
  if(pathDraw?.pointerId===e.pointerId){stage.releasePointerCapture?.(e.pointerId);stage.classList.remove('path-draw');announce('Celestial path saved.');pathDraw=null;return}
  pointers.delete(e.pointerId);
  if(!pointers.size){panStart=pinchStart=null;stage.classList.remove('dragging')}
  else if(pointers.size===1){const[r]=[...pointers.values()];panStart={pointerX:r.x,pointerY:r.y,x,y};pinchStart=null}
}
stage.addEventListener('pointerup',release);
stage.addEventListener('pointercancel',release);
window.addEventListener('resize',fitMap,{passive:true});
document.addEventListener('keydown',e=>{if(e.key!=='Escape')return;if(!celestialAdvancedPanel.hidden){closeCelestialAdvanced();return}if(pathDraw){pathDraw=null;stage.classList.remove('path-draw');announce('Path drawing canceled.');return}if(!viewerSettingsPanel.hidden){closeViewerSettings();return}if(!imageUploadPanel.hidden){closeImageUpload();return}if(!keyboard.hidden)closeKeyboard()});

window.ShaelvienPrototype=Object.freeze({
  mapTruth:MAP_TRUTH,
  getViewerState:()=>({viewerZ,...splitZ(viewerZ),parallaxOverride:true,lockedTier:null,editableTier:null,visibleTierWindow:null,parallax:lastMix,focusPath:focusPath.map(v=>({...v})),focusSelected,keyboardOpen:!keyboard.hidden,keyboardMode,toolMode})
});
focusSelected='all';
renderKeyboardTabs();
renderState();
})();