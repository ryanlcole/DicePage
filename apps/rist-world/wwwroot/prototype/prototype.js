(() => {
'use strict';
const QUERY=new URLSearchParams(location.search);
const LIVE_WORLDBUILDER=QUERY.get('live-worldbuilder')==='1';
const WORLD_ID=QUERY.get('worldId')||'';
const WORLD_NAME=QUERY.get('worldName')||'';
const WORLD_SEED=QUERY.get('seed')||(LIVE_WORLDBUILDER?'empty':'geonaph');
const IS_GEONAPH_SEED=WORLD_SEED==='geonaph';
const ASSET_ROOT='https://d2d6rnm6fnsp89.cloudfront.net/library/terrains/standard/world/whole_maps/geonaph/';
const TIERS=Object.freeze([
  Object.freeze({key:'sea',label:'Sea Level',index:0,glyph:'≈'}),
  Object.freeze({key:'hills',label:'Hills / Low Clouds',index:1,glyph:'⌁'}),
  Object.freeze({key:'mountains',label:'Mountains / Weather',index:2,glyph:'▲'})
]);
const BASE_WORLD_ASSETS=Object.freeze(IS_GEONAPH_SEED?[
  Object.freeze({key:'surface',tier:0,file:'geonaph_full_static_canonical_surface_v001.png',upscaleFile:'./upscale/geonaph_full_static_canonical_surface_v001_2x.png'}),
  Object.freeze({key:'highlands',tier:1,file:'geonaph_full_static_highlands_rivers_v001.png',upscaleFile:'./upscale/geonaph_full_static_highlands_rivers_v001_2x.png'}),
  Object.freeze({key:'mountains',tier:2,file:'geonaph_full_static_mountain_volcanic_archipelago_v001.png',upscaleFile:'./upscale/geonaph_full_static_mountain_volcanic_archipelago_v001_2x.png'})
]:[]);
const BASE_LAYER_COUNT=BASE_WORLD_ASSETS.length;
const TIER_NAMES_KEY='rist.worldbuilder.tierNames.v1.'+(WORLD_ID||'prototype');
const UPSCALE_KEY='rist.worldbuilder.upscale.v1.'+(WORLD_ID||WORLD_SEED||'prototype');
const tierNames=(()=>{try{return JSON.parse(localStorage.getItem(TIER_NAMES_KEY)||'{}')||{}}catch{return{}}})();
let upscaleEnabled=(()=>{try{const saved=localStorage.getItem(UPSCALE_KEY);return saved===null?IS_GEONAPH_SEED:saved==='on'}catch{return IS_GEONAPH_SEED}})();
const upscaleCache=new Map();
const $=id=>document.getElementById(id);
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
const smoothstep=(a,b,v)=>{const t=clamp((v-a)/(b-a),0,1);return t*t*(3-2*t)};
const reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
const stage=$('stage'),world=$('world'),surface=$('surfacePlane'),highlands=$('highlandsPlane'),mountains=$('mountainPlane'),loading=$('loading'),battle=$('battleInstance'),battleText=$('battleText'),keyboard=$('viewerKeyboard'),keyboardToggle=$('keyboardToggle'),persistentSave=$('persistentSave'),imageUploadToggle=$('imageUploadToggle'),tierToggle=$('tierToggle'),tierGlyph=$('tierGlyph'),tierMenu=$('tierMenu'),settingsToggle=$('settingsToggle'),viewerSettingsPanel=$('viewerSettingsPanel'),viewerSettingsClose=$('viewerSettingsClose'),settingsFit=$('settingsFit'),settingsResetTilt=$('settingsResetTilt'),settingsUpscale=$('settingsUpscale'),settingsUpscaleLabel=$('settingsUpscaleLabel'),settingsStartMenu=$('settingsStartMenu'),imageUploadPanel=$('imageUploadPanel'),imageUploadClose=$('imageUploadClose'),imageDropzone=$('imageDropzone'),imageBrowse=$('imageBrowse'),imageFile=$('imageFile'),imageX=$('imageX'),imageY=$('imageY'),imageTier=$('imageTier'),imageLayer=$('imageLayer'),imageTransparency=$('imageTransparency'),spriteUploadPanel=$('spriteUploadPanel'),spriteUploadClose=$('spriteUploadClose'),spriteDropzone=$('spriteDropzone'),spriteBrowse=$('spriteBrowse'),spriteFile=$('spriteFile'),spriteColumns=$('spriteColumns'),spriteRows=$('spriteRows'),spriteFps=$('spriteFps'),spriteFrameCount=$('spriteFrameCount'),keyboardTabs=$('keyboardTabs'),keyboardKeys=$('keyboardKeys'),live=$('live');
const planeByKey={surface,highlands,mountains};
const layerReady={surface:false,highlands:false,mountains:false};
const pointers=new Map();
let naturalWidth=1,naturalHeight=1,scale=1,minScale=.1,maxScale=12,x=0,y=0,fitX=0,fitY=0,panStart=null,pinchStart=null,keyboardMode='Viewer',toolMode='Inspect',tiltBaseline=null,tiltTargetX=0,tiltTargetY=0,tiltX=0,tiltY=0,tiltFrame=0,selectedImage=null,imageDrag=null,viewerTier='all',viewerLayer=0,upscaleStarted=false;
const userLayers=[];
const WORLDBUILDER_SAVE_DB='rist-worldbuilder-prototype-v1';
const WORLDBUILDER_SAVE_STORE='worlds';
const WORLDBUILDER_SAVE_KEY=WORLD_ID||WORLD_SEED||'prototype';
let restoreSaveStarted=false;
const TILE_LIBRARY_URL='../assets/drive-tiles/catalog.json?v=20260918-tiles-keyboard-1';
const TILE_LIBRARY_PAGE_SIZE=12;
const WORLD_TERRAIN_FOLDERS=Object.freeze(['Vent Fields','Canyons','Lakes','Rivers','Cliffs','Volcano','Ice','Snow','Mountains','Hills','Desert','Swamp','Jungle','Forest','Plains','Beach','Coast','Ocean']);
let tileCatalog=[],tileLibraryFolder=null,tileLibraryPage=0,tileLibraryLoading=false,tileLibraryError='';
const SPRITE_LIBRARY_URL='../assets/sprites/catalog.json?v=20260918-prototype-sprites-1';
const SPRITE_LIBRARY_PAGE_SIZE=12;
let spriteCatalog=[],spriteLibraryFolder=null,spriteLibraryPage=0,spriteLibraryLoading=false,spriteLibraryError='';
const spriteTimers=new Map();
const REGION_ENHANCE_ENTER=4.25;
const REGION_ENHANCE_EXIT=3.6;
const REGION_ENHANCE_DELAY=140;
const REGION_ENHANCE_MAX_DPR=2;
const IMAGE_PASS_COVERAGE=1;
const IMAGE_RETURN_COVERAGE=.9;
const regionSourceCache=new Map();
let regionEnhanceCanvas=null,regionEnhanceTimer=0,regionEnhanceToken=0,regionEnhanceActive=false,regionEnhanceRendering=false,regionCameraRevision=0;
const collisionMasks=new Map();
const COLLISION_MASK_MAX=512;

function collisionSource(node){return String(node?.currentSrc||node?.src||'')}
async function primeCollisionMask(src){
  src=String(src||'');
  if(!src)return null;
  const existing=collisionMasks.get(src);
  if(existing)return existing.promise;
  const record={ready:false,failed:false,width:0,height:0,alpha:null,promise:null};
  record.promise=(async()=>{
    try{
      const response=await fetch(src,{mode:'cors',cache:'force-cache'});
      if(!response.ok)throw new Error('collision source unavailable');
      const blob=await response.blob();
      const bitmap=await createImageBitmap(blob);
      const ratio=Math.min(1,COLLISION_MASK_MAX/Math.max(bitmap.width,bitmap.height));
      const width=Math.max(1,Math.round(bitmap.width*ratio)),height=Math.max(1,Math.round(bitmap.height*ratio));
      const canvas=document.createElement('canvas');canvas.width=width;canvas.height=height;
      const ctx=canvas.getContext('2d',{willReadFrequently:true});
      ctx.clearRect(0,0,width,height);ctx.drawImage(bitmap,0,0,width,height);bitmap.close?.();
      const rgba=ctx.getImageData(0,0,width,height).data,alpha=new Uint8Array(width*height);
      for(let i=0,p=3;i<alpha.length;i++,p+=4)alpha[i]=rgba[p];
      record.width=width;record.height=height;record.alpha=alpha;record.ready=true;
    }catch{record.failed=true}
    return record;
  })();
  collisionMasks.set(src,record);
  return record.promise;
}
function sourceCollides(src,nx,ny){
  if(nx<0||nx>1||ny<0||ny>1)return false;
  const record=collisionMasks.get(src);
  if(!record){void primeCollisionMask(src);return false}
  if(!record.ready||record.failed||!record.alpha)return false;
  const ix=clamp(Math.floor(nx*record.width),0,record.width-1),iy=clamp(Math.floor(ny*record.height),0,record.height-1);
  return record.alpha[(iy*record.width)+ix]>0;
}
function builtinCollision(node,key,clientX,clientY){
  if(!node||!layerReady[key])return null;
  const opacity=Number(getComputedStyle(node).opacity);
  if(!(opacity>0))return null;
  const rect=node.getBoundingClientRect();
  if(rect.width<1||rect.height<1||clientX<rect.left||clientX>rect.right||clientY<rect.top||clientY>rect.bottom)return null;
  const nx=(clientX-rect.left)/rect.width,ny=(clientY-rect.top)/rect.height,src=collisionSource(node);
  if(!sourceCollides(src,nx,ny))return null;
  return{kind:'builtin',node,key,nx,ny,src};
}
function userImageBaseSize(item){
  const node=item?.node;
  const baseW=naturalWidth*.12;
  const aspect=(node?.naturalWidth>0&&node?.naturalHeight>0)?node.naturalHeight/node.naturalWidth:1;
  return{width:baseW*Math.max(Number(item?.size)||1,.00001),height:(baseW*aspect)*Math.max(Number(item?.size)||1,.00001)};
}
function userImageCoverageAtScale(item,targetScale=scale){
  const r=stage.getBoundingClientRect(),size=userImageBaseSize(item),s=Math.max(Number(targetScale)||scale,.00001);
  if(r.width<1||r.height<1)return 0;
  return Math.min((size.width*s)/r.width,(size.height*s)/r.height);
}
function passUserImage(item){
  if(!item||item.zoomPassed)return false;
  item.zoomPassed=true;
  item.zoomPassScale=scale;
  item.node?.setAttribute('data-zoom-passed','true');
  stage.dataset.zoomPassedImage=item.id||'user-image';
  return true;
}
function restorePassedImages(targetScale){
  let restored=false;
  for(const item of userLayers){
    if(!item?.zoomPassed)continue;
    if(userImageCoverageAtScale(item,targetScale)>IMAGE_RETURN_COVERAGE)continue;
    item.zoomPassed=false;item.zoomPassScale=null;item.node?.removeAttribute('data-zoom-passed');restored=true;
  }
  if(restored)stage.dataset.zoomPassedImage='';
  return restored;
}
function prepareZoomCollision(clientX,clientY,oldScale,nextScale,existing=null){
  const restored=nextScale<oldScale?restorePassedImages(nextScale):false;
  let hit=restored?collisionAt(clientX,clientY):(existing??collisionAt(clientX,clientY));
  if(nextScale>oldScale&&hit?.kind==='user'&&userImageCoverageAtScale(hit.item,oldScale)>=IMAGE_PASS_COVERAGE){
    passUserImage(hit.item);
    hit=collisionAt(clientX,clientY);
  }
  return hit;
}
function userCollision(item,clientX,clientY){
  if(!item?.node||item.zoomPassed)return null;
  const visible=viewerTier==='all'||item.tier===tierByKey(viewerTier).index;
  if(!visible||!(Number(item.opacity)>0))return null;
  const r=stage.getBoundingClientRect(),worldX=(clientX-r.left-x)/Math.max(scale,.00001),worldY=(clientY-r.top-y)/Math.max(scale,.00001);
  const baseW=naturalWidth*.12,aspect=(item.node.naturalWidth>0&&item.node.naturalHeight>0)?item.node.naturalHeight/item.node.naturalWidth:1,baseH=baseW*aspect;
  const centerX=(item.x*naturalWidth)+(Number(item.parallaxX)||0),centerY=(item.y*naturalHeight)+(Number(item.parallaxY)||0);
  const rad=-(Number(item.rotation)||0)*Math.PI/180,c=Math.cos(rad),s=Math.sin(rad),size=Math.max(Number(item.size)||1,.00001);
  const dx=(worldX-centerX)/size,dy=(worldY-centerY)/size;
  const localX=(dx*c)-(dy*s)+(baseW/2),localY=(dx*s)+(dy*c)+(baseH/2);
  const nx=localX/Math.max(baseW,.00001),ny=localY/Math.max(baseH,.00001);
  const src=item.kind==='sprite'?collisionSource(item.node):(item.transparent&&item.transparentSrc?item.transparentSrc:item.originalSrc);
  if(!sourceCollides(src,nx,ny))return null;
  return{kind:'user',item,nx,ny,src};
}
function collisionAt(clientX,clientY){
  const ordered=[...userLayers].sort((a,b)=>((b.tier*100)+b.layer+(b.stackOrder||0)/100)-((a.tier*100)+a.layer+(a.stackOrder||0)/100));
  for(const item of ordered){const hit=userCollision(item,clientX,clientY);if(hit)return hit}
  for(const [node,key] of [[mountains,'mountains'],[highlands,'highlands']]){const hit=builtinCollision(node,key,clientX,clientY);if(hit)return hit}
  return null;
}
function collisionScreenPoint(hit){
  if(!hit)return null;
  if(hit.kind==='builtin'){
    const rect=hit.node.getBoundingClientRect();
    return{x:rect.left+(hit.nx*rect.width),y:rect.top+(hit.ny*rect.height)};
  }
  const item=hit.item,node=item?.node;
  if(!node)return null;
  const baseW=naturalWidth*.12,aspect=(node.naturalWidth>0&&node.naturalHeight>0)?node.naturalHeight/node.naturalWidth:1,baseH=baseW*aspect,size=Math.max(Number(item.size)||1,.00001);
  let lx=(hit.nx-.5)*baseW*size,ly=(hit.ny-.5)*baseH*size;
  const rad=(Number(item.rotation)||0)*Math.PI/180,c=Math.cos(rad),s=Math.sin(rad),rx=(lx*c)-(ly*s),ry=(lx*s)+(ly*c);
  const wx=(item.x*naturalWidth)+(Number(item.parallaxX)||0)+rx,wy=(item.y*naturalHeight)+(Number(item.parallaxY)||0)+ry,r=stage.getBoundingClientRect();
  return{x:r.left+x+(wx*scale),y:r.top+y+(wy*scale)};
}
function settleCollisionAnchor(hit,clientX,clientY){
  if(!hit)return;
  for(let i=0;i<2;i++){
    const point=collisionScreenPoint(hit);if(!point)break;
    const dx=clientX-point.x,dy=clientY-point.y;
    if(Math.abs(dx)<.05&&Math.abs(dy)<.05)break;
    x+=dx;y+=dy;applyTransform();
  }
  stage.dataset.zoomCollision=hit.kind==='user'?'user-image':hit.key;
}
function announce(text){live.textContent='';requestAnimationFrame(()=>{live.textContent=text})}
function openSaveDb(){
  return new Promise((resolve,reject)=>{
    if(!('indexedDB'in window)){reject(new Error('IndexedDB unavailable'));return}
    const request=indexedDB.open(WORLDBUILDER_SAVE_DB,1);
    request.onupgradeneeded=()=>{const db=request.result;if(!db.objectStoreNames.contains(WORLDBUILDER_SAVE_STORE))db.createObjectStore(WORLDBUILDER_SAVE_STORE)};
    request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error||new Error('Save database unavailable'));
  });
}
async function writeSavedWorldBuilder(state){
  const db=await openSaveDb();
  try{
    await new Promise((resolve,reject)=>{
      const tx=db.transaction(WORLDBUILDER_SAVE_STORE,'readwrite');
      tx.objectStore(WORLDBUILDER_SAVE_STORE).put(state,WORLDBUILDER_SAVE_KEY);
      tx.oncomplete=()=>resolve();tx.onerror=()=>reject(tx.error||new Error('Save failed'));tx.onabort=()=>reject(tx.error||new Error('Save aborted'));
    });
  }finally{db.close()}
}
async function readSavedWorldBuilder(){
  const db=await openSaveDb();
  try{
    return await new Promise((resolve,reject)=>{
      const tx=db.transaction(WORLDBUILDER_SAVE_STORE,'readonly'),request=tx.objectStore(WORLDBUILDER_SAVE_STORE).get(WORLDBUILDER_SAVE_KEY);
      request.onsuccess=()=>resolve(request.result||null);request.onerror=()=>reject(request.error||new Error('Load failed'));
    });
  }finally{db.close()}
}
function serializableUserLayer(item){
  return{
    id:item.id,assetId:item.assetId||null,name:item.name||'',libraryTile:!!item.libraryTile,kind:item.kind||'image',
    originalSrc:item.originalSrc||'',transparentSrc:item.transparentSrc||'',transparent:!!item.transparent,
    spriteSheetSrc:item.spriteSheetSrc||null,spriteColumns:item.spriteColumns||null,spriteRows:item.spriteRows||null,
    spriteFrameCount:item.spriteFrameCount||null,spriteFps:item.spriteFps||null,spriteSourceWidth:item.spriteSourceWidth||null,
    spriteSourceHeight:item.spriteSourceHeight||null,spriteCropX:item.spriteCropX||0,spriteCropY:item.spriteCropY||0,
    spriteCropWidth:item.spriteCropWidth||null,spriteCropHeight:item.spriteCropHeight||null,spriteWhiteTransparent:item.spriteWhiteTransparent!==false,
    x:clamp(Number(item.x)||0,0,1),y:clamp(Number(item.y)||0,0,1),tier:clamp(Math.trunc(Number(item.tier)||0),0,TIERS.length-1),
    layer:clamp(Math.trunc(Number(item.layer)||0),0,9),size:clamp(Number(item.size)||1,.05,20),
    rotation:Number(item.rotation)||0,opacity:clamp(Number(item.opacity)||1,.01,1),committed:true
  };
}
async function saveWorldBuilder(){
  if(!persistentSave)return false;
  persistentSave.disabled=true;persistentSave.classList.add('saving');persistentSave.classList.remove('saved');
  try{
    const state={
      format:'RIST_WORLDBUILDER_PROTOTYPE',version:1,worldId:WORLD_ID,worldSeed:WORLD_SEED,savedAt:new Date().toISOString(),
      viewerTier,viewerLayer,userLayers:userLayers.map(serializableUserLayer)
    };
    await writeSavedWorldBuilder(state);
    for(const item of userLayers){
      item.committed=true;refreshUserImage(item);
      if(item.kind==='sprite'&&Array.isArray(item.frameSources)&&item.frameSources.length>1)startSpriteMotion(item);
    }
    deselectUserImage(false);
    persistentSave.classList.add('saved');
    setTimeout(()=>persistentSave?.classList.remove('saved'),900);
    announce(`World Builder saved. ${state.userLayers.length} placed image layer${state.userLayers.length===1?'':'s'} committed. Use the Select keyboard to edit saved content.`);
    return true;
  }catch(error){
    announce(`Save failed: ${String(error?.message||error||'unknown error')}`);
    return false;
  }finally{
    persistentSave.disabled=false;persistentSave.classList.remove('saving');
  }
}
async function attachRestoredLayer(raw){
  if(!raw?.originalSrc&&!raw?.spriteSheetSrc)return null;
  const kind=String(raw.kind||'image').toLowerCase(),isSprite=kind==='sprite';
  let frameSources=[];
  if(isSprite){
    const sheet=String(raw.spriteSheetSrc||raw.originalSrc||'');
    try{
      frameSources=await extractSpriteFrames(sheet,{
        columns:raw.spriteColumns||1,rows:raw.spriteRows||1,frameCount:raw.spriteFrameCount||1,
        sourceWidth:raw.spriteSourceWidth||0,sourceHeight:raw.spriteSourceHeight||0,
        cropX:raw.spriteCropX||0,cropY:raw.spriteCropY||0,cropWidth:raw.spriteCropWidth||0,cropHeight:raw.spriteCropHeight||0,
        whiteTransparent:raw.spriteWhiteTransparent!==false
      });
    }catch{frameSources=[String(raw.originalSrc||sheet)]}
  }
  const first=isSprite?(frameSources[0]||String(raw.originalSrc||raw.spriteSheetSrc||'')):String(raw.originalSrc||'');
  const item={
    id:String(raw.id||crypto.randomUUID?.()||Date.now()),assetId:raw.assetId||null,name:String(raw.name||''),libraryTile:!!raw.libraryTile,kind:isSprite?'sprite':'image',
    originalSrc:first,transparentSrc:String(raw.transparentSrc||first),transparent:isSprite?true:!!raw.transparent,
    spriteSheetSrc:isSprite?String(raw.spriteSheetSrc||raw.originalSrc||''):null,spriteColumns:Number(raw.spriteColumns)||null,spriteRows:Number(raw.spriteRows)||null,
    spriteFrameCount:isSprite?(Number(raw.spriteFrameCount)||frameSources.length):null,spriteFps:isSprite?Math.max(1,Number(raw.spriteFps)||6):null,
    spriteSourceWidth:Number(raw.spriteSourceWidth)||null,spriteSourceHeight:Number(raw.spriteSourceHeight)||null,spriteCropX:Number(raw.spriteCropX)||0,spriteCropY:Number(raw.spriteCropY)||0,
    spriteCropWidth:Number(raw.spriteCropWidth)||null,spriteCropHeight:Number(raw.spriteCropHeight)||null,spriteWhiteTransparent:raw.spriteWhiteTransparent!==false,
    frameSources,currentFrame:0,playing:false,
    x:clamp(Number(raw.x)||0,0,1),y:clamp(Number(raw.y)||0,0,1),tier:clamp(Math.trunc(Number(raw.tier)||0),0,TIERS.length-1),
    layer:clamp(Math.trunc(Number(raw.layer)||0),0,9),size:clamp(Number(raw.size)||1,.05,20),rotation:Number(raw.rotation)||0,
    opacity:clamp(Number(raw.opacity)||1,.01,1),committed:raw.committed!==false,renderOpacity:1,zoomPassed:false,zoomPassScale:null,node:null
  };
  const node=document.createElement('img');node.className=`user-image-placement${item.libraryTile?' library-tile-placement':''}${isSprite?' sprite-placement':''}`;node.alt=item.name||(isSprite?'Placed sprite':'Placed image');node.draggable=false;item.node=node;
  node.addEventListener('pointerdown',event=>beginImageDrag(event,item));node.addEventListener('pointermove',moveImageDrag);node.addEventListener('pointerup',endImageDrag);node.addEventListener('pointercancel',endImageDrag);
  node.addEventListener('load',()=>{refreshUserImage(item);applyParallax();scheduleRegionEnhancement(30)},{once:true});
  userLayers.push(item);world.appendChild(node);refreshUserImage(item);
  if(item.committed&&isSprite&&frameSources.length>1)startSpriteMotion(item);
  return item;
}
async function restoreSavedWorldBuilder(){
  if(restoreSaveStarted)return;restoreSaveStarted=true;
  try{
    const state=await readSavedWorldBuilder();
    if(!state||state.format!=='RIST_WORLDBUILDER_PROTOTYPE'||String(state.worldId||'')!==String(WORLD_ID||''))return;
    userLayers.splice(0,userLayers.length);
    world.querySelectorAll('.user-image-placement').forEach(node=>node.remove());
    for(const raw of Array.isArray(state.userLayers)?state.userLayers:[])await attachRestoredLayer(raw);
    viewerTier=state.viewerTier==='all'?'all':tierByKey(state.viewerTier).key;
    viewerLayer=clamp(Math.trunc(Number(state.viewerLayer)||0),0,9);
    selectedImage=null;updateLayerOrder();updateTierButton();renderTierMenu();applyParallax();renderKeyboardKeys();scheduleRegionEnhancement(50);
    announce(`Saved World Builder restored. ${userLayers.length} placed image layer${userLayers.length===1?'':'s'} loaded.`);
  }catch{}
}
function ensureRegionEnhanceCanvas(){
  if(regionEnhanceCanvas?.isConnected)return regionEnhanceCanvas;
  const canvas=document.createElement('canvas');
  canvas.className='region-enhance-canvas';
  canvas.setAttribute('aria-hidden','true');
  stage.appendChild(canvas);
  regionEnhanceCanvas=canvas;
  return canvas;
}
function regionZoomRatio(){return scale/Math.max(minScale,.00001)}
function regionDetailWanted(){
  const ratio=regionZoomRatio();
  return layerReady.surface&&(regionEnhanceActive?ratio>=REGION_ENHANCE_EXIT:ratio>=REGION_ENHANCE_ENTER);
}
function suspendRegionEnhancement(){
  clearTimeout(regionEnhanceTimer);regionEnhanceTimer=0;regionEnhanceToken++;
  regionEnhanceCanvas?.classList.remove('active');
  stage.dataset.detailMode='world';
}
function invalidateRegionCamera(){
  regionCameraRevision++;
  suspendRegionEnhancement();
}
function regionRenderStillValid(token,revision){
  return token===regionEnhanceToken&&revision===regionCameraRevision&&regionDetailWanted();
}
async function regionBitmap(src){
  src=String(src||'');
  if(!src)return null;
  if(regionSourceCache.has(src))return regionSourceCache.get(src);
  const pending=(async()=>{
    try{
      const response=await fetch(src,{mode:'cors',cache:'force-cache'});
      if(!response.ok)throw new Error('region source unavailable');
      return await createImageBitmap(await response.blob());
    }catch{return null}
  })();
  regionSourceCache.set(src,pending);
  return pending;
}
function sharpenRegionPixels(ctx,width,height,strength=.34){
  if(width<3||height<3)return;
  const image=ctx.getImageData(0,0,width,height),data=image.data,src=new Uint8ClampedArray(data),row=width*4;
  for(let y=1;y<height-1;y++){
    let i=(y*width+1)*4;
    for(let x=1;x<width-1;x++,i+=4){
      for(let c=0;c<3;c++){
        const center=src[i+c];
        const lap=(center*4)-src[i-4+c]-src[i+4+c]-src[i-row+c]-src[i+row+c];
        data[i+c]=clamp(Math.round(((center-128)*1.025)+128+(lap*strength)),0,255);
      }
    }
  }
  ctx.putImageData(image,0,0);
}
async function renderRegionEnhancement(){
  regionEnhanceTimer=0;
  if(!regionDetailWanted()){regionEnhanceActive=false;suspendRegionEnhancement();return}
  if(regionEnhanceRendering){scheduleRegionEnhancement();return}
  const token=++regionEnhanceToken,revision=regionCameraRevision,canvas=ensureRegionEnhanceCanvas(),r=stage.getBoundingClientRect();
  if(r.width<2||r.height<2)return;
  regionEnhanceRendering=true;
  try{
    const entries=[
      {node:surface,key:'surface'},
      {node:highlands,key:'highlands'},
      {node:mountains,key:'mountains'}
    ];
    for(const entry of entries){
      if(!entry.node||!layerReady[entry.key])continue;
      entry.bitmap=await regionBitmap(collisionSource(entry.node));
      if(!regionRenderStillValid(token,revision))return;
    }
    const overlays=[...userLayers]
      .filter(item=>item?.node&&Number(item.renderOpacity)>0.001)
      .sort((a,b)=>((a.tier*100)+a.layer+(a.stackOrder||0)/100)-((b.tier*100)+b.layer+(b.stackOrder||0)/100));
    for(const item of overlays){
      const src=item.transparent&&item.transparentSrc?item.transparentSrc:item.originalSrc;
      item.regionBitmap=await regionBitmap(src);
      if(!regionRenderStillValid(token,revision))return;
    }
    if(!regionRenderStillValid(token,revision))return;
    const dpr=Math.min(Math.max(Number(devicePixelRatio)||1,1),REGION_ENHANCE_MAX_DPR);
    const width=Math.max(1,Math.round(r.width*dpr)),height=Math.max(1,Math.round(r.height*dpr));
    if(canvas.width!==width)canvas.width=width;if(canvas.height!==height)canvas.height=height;
    canvas.style.width=`${r.width}px`;canvas.style.height=`${r.height}px`;
    const ctx=canvas.getContext('2d',{willReadFrequently:true,alpha:true});
    if(!ctx)return;
    ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,r.width,r.height);ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality='high';
    for(const entry of entries){
      if(!entry.bitmap||!regionRenderStillValid(token,revision))return;
      const opacity=Number(getComputedStyle(entry.node).opacity);if(!(opacity>0.001))continue;
      const px=Number(entry.node.dataset.parallaxX)||0,py=Number(entry.node.dataset.parallaxY)||0;
      ctx.globalAlpha=clamp(opacity,0,1);
      ctx.drawImage(entry.bitmap,x+(px*scale),y+(py*scale),naturalWidth*scale,naturalHeight*scale);
    }
    ctx.globalAlpha=1;ctx.setTransform(1,0,0,1,0,0);
    if(!regionRenderStillValid(token,revision))return;
    sharpenRegionPixels(ctx,width,height,.34);
    if(!regionRenderStillValid(token,revision))return;

    ctx.setTransform(dpr,0,0,dpr,0,0);ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality='high';
    for(const item of overlays){
      const bitmap=item.regionBitmap;if(!bitmap||!regionRenderStillValid(token,revision))continue;
      const px=Number(item.parallaxX)||0,py=Number(item.parallaxY)||0;
      const centerX=x+((item.x*naturalWidth+px)*scale),centerY=y+((item.y*naturalHeight+py)*scale);
      const baseW=naturalWidth*.12,baseH=baseW*(bitmap.height/Math.max(bitmap.width,1));
      const w=baseW*Math.max(Number(item.size)||1,.00001)*scale,h=baseH*Math.max(Number(item.size)||1,.00001)*scale;
      ctx.save();
      ctx.globalAlpha=clamp(Number(item.renderOpacity??item.opacity)||0,0,1);
      ctx.translate(centerX,centerY);
      ctx.rotate((Number(item.rotation)||0)*Math.PI/180);
      ctx.drawImage(bitmap,-w/2,-h/2,w,h);
      if(item===selectedImage){
        ctx.globalAlpha=1;ctx.lineWidth=Math.max(1,2/dpr);ctx.strokeStyle='rgba(240,204,105,.95)';ctx.strokeRect(-w/2,-h/2,w,h);
      }
      ctx.restore();
    }
    ctx.globalAlpha=1;ctx.setTransform(1,0,0,1,0,0);
    if(!regionRenderStillValid(token,revision))return;
    const wasActive=regionEnhanceActive;regionEnhanceActive=true;
    stage.dataset.detailMode='region-enhanced';
    stage.dataset.detailScale=regionZoomRatio().toFixed(2);
    canvas.classList.add('active');
    if(!wasActive)announce('Region detail enhancement active. World truth is unchanged; this is a higher-detail working representation.');
  }finally{regionEnhanceRendering=false}
}
function scheduleRegionEnhancement(delay=REGION_ENHANCE_DELAY){
  clearTimeout(regionEnhanceTimer);
  if(!regionDetailWanted()){
    if(regionEnhanceActive){regionEnhanceActive=false;suspendRegionEnhancement()}
    return;
  }
  regionEnhanceTimer=setTimeout(()=>void renderRegionEnhancement(),Math.max(0,delay));
}
function updateUpscaleControl(){
  settingsUpscale?.setAttribute('aria-pressed',String(upscaleEnabled));
  settingsUpscale?.setAttribute('aria-label',upscaleEnabled?'Disable two times high resolution rendering':'Enable two times high resolution rendering');
  if(settingsUpscaleLabel)settingsUpscaleLabel.textContent=upscaleEnabled?'Upscale 2× On':'Upscale 2×';
  stage.classList.toggle('upscale-on',upscaleEnabled);
}
function canvasBlob(canvas){return new Promise(resolve=>canvas.toBlob(resolve,'image/png'))}
async function buildUpscaledRepresentation(asset){
  if(upscaleCache.has(asset.key))return upscaleCache.get(asset.key);
  const canonical=ASSET_ROOT+asset.file;
  if(asset.upscaleFile){
    try{
      const local=new URL(asset.upscaleFile,location.href).href;
      const probe=await fetch(local,{method:'HEAD',cache:'force-cache'});
      if(probe.ok){const result={url:local,factor:2,derived:true,buildTime:true};upscaleCache.set(asset.key,result);return result}
    }catch{}
  }
  try{
    const response=await fetch(canonical,{mode:'cors',cache:'force-cache'});
    if(!response.ok)throw new Error('asset fetch failed');
    const blob=await response.blob();
    const bitmap=await createImageBitmap(blob);
    const factor=Math.min(2,4096/Math.max(bitmap.width,bitmap.height));
    if(factor<=1.05){bitmap.close?.();const result={url:canonical,factor:1,derived:false};upscaleCache.set(asset.key,result);return result}
    const canvas=document.createElement('canvas');
    canvas.width=Math.max(1,Math.round(bitmap.width*factor));canvas.height=Math.max(1,Math.round(bitmap.height*factor));
    const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality='high';ctx.drawImage(bitmap,0,0,canvas.width,canvas.height);bitmap.close?.();
    const out=await canvasBlob(canvas);if(!out)throw new Error('upscale encoding failed');
    const result={url:URL.createObjectURL(out),factor,derived:true};upscaleCache.set(asset.key,result);return result;
  }catch{
    const result={url:canonical,factor:1,derived:false,fallback:true};upscaleCache.set(asset.key,result);return result;
  }
}
async function applyUpscalePreference(){
  updateUpscaleControl();
  maxScale=upscaleEnabled?24:12;
  if(!BASE_WORLD_ASSETS.length)return;
  if(!upscaleEnabled){
    for(const asset of BASE_WORLD_ASSETS){const node=planeByKey[asset.key];node.dataset.derivedUpscale='0';node.dataset.renderFactor='1';if(node.src!==ASSET_ROOT+asset.file)node.src=ASSET_ROOT+asset.file}
    stage.dataset.upscale='original';return;
  }
  stage.dataset.upscale='loading';
  const results=[];
  for(const asset of BASE_WORLD_ASSETS){
    const result=await buildUpscaledRepresentation(asset);results.push(result);
    if(!upscaleEnabled)break;
    const node=planeByKey[asset.key];node.dataset.derivedUpscale=result.derived?'1':'0';node.dataset.renderFactor=String(result.factor);if(node.src!==result.url)node.src=result.url;
  }
  stage.dataset.upscale=results.some(x=>x.derived)?'2x-derived':'browser-interpolation';
  announce(results.some(x=>x.derived)?'High resolution Geonaph representation active. Original world images remain canonical.':'Upscale enabled. Browser high-quality interpolation is active; canonical images are unchanged.');
}
async function toggleUpscale(){
  upscaleEnabled=!upscaleEnabled;try{localStorage.setItem(UPSCALE_KEY,upscaleEnabled?'on':'off')}catch{}
  updateUpscaleControl();
  if(upscaleEnabled&&!layerReady.surface){stage.dataset.upscale='waiting-for-canonical';announce('Upscale will activate after the canonical surface finishes loading.');return}
  upscaleStarted=upscaleEnabled;
  await applyUpscalePreference();
}
function tierByIndex(index){return TIERS.find(t=>t.index===index)||TIERS[0]}
function tierByKey(key){return TIERS.find(t=>t.key===key)||TIERS[0]}
function tierLabel(tier){return String(tierNames[tier.key]||'').trim()||tier.label}
function renameViewerTier(){
  if(viewerTier==='all'){announce('Select a tier before naming it.');return}
  const tier=tierByKey(viewerTier),next=prompt('Name this tier',String(tierNames[tier.key]||''));
  if(next===null)return;const value=String(next).trim().slice(0,60);if(value)tierNames[tier.key]=value;else delete tierNames[tier.key];
  try{localStorage.setItem(TIER_NAMES_KEY,JSON.stringify(tierNames))}catch{}
  updateTierButton();renderTierMenu();announce(value?`Tier named ${value}.`:'Custom tier name cleared.');
}
function currentTierIndex(){return viewerTier==='all'?0:tierByKey(viewerTier).index}
function updateLayerOrder(){
  userLayers.forEach((item,index)=>{item.stackOrder=index;item.node.style.zIndex=String(10+(item.tier*20)+item.layer+index/100);item.node.dataset.tier=String(item.tier);item.node.dataset.layer=String(item.layer)});
}
function closeTierMenu(){tierMenu.hidden=true;tierToggle.setAttribute('aria-expanded','false')}
function renderTierMenu(){
  tierMenu.replaceChildren();
  const options=[{key:'all',label:'All Parallax',glyph:'≋'},...TIERS];
  for(const option of options){
    const button=document.createElement('button');button.type='button';button.role='menuitemradio';button.textContent=option.glyph;button.setAttribute('aria-label',option.key==='all'?option.label:tierLabel(option));
    const selected=viewerTier===option.key;button.setAttribute('aria-checked',String(selected));button.setAttribute('aria-current',String(selected));
    button.addEventListener('click',()=>{setViewerTier(option.key);closeTierMenu();tierToggle.focus()});tierMenu.appendChild(button);
  }
}
function updateTierButton(){
  const option=viewerTier==='all'?{label:'All Parallax',glyph:'≋'}:tierByKey(viewerTier);tierGlyph.textContent=option.glyph;tierToggle.setAttribute('aria-label',`${viewerTier==='all'?option.label:tierLabel(option)}. Open tier selector`);
}
function setViewerTier(key){
  viewerTier=key==='all'?'all':tierByKey(key).key;viewerLayer=0;updateTierButton();renderTierMenu();applyTransform();scheduleRegionEnhancement(40);renderKeyboardKeys();announce(viewerTier==='all'?'All Parallax selected. Zoom blends through all world tiers.':`${tierLabel(tierByKey(viewerTier))} selected.`);
}
function moveSelectedTier(delta){
  if(!selectedImage)return;
  selectedImage.tier=clamp(selectedImage.tier+delta,0,TIERS.length-1);
  updateLayerOrder();applyParallax();renderKeyboardKeys();
  announce(`${selectedImage.kind==='sprite'?'Sprite':'Image'} moved to ${tierByIndex(selectedImage.tier).label} parallax tier.`);
}
function moveSelectedLayer(delta){
  if(!selectedImage)return;
  const maxSceneZ=(TIERS.length*10)-1,currentSceneZ=(selectedImage.tier*10)+selectedImage.layer,nextSceneZ=clamp(currentSceneZ+delta,0,maxSceneZ);
  selectedImage.tier=Math.floor(nextSceneZ/10);selectedImage.layer=nextSceneZ%10;
  updateLayerOrder();applyParallax();renderKeyboardKeys();
  announce(`${selectedImage.kind==='sprite'?'Sprite':'Image'} moved to tier ${selectedImage.tier}, layer ${selectedImage.layer}.`);
}
function placementAddress(tier,layerDelta=1){
  const maxSceneZ=(TIERS.length*10)-1,sceneZ=clamp((clamp(tier,0,TIERS.length-1)*10)+viewerLayer+layerDelta,0,maxSceneZ);
  return{tier:Math.floor(sceneZ/10),layer:sceneZ%10};
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
  const address=placementAddress(currentTierIndex(),1);
  imageTier.value=String(address.tier);imageLayer.value=String(address.layer);
  imageTransparency.checked=true;imageUploadPanel.hidden=false;stage.classList.add('image-upload-open');imageDropzone.focus();
  announce(`Image upload opened. Viewer frozen. Position defaults to ${tierLabel(tierByIndex(currentTierIndex()))}, layer ${viewerLayer}.`);
}function closeImageUpload(){imageUploadPanel.hidden=true;stage.classList.remove('image-upload-open');imageUploadToggle.focus()}
function fileDataUrl(file){return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result||''));reader.onerror=()=>reject(reader.error);reader.readAsDataURL(file)})}
function loadDataImage(src){return new Promise((resolve,reject)=>{const img=new Image();if(!String(src).startsWith('data:')&&!String(src).startsWith('blob:'))img.crossOrigin='anonymous';img.onload=()=>resolve(img);img.onerror=reject;img.src=src})}
function openSpriteUpload(){
  spriteColumns.value='3';spriteRows.value='2';spriteFps.value='6';spriteFrameCount.value='6';
  spriteUploadPanel.hidden=false;stage.classList.add('image-upload-open');spriteDropzone.focus();
  announce('Sprite upload opened. Frame one will be used for placement. Save will start animation.');
}
function closeSpriteUpload(){spriteUploadPanel.hidden=true;stage.classList.remove('image-upload-open');keyboardMode='Sprites';renderKeyboardTabs();renderKeyboardKeys()}
function syncSpriteFrameCount(){const cols=clamp(Math.trunc(Number(spriteColumns.value)||1),1,16),rows=clamp(Math.trunc(Number(spriteRows.value)||1),1,16);spriteFrameCount.value=String(cols*rows)}
function whitenToAlpha(data){
  const px=data.data;
  for(let i=0;i<px.length;i+=4){
    const min=Math.min(px[i],px[i+1],px[i+2]);
    if(min>=248){px[i+3]=0;continue}
    if(min>=228){px[i+3]=Math.round(px[i+3]*((248-min)/20))}
  }
  return data;
}
async function extractSpriteFrames(sheetSrc,options={}){
  const img=await loadDataImage(sheetSrc);
  const columns=clamp(Math.trunc(Number(options.columns)||1),1,32),rows=clamp(Math.trunc(Number(options.rows)||1),1,32);
  const frameCount=clamp(Math.trunc(Number(options.frameCount)||columns*rows),1,columns*rows);
  const sourceWidth=Math.max(1,Math.trunc(Number(options.sourceWidth)||img.naturalWidth||1));
  const sourceHeight=Math.max(1,Math.trunc(Number(options.sourceHeight)||img.naturalHeight||1));
  const cropX=Math.max(0,Math.trunc(Number(options.cropX)||0)),cropY=Math.max(0,Math.trunc(Number(options.cropY)||0));
  const cropWidth=Math.max(1,Math.trunc(Number(options.cropWidth)||Math.floor(sourceWidth/columns)));
  const cropHeight=Math.max(1,Math.trunc(Number(options.cropHeight)||Math.floor(sourceHeight/rows)));
  const frames=[];
  for(let frame=0;frame<frameCount;frame++){
    const column=frame%columns,row=Math.floor(frame/columns),sx=cropX+(column*cropWidth),sy=cropY+(row*cropHeight);
    const canvas=document.createElement('canvas');canvas.width=cropWidth;canvas.height=cropHeight;
    const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.clearRect(0,0,cropWidth,cropHeight);ctx.drawImage(img,sx,sy,cropWidth,cropHeight,0,0,cropWidth,cropHeight);
    if(options.whiteTransparent!==false){const image=ctx.getImageData(0,0,cropWidth,cropHeight);ctx.putImageData(whitenToAlpha(image),0,0)}
    frames.push(canvas.toDataURL('image/png'));
  }
  return frames;
}
function stopSpriteMotion(item){
  const timer=spriteTimers.get(item?.id);if(timer)clearTimeout(timer);if(item?.id)spriteTimers.delete(item.id);if(item)item.playing=false;
}
function startSpriteMotion(item){
  if(!item||item.kind!=='sprite'||!Array.isArray(item.frameSources)||item.frameSources.length<2)return;
  stopSpriteMotion(item);item.playing=true;
  const step=()=>{
    if(!item.playing||!item.committed||!item.node?.isConnected){stopSpriteMotion(item);return}
    item.currentFrame=((Number(item.currentFrame)||0)+1)%item.frameSources.length;
    refreshUserImage(item);
    spriteTimers.set(item.id,setTimeout(step,1000/Math.max(1,Number(item.spriteFps)||6)));
  };
  spriteTimers.set(item.id,setTimeout(step,1000/Math.max(1,Number(item.spriteFps)||6)));
}
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
  const spriteFrame=item.kind==='sprite'&&Array.isArray(item.frameSources)&&item.frameSources.length?item.frameSources[clamp(Math.trunc(Number(item.currentFrame)||0),0,item.frameSources.length-1)]:null;
  const desired=spriteFrame||(item.transparent&&item.transparentSrc?item.transparentSrc:item.originalSrc);
  if(item.renderedSrc!==desired){item.node.src=desired;item.renderedSrc=desired;void primeCollisionMask(desired)}
  item.node.style.left=`${item.x*naturalWidth}px`;item.node.style.top=`${item.y*naturalHeight}px`;
  item.node.style.opacity=String(item.renderOpacity??item.opacity);
  item.node.style.pointerEvents=item.committed&&selectedImage!==item?'none':'auto';
  item.node.dataset.committed=item.committed?'true':'false';
  const px=Number(item.parallaxX)||0,py=Number(item.parallaxY)||0;
  item.node.style.transform=`translate(-50%,-50%) translate3d(${px.toFixed(2)}px,${py.toFixed(2)}px,0) rotate(${item.rotation}deg) scale(${item.size})`;
}function selectUserImage(item){
  const previous=selectedImage;
  previous?.node?.classList.remove('selected');selectedImage=item||null;selectedImage?.node?.classList.add('selected');
  if(previous&&previous!==selectedImage)refreshUserImage(previous);
  if(selectedImage)refreshUserImage(selectedImage);
  renderKeyboardKeys();scheduleRegionEnhancement(20);
}
function deselectUserImage(announceChange=false){
  if(!selectedImage)return false;
  const previous=selectedImage;
  previous.node?.classList.remove('selected');selectedImage=null;refreshUserImage(previous);renderKeyboardKeys();scheduleRegionEnhancement(20);
  if(announceChange)announce('Selection cleared.');
  return true;
}
function placedContentLabel(item,index){
  const name=String(item?.name||item?.assetId||'Placed image').trim()||'Placed image';
  return `${index+1}. ${name} · T${Number(item?.tier)||0} L${Number(item?.layer)||0}`;
}
function selectablePlacedContent(){
  return userLayers.filter(item=>item?.node);
}
function cyclePlacedSelection(delta=1){
  const items=selectablePlacedContent();
  if(!items.length){deselectUserImage(false);announce('No placed content to select.');return}
  const current=selectedImage?items.indexOf(selectedImage):-1;
  const next=current<0?(delta<0?items.length-1:0):(current+delta+items.length)%items.length;
  selectUserImage(items[next]);announce(`Selected ${placedContentLabel(items[next],next)}.`);
}
function placedContentSelect(){
  const select=document.createElement('select');select.className='placed-content-select';select.setAttribute('aria-label','Select existing placed content');
  const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent=userLayers.length?'Select existing content…':'No placed content';placeholder.disabled=!!userLayers.length;placeholder.selected=!selectedImage;select.appendChild(placeholder);
  selectablePlacedContent().forEach((item,index)=>{
    const option=document.createElement('option');option.value=item.id;option.textContent=placedContentLabel(item,index);option.selected=item===selectedImage;select.appendChild(option);
  });
  select.disabled=!userLayers.length;
  select.addEventListener('change',()=>{
    const item=userLayers.find(entry=>String(entry.id)===select.value);
    if(item){selectUserImage(item);announce(`${placedContentLabel(item,userLayers.indexOf(item))} selected.`)}
  });
  return select;
}
function removeSelectedImage(){if(!selectedImage)return;const doomed=selectedImage,index=userLayers.indexOf(doomed);stopSpriteMotion(doomed);doomed.node.remove();if(index>=0)userLayers.splice(index,1);selectedImage=null;updateLayerOrder();applyParallax();renderKeyboardKeys();announce('Placed content removed from the layer stack.')}
function beginImageDrag(event,item){
  if(item?.committed&&selectedImage!==item)return;
  event.preventDefault();event.stopPropagation();selectUserImage(item);item.node.setPointerCapture?.(event.pointerId);
  suspendRegionEnhancement();
  imageDrag={id:event.pointerId,item,startX:event.clientX,startY:event.clientY,x:item.x,y:item.y};
}
function moveImageDrag(event){
  if(!imageDrag||imageDrag.id!==event.pointerId)return;event.preventDefault();event.stopPropagation();
  imageDrag.item.x=clamp(imageDrag.x+(event.clientX-imageDrag.startX)/(Math.max(scale,.00001)*Math.max(naturalWidth,1)),0,1);
  imageDrag.item.y=clamp(imageDrag.y+(event.clientY-imageDrag.startY)/(Math.max(scale,.00001)*Math.max(naturalHeight,1)),0,1);
  refreshUserImage(imageDrag.item);
}
function endImageDrag(event){if(!imageDrag||imageDrag.id!==event.pointerId)return;imageDrag.item.node.releasePointerCapture?.(event.pointerId);imageDrag=null;scheduleRegionEnhancement(40)}
async function placeUploadedImage(file){
  if(!file?.type?.startsWith('image/')){announce('Choose an image file.');return}
  const originalSrc=await fileDataUrl(file),transparentSrc=await transparencyCandidate(originalSrc);
  const tier=clamp(Math.trunc(Number(imageTier.value)||0),0,TIERS.length-1),layer=clamp(Math.trunc(Number(imageLayer.value)||0),0,9);
  const item={
    id:crypto.randomUUID?.()||String(Date.now()),originalSrc,transparentSrc,transparent:!!imageTransparency.checked,
    x:clamp(Number(imageX.value)||0,0,1),y:clamp(Number(imageY.value)||0,0,1),tier,layer,size:1,rotation:0,opacity:1,committed:false,renderOpacity:1,zoomPassed:false,zoomPassScale:null,node:null
  };
  const node=document.createElement('img');node.className='user-image-placement';node.alt='Placed user image';node.draggable=false;item.node=node;
  node.addEventListener('pointerdown',event=>beginImageDrag(event,item));node.addEventListener('pointermove',moveImageDrag);node.addEventListener('pointerup',endImageDrag);node.addEventListener('pointercancel',endImageDrag);
  userLayers.push(item);world.appendChild(node);void primeCollisionMask(originalSrc);if(transparentSrc!==originalSrc)void primeCollisionMask(transparentSrc);updateLayerOrder();refreshUserImage(item);selectUserImage(item);closeImageUpload();keyboardMode='Image';openKeyboard();renderKeyboardTabs();renderKeyboardKeys();applyParallax();scheduleRegionEnhancement(30);
  announce(`Image placed above ${tierLabel(tierByIndex(tier))} as layer ${layer}. Image editing keyboard opened.`);
}
function tierMix(){
  if(viewerTier!=='all'){const index=tierByKey(viewerTier).index;return{surface:index===0?1:0,highlands:index===1?1:0,mountains:index===2?1:0}}
  const ratio=Math.max(.01,scale/Math.max(minScale,.00001));
  const peakToHighlands=smoothstep(1.00,1.60,ratio);
  const highlandsToSurface=smoothstep(1.45,2.75,ratio);
  return{
    surface:layerReady.surface?1:0,
    highlands:layerReady.highlands?clamp(1-highlandsToSurface,0,1):0,
    mountains:layerReady.mountains?clamp(.82*(1-peakToHighlands),0,1):0
  };
}
function applyParallax(){
  const dx=x-fitX,dy=y-fitY,mix=tierMix();
  const builtins=[
    {node:surface,key:'surface',sceneZ:0,alpha:mix.surface},
    {node:highlands,key:'highlands',sceneZ:4,alpha:mix.highlands},
    {node:mountains,key:'mountains',sceneZ:7,alpha:mix.mountains}
  ];
  for(const entry of builtins){
    entry.node.style.opacity=layerReady[entry.key]?String(clamp(Number(entry.alpha)||0,0,1)):'0';
    const depth=entry.sceneZ/10;
    const panStrength=depth*.055;
    const tiltStrength=.42+(depth*.78);
    const px=((-dx*panStrength)+(tiltX*tiltStrength))/Math.max(scale,.00001),py=((-dy*panStrength)+(tiltY*tiltStrength))/Math.max(scale,.00001);
    entry.node.dataset.parallaxX=px.toFixed(4);entry.node.dataset.parallaxY=py.toFixed(4);
    entry.node.style.transform=`translate3d(${px.toFixed(2)}px,${py.toFixed(2)}px,0)`;
  }
  for(const item of userLayers){
    const visible=viewerTier==='all'||item.tier===tierByKey(viewerTier).index;
    const depth=item.tier;
    const panStrength=depth*.022,tiltStrength=depth*.48;
    item.parallaxX=((-dx*panStrength)+(tiltX*tiltStrength))/Math.max(scale,.00001);
    item.parallaxY=((-dy*panStrength)+(tiltY*tiltStrength))/Math.max(scale,.00001);
    item.renderOpacity=visible&&!item.zoomPassed?item.opacity:0;refreshUserImage(item);
  }
}
function updateReadouts(){
  stage.dataset.worldId=WORLD_ID;
  stage.dataset.worldSeed=WORLD_SEED;
  stage.dataset.viewerTier=viewerTier;
  stage.dataset.viewerLayer=String(viewerLayer);
  stage.dataset.layerCount=String(BASE_LAYER_COUNT+userLayers.length);
  const label=viewerTier==='all'?'All Parallax':tierLabel(tierByKey(viewerTier));
  const worldLabel=WORLD_NAME?WORLD_NAME+' world. ':'';
  stage.setAttribute('aria-label',`Interactive tiered ${worldLabel}viewer. ${label}. Layer ${viewerLayer}. ${BASE_LAYER_COUNT+userLayers.length} total image layers.`);
}
function applyTransform(){
  invalidateRegionCamera();
  world.style.width=naturalWidth+'px';
  world.style.height=naturalHeight+'px';
  world.style.transform=`translate3d(${x}px,${y}px,0) scale(${scale})`;
  applyParallax();
  updateReadouts();
  scheduleRegionEnhancement();
}
function fitMap(){
  if(!naturalWidth||!naturalHeight)return;
  suspendRegionEnhancement();
  const r=stage.getBoundingClientRect();
  minScale=Math.min(r.width/naturalWidth,r.height/naturalHeight);
  scale=minScale;
  maxScale=Math.max(minScale*24,8);
  x=fitX=(r.width-naturalWidth*scale)/2;
  y=fitY=0;
  applyTransform();
}
function zoomAt(cx,cy,factor){
  suspendRegionEnhancement();
  const r=stage.getBoundingClientRect(),sx=cx-r.left,sy=cy-r.top,old=scale,next=clamp(old*factor,minScale*.75,maxScale);
  if(Math.abs(next-old)<.0001)return;
  const collision=prepareZoomCollision(cx,cy,old,next);
  const wx=(sx-x)/old,wy=(sy-y)/old;
  scale=next;
  x=sx-wx*scale;
  y=sy-wy*scale;
  applyTransform();
  if(collision)settleCollisionAnchor(collision,cx,cy);else stage.dataset.zoomCollision='world';
  scheduleRegionEnhancement();
}
function zoomCenter(factor){
  const r=stage.getBoundingClientRect();
  zoomAt(r.left+r.width/2,r.top+r.height/2,factor);
}
function bindTap(button,fn){
  let lastTouch=0;
  button.addEventListener('pointerup',event=>{
    if(event.pointerType!=='touch'&&event.pointerType!=='pen')return;
    event.preventDefault();event.stopPropagation();lastTouch=performance.now();fn();
  });
  button.addEventListener('click',event=>{
    if(performance.now()-lastTouch<500)return;
    event.stopPropagation();fn();
  });
}

function renderState(){applyTransform();renderKeyboardKeys()}
const BASE_KEYBOARD_MODES=['Viewer','Tiers','Select','Image','Pixels','Tiles','Sprites','Labels','Litch','CAD','Stylus','Tethers','Metadata'];
function keyboardModes(){return BASE_KEYBOARD_MODES}
function toolKey(label,sub,fn,disabled=false){const b=document.createElement('button');b.type='button';b.disabled=disabled;b.innerHTML=`<strong>${label}</strong><small>${sub}</small>`;b.setAttribute('aria-label',label==='⛶'?'Fit map to screen':`${label}: ${sub}`);b.addEventListener('click',fn);return b}
function tileLibraryAsset(raw){
  return{
    id:String(raw?.id||raw?.Id||''),
    name:String(raw?.name||raw?.Name||'Asset'),
    image:String(raw?.image||raw?.Image||''),
    layer:String(raw?.layer||raw?.Layer||''),
    directory:String(raw?.directory||raw?.Directory||''),
    folder:String(raw?.folder||raw?.Folder||''),
    kind:String(raw?.assetKind||raw?.AssetKind||'tile').toLowerCase()
  };
}
async function ensureTileLibrary(force=false){
  if(tileLibraryLoading)return;
  if(tileCatalog.length&&!force)return;
  tileLibraryLoading=true;tileLibraryError='';
  if(keyboardMode==='Tiles')renderKeyboardKeys();
  try{
    const response=await fetch(TILE_LIBRARY_URL,{cache:'force-cache'});
    if(!response.ok)throw new Error(`Tile library unavailable (${response.status})`);
    const raw=await response.json();
    tileCatalog=(Array.isArray(raw)?raw:[]).map(tileLibraryAsset).filter(asset=>
      asset.id&&asset.image&&asset.kind!=='sprite'&&asset.layer.toUpperCase()==='WORLD'&&asset.directory.toLowerCase()==='terrain'
    );
    if(!tileCatalog.length)throw new Error('No World terrain tiles are registered.');
    const folders=tileLibraryFolders();
    if(tileLibraryFolder&&!folders.includes(tileLibraryFolder))tileLibraryFolder=null;
    tileLibraryPage=0;
  }catch(error){
    tileCatalog=[];tileLibraryError=String(error?.message||error||'Tile library unavailable.');
  }finally{
    tileLibraryLoading=false;
    if(keyboardMode==='Tiles')renderKeyboardKeys();
  }
}
function tileLibraryFolders(){
  const present=new Set(tileCatalog.map(asset=>asset.folder).filter(Boolean));
  const canonical=WORLD_TERRAIN_FOLDERS.filter(folder=>present.has(folder));
  const extras=[...present].filter(folder=>!WORLD_TERRAIN_FOLDERS.includes(folder)).sort((a,b)=>a.localeCompare(b));
  return [...canonical,...extras];
}
function currentTileLibraryAssets(){
  if(!tileLibraryFolder)return[];
  return tileCatalog.filter(asset=>asset.folder===tileLibraryFolder);
}
function tileLibraryPageCount(){return Math.max(1,Math.ceil(currentTileLibraryAssets().length/TILE_LIBRARY_PAGE_SIZE))}
function tileLibraryPageAssets(){
  tileLibraryPage=clamp(tileLibraryPage,0,tileLibraryPageCount()-1);
  const start=tileLibraryPage*TILE_LIBRARY_PAGE_SIZE;
  return currentTileLibraryAssets().slice(start,start+TILE_LIBRARY_PAGE_SIZE);
}
function snapWorldCell(value){return(clamp(Math.floor(clamp(value,0,.999999)*30),0,29)+.5)/30}
function placeLibraryTile(asset){
  if(!asset?.image)return;
  const point=viewerCenterPosition(),item={
    id:`library:${asset.id}:${crypto.randomUUID?.()||Date.now()}`,
    assetId:asset.id,name:asset.name,libraryTile:true,
    originalSrc:asset.image,transparentSrc:asset.image,transparent:false,
    x:point.x,y:point.y,tier:placementAddress(currentTierIndex(),1).tier,layer:placementAddress(currentTierIndex(),1).layer,
    size:1,rotation:0,opacity:1,committed:false,renderOpacity:1,zoomPassed:false,zoomPassScale:null,node:null
  };
  const node=document.createElement('img');node.className='user-image-placement library-tile-placement';node.alt=asset.name;node.draggable=false;item.node=node;
  node.addEventListener('pointerdown',event=>beginImageDrag(event,item));node.addEventListener('pointermove',moveImageDrag);node.addEventListener('pointerup',endImageDrag);node.addEventListener('pointercancel',endImageDrag);
  userLayers.push(item);world.appendChild(node);void primeCollisionMask(asset.image);updateLayerOrder();refreshUserImage(item);selectUserImage(item);
  keyboardMode='Image';openKeyboard();renderKeyboardTabs();renderKeyboardKeys();applyParallax();scheduleRegionEnhancement(30);
  announce(`${asset.name} placed at the viewer center above ${tierLabel(tierByIndex(item.tier))} as layer ${item.layer}. Image editing keyboard opened.`);
}
function libraryTileKey(asset){
  const button=document.createElement('button');button.type='button';button.className='library-tile-key';button.setAttribute('aria-label',`${asset.name}. Tap to place this tile at the viewer center.`);
  const image=document.createElement('img');image.src=asset.image;image.alt='';image.loading='lazy';image.decoding='async';image.draggable=false;
  const label=document.createElement('small');label.textContent=asset.name;button.append(image,label);button.addEventListener('click',()=>placeLibraryTile(asset));return button;
}
function openTileLibraryFolder(folder){tileLibraryFolder=folder;tileLibraryPage=0;renderKeyboardKeys();announce(`${folder} tile folder opened.`)}
function closeTileLibraryFolder(){tileLibraryFolder=null;tileLibraryPage=0;renderKeyboardKeys();announce('World tile folders.')}
function resolveSpriteUrl(value){
  const raw=String(value||'');if(!raw)return'';
  if(/^(?:https?:|data:|blob:|\/)/i.test(raw))return raw;
  try{return new URL(raw.startsWith('assets/')?`../${raw}`:raw,location.href).href}catch{return raw}
}
function spriteLibraryAsset(raw){
  const image=resolveSpriteUrl(raw?.image||raw?.Image||'');
  const sourceWidth=Math.max(0,Math.trunc(Number(raw?.sourceWidth||raw?.SourceWidth)||0));
  const sourceHeight=Math.max(0,Math.trunc(Number(raw?.sourceHeight||raw?.SourceHeight)||0));
  const cropX=Math.max(0,Math.trunc(Number(raw?.cropX||raw?.CropX)||0)),cropY=Math.max(0,Math.trunc(Number(raw?.cropY||raw?.CropY)||0));
  const cropWidth=Math.max(0,Math.trunc(Number(raw?.cropWidth||raw?.CropWidth)||0)),cropHeight=Math.max(0,Math.trunc(Number(raw?.cropHeight||raw?.CropHeight)||0));
  const frameCount=Math.max(1,Math.trunc(Number(raw?.frameCount||raw?.FrameCount)||1)),fps=Math.max(1,Number(raw?.framesPerSecond||raw?.FramesPerSecond)||6);
  const columns=cropWidth&&sourceWidth?Math.max(1,Math.floor((sourceWidth-cropX)/cropWidth)):1;
  const rows=cropHeight&&sourceHeight?Math.max(1,Math.floor((sourceHeight-cropY)/cropHeight)):1;
  return{
    id:String(raw?.id||raw?.Id||''),name:String(raw?.name||raw?.Name||'Sprite'),image,
    folder:String(raw?.folder||raw?.Folder||'Sprites'),kind:String(raw?.assetKind||raw?.AssetKind||'sprite').toLowerCase(),
    defaultTierIndex:clamp(Math.trunc(Number(raw?.defaultTierIndex||raw?.DefaultTierIndex)||0),0,TIERS.length-1),
    defaultLayerOffset:clamp(Math.trunc(Number(raw?.defaultLayerOffset||raw?.DefaultLayerOffset)||0),0,9),
    frameCount,fps,sourceWidth,sourceHeight,cropX,cropY,cropWidth,cropHeight,columns,rows
  };
}
async function ensureSpriteLibrary(force=false){
  if(spriteLibraryLoading)return;if(spriteCatalog.length&&!force)return;
  spriteLibraryLoading=true;spriteLibraryError='';if(keyboardMode==='Sprites')renderKeyboardKeys();
  try{
    const response=await fetch(SPRITE_LIBRARY_URL,{cache:'force-cache'});if(!response.ok)throw new Error(`Sprite library unavailable (${response.status})`);
    const raw=await response.json();spriteCatalog=(Array.isArray(raw)?raw:[]).map(spriteLibraryAsset).filter(asset=>asset.id&&asset.image&&asset.kind==='sprite');
    if(!spriteCatalog.length)throw new Error('No registered sprites found.');
    if(spriteLibraryFolder&&!spriteCatalog.some(asset=>asset.folder===spriteLibraryFolder))spriteLibraryFolder=null;spriteLibraryPage=0;
  }catch(error){spriteCatalog=[];spriteLibraryError=String(error?.message||error||'Sprite library unavailable.')}
  finally{spriteLibraryLoading=false;if(keyboardMode==='Sprites')renderKeyboardKeys()}
}
function spriteLibraryFolders(){return[...new Set(spriteCatalog.map(asset=>asset.folder).filter(Boolean))].sort((a,b)=>a.localeCompare(b))}
function currentSpriteLibraryAssets(){return spriteLibraryFolder?spriteCatalog.filter(asset=>asset.folder===spriteLibraryFolder):[]}
function spriteLibraryPageCount(){return Math.max(1,Math.ceil(currentSpriteLibraryAssets().length/SPRITE_LIBRARY_PAGE_SIZE))}
function spriteLibraryPageAssets(){spriteLibraryPage=clamp(spriteLibraryPage,0,spriteLibraryPageCount()-1);const start=spriteLibraryPage*SPRITE_LIBRARY_PAGE_SIZE;return currentSpriteLibraryAssets().slice(start,start+SPRITE_LIBRARY_PAGE_SIZE)}
async function placeSpriteDefinition(definition){
  const point=viewerCenterPosition(),address=placementAddress(currentTierIndex(),1);
  const frames=await extractSpriteFrames(definition.sheetSrc,{
    columns:definition.columns,rows:definition.rows,frameCount:definition.frameCount,
    sourceWidth:definition.sourceWidth||0,sourceHeight:definition.sourceHeight||0,cropX:definition.cropX||0,cropY:definition.cropY||0,
    cropWidth:definition.cropWidth||0,cropHeight:definition.cropHeight||0,whiteTransparent:definition.whiteTransparent!==false
  });
  if(!frames.length)throw new Error('No sprite frames were extracted.');
  const item={
    id:definition.id||crypto.randomUUID?.()||String(Date.now()),assetId:definition.assetId||null,name:definition.name||'Sprite',kind:'sprite',libraryTile:false,
    spriteSheetSrc:definition.sheetSrc,spriteColumns:definition.columns,spriteRows:definition.rows,spriteFrameCount:frames.length,spriteFps:Math.max(1,Number(definition.fps)||6),
    spriteSourceWidth:definition.sourceWidth||null,spriteSourceHeight:definition.sourceHeight||null,spriteCropX:definition.cropX||0,spriteCropY:definition.cropY||0,
    spriteCropWidth:definition.cropWidth||null,spriteCropHeight:definition.cropHeight||null,spriteWhiteTransparent:definition.whiteTransparent!==false,
    frameSources:frames,currentFrame:0,playing:false,originalSrc:frames[0],transparentSrc:frames[0],transparent:true,
    x:point.x,y:point.y,tier:address.tier,layer:address.layer,size:1,rotation:0,opacity:1,committed:false,renderOpacity:1,zoomPassed:false,zoomPassScale:null,node:null
  };
  const node=document.createElement('img');node.className='user-image-placement sprite-placement';node.alt=item.name;node.draggable=false;item.node=node;
  node.addEventListener('pointerdown',event=>beginImageDrag(event,item));node.addEventListener('pointermove',moveImageDrag);node.addEventListener('pointerup',endImageDrag);node.addEventListener('pointercancel',endImageDrag);
  userLayers.push(item);world.appendChild(node);frames.forEach(frame=>void primeCollisionMask(frame));updateLayerOrder();refreshUserImage(item);selectUserImage(item);
  keyboardMode='Image';openKeyboard();renderKeyboardTabs();renderKeyboardKeys();applyParallax();scheduleRegionEnhancement(30);
  announce(`${item.name} placed using frame 1. Adjust its layer or parallax tier, then Save to commit and begin motion.`);
  return item;
}
async function placeUploadedSprite(file){
  if(!file?.type?.startsWith('image/')){announce('Choose a sprite sheet image.');return}
  try{
    const sheetSrc=await fileDataUrl(file),columns=clamp(Math.trunc(Number(spriteColumns.value)||3),1,16),rows=clamp(Math.trunc(Number(spriteRows.value)||2),1,16);
    const frameCount=clamp(Math.trunc(Number(spriteFrameCount.value)||columns*rows),1,columns*rows),fps=clamp(Number(spriteFps.value)||6,1,30);
    closeSpriteUpload();
    await placeSpriteDefinition({name:file.name||'Uploaded sprite',sheetSrc,columns,rows,frameCount,fps,whiteTransparent:true});
  }catch(error){announce(`Sprite upload failed: ${String(error?.message||error||'unknown error')}`)}
}
async function placeLibrarySprite(asset){
  try{
    await placeSpriteDefinition({
      id:`sprite:${asset.id}:${crypto.randomUUID?.()||Date.now()}`,assetId:asset.id,name:asset.name,sheetSrc:asset.image,
      columns:asset.columns,rows:asset.rows,frameCount:asset.frameCount,fps:asset.fps,sourceWidth:asset.sourceWidth,sourceHeight:asset.sourceHeight,
      cropX:asset.cropX,cropY:asset.cropY,cropWidth:asset.cropWidth,cropHeight:asset.cropHeight,whiteTransparent:false
    });
  }catch(error){announce(`Could not place ${asset.name}: ${String(error?.message||error||'sprite sheet unavailable')}`)}
}
function spriteLibraryKey(asset){
  const button=document.createElement('button');button.type='button';button.className='sprite-library-key';button.setAttribute('aria-label',`${asset.name}. Tap to place frame one at the viewer center.`);
  const preview=document.createElement('span');preview.className='sprite-library-preview';const image=document.createElement('img');image.src=asset.image;image.alt='';image.loading='lazy';image.decoding='async';image.draggable=false;
  if(asset.cropWidth&&asset.cropHeight&&asset.sourceWidth&&asset.sourceHeight){
    image.style.width=`${asset.sourceWidth*100/asset.cropWidth}%`;image.style.height=`${asset.sourceHeight*100/asset.cropHeight}%`;
    image.style.left=`${-(asset.cropX/asset.cropWidth)*100}%`;image.style.top=`${-(asset.cropY/asset.cropHeight)*100}%`;
  }else{image.style.width='100%';image.style.height='100%';image.style.objectFit='cover';image.style.left='0';image.style.top='0'}
  const label=document.createElement('small');label.textContent=asset.name;preview.append(image);button.append(preview,label);button.addEventListener('click',()=>void placeLibrarySprite(asset));return button;
}
function openSpriteLibraryFolder(folder){spriteLibraryFolder=folder;spriteLibraryPage=0;renderKeyboardKeys();announce(`${folder} sprite folder opened.`)}
function closeSpriteLibraryFolder(){spriteLibraryFolder=null;spriteLibraryPage=0;renderKeyboardKeys();announce('Sprite folders.')}
function setTool(name){toolMode=name;announce(`${name} tool selected. Prototype tool mode changes controls only; world truth is not altered.`);renderKeyboardKeys()}
function renderKeyboardTabs(){const modes=keyboardModes();if(!modes.includes(keyboardMode))keyboardMode=modes[0];keyboardTabs.replaceChildren();modes.forEach(mode=>{const b=document.createElement('button');b.type='button';b.role='tab';b.textContent=mode;b.classList.toggle('active',mode===keyboardMode);b.setAttribute('aria-selected',String(mode===keyboardMode));b.addEventListener('click',()=>{keyboardMode=mode;renderKeyboardTabs();renderKeyboardKeys();announce(`${mode} keyboard opened.`)});keyboardTabs.append(b)})}
function renderKeyboardKeys(){
  if(!keyboardKeys)return;
  keyboardKeys.replaceChildren();
  if(keyboardMode==='Viewer'){
    keyboardKeys.append(
      toolKey('−','zoom',()=>zoomCenter(1/1.22)),
      toolKey('+','zoom',()=>zoomCenter(1.22)),
      toolKey('⛶','camera',fitMap),
      toolKey('⌁','reset tilt',resetTilt)
    );return;
  }
  if(keyboardMode==='Tiers'){
    keyboardKeys.append(
      toolKey('≋','All Parallax',()=>setViewerTier('all')),
      toolKey('≈',tierLabel(TIERS[0]),()=>setViewerTier('sea')),
      toolKey('⌁',tierLabel(TIERS[1]),()=>setViewerTier('hills')),
      toolKey('▲',tierLabel(TIERS[2]),()=>setViewerTier('mountains')),
      toolKey('L −','layer',()=>{viewerLayer=clamp(viewerLayer-1,0,9);renderState();announce(`Viewer layer ${viewerLayer}.`)}),
      toolKey('L +','layer',()=>{viewerLayer=clamp(viewerLayer+1,0,9);renderState();announce(`Viewer layer ${viewerLayer}.`)}),
      toolKey('NAME','tier',renameViewerTier,viewerTier==='all')
    );return;
  }
  if(keyboardMode==='Tiles'){
    if(!tileCatalog.length&&!tileLibraryLoading&&!tileLibraryError)void ensureTileLibrary();
    if(tileLibraryLoading){keyboardKeys.append(toolKey('LOADING','World tile library',()=>{},true));return}
    if(tileLibraryError){
      keyboardKeys.append(toolKey('RETRY','Tile library',()=>{tileLibraryError='';void ensureTileLibrary(true)}),toolKey('ERROR',tileLibraryError,()=>{},true));return;
    }
    if(!tileLibraryFolder){
      const folders=tileLibraryFolders();
      keyboardKeys.append(toolKey('WORLD','Tile Library',()=>{},true));
      folders.forEach(folder=>keyboardKeys.append(toolKey(folder,'Folder',()=>openTileLibraryFolder(folder))));
      if(!folders.length)keyboardKeys.append(toolKey('EMPTY','No registered folders',()=>{},true));
      return;
    }
    const count=tileLibraryPageCount();
    keyboardKeys.append(
      toolKey('‹','Folders',closeTileLibraryFolder),
      toolKey(tileLibraryFolder,`Page ${tileLibraryPage+1} / ${count}`,()=>{},true)
    );
    tileLibraryPageAssets().forEach(asset=>keyboardKeys.append(libraryTileKey(asset)));
    keyboardKeys.append(
      toolKey('‹','Previous',()=>{tileLibraryPage=(tileLibraryPage-1+count)%count;renderKeyboardKeys()}),
      toolKey('›','Next',()=>{tileLibraryPage=(tileLibraryPage+1)%count;renderKeyboardKeys()})
    );
    return;
  }
  if(keyboardMode==='Sprites'){
    if(!spriteCatalog.length&&!spriteLibraryLoading&&!spriteLibraryError)void ensureSpriteLibrary();
    keyboardKeys.append(toolKey('UPLOAD','sprite set',openSpriteUpload));
    if(selectedImage?.kind==='sprite'){
      keyboardKeys.append(
        toolKey('FPS −',`${Math.max(1,Number(selectedImage.spriteFps)||6)} fps`,()=>{selectedImage.spriteFps=clamp((Number(selectedImage.spriteFps)||6)-1,1,30);if(selectedImage.playing)startSpriteMotion(selectedImage);renderKeyboardKeys()}),
        toolKey('FPS +',`${Math.max(1,Number(selectedImage.spriteFps)||6)} fps`,()=>{selectedImage.spriteFps=clamp((Number(selectedImage.spriteFps)||6)+1,1,30);if(selectedImage.playing)startSpriteMotion(selectedImage);renderKeyboardKeys()}),
        toolKey(selectedImage.playing?'PAUSE':'PLAY','motion',()=>{if(selectedImage.playing)stopSpriteMotion(selectedImage);else if(selectedImage.committed)startSpriteMotion(selectedImage);else announce('Save the sprite first to begin world motion.');renderKeyboardKeys()})
      );
    }
    if(spriteLibraryLoading){keyboardKeys.append(toolKey('LOADING','Sprite library',()=>{},true));return}
    if(spriteLibraryError){
      keyboardKeys.append(toolKey('RETRY','Sprite library',()=>{spriteLibraryError='';void ensureSpriteLibrary(true)}),toolKey('ERROR',spriteLibraryError,()=>{},true));return;
    }
    if(!spriteLibraryFolder){
      const folders=spriteLibraryFolders();
      folders.forEach(folder=>keyboardKeys.append(toolKey(folder,'Folder',()=>openSpriteLibraryFolder(folder))));
      if(!folders.length)keyboardKeys.append(toolKey('EMPTY','No registered sprites',()=>{},true));
      return;
    }
    const count=spriteLibraryPageCount();
    keyboardKeys.append(toolKey('‹','Folders',closeSpriteLibraryFolder),toolKey(spriteLibraryFolder,`Page ${spriteLibraryPage+1} / ${count}`,()=>{},true));
    spriteLibraryPageAssets().forEach(asset=>keyboardKeys.append(spriteLibraryKey(asset)));
    keyboardKeys.append(
      toolKey('‹','Previous',()=>{spriteLibraryPage=(spriteLibraryPage-1+count)%count;renderKeyboardKeys()}),
      toolKey('›','Next',()=>{spriteLibraryPage=(spriteLibraryPage+1)%count;renderKeyboardKeys()})
    );
    return;
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
      toolKey('TIER −','tier',()=>moveSelectedTier(-1),selectedImage.tier<=0),
      toolKey('TIER +','tier',()=>moveSelectedTier(1),selectedImage.tier>=TIERS.length-1),
      toolKey('LAYER −','layer',()=>moveSelectedLayer(-1),selectedImage.tier<=0&&selectedImage.layer<=0),
      toolKey('LAYER +','layer',()=>moveSelectedLayer(1),selectedImage.tier>=TIERS.length-1&&selectedImage.layer>=9),
      toolKey('DELETE','image',removeSelectedImage)
    );return;
  }
  if(keyboardMode==='Select'){
    const items=selectablePlacedContent();
    keyboardKeys.append(
      toolKey('‹','previous image',()=>cyclePlacedSelection(-1),!items.length),
      toolKey('›','next image',()=>cyclePlacedSelection(1),!items.length),
      placedContentSelect(),
      toolKey('EDIT','selected image',()=>{if(!selectedImage)return;keyboardMode='Image';renderKeyboardTabs();renderKeyboardKeys();announce('Image editing controls opened.')},!selectedImage),
      toolKey('CLEAR','selection',()=>deselectUserImage(true),!selectedImage)
    );return;
  }
  const sets={Pixels:['Select','Paint','Erase','Fill'],Labels:['New Label','Style','Anchor','Offset'],Litch:['Light','Shadow','Intensity','Falloff'],CAD:['Line','Shape','Measure','Snap'],Stylus:['Draw','Pressure','Erase','Sample'],Tethers:['Link','Unlink','Anchor','Trace'],Metadata:['Inspect','Identity','Provenance','Relations']};
  (sets[keyboardMode]||['Inspect']).forEach(name=>keyboardKeys.append(toolKey(name,keyboardMode.toLowerCase(),()=>setTool(name))));
}
function openKeyboard(){keyboard.hidden=false;stage.classList.add('keyboard-open');keyboardToggle.setAttribute('aria-expanded','true');keyboardToggle.setAttribute('aria-label','Close World Builder keyboard');renderKeyboardTabs();renderKeyboardKeys();announce(`${keyboardMode} keyboard opened over viewer. Viewer size unchanged.`)}
function closeKeyboard(){keyboard.hidden=true;stage.classList.remove('keyboard-open');keyboardToggle.setAttribute('aria-expanded','false');keyboardToggle.setAttribute('aria-label','Open World Builder keyboard');announce('Keyboard hidden. Viewer unobstructed.')}

BASE_WORLD_ASSETS.forEach(asset=>{
  const node=planeByKey[asset.key];
  node.addEventListener('load',()=>{
    layerReady[asset.key]=true;
    if(asset.key!=='surface')void primeCollisionMask(collisionSource(node));
    if(asset.key==='surface'&&node.dataset.derivedUpscale!=='1'){
      naturalWidth=node.naturalWidth||1;
      naturalHeight=node.naturalHeight||1;
      loading.hidden=true;
      fitMap();
      if(upscaleEnabled&&!upscaleStarted){upscaleStarted=true;void applyUpscalePreference()}
      scheduleRegionEnhancement(60);
      void restoreSavedWorldBuilder();
    }else{
      if(asset.key==='surface')loading.hidden=true;
      renderState();
    }
  });
  node.addEventListener('error',()=>{
    layerReady[asset.key]=false;
    if(asset.key==='surface'){loading.hidden=false;loading.textContent='WORLD MAP ASSET UNAVAILABLE'}
    renderState();
  });
  node.src=ASSET_ROOT+asset.file;
});

if(!BASE_WORLD_ASSETS.length){
  naturalWidth=1280;
  naturalHeight=1280;
  loading.hidden=true;
  world.dataset.emptyWorld='true';
  fitMap();
  void restoreSavedWorldBuilder();
  announce('Empty world loaded. Add images to begin building.');
}

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
function goHome(){
  try{(window.top||window).localStorage.setItem('rist.shell.workspace.v1','hub')}catch{try{localStorage.setItem('rist.shell.workspace.v1','hub')}catch{}}
  if(window.top&&window.top!==window)window.top.location.href='/Game/index.html';else location.href='/Game/index.html';
}
function openStartMenu(){
  try{
    if(window.parent&&window.parent!==window){
      const ticker=window.parent.document.querySelector('.site-ticker-root');
      if(ticker){ticker.click();return}
    }
  }catch{}
  goHome();
}

persistentSave?.addEventListener('click',()=>void saveWorldBuilder());
bindTap($('fit'),fitMap);
bindTap($('zoomIn'),()=>zoomCenter(1.22));
bindTap($('zoomOut'),()=>zoomCenter(1/1.22));
$('back').addEventListener('click',goHome);
keyboardToggle.addEventListener('click',()=>keyboard.hidden?openKeyboard():closeKeyboard());
settingsToggle.addEventListener('click',openViewerSettings);
viewerSettingsClose.addEventListener('click',closeViewerSettings);
settingsFit.addEventListener('click',()=>{fitMap();closeViewerSettings()});
settingsResetTilt.addEventListener('click',()=>{resetTilt();closeViewerSettings();announce('Viewer tilt reset.')});
settingsUpscale.addEventListener('click',()=>void toggleUpscale());
settingsStartMenu.addEventListener('click',openStartMenu);
imageUploadToggle.addEventListener('click',openImageUpload);
tierToggle.addEventListener('click',()=>{const opening=tierMenu.hidden;renderTierMenu();tierMenu.hidden=!opening;tierToggle.setAttribute('aria-expanded',String(opening));if(opening)tierMenu.querySelector('button[aria-current="true"]')?.focus()});
document.addEventListener('pointerdown',event=>{if(tierMenu.hidden)return;if(event.target===tierToggle||tierToggle.contains(event.target)||tierMenu.contains(event.target))return;closeTierMenu()},{capture:true});
imageUploadClose.addEventListener('click',closeImageUpload);
imageBrowse.addEventListener('click',()=>imageFile.click());
imageFile.addEventListener('change',()=>{const file=imageFile.files?.[0];if(file)void placeUploadedImage(file);imageFile.value=''});
imageDropzone.addEventListener('click',event=>{if(event.target===imageDropzone)imageFile.click()});
imageDropzone.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();imageFile.click()}});
for(const type of ['dragenter','dragover'])imageDropzone.addEventListener(type,event=>{event.preventDefault();event.stopPropagation();imageDropzone.classList.add('dragover')});
for(const type of ['dragleave','drop'])imageDropzone.addEventListener(type,event=>{event.preventDefault();event.stopPropagation();imageDropzone.classList.remove('dragover')});
imageDropzone.addEventListener('drop',event=>{const file=[...(event.dataTransfer?.files||[])].find(f=>f.type.startsWith('image/'));if(file)void placeUploadedImage(file)});
spriteUploadClose.addEventListener('click',closeSpriteUpload);
spriteBrowse.addEventListener('click',()=>spriteFile.click());
spriteFile.addEventListener('change',()=>{const file=spriteFile.files?.[0];if(file)void placeUploadedSprite(file);spriteFile.value=''});
spriteColumns.addEventListener('input',syncSpriteFrameCount);spriteRows.addEventListener('input',syncSpriteFrameCount);
spriteDropzone.addEventListener('click',event=>{if(event.target===spriteDropzone)spriteFile.click()});
spriteDropzone.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();spriteFile.click()}});
for(const type of ['dragenter','dragover'])spriteDropzone.addEventListener(type,event=>{event.preventDefault();event.stopPropagation();spriteDropzone.classList.add('dragover')});
for(const type of ['dragleave','drop'])spriteDropzone.addEventListener(type,event=>{event.preventDefault();event.stopPropagation();spriteDropzone.classList.remove('dragover')});
spriteDropzone.addEventListener('drop',event=>{const file=[...(event.dataTransfer?.files||[])].find(f=>f.type.startsWith('image/'));if(file)void placeUploadedSprite(file)});
$('keyboardClose').addEventListener('click',closeKeyboard);

stage.addEventListener('wheel',e=>{if(e.target instanceof Element&&e.target.closest('[data-ui]'))return;e.preventDefault();zoomAt(e.clientX,e.clientY,e.deltaY<0?1.12:1/1.12)},{passive:false});
stage.addEventListener('pointerdown',e=>{
  if(e.target instanceof Element&&e.target.closest('[data-ui]'))return;
  if(!(e.target instanceof Element&&e.target.closest('.user-image-placement')))deselectUserImage(false);
  suspendRegionEnhancement();
  if(e.pointerType==='mouse'&&e.button!==0)return;
  if(e.pointerType!=='mouse')e.preventDefault();
  if(e.pointerType==='mouse')stage.setPointerCapture?.(e.pointerId);
  pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
  stage.classList.add('dragging');
  if(pointers.size===1){panStart={pointerX:e.clientX,pointerY:e.clientY,x,y};pinchStart=null}
  else if(pointers.size===2){
    const[a,b]=[...pointers.values()],r=stage.getBoundingClientRect(),cx=(a.x+b.x)/2-r.left,cy=(a.y+b.y)/2-r.top,d=Math.hypot(a.x-b.x,a.y-b.y)||1;
    pinchStart={distance:d,scale,worldX:(cx-x)/scale,worldY:(cy-y)/scale,collision:collisionAt(r.left+cx,r.top+cy)};
    panStart=null;
  }
});
stage.addEventListener('pointermove',e=>{
  if(!pointers.has(e.pointerId))return;
  if(e.pointerType!=='mouse')e.preventDefault();
  pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
  if(pointers.size===1&&panStart){x=panStart.x+(e.clientX-panStart.pointerX);y=panStart.y+(e.clientY-panStart.pointerY);applyTransform();scheduleRegionEnhancement();return}
  if(pointers.size===2&&pinchStart){
    const[a,b]=[...pointers.values()],r=stage.getBoundingClientRect(),cx=(a.x+b.x)/2-r.left,cy=(a.y+b.y)/2-r.top,d=Math.hypot(a.x-b.x,a.y-b.y)||1;
    const oldScale=scale,nextScale=clamp(pinchStart.scale*(d/pinchStart.distance),minScale*.75,maxScale);
    pinchStart.collision=prepareZoomCollision(r.left+cx,r.top+cy,oldScale,nextScale,pinchStart.collision);
    scale=nextScale;
    x=cx-pinchStart.worldX*scale;
    y=cy-pinchStart.worldY*scale;
    applyTransform();
    if(pinchStart.collision)settleCollisionAnchor(pinchStart.collision,r.left+cx,r.top+cy);else stage.dataset.zoomCollision='world';
    scheduleRegionEnhancement();
  }
});
function release(e){
  pointers.delete(e.pointerId);
  if(!pointers.size){panStart=pinchStart=null;stage.classList.remove('dragging');scheduleRegionEnhancement(45)}
  else if(pointers.size===1){const[r]=[...pointers.values()];panStart={pointerX:r.x,pointerY:r.y,x,y};pinchStart=null}
}
stage.addEventListener('pointerup',release);
stage.addEventListener('pointercancel',release);
window.addEventListener('resize',()=>{fitMap();scheduleRegionEnhancement(80)},{passive:true});
document.addEventListener('keydown',e=>{if(e.key!=='Escape')return;if(!tierMenu.hidden){closeTierMenu();tierToggle.focus();return}if(!viewerSettingsPanel.hidden){closeViewerSettings();return}if(!spriteUploadPanel.hidden){closeSpriteUpload();return}if(!imageUploadPanel.hidden){closeImageUpload();return}if(!keyboard.hidden)closeKeyboard()});

window.ShaelvienPrototype=Object.freeze({
  world:Object.freeze({id:WORLD_ID,name:WORLD_NAME,seed:WORLD_SEED}),
  getUpscaleState:()=>({enabled:upscaleEnabled,mode:stage.dataset.upscale||'original'}),
  save:saveWorldBuilder,
  tiers:TIERS,
  baseLayers:BASE_WORLD_ASSETS,
  getViewerState:()=>({
    viewerTier,viewerLayer,
    layerCount:BASE_LAYER_COUNT+userLayers.length,
    userLayers:userLayers.map(item=>({id:item.id,tier:item.tier,layer:item.layer,x:item.x,y:item.y,size:item.size,rotation:item.rotation,opacity:item.opacity,transparent:item.transparent,committed:!!item.committed,zoomPassed:!!item.zoomPassed})),
    keyboardOpen:!keyboard.hidden,keyboardMode,toolMode,
    tileLibrary:{loaded:tileCatalog.length,folder:tileLibraryFolder,page:tileLibraryPage,count:tileCatalog.length,error:tileLibraryError||null},
    detailMode:stage.dataset.detailMode||'world',detailScale:Number(stage.dataset.detailScale||regionZoomRatio().toFixed(2))
  })
});
updateTierButton();
renderTierMenu();
renderKeyboardTabs();
renderState();
updateUpscaleControl();
if(upscaleEnabled)stage.dataset.upscale='waiting-for-canonical';
})();