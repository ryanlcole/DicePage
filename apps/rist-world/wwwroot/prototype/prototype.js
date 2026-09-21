(() => {
'use strict';
const QUERY=new URLSearchParams(location.search);
const LIVE_WORLDBUILDER=QUERY.get('live-worldbuilder')==='1';
const WORKSPACE_MODE=String(QUERY.get('mode')||'worldbuilder').toLowerCase();
const REGION_DEFINER=WORKSPACE_MODE==='regiondefiner';
const REGION_FLOW=String(QUERY.get('regionFlow')||'').toLowerCase();
const REQUESTED_REGION_ID=String(QUERY.get('regionId')||'');
const WORLD_ID=QUERY.get('worldId')||'';
const WORLD_NAME=QUERY.get('worldName')||'';
const WORLD_SEED=QUERY.get('seed')||(LIVE_WORLDBUILDER?'empty':'geonaph');
const IS_GEONAPH_SEED=WORLD_SEED==='geonaph';
const DISPLAY_WORLD_NAME=WORLD_NAME||'Shaelvien';
const CONTINENT_NAME=IS_GEONAPH_SEED?'Jeyrusal':'';
const SURFACE_POLICY=QUERY.get('surfacePolicy')||'included';
const ACCESS_MODE=String(QUERY.get('access')||'edit').toLowerCase();
const CLAIM_ONLY=ACCESS_MODE==='claim';
const READ_ONLY=ACCESS_MODE==='view';
const MAP_AUTHORITY_SCOPED=REGION_DEFINER;
const ASSET_SCALE=REGION_DEFINER?'REGION':'WORLD';
const SURFACE_WORLD_PIXELS=Math.max(2048,Math.min(32768,Math.trunc(Number(QUERY.get('surfacePixels'))||2048)));
const MIN_VIEW_SCALE=1e-6;
const ASSET_ROOT='https://d2d6rnm6fnsp89.cloudfront.net/library/terrains/standard/world/whole_maps/geonaph/';
const DEFAULT_SEA_LEVEL_REFERENCE='https://d2d6rnm6fnsp89.cloudfront.net/tilesets/world/terrain/ocean/ocean-067/tile-03-03.jpg';
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
const stage=$('stage'),world=$('world'),surface=$('surfacePlane'),highlands=$('highlandsPlane'),mountains=$('mountainPlane'),loading=$('loading'),battle=$('battleInstance'),battleText=$('battleText'),keyboard=$('viewerKeyboard'),keyboardToggle=$('keyboardToggle'),persistentSave=$('persistentSave'),imageUploadToggle=$('imageUploadToggle'),tierToggle=$('tierToggle'),tierGlyph=$('tierGlyph'),tierMenu=$('tierMenu'),settingsToggle=$('settingsToggle'),viewerSettingsPanel=$('viewerSettingsPanel'),viewerSettingsClose=$('viewerSettingsClose'),settingsFit=$('settingsFit'),settingsResetTilt=$('settingsResetTilt'),settingsUpscale=$('settingsUpscale'),settingsUpscaleLabel=$('settingsUpscaleLabel'),settingsStartMenu=$('settingsStartMenu'),imageUploadPanel=$('imageUploadPanel'),imageUploadClose=$('imageUploadClose'),imagePlacementRole=$('imagePlacementRole'),imagePlacementHint=$('imagePlacementHint'),imagePositionGrid=$('imagePositionGrid'),imageDropzone=$('imageDropzone'),imageBrowse=$('imageBrowse'),imageFile=$('imageFile'),imageX=$('imageX'),imageY=$('imageY'),imageTier=$('imageTier'),imageLayer=$('imageLayer'),imageTransparency=$('imageTransparency'),spriteUploadPanel=$('spriteUploadPanel'),spriteUploadClose=$('spriteUploadClose'),spriteDropzone=$('spriteDropzone'),spriteBrowse=$('spriteBrowse'),spriteFile=$('spriteFile'),spriteColumns=$('spriteColumns'),spriteRows=$('spriteRows'),spriteFps=$('spriteFps'),spriteFrameCount=$('spriteFrameCount'),keyboardTabs=$('keyboardTabs'),keyboardKeys=$('keyboardKeys'),live=$('live');
if(READ_ONLY){
  stage.classList.add('read-only');stage.setAttribute('aria-readonly','true');stage.dataset.access='view';
  persistentSave.disabled=true;persistentSave.title='Read-only world reference';
  imageUploadToggle.disabled=true;imageUploadToggle.title='Read-only world reference';
  const banner=document.createElement('div');banner.className='read-only-reference';banner.textContent='VIEW ONLY · WORLD REFERENCE';banner.setAttribute('role','status');stage.appendChild(banner);
}else if(CLAIM_ONLY){
  stage.dataset.access='claim';
  persistentSave.disabled=true;persistentSave.title='Claim requests do not directly edit the world';
  imageUploadToggle.disabled=true;imageUploadToggle.title='Wait for GM approval before building';
  const banner=document.createElement('div');banner.className='claim-request-reference';banner.textContent='CLAIM REQUEST MODE · GM APPROVAL REQUIRED';banner.setAttribute('role','status');stage.appendChild(banner);
}else stage.dataset.access='edit';
if(REGION_DEFINER){
  document.title='Shaelvien Region Definer';
  stage.classList.add('region-definer-mode');
  stage.dataset.workspace='regiondefiner';
  stage.dataset.mapAuthority='region-scoped';
  keyboard?.setAttribute('aria-label','Region Definer contextual keyboard');
  keyboardToggle?.setAttribute('aria-label','Open Region Definer keyboard');
  persistentSave.title='Save authorized changes to the canonical map';
  persistentSave.setAttribute('aria-label','Save authorized region changes to the canonical map');
  imageUploadToggle?.setAttribute('aria-label','Add regional image');
  const banner=document.createElement('div');banner.className='region-mode-reference';banner.textContent='REGION DEFINER · CANONICAL MAP · 15° VIEW';banner.setAttribute('role','status');stage.appendChild(banner);
  // A new-region flow is tier choice first. Hide viewer chrome from the first JS paint
  // instead of exposing the canonical viewer while the database source hydrates.
  if(REGION_FLOW==='new'&&!READ_ONLY){
    stage.classList.add('region-tier-previewing');
    stage.dataset.regionEntry='tier-preview';
  }
}
const planeByKey={surface,highlands,mountains};
const CANONICAL_PLANE_KEYS=Object.freeze(['surface','highlands','mountains']);
const layerReady={surface:false,highlands:false,mountains:false};
const pointers=new Map();
let viewerSize=null;
let naturalWidth=1,naturalHeight=1,scale=1,minScale=.1,maxScale=12,x=0,y=0,fitX=0,fitY=0,panStart=null,pinchStart=null,keyboardMode=REGION_DEFINER&&REGION_FLOW==='new'?'Select':'Viewer',toolMode='Inspect',tiltBaseline=null,tiltTargetX=0,tiltTargetY=0,tiltX=0,tiltY=0,tiltFrame=0,selectedImage=null,imageDrag=null,viewerTier=REGION_DEFINER?'sea':'all',viewerLayer=0,upscaleStarted=false;
const userLayers=[];
const WORLDBUILDER_SAVE_DB='rist-worldbuilder-prototype-v1';
const WORLDBUILDER_SAVE_STORE='worlds';
const WORLD_SOURCE_SAVE_KEY=WORLD_ID||WORLD_SEED||'prototype';
const REGION_OVERLAY_SAVE_KEY='regiondefiner:'+(WORLD_ID||WORLD_SEED||'prototype');
const WORLDBUILDER_SAVE_KEY=REGION_DEFINER?REGION_OVERLAY_SAVE_KEY:WORLD_SOURCE_SAVE_KEY;
let restoreSaveStarted=false;
const REGION_GRID_COLUMNS=30;
const REGION_GRID_ROWS=30;
const regionSelectedCells=new Set();
let regionCatalog=[],regionSelectionOverlay=null,regionSelectionEnabled=false,regionNameDraft='',regionCreatePending=false;
let regionGridShape='hex',regionClaimPhase=REGION_DEFINER&&REGION_FLOW==='new'?'tier-preview':'idle',regionCropPreview=false,regionClaimedRegion=null,pendingClaimedRegionId=REQUESTED_REGION_ID;
let regionWorldSourceMeta=null;
let regionClaimMaskUrl='';
const regionWorldSourceTiles=[];
const regionWorldTierImages=[];
let regionWorldSourceOcean=null;
let regionCanonicalTierImages=BASE_WORLD_ASSETS.map(asset=>ASSET_ROOT+asset.file);
let regionTierPreview=null,regionTierPreviewPointer=null;
let canonicalHydrationRevision=0;
const regionWorldLayerVisibility=Array.from({length:TIERS.length},()=>new Set(Array.from({length:10},(_,index)=>index)));
const TILE_LIBRARY_URL='../assets/drive-tiles/catalog.json?v=20260918-tiles-keyboard-1';
const TILE_LIBRARY_PAGE_SIZE=12;
const WORLD_TERRAIN_FOLDERS=Object.freeze(['Vent Fields','Canyons','Lakes','Rivers','Cliffs','Volcano','Ice','Snow','Mountains','Hills','Desert','Swamp','Jungle','Forest','Plains','Beach','Coast','Ocean']);
let tileCatalog=[],tileLibraryFolder=null,tileLibraryPage=0,tileLibraryLoading=false,tileLibraryError='',assetPlacementRole='auto';
const SPRITE_LIBRARY_URL='../assets/sprites/catalog.json?v=20260918-prototype-sprites-1';
const SPRITE_LIBRARY_PAGE_SIZE=12;
let spriteCatalog=[],spriteLibraryFolder=null,spriteLibraryPage=0,spriteLibraryLoading=false,spriteLibraryError='';
const PERSONAL_ASSET_INDEX_KEY='uploads/index.json';
const PERSONAL_ASSET_PAGE_SIZE=12;
const PERSONAL_ASSET_MAX_BYTES=20*1024*1024;
let personalAssets=[],personalAssetLoading=false,personalAssetError='',personalFolderType=null,personalAssetPage=0,personalAuthConfigPromise=null;
const pendingPersonalUploads=new Set();
let worldSourceHostReady=false;
let worldSourceDatabaseMissing=false;
let localWorldBuilderRestoreComplete=false;
const worldSourceSaveWaiters=new Map();
const regionMapSaveWaiters=new Map();
const spriteTimers=new Map();
const REGION_ENHANCE_ENTER=4.25;
const REGION_ENHANCE_EXIT=3.6;
const REGION_ENHANCE_DELAY=140;
const REGION_ENHANCE_MAX_DPR=2;
const MAX_VIEW_ZOOM_RATIO=256;
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
  // A placed image remains part of the current representation at every camera
  // zoom. Filling the viewport is not a semantic boundary and must not make the
  // image disappear. Scale/layer transitions are explicit viewer operations.
  const restored=nextScale<oldScale?restorePassedImages(nextScale):false;
  return restored?collisionAt(clientX,clientY):(existing??collisionAt(clientX,clientY));
}
function userCollision(item,clientX,clientY){
  if(!item?.node||item.zoomPassed||item.kind==='label'||isWorldMapItem(item))return null;
  const visible=(viewerTier==='all'||item.tier===tierByKey(viewerTier).index)&&(!REGION_DEFINER||!item.sourceLocked||regionSourceLayerVisible(item.tier,item.layer));
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
function postWorldBuilderHostMessage(type,payload={}){
  if(REGION_DEFINER||window.parent===window)return false;
  try{window.parent.postMessage({source:'shaelvien-worldbuilder',type,...payload},location.origin);return true}catch{return false}
}
function worldBuilderTierImages(){
  return BASE_WORLD_ASSETS.map(asset=>ASSET_ROOT+asset.file);
}
function worldBuilderSourceState(layers=userLayers){
  return{
    format:'RIST_WORLDBUILDER_PROTOTYPE',
    version:4,
    worldId:WORLD_ID,
    worldSeed:WORLD_SEED,
    savedAt:new Date().toISOString(),
    coordinateSpace:'world-normalized-v1',
    sourcePixelWidth:Math.max(1,Math.trunc(Number(naturalWidth)||SURFACE_WORLD_PIXELS)),
    sourcePixelHeight:Math.max(1,Math.trunc(Number(naturalHeight)||SURFACE_WORLD_PIXELS)),
    viewerTier,
    viewerLayer,
    gridColumns:REGION_GRID_COLUMNS,
    gridRows:REGION_GRID_ROWS,
    gridStyle:'square',
    tierImages:worldBuilderTierImages(),
    userLayers:layers.map(serializableUserLayer)
  };
}
function saveWorldSourceToDatabase(state){
  if(REGION_DEFINER||!LIVE_WORLDBUILDER||window.parent===window)return Promise.resolve(false);
  if(!worldSourceHostReady)return Promise.reject(new Error('World source database bridge is not ready.'));
  const requestId=crypto.randomUUID?.()||('world-source-'+Date.now()+'-'+Math.random().toString(16).slice(2));
  return new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>{
      worldSourceSaveWaiters.delete(requestId);
      reject(new Error('World source database save timed out.'));
    },12000);
    worldSourceSaveWaiters.set(requestId,{resolve,reject,timeout});
    if(!postWorldBuilderHostMessage('save-source',{requestId,state})){
      clearTimeout(timeout);worldSourceSaveWaiters.delete(requestId);
      reject(new Error('World source database bridge is unavailable.'));
    }
  });
}
async function bootstrapWorldSourceDatabase(){
  if(REGION_DEFINER||READ_ONLY||!worldSourceDatabaseMissing||!localWorldBuilderRestoreComplete||!worldSourceHostReady)return;
  worldSourceDatabaseMissing=false;
  try{
    const state=worldBuilderSourceState(userLayers);
    await saveWorldSourceToDatabase(state);
    await writeSavedWorldBuilder(state,WORLD_SOURCE_SAVE_KEY);
    announce('World Builder source published to the shared database.');
  }catch(error){
    worldSourceDatabaseMissing=true;
    announce('World source database bootstrap failed: '+String(error?.message||error||'unknown error'));
  }
}
async function applyDatabaseWorldBuilderState(envelope){
  if(REGION_DEFINER)return;
  const state=envelope&&typeof envelope==='object'&&envelope.state&&typeof envelope.state==='object'?envelope.state:envelope;
  if(!state||typeof state!=='object'||state.format!=='RIST_WORLDBUILDER_PROTOTYPE'||String(state.worldId||'')!==String(WORLD_ID||''))return;
  const canonical=await applyCanonicalWorldBuilderSnapshot(state,{region:false});
  if(!canonical.loaded)return;
  viewerTier=state.viewerTier==='all'?'all':tierByKey(state.viewerTier||'sea').key;
  viewerLayer=clamp(Math.trunc(Number(state.viewerLayer)||0),0,9);
  selectedImage=null;
  updateLayerOrder();updateTierButton();renderTierMenu();applyParallax();renderKeyboardKeys();scheduleRegionEnhancement(50);
  localWorldBuilderRestoreComplete=true;
  worldSourceDatabaseMissing=false;
  try{await writeSavedWorldBuilder(state,WORLD_SOURCE_SAVE_KEY)}catch{}
  announce('World Builder loaded from the shared database.');
}
async function handleWorldBuilderHostMessage(event){
  if(REGION_DEFINER||event.origin!==location.origin||event.source!==window.parent)return;
  const data=event.data;if(!data||data.source!=='shaelvien-worldbuilder-host')return;
  if(data.type==='bridge-ready'){
    worldSourceHostReady=true;
    postWorldBuilderHostMessage('ready');
    return;
  }
  if(data.type==='world-source'){
    worldSourceHostReady=true;
    await applyDatabaseWorldBuilderState(data.worldSource||{});
    return;
  }
  if(data.type==='world-source-missing'){
    worldSourceHostReady=true;
    worldSourceDatabaseMissing=true;
    void bootstrapWorldSourceDatabase();
    return;
  }
  if(data.type==='source-saved'||data.type==='source-save-error'){
    const requestId=String(data.requestId||''),waiter=worldSourceSaveWaiters.get(requestId);
    if(!waiter)return;
    clearTimeout(waiter.timeout);worldSourceSaveWaiters.delete(requestId);
    if(data.type==='source-saved'&&data.result?.success!==false)waiter.resolve(data.result||true);
    else waiter.reject(new Error(String(data.message||'World source database save failed.')));
  }
}
function activeRegionMapId(){
  return String(regionClaimedRegion?.id||pendingClaimedRegionId||REQUESTED_REGION_ID||'').trim();
}
function saveRegionMapToDatabase(userLayers){
  if(!REGION_DEFINER||window.parent===window)return Promise.resolve(false);
  const regionId=activeRegionMapId();
  if(!regionId)return Promise.reject(new Error('Choose or create a region before saving map changes.'));
  const requestId=crypto.randomUUID?.()||('region-map-'+Date.now()+'-'+Math.random().toString(16).slice(2));
  return new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>{
      regionMapSaveWaiters.delete(requestId);
      reject(new Error('Canonical world map save timed out.'));
    },12000);
    regionMapSaveWaiters.set(requestId,{resolve,reject,timeout});
    if(!postRegionMessage('save-map-region',{requestId,regionId,userLayers})){
      clearTimeout(timeout);regionMapSaveWaiters.delete(requestId);
      reject(new Error('Region map database bridge is unavailable.'));
    }
  });
}
function openSaveDb(){
  return new Promise((resolve,reject)=>{
    if(!('indexedDB'in window)){reject(new Error('IndexedDB unavailable'));return}
    const request=indexedDB.open(WORLDBUILDER_SAVE_DB,1);
    request.onupgradeneeded=()=>{const db=request.result;if(!db.objectStoreNames.contains(WORLDBUILDER_SAVE_STORE))db.createObjectStore(WORLDBUILDER_SAVE_STORE)};
    request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error||new Error('Save database unavailable'));
  });
}
async function writeSavedWorldBuilder(state,key=WORLDBUILDER_SAVE_KEY){
  const db=await openSaveDb();
  try{
    await new Promise((resolve,reject)=>{
      const tx=db.transaction(WORLDBUILDER_SAVE_STORE,'readwrite');
      tx.objectStore(WORLDBUILDER_SAVE_STORE).put(state,key);
      tx.oncomplete=()=>resolve();tx.onerror=()=>reject(tx.error||new Error('Save failed'));tx.onabort=()=>reject(tx.error||new Error('Save aborted'));
    });
  }finally{db.close()}
}
async function readSavedWorldBuilder(key=WORLDBUILDER_SAVE_KEY){
  const db=await openSaveDb();
  try{
    return await new Promise((resolve,reject)=>{
      const tx=db.transaction(WORLDBUILDER_SAVE_STORE,'readonly'),request=tx.objectStore(WORLDBUILDER_SAVE_STORE).get(key);
      request.onsuccess=()=>resolve(request.result||null);request.onerror=()=>reject(request.error||new Error('Load failed'));
    });
  }finally{db.close()}
}
function serializableUserLayer(item){
  if(item?.kind==='label'){
    return{
      id:item.id,regionId:String(item.regionId||''),name:item.name||item.text||'Label',kind:'label',text:String(item.text||'').slice(0,120),
      x:clamp(Number(item.x)||0,0,1),y:clamp(Number(item.y)||0,0,1),tier:clamp(Math.trunc(Number(item.tier)||0),0,TIERS.length-1),
      layer:clamp(Math.trunc(Number(item.layer)||0),0,9),rotation:Number(item.rotation)||0,opacity:clamp(Number(item.opacity)||1,.01,1),
      fontSize:clamp(Number(item.fontSize)||48,12,180),bold:!!item.bold,italic:!!item.italic,color:String(item.color||LABEL_COLORS[0]),
      textAlign:['left','center','right'].includes(item.textAlign)?item.textAlign:'center',letterSpacing:clamp(Number(item.letterSpacing)||0,-2,12),
      plate:!!item.plate,offsetX:clamp(Number(item.offsetX)||0,-400,400),offsetY:clamp(Number(item.offsetY)||0,-400,400),committed:true
    };
  }
  return{
    id:item.id,regionId:String(item.regionId||''),assetId:item.assetId||null,personalAssetKey:item.personalAssetKey||null,name:item.name||'',libraryTile:!!item.libraryTile,kind:item.kind||'image',
    placementRole:isWorldMapItem(item)?'world-map':'layer',fullWorld:isWorldMapItem(item),
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
  if(READ_ONLY){announce('World reference mode is view only.');return false;}
  if(!persistentSave)return false;
  persistentSave.disabled=true;persistentSave.classList.add('saving');persistentSave.classList.remove('saved');
  try{
    if(pendingPersonalUploads.size){
      announce(`Saving ${pendingPersonalUploads.size} personal upload${pendingPersonalUploads.size===1?'':'s'} before committing the ${REGION_DEFINER?'region':'world'}…`);
      await Promise.allSettled([...pendingPersonalUploads]);
    }
    const editableLayers=REGION_DEFINER?userLayers.filter(item=>!item.sourceLocked):userLayers;
    const serializedLayers=editableLayers.map(item=>{
      if(REGION_DEFINER&&!item.regionId)item.regionId=activeRegionMapId();
      return serializableUserLayer(item);
    });
    const state=REGION_DEFINER?null:worldBuilderSourceState(editableLayers);
    if(REGION_DEFINER){
      await saveRegionMapToDatabase(serializedLayers);
    }else{
      if(LIVE_WORLDBUILDER&&window.parent!==window)await saveWorldSourceToDatabase(state);
      await writeSavedWorldBuilder(state,WORLD_SOURCE_SAVE_KEY);
    }
    for(const item of editableLayers){
      item.committed=true;refreshUserImage(item);
      if(item.kind==='sprite'&&Array.isArray(item.frameSources)&&item.frameSources.length>1)startSpriteMotion(item);
    }
    updateLayerOrder();applyParallax();
    deselectUserImage(false);
    persistentSave.classList.add('saved');
    setTimeout(()=>persistentSave?.classList.remove('saved'),900);
    announce(REGION_DEFINER
      ? `Saved ${serializedLayers.length} regional item${serializedLayers.length===1?'':'s'} directly onto the canonical world map. Perspective and permissions changed; the map did not.`
      : `World Builder saved. ${serializedLayers.length} placed item${serializedLayers.length===1?'':'s'} committed. Use Select or the matching keyboard to edit saved content.`);
    return true;
  }catch(error){
    announce(`Save failed: ${String(error?.message||error||'unknown error')}`);
    return false;
  }finally{
    persistentSave.disabled=false;persistentSave.classList.remove('saving');
  }
}
async function attachRestoredLayer(raw,options={}){
  const sourceLocked=!!options.sourceLocked,regionOverlay=!!options.regionOverlay,canonicalSource=!!options.canonicalSource;
  const kind=String(raw?.kind||'image').toLowerCase();
  if(kind==='label'){
    const item={
      id:String(raw.id||`label:${crypto.randomUUID?.()||Date.now()}`),regionId:String(raw.regionId||''),kind:'label',name:String(raw.name||raw.text||'Label'),text:String(raw.text||raw.name||'Label').slice(0,120),sourceLocked,regionOverlay,canonicalSource,
      x:clamp(Number(raw.x)||0,0,1),y:clamp(Number(raw.y)||0,0,1),tier:clamp(Math.trunc(Number(raw.tier)||0),0,TIERS.length-1),
      layer:clamp(Math.trunc(Number(raw.layer)||0),0,9),rotation:Number(raw.rotation)||0,opacity:clamp(Number(raw.opacity)||1,.01,1),
      fontSize:clamp(Number(raw.fontSize)||48,12,180),bold:!!raw.bold,italic:!!raw.italic,color:String(raw.color||LABEL_COLORS[0]),
      textAlign:['left','center','right'].includes(raw.textAlign)?raw.textAlign:'center',letterSpacing:clamp(Number(raw.letterSpacing)||0,-2,12),
      plate:!!raw.plate,offsetX:clamp(Number(raw.offsetX)||0,-400,400),offsetY:clamp(Number(raw.offsetY)||0,-400,400),
      committed:raw.committed!==false,renderOpacity:1,parallaxX:0,parallaxY:0,node:null
    };
    const node=document.createElement('div');node.className='user-image-placement user-label-placement';node.setAttribute('role','text');node.setAttribute('aria-label',`World label: ${item.text}`);item.node=node;
    node.addEventListener('pointerdown',event=>beginImageDrag(event,item));node.addEventListener('pointermove',moveImageDrag);node.addEventListener('pointerup',endImageDrag);node.addEventListener('pointercancel',endImageDrag);
    userLayers.push(item);world.appendChild(node);refreshUserLabel(item);return item;
  }
  if(!raw?.originalSrc&&!raw?.spriteSheetSrc)return null;
  const isSprite=kind==='sprite';
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
    id:String(raw.id||crypto.randomUUID?.()||Date.now()),regionId:String(raw.regionId||''),assetId:raw.assetId||null,personalAssetKey:raw.personalAssetKey||null,name:String(raw.name||''),libraryTile:!!raw.libraryTile,kind:isSprite?'sprite':'image',sourceLocked,regionOverlay,canonicalSource,
    placementRole:storedPlacementRole(raw),fullWorld:storedPlacementRole(raw)==='world-map',
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
  const node=document.createElement('img');node.className=`user-image-placement${item.libraryTile?' library-tile-placement':''}${isSprite?' sprite-placement':''}${isWorldMapItem(item)?' full-world-placement':''}`;node.alt=item.name||(isSprite?'Placed sprite':'Placed image');node.draggable=false;item.node=node;
  node.addEventListener('pointerdown',event=>beginImageDrag(event,item));node.addEventListener('pointermove',moveImageDrag);node.addEventListener('pointerup',endImageDrag);node.addEventListener('pointercancel',endImageDrag);
  node.addEventListener('load',()=>{refreshUserImage(item);applyParallax();scheduleRegionEnhancement(30)},{once:true});
  userLayers.push(item);world.appendChild(node);refreshUserImage(item);
  if(item.committed&&isSprite&&frameSources.length>1)startSpriteMotion(item);
  if(!item.sourceLocked&&!item.personalAssetKey&&!item.assetId){
    item.personalUploadPromise=trackPersonalUpload(
      promoteRestoredLayerToPersonal(item).catch(()=>null)
    );
  }
  return item;
}
async function restoreSavedWorldBuilder(){
  if(restoreSaveStarted)return;restoreSaveStarted=true;
  try{
    if(REGION_DEFINER){
      // Region Definer never enters the World Builder's local restore pipeline.
      // Its current tier/selection belongs to the viewer and must not be reset when
      // a base image finishes loading; the host bridge hydrates canonical map truth.
    }else{
      userLayers.splice(0,userLayers.length);
      world.querySelectorAll('.user-image-placement,.progressive-parallax-placement').forEach(node=>node.remove());
      const state=await readSavedWorldBuilder(WORLD_SOURCE_SAVE_KEY);
      if(!state||state.format!=='RIST_WORLDBUILDER_PROTOTYPE'||String(state.worldId||'')!==String(WORLD_ID||''))return;
      for(const raw of Array.isArray(state.userLayers)?state.userLayers:[])await attachRestoredLayer(raw);
      viewerTier=state.viewerTier==='all'?'all':tierByKey(state.viewerTier).key;
      viewerLayer=clamp(Math.trunc(Number(state.viewerLayer)||0),0,9);
    }
    selectedImage=null;updateLayerOrder();updateTierButton();renderTierMenu();applyParallax();renderKeyboardKeys();scheduleRegionEnhancement(50);
    announce(REGION_DEFINER
      ? 'Region Definer ready. Loading the canonical world map with regional permissions.'
      : `Saved World Builder restored. ${userLayers.length} placed item${userLayers.length===1?'':'s'} loaded.`);
  }catch(error){
    if(REGION_DEFINER)announce(`Region Definer restore warning: ${String(error?.message||error)}`);
  }finally{
    if(!REGION_DEFINER){
      localWorldBuilderRestoreComplete=true;
      void bootstrapWorldSourceDatabase();
    }
  }
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
  if(REGION_DEFINER)return false;
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
      .filter(item=>item?.node&&item.kind!=='label'&&Number(item.renderOpacity)>0.001)
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
      if(isWorldMapItem(item)){
        ctx.save();ctx.globalAlpha=clamp(Number(item.renderOpacity??item.opacity)||0,0,1);ctx.drawImage(bitmap,x,y,naturalWidth*scale,naturalHeight*scale);
        if(item===selectedImage){ctx.globalAlpha=1;ctx.lineWidth=Math.max(1,2/dpr);ctx.strokeStyle='rgba(240,204,105,.95)';ctx.strokeRect(x,y,naturalWidth*scale,naturalHeight*scale)}
        ctx.restore();continue;
      }
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
  recomputeMaxViewScale();
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
  announce(results.some(x=>x.derived)?'High resolution Endemar representation active. Original world images remain canonical.':'Upscale enabled. Browser high-quality interpolation is active; canonical images are unchanged.');
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
  if(REGION_DEFINER){announce('World tier names are locked in Region Definer.');return;}
  if(READ_ONLY){announce('World reference mode is view only.');return;}
  if(viewerTier==='all'){announce('Select a tier before naming it.');return}
  const tier=tierByKey(viewerTier),next=prompt('Name this tier',String(tierNames[tier.key]||''));
  if(next===null)return;const value=String(next).trim().slice(0,60);if(value)tierNames[tier.key]=value;else delete tierNames[tier.key];
  try{localStorage.setItem(TIER_NAMES_KEY,JSON.stringify(tierNames))}catch{}
  updateTierButton();renderTierMenu();announce(value?`Tier named ${value}.`:'Custom tier name cleared.');
}
function currentTierIndex(){return viewerTier==='all'?0:tierByKey(viewerTier).index}
function tierStackBase(tier){return 100+(clamp(Math.trunc(Number(tier)||0),0,TIERS.length-1)*100)}
function updateLayerOrder(){
  // Tier is the committed parallax/depth boundary. Unsaved placements float above
  // the stack only while the user is positioning them; Save drops them into truth.
  surface.style.zIndex=String(tierStackBase(0));
  highlands.style.zIndex=String(tierStackBase(1));
  mountains.style.zIndex=String(tierStackBase(2));
  userLayers.forEach((item,index)=>{
    item.stackOrder=index;
    const committedZ=tierStackBase(item.tier)+1+clamp(Math.trunc(Number(item.layer)||0),0,9)+(index/100);
    item.node.style.zIndex=String(isWorldMapItem(item)?tierStackBase(0)+1:(item.committed?committedZ:1000+(index/100)));
    item.node.dataset.tier=String(item.tier);
    item.node.dataset.layer=String(item.layer);
    item.node.dataset.placementRole=isWorldMapItem(item)?'world-map':'layer';
    item.node.dataset.placementPreview=item.committed?'false':'true';
  });
}
function closeTierMenu(){tierMenu.hidden=true;tierToggle.setAttribute('aria-expanded','false')}
function renderTierMenu(){
  tierMenu.replaceChildren();
  const options=REGION_DEFINER?[...TIERS]:[{key:'all',label:'All Parallax',glyph:'≋'},...TIERS];
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
  const previous=viewerTier;
  viewerTier=REGION_DEFINER?(key==='all'?'sea':tierByKey(key).key):(key==='all'?'all':tierByKey(key).key);
  viewerLayer=0;
  if(REGION_DEFINER&&previous!==viewerTier){clearRegionSelection(false);deselectUserImage(false)}
  updateTierButton();renderTierMenu();applyTransform();scheduleRegionEnhancement(40);renderKeyboardKeys();
  announce(viewerTier==='all'?'All Parallax selected. Zoom blends through all world tiers.':`${tierLabel(tierByKey(viewerTier))} selected${REGION_DEFINER?' for regional definition.':''}`);
}
function adjustSelectedSize(direction){
  if(READ_ONLY)return;
  if(!selectedImage)return;
  if(isWorldMapItem(selectedImage)){announce('World Map always fills 100% by 100% of the world.');return}
  const current=Math.max(.2,Number(selectedImage.size)||1);
  const step=current<2?.1:current<6?.25:.5;
  selectedImage.size=clamp(current+(Math.sign(direction||1)*step),.2,20);
  refreshUserImage(selectedImage);scheduleRegionEnhancement(20);renderKeyboardKeys();
  announce(`${selectedImage.kind==='sprite'?'Sprite':'Image'} size ${selectedImage.size.toFixed(selectedImage.size<2?1:2)}.`);
}
function moveSelectedTier(delta){
  if(READ_ONLY)return;
  if(REGION_DEFINER){announce('Choose the working tier from the Tiers keyboard. Regional assets stay on that tier.');return}
  if(!selectedImage)return;
  if(isWorldMapItem(selectedImage)){announce('World Map is locked to Sea Level.');return}
  selectedImage.tier=clamp(selectedImage.tier+delta,0,TIERS.length-1);
  updateLayerOrder();applyParallax();renderKeyboardKeys();
  const pos=selectedPositionSummary(selectedImage);
  announce(`${selectedImage.kind==='label'?'Label':selectedImage.kind==='sprite'?'Sprite':'Image'} moved to Tier ${pos.tier}, ${pos.tierLabel}, Layer ${pos.layer}.`);
}
function moveSelectedLayer(delta){
  if(READ_ONLY)return;
  if(!selectedImage)return;
  if(isWorldMapItem(selectedImage)){announce('World Map is the Sea Level base layer.');return}
  if(REGION_DEFINER){
    selectedImage.tier=currentRegionTierIndex();
    selectedImage.layer=clamp(selectedImage.layer+delta,0,9);
  }else{
    const maxSceneZ=(TIERS.length*10)-1,currentSceneZ=(selectedImage.tier*10)+selectedImage.layer,nextSceneZ=clamp(currentSceneZ+delta,0,maxSceneZ);
    selectedImage.tier=Math.floor(nextSceneZ/10);selectedImage.layer=nextSceneZ%10;
  }
  updateLayerOrder();applyParallax();renderKeyboardKeys();
  const pos=selectedPositionSummary(selectedImage);
  announce(`${selectedImage.kind==='label'?'Label':selectedImage.kind==='sprite'?'Sprite':'Image'} moved to Tier ${pos.tier}, ${pos.tierLabel}, Layer ${pos.layer}.`);
}
function isWorldMapItem(item){return item?.placementRole==='world-map'||item?.fullWorld===true}
function storedPlacementRole(raw){return raw?.placementRole==='world-map'||raw?.fullWorld===true?'world-map':'layer'}
function customWorldMap(){return userLayers.find(isWorldMapItem)||null}
function hasSeaLevelRepresentation(){return !!customWorldMap()||layerReady.surface||!!String(surface?.currentSrc||surface?.src||'').trim()||BASE_WORLD_ASSETS.length>0}
function defaultNewPlacementRole(){return !REGION_DEFINER&&!hasSeaLevelRepresentation()?'world-map':'layer'}
function requestedPlacementRole(value){return !REGION_DEFINER&&String(value||'').toLowerCase()==='world-map'?'world-map':'layer'}
function currentAssetPlacementRole(){return assetPlacementRole==='auto'?defaultNewPlacementRole():requestedPlacementRole(assetPlacementRole)}
function removeCustomWorldMap(except=null){
  for(let index=userLayers.length-1;index>=0;index--){
    const item=userLayers[index];if(item===except||!isWorldMapItem(item))continue;
    stopSpriteMotion(item);item.node?.remove();if(selectedImage===item)selectedImage=null;userLayers.splice(index,1);
  }
}
function syncImagePlacementRole(){
  if(!imagePlacementRole)return;
  if(REGION_DEFINER){imagePlacementRole.value='layer';imagePlacementRole.disabled=true}
  const role=requestedPlacementRole(imagePlacementRole.value),locked=role==='world-map';
  imageX.disabled=locked;imageY.disabled=locked;imageLayer.disabled=locked;imageTier.disabled=locked||REGION_DEFINER;
  imagePositionGrid?.classList.toggle('placement-locked',locked);
  if(imagePlacementHint)imagePlacementHint.textContent=locked
    ?'World Map fills Sea Level at 100% × 100%. Replaces the current custom world map.'
    :'Adjustable layer keeps the Sea Level world map underneath and opens size, position, rotation, opacity, tier, and layer controls.';
}
function appendPlacementRoleControls(){
  if(REGION_DEFINER)return;
  const role=currentAssetPlacementRole();
  keyboardKeys.append(
    toolKey(role==='world-map'?'WORLD MAP ✓':'WORLD MAP','Sea Level · 100% × 100%',()=>{assetPlacementRole='world-map';renderKeyboardKeys();announce('New images and tiles will become the full Sea Level world map.')}),
    toolKey(role==='layer'?'LAYER ✓':'LAYER','adjustable above Sea Level',()=>{assetPlacementRole='layer';renderKeyboardKeys();announce('New images and tiles will be adjustable layers above the world map.')})
  );
}
function placementAddress(tier,layerDelta=1){
  tier=clamp(tier,0,TIERS.length-1);
  if(REGION_DEFINER)return{tier,layer:clamp(viewerLayer+layerDelta,0,9)};
  const maxSceneZ=(TIERS.length*10)-1,sceneZ=clamp((tier*10)+viewerLayer+layerDelta,0,maxSceneZ);
  return{tier:Math.floor(sceneZ/10),layer:sceneZ%10};
}
function viewerCenterPosition(){
  const r=stage.getBoundingClientRect();
  const wx=((r.width/2)-x)/Math.max(scale,.00001);
  const wy=((r.height/2)-y)/Math.max(scale,.00001);
  const point={x:clamp(wx/Math.max(naturalWidth,1),0,1),y:clamp(wy/Math.max(naturalHeight,1),0,1)};
  return REGION_DEFINER?snapRegionPoint(point.x,point.y):point;
}
function openImageUpload(){
  if(READ_ONLY){announce('World reference mode is view only.');return;}
  const point=viewerCenterPosition();
  imageX.value=point.x.toFixed(3);imageY.value=point.y.toFixed(3);
  const address=placementAddress(currentTierIndex(),1);
  imageTier.value=String(address.tier);imageLayer.value=String(address.layer);
  if(imagePlacementRole)imagePlacementRole.value=currentAssetPlacementRole();
  syncImagePlacementRole();
  imageTransparency.checked=true;imageUploadPanel.hidden=false;stage.classList.add('image-upload-open');imageDropzone.focus();
  announce(currentAssetPlacementRole()==='world-map'
    ?'Image upload opened. World Map will fill Sea Level at 100% by 100%.'
    :`Image upload opened. Adjustable layer defaults to ${tierLabel(tierByIndex(currentTierIndex()))}.`);
}function closeImageUpload(){imageUploadPanel.hidden=true;stage.classList.remove('image-upload-open');imageUploadToggle.focus()}
function fileDataUrl(file){return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result||''));reader.onerror=()=>reject(reader.error);reader.readAsDataURL(file)})}
function loadDataImage(src){return new Promise((resolve,reject)=>{const img=new Image();if(!String(src).startsWith('data:')&&!String(src).startsWith('blob:'))img.crossOrigin='anonymous';img.onload=()=>resolve(img);img.onerror=reject;img.src=src})}
function openSpriteUpload(){
  if(READ_ONLY){announce('World reference mode is view only.');return;}
  spriteColumns.value='3';spriteRows.value='2';spriteFps.value='6';spriteFrameCount.value='6';
  spriteUploadPanel.hidden=false;stage.classList.add('image-upload-open');spriteDropzone.focus();
  announce('Sprite upload opened. Frame one will be used for placement. Save will start animation.');
}
function closeSpriteUpload(returnToSprites=true){
  spriteUploadPanel.hidden=true;stage.classList.remove('image-upload-open');
  if(returnToSprites){keyboardMode='Sprites';renderKeyboardTabs();renderKeyboardKeys()}
  keyboardToggle.focus();
}
function syncSpriteFrameCount(){const cols=clamp(Math.trunc(Number(spriteColumns.value)||1),1,16),rows=clamp(Math.trunc(Number(spriteRows.value)||1),1,16);spriteFrameCount.value=String(cols*rows)}
function whitenToAlpha(data){
  const px=data.data,width=data.width,height=data.height,count=width*height;
  const mask=new Uint8Array(count),seen=new Uint8Array(count),queue=new Int32Array(count);
  for(let p=0,i=0;p<count;p++,i+=4){
    const r=px[i],g=px[i+1],b=px[i+2],lo=Math.min(r,g,b),hi=Math.max(r,g,b);
    if(lo>=226&&hi-lo<=24)mask[p]=1;
  }
  const minimumRegion=Math.max(512,Math.floor(count*.02));
  for(let start=0;start<count;start++){
    if(!mask[start]||seen[start])continue;
    let head=0,tail=0;queue[tail++]=start;seen[start]=1;
    while(head<tail){
      const p=queue[head++],x=p%width,y=(p/width)|0;
      if(x>0){const n=p-1;if(mask[n]&&!seen[n]){seen[n]=1;queue[tail++]=n}}
      if(x+1<width){const n=p+1;if(mask[n]&&!seen[n]){seen[n]=1;queue[tail++]=n}}
      if(y>0){const n=p-width;if(mask[n]&&!seen[n]){seen[n]=1;queue[tail++]=n}}
      if(y+1<height){const n=p+width;if(mask[n]&&!seen[n]){seen[n]=1;queue[tail++]=n}}
    }
    if(tail<minimumRegion)continue;
    for(let q=0;q<tail;q++)px[(queue[q]*4)+3]=0;
  }
  return data;
}
async function extractSpriteFrame(sheetSrc,options={},frameIndex=0){
  const img=await loadDataImage(sheetSrc);
  const columns=clamp(Math.trunc(Number(options.columns)||1),1,32),rows=clamp(Math.trunc(Number(options.rows)||1),1,32);
  const frameCount=clamp(Math.trunc(Number(options.frameCount)||columns*rows),1,columns*rows);
  const frame=clamp(Math.trunc(Number(frameIndex)||0),0,frameCount-1);
  const sourceWidth=Math.max(1,Math.trunc(Number(options.sourceWidth)||img.naturalWidth||1));
  const sourceHeight=Math.max(1,Math.trunc(Number(options.sourceHeight)||img.naturalHeight||1));
  const cropX=Math.max(0,Math.trunc(Number(options.cropX)||0)),cropY=Math.max(0,Math.trunc(Number(options.cropY)||0));
  const cropWidth=Math.max(1,Math.trunc(Number(options.cropWidth)||Math.floor(sourceWidth/columns)));
  const cropHeight=Math.max(1,Math.trunc(Number(options.cropHeight)||Math.floor(sourceHeight/rows)));
  const column=frame%columns,row=Math.floor(frame/columns),sx=cropX+(column*cropWidth),sy=cropY+(row*cropHeight);
  const canvas=document.createElement('canvas');canvas.width=cropWidth;canvas.height=cropHeight;
  const ctx=canvas.getContext('2d',{willReadFrequently:true});if(!ctx)throw new Error('Sprite canvas unavailable');
  ctx.clearRect(0,0,cropWidth,cropHeight);ctx.drawImage(img,sx,sy,cropWidth,cropHeight,0,0,cropWidth,cropHeight);
  if(options.whiteTransparent!==false){const image=ctx.getImageData(0,0,cropWidth,cropHeight);ctx.putImageData(whitenToAlpha(image),0,0)}
  return canvas.toDataURL('image/png');
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
const LABEL_COLORS=Object.freeze(['#fff2c7','#ffffff','#f0cc69','#a9d8ff','#b7f0c2','#ffb7b7','#d6c2ff','#121820']);
function refreshUserLabel(item){
  if(!item?.node)return;
  item.node.textContent=String(item.text||'Label');
  item.node.style.left=`${item.x*naturalWidth}px`;
  item.node.style.top=`${item.y*naturalHeight}px`;
  item.node.style.opacity=String(item.renderOpacity??item.opacity??1);
  item.node.style.pointerEvents=item.sourceLocked?'none':(item.committed&&selectedImage!==item?'none':'auto');
  item.node.dataset.committed=item.committed?'true':'false';
  item.node.dataset.anchor='world';
  item.node.dataset.presentationOffsetX=String(Number(item.offsetX)||0);
  item.node.dataset.presentationOffsetY=String(Number(item.offsetY)||0);
  item.node.style.fontSize=`${clamp(Number(item.fontSize)||48,12,180)}px`;
  item.node.style.fontWeight=item.bold?'900':'700';
  item.node.style.fontStyle=item.italic?'italic':'normal';
  item.node.style.color=String(item.color||LABEL_COLORS[0]);
  item.node.style.textAlign=['left','center','right'].includes(item.textAlign)?item.textAlign:'center';
  item.node.style.letterSpacing=`${clamp(Number(item.letterSpacing)||0,-2,12)}px`;
  item.node.classList.toggle('plate',!!item.plate);
  const px=(Number(item.parallaxX)||0)+(Number(item.offsetX)||0),py=(Number(item.parallaxY)||0)+(Number(item.offsetY)||0);
  item.node.style.transform=`translate(-50%,-50%) translate3d(${px.toFixed(2)}px,${py.toFixed(2)}px,0) rotate(${Number(item.rotation)||0}deg)`;
}
function labelInput(value,placeholder,onInput,onEnter){
  const input=document.createElement('input');input.type='text';input.className='label-text-input';input.maxLength=120;input.value=String(value||'');input.placeholder=placeholder||'Label text';
  input.setAttribute('aria-label',placeholder||'Label text');
  input.addEventListener('input',()=>onInput?.(input.value));
  input.addEventListener('keydown',event=>{
    if(event.key==='Enter'){event.preventDefault();event.stopPropagation();onEnter?.(input.value,input)}
  });
  return input;
}
function labelSelection(){
  const labels=userLayers.filter(item=>item?.kind==='label'&&item.node&&!item.sourceLocked);
  const select=document.createElement('select');select.className='placed-content-select';select.setAttribute('aria-label','Select placed label');
  const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent=labels.length?'Select label…':'No labels placed';placeholder.selected=selectedImage?.kind!=='label';select.appendChild(placeholder);
  labels.forEach((item,index)=>{
    const option=document.createElement('option');option.value=String(item.id);option.textContent=`${index+1}. ${String(item.text||'Label').slice(0,40)}`;option.selected=item===selectedImage;select.appendChild(option);
  });
  select.disabled=!labels.length;
  select.addEventListener('change',()=>{const item=labels.find(entry=>String(entry.id)===select.value);if(item){selectUserImage(item);renderKeyboardKeys();announce(`Label selected: ${item.text}.`)}});
  return select;
}
function placeLabel(text){
  if(READ_ONLY){announce('World reference mode is view only.');return null}
  text=String(text||'').trim().slice(0,120);if(!text){announce('Type label text first.');return null}
  const point=viewerCenterPosition(),address=placementAddress(currentTierIndex(),1);
  const item={
    id:`label:${crypto.randomUUID?.()||Date.now()}`,kind:'label',name:text,text,sourceLocked:false,regionOverlay:REGION_DEFINER,regionId:REGION_DEFINER?activeRegionMapId():'',
    x:point.x,y:point.y,tier:address.tier,layer:address.layer,rotation:0,opacity:1,committed:false,renderOpacity:1,
    fontSize:48,bold:false,italic:false,color:LABEL_COLORS[0],textAlign:'center',letterSpacing:0,plate:false,
    offsetX:0,offsetY:0,parallaxX:0,parallaxY:0,node:null
  };
  const node=document.createElement('div');node.className='user-image-placement user-label-placement';node.setAttribute('role','text');node.setAttribute('aria-label',`World label: ${text}`);item.node=node;
  node.addEventListener('pointerdown',event=>beginImageDrag(event,item));node.addEventListener('pointermove',moveImageDrag);node.addEventListener('pointerup',endImageDrag);node.addEventListener('pointercancel',endImageDrag);
  userLayers.push(item);world.appendChild(node);updateLayerOrder();refreshUserLabel(item);selectUserImage(item);keyboardMode='Labels';openKeyboard();renderKeyboardTabs();renderKeyboardKeys();applyParallax();
  announce(`${text} placed at Tier ${tierDisplay(item.tier).number}, Layer ${layerDisplay(item.layer)}. Drag to move the world anchor; Save commits it.`);
  return item;
}
function adjustSelectedLabelFont(delta){
  if(READ_ONLY||selectedImage?.kind!=='label')return;
  selectedImage.fontSize=clamp((Number(selectedImage.fontSize)||48)+(Math.sign(delta||1)*4),12,180);refreshUserLabel(selectedImage);renderKeyboardKeys();
}
function cycleLabelColor(){
  if(READ_ONLY||selectedImage?.kind!=='label')return;
  const current=LABEL_COLORS.indexOf(String(selectedImage.color||LABEL_COLORS[0]));selectedImage.color=LABEL_COLORS[(current+1+LABEL_COLORS.length)%LABEL_COLORS.length];refreshUserLabel(selectedImage);renderKeyboardKeys();
}
function cycleLabelAlignment(){
  if(READ_ONLY||selectedImage?.kind!=='label')return;
  const align=['left','center','right'],current=align.indexOf(selectedImage.textAlign);selectedImage.textAlign=align[(current+1+align.length)%align.length];refreshUserLabel(selectedImage);renderKeyboardKeys();
}
function nudgeLabelOffset(dx,dy){
  if(READ_ONLY||selectedImage?.kind!=='label')return;
  selectedImage.offsetX=clamp((Number(selectedImage.offsetX)||0)+dx,-400,400);selectedImage.offsetY=clamp((Number(selectedImage.offsetY)||0)+dy,-400,400);refreshUserLabel(selectedImage);
}
function renderLabelsKeyboard(){
  const selected=selectedImage?.kind==='label'?selectedImage:null;
  if(!selected){
    const composer=labelInput('','Type label, then Return',()=>{},value=>{const placed=placeLabel(value);if(placed)renderKeyboardKeys()});
    keyboardKeys.append(composer,labelSelection(),toolKey('PLACE','viewer center',()=>{const input=keyboardKeys.querySelector('.label-text-input');placeLabel(input?.value||'')}));
    return;
  }
  const pos=selectedPositionSummary(selected);
  const editor=labelInput(selected.text,'Edit label text',value=>{selected.text=String(value||'').slice(0,120);selected.name=selected.text||'Label';refreshUserLabel(selected)},()=>{selected.node?.focus?.();announce('Label text updated.')});
  keyboardKeys.append(
    editor,labelSelection(),
    readoutKey(`TIER ${pos.tier}`,pos.tierLabel),readoutKey(`LAYER ${pos.layer}`,'label layer'),
    toolKey('A−',`${Math.round(selected.fontSize||48)} px`,()=>adjustSelectedLabelFont(-1),selected.fontSize<=12),
    toolKey('A+',`${Math.round(selected.fontSize||48)} px`,()=>adjustSelectedLabelFont(1),selected.fontSize>=180),
    toolKey(selected.bold?'B ✓':'B','bold',()=>{selected.bold=!selected.bold;refreshUserLabel(selected);renderKeyboardKeys()}),
    toolKey(selected.italic?'I ✓':'I','italic',()=>{selected.italic=!selected.italic;refreshUserLabel(selected);renderKeyboardKeys()}),
    toolKey('COLOR',String(selected.color||LABEL_COLORS[0]),cycleLabelColor),
    toolKey(String(selected.textAlign||'center').toUpperCase(),'alignment',cycleLabelAlignment),
    toolKey(selected.plate?'PLATE ✓':'PLATE','background',()=>{selected.plate=!selected.plate;refreshUserLabel(selected);renderKeyboardKeys()}),
    toolKey('OP −',`${Math.round((selected.opacity||1)*100)}%`,()=>{selected.opacity=clamp((Number(selected.opacity)||1)-.1,.1,1);refreshUserLabel(selected);renderKeyboardKeys()},selected.opacity<=.1),
    toolKey('OP +',`${Math.round((selected.opacity||1)*100)}%`,()=>{selected.opacity=clamp((Number(selected.opacity)||1)+.1,.1,1);refreshUserLabel(selected);renderKeyboardKeys()},selected.opacity>=1),
    toolKey('↺','rotate',()=>{selected.rotation=(Number(selected.rotation)||0)-15;refreshUserLabel(selected)}),
    toolKey('↻','rotate',()=>{selected.rotation=(Number(selected.rotation)||0)+15;refreshUserLabel(selected)}),
    toolKey('←','offset',()=>nudgeLabelOffset(-8,0)),toolKey('→','offset',()=>nudgeLabelOffset(8,0)),
    toolKey('↑','offset',()=>nudgeLabelOffset(0,-8)),toolKey('↓','offset',()=>nudgeLabelOffset(0,8)),
    toolKey('OFFSET 0','reset',()=>{selected.offsetX=0;selected.offsetY=0;refreshUserLabel(selected)}),
    toolKey('TIER −',`T${pos.tier}`,()=>moveSelectedTier(-1),REGION_DEFINER||selected.tier<=0),
    toolKey('TIER +',`T${pos.tier}`,()=>moveSelectedTier(1),REGION_DEFINER||selected.tier>=TIERS.length-1),
    toolKey('LAYER −',`L${pos.layer}`,()=>moveSelectedLayer(-1),selected.tier<=0&&selected.layer<=0),
    toolKey('LAYER +',`L${pos.layer}`,()=>moveSelectedLayer(1),selected.tier>=TIERS.length-1&&selected.layer>=9),
    toolKey('NEW','label',()=>{deselectUserImage(false);renderKeyboardKeys()}),
    toolKey('DELETE','label',removeSelectedImage)
  );
}
function progressiveParallaxEligible(item){
  return !!item&&!isWorldMapItem(item)&&item.kind!=='label';
}
function ensureProgressiveParallaxSlices(item){
  if(!progressiveParallaxEligible(item)||!item?.node)return null;
  let host=item.progressiveParallaxHost;
  if(host?.isConnected)return host;
  host=document.createElement('div');
  host.className='progressive-parallax-placement';
  host.setAttribute('aria-hidden','true');
  const slices=[];
  const count=12;
  for(let i=0;i<count;i++){
    const slice=document.createElement('img');
    slice.className='progressive-parallax-slice';
    slice.draggable=false;
    const top=(i/count)*100,bottom=100-((i+1)/count)*100;
    slice.style.clipPath=`inset(${top}% 0 ${bottom}% 0)`;
    host.appendChild(slice);slices.push(slice);
  }
  item.node.parentElement?.insertBefore(host,item.node);
  item.progressiveParallaxHost=host;item.progressiveParallaxSlices=slices;
  return host;
}
function refreshProgressiveParallax(item){
  if(!progressiveParallaxEligible(item)||!item?.node)return false;
  const host=ensureProgressiveParallaxSlices(item);if(!host)return false;
  const slices=item.progressiveParallaxSlices||[],desired=item.renderedSrc||item.node.currentSrc||item.node.src;
  host.style.left=item.node.style.left;host.style.top=item.node.style.top;
  host.style.width=item.node.style.width;host.style.opacity=item.node.style.opacity;
  host.style.setProperty('--rist-rotation',`${Number(item.rotation)||0}deg`);
  host.style.setProperty('--rist-size',String(Number(item.size)||1));
  const baseX=Number(item.parallaxX)||0,baseY=Number(item.parallaxY)||0;
  const selectionFrozen=REGION_DEFINER&&regionClaimPhase==='select'&&regionSelectionEnabled;
  const nextDepth=selectionFrozen?(Number(item.tier)||0):Math.min(TIERS.length-1,(Number(item.tier)||0)+1);
  const depthDelta=Math.max(0,nextDepth-(Number(item.tier)||0));
  const dx=x-fitX,dy=y-fitY;
  const nextX=((-dx*(nextDepth*.022))+(tiltX*(nextDepth*.48)))/Math.max(scale,.00001);
  const nextY=((-dy*(nextDepth*.022))+(tiltY*(nextDepth*.48)))/Math.max(scale,.00001);
  slices.forEach((slice,i)=>{
    if(slice.src!==desired)slice.src=desired;
    // Images are sliced from top to bottom. Top approaches the next tier;
    // bottom remains planted on the item's current map/tier.
    const vertical=1-((i+.5)/Math.max(1,slices.length));
    const influence=depthDelta?vertical:0;
    const px=baseX+((nextX-baseX)*influence),py=baseY+((nextY-baseY)*influence);
    slice.style.transform=`translate(-50%,-50%) translate3d(${px.toFixed(2)}px,${py.toFixed(2)}px,0) rotate(var(--rist-rotation)) scale(var(--rist-size))`;
  });
  item.node.style.visibility='hidden';
  return true;
}
function refreshUserImage(item){
  if(!item?.node)return;
  if(item.kind==='label'){refreshUserLabel(item);return}
  const spriteFrame=item.kind==='sprite'&&Array.isArray(item.frameSources)&&item.frameSources.length?item.frameSources[clamp(Math.trunc(Number(item.currentFrame)||0),0,item.frameSources.length-1)]:null;
  const desired=spriteFrame||(item.transparent&&item.transparentSrc?item.transparentSrc:item.originalSrc);
  if(item.renderedSrc!==desired){item.node.src=desired;item.renderedSrc=desired;void primeCollisionMask(desired)}
  item.node.style.opacity=String(item.renderOpacity??item.opacity);
  item.node.dataset.committed=item.committed?'true':'false';
  item.node.dataset.sourceLocked=item.sourceLocked?'true':'false';
  item.node.dataset.placementRole=isWorldMapItem(item)?'world-map':'layer';
  item.node.classList.toggle('full-world-placement',isWorldMapItem(item));
  if(isWorldMapItem(item)){
    item.node.style.left='0';item.node.style.top='0';item.node.style.width='100%';item.node.style.height='100%';
    item.node.style.maxWidth='none';item.node.style.maxHeight='none';item.node.style.objectFit='fill';
    item.node.style.pointerEvents='none';item.node.style.transform='none';item.node.style.transformOrigin='0 0';return;
  }
  item.node.style.width='12%';item.node.style.height='auto';item.node.style.maxWidth='';item.node.style.maxHeight='';item.node.style.objectFit='';
  item.node.style.left=`${item.x*naturalWidth}px`;item.node.style.top=`${item.y*naturalHeight}px`;
  item.node.style.pointerEvents=item.sourceLocked?'none':(item.committed&&selectedImage!==item?'none':'auto');
  item.node.style.transformOrigin='50% 50%';
  const px=Number(item.parallaxX)||0,py=Number(item.parallaxY)||0;
  item.node.style.transform=`translate(-50%,-50%) translate3d(${px.toFixed(2)}px,${py.toFixed(2)}px,0) rotate(${item.rotation}deg) scale(${item.size})`;
  refreshProgressiveParallax(item);
}function selectUserImage(item){
  if(item?.sourceLocked){announce('This map content is outside your Region Definer edit permission.');return}
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
  const fallback=item?.kind==='label'?String(item?.text||'Label'):'Placed image';
  const name=String(item?.name||item?.assetId||fallback).trim()||fallback,pos=selectedPositionSummary(item);
  if(isWorldMapItem(item))return `${index+1}. ${name} · WORLD MAP · SEA LEVEL · 100% × 100%`;
  return `${index+1}. ${name} · T${pos.tier} L${pos.layer} · X${pos.x} Y${pos.y}`;
}
function selectablePlacedContent(){
  return userLayers.filter(item=>item?.node&&(!REGION_DEFINER||!item.sourceLocked));
}
function cyclePlacedSelection(delta=1){
  const items=selectablePlacedContent();
  if(!items.length){deselectUserImage(false);announce('No placed content to select.');return}
  const current=selectedImage?items.indexOf(selectedImage):-1;
  const next=current<0?(delta<0?items.length-1:0):(current+delta+items.length)%items.length;
  selectUserImage(items[next]);announce(`Selected ${placedContentLabel(items[next],next)}.`);
}
function placedContentSelect(){
  const select=document.createElement('select');select.className='placed-content-select';select.setAttribute('data-focus-key','placed-content');select.setAttribute('aria-label','Select existing placed content');
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
function removeSelectedImage(){
  if(READ_ONLY)return;if(!selectedImage)return;
  if(selectedImage.sourceLocked){announce('This map content is outside your Region Definer edit permission.');return}
  const doomed=selectedImage,index=userLayers.indexOf(doomed);stopSpriteMotion(doomed);doomed.node.remove();if(index>=0)userLayers.splice(index,1);selectedImage=null;updateLayerOrder();applyParallax();renderKeyboardKeys();announce('Placed content removed from the layer stack.')}
function beginImageDrag(event,item){
  if(READ_ONLY||item?.sourceLocked||isWorldMapItem(item))return;
  if(event.pointerType==='mouse'&&event.button!==0)return;
  if(item?.committed&&selectedImage!==item)return;
  event.preventDefault();event.stopPropagation();selectUserImage(item);item.node.setPointerCapture?.(event.pointerId);
  suspendRegionEnhancement();
  imageDrag={id:event.pointerId,item,startX:event.clientX,startY:event.clientY,x:item.x,y:item.y};
}
function moveImageDrag(event){
  if(READ_ONLY)return;
  if(!imageDrag||imageDrag.id!==event.pointerId)return;event.preventDefault();event.stopPropagation();
  const rawX=clamp(imageDrag.x+(event.clientX-imageDrag.startX)/(Math.max(scale,.00001)*Math.max(naturalWidth,1)),0,1);
  const rawY=clamp(imageDrag.y+(event.clientY-imageDrag.startY)/(Math.max(scale,.00001)*Math.max(naturalHeight,1)),0,1);
  const snapped=REGION_DEFINER?snapRegionPoint(rawX,rawY):{x:rawX,y:rawY};
  imageDrag.item.x=snapped.x;imageDrag.item.y=snapped.y;
  refreshUserImage(imageDrag.item);
  if((keyboardMode==='Image'||keyboardMode==='Labels')&&selectedImage===imageDrag.item)renderKeyboardKeys();
}
function endImageDrag(event){
  if(!imageDrag||imageDrag.id!==event.pointerId)return;
  const drag=imageDrag;imageDrag=null;
  if(drag.item.node.hasPointerCapture?.(event.pointerId))drag.item.node.releasePointerCapture(event.pointerId);
  scheduleRegionEnhancement(40);
}
async function placeUploadedImage(file){
  if(READ_ONLY){announce('World reference mode is view only.');return;}
  if(!file?.type?.startsWith('image/')){announce('Choose an image file.');return}
  const originalSrc=await fileDataUrl(file),transparentSrc=await transparencyCandidate(originalSrc);
  const placementRole=requestedPlacementRole(imagePlacementRole?.value||currentAssetPlacementRole());
  const address=placementAddress(currentTierIndex(),1);
  const tier=placementRole==='world-map'?0:(REGION_DEFINER?currentRegionTierIndex():clamp(Math.trunc(Number(imageTier.value)||address.tier),0,TIERS.length-1));
  const layer=placementRole==='world-map'?0:clamp(Math.trunc(Number(imageLayer.value)||address.layer),0,9);
  const requestedPoint={x:clamp(Number(imageX.value)||0,0,1),y:clamp(Number(imageY.value)||0,0,1)};
  const placementPoint=placementRole==='world-map'?{x:.5,y:.5}:(REGION_DEFINER?snapRegionPoint(requestedPoint.x,requestedPoint.y):requestedPoint);
  const item={
    id:crypto.randomUUID?.()||String(Date.now()),assetId:null,personalAssetKey:null,name:String(file.name||'Uploaded image').replace(/\.[^.]+$/,''),kind:'image',libraryTile:false,sourceLocked:false,regionOverlay:REGION_DEFINER,regionId:REGION_DEFINER?activeRegionMapId():'',
    placementRole,fullWorld:placementRole==='world-map',
    originalSrc,transparentSrc,transparent:!!imageTransparency.checked,
    x:placementPoint.x,y:placementPoint.y,tier,layer,size:1,rotation:0,opacity:1,committed:false,renderOpacity:1,zoomPassed:false,zoomPassScale:null,node:null
  };
  if(isWorldMapItem(item))removeCustomWorldMap(item);
  const node=document.createElement('img');node.className=`user-image-placement${isWorldMapItem(item)?' full-world-placement':''}`;node.alt=item.name;node.draggable=false;item.node=node;
  node.addEventListener('pointerdown',event=>beginImageDrag(event,item));node.addEventListener('pointermove',moveImageDrag);node.addEventListener('pointerup',endImageDrag);node.addEventListener('pointercancel',endImageDrag);
  userLayers.push(item);world.appendChild(node);world.dataset.emptyWorld='false';void primeCollisionMask(originalSrc);if(transparentSrc!==originalSrc)void primeCollisionMask(transparentSrc);updateLayerOrder();refreshUserImage(item);selectUserImage(item);closeImageUpload();keyboardMode='Image';openKeyboard();renderKeyboardTabs();renderKeyboardKeys();applyParallax();scheduleRegionEnhancement(30);
  item.personalUploadPromise=trackPersonalUpload(
    saveFileToPersonalLibrary(file,{category:'Images',folder:'My Images',assetKind:'image',name:item.name})
      .then(asset=>{item.assetId=`private:${asset.key}`;item.personalAssetKey=asset.key;announce(`${item.name} added to My Images.`);return asset})
      .catch(error=>{announce(`${item.name} is placed, but My Images could not save it: ${String(error?.message||error)}`);return null})
  );
  if(isWorldMapItem(item)){
    assetPlacementRole='layer';
    announce(`${item.name} is now the Sea Level World Map at 100% by 100%. Future images and tiles default to adjustable layers.`);
  }else announce(`Image placed above ${tierLabel(tierByIndex(tier))} as adjustable layer ${layer}.`);
}
function tierMix(){
  if(viewerTier!=='all'){
    const index=tierByKey(viewerTier).index;
    // Region Definer works on one tier at a time, but a tier is still a view into
    // the same stacked world. Keep lower canonical tiers visible as context.
    if(REGION_DEFINER)return{surface:1,highlands:index>=1?1:0,mountains:index>=2?1:0};
    return{surface:index===0?1:0,highlands:index===1?1:0,mountains:index===2?1:0};
  }
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
  const selectionFrozen=REGION_DEFINER&&regionClaimPhase==='select'&&regionSelectionEnabled;
  const dx=selectionFrozen?0:x-fitX,dy=selectionFrozen?0:y-fitY,mix=tierMix(),worldMap=customWorldMap();
  if(REGION_DEFINER)updateRegionWorldSourceVisibility();
  const builtins=[
    {node:surface,key:'surface',tier:0,layer:0,sceneZ:0,alpha:worldMap?0:mix.surface},
    {node:highlands,key:'highlands',tier:1,layer:0,sceneZ:4,alpha:mix.highlands},
    {node:mountains,key:'mountains',tier:2,layer:0,sceneZ:7,alpha:mix.mountains}
  ];
  for(const entry of builtins){
    const sourceVisible=!REGION_DEFINER||(entry.tier<=currentRegionTierIndex()&&regionSourceLayerVisible(entry.tier,entry.layer));
    entry.node.style.opacity=layerReady[entry.key]&&sourceVisible?String(clamp(Number(entry.alpha)||0,0,1)):'0';
    const depth=entry.sceneZ/10;
    const panStrength=depth*.055;
    const tiltStrength=.42+(depth*.78);
    const px=selectionFrozen?0:((-dx*panStrength)+(tiltX*tiltStrength))/Math.max(scale,.00001),py=selectionFrozen?0:((-dy*panStrength)+(tiltY*tiltStrength))/Math.max(scale,.00001);
    entry.node.dataset.parallaxX=px.toFixed(4);entry.node.dataset.parallaxY=py.toFixed(4);
    entry.node.style.transform=`translate3d(${px.toFixed(2)}px,${py.toFixed(2)}px,0)`;
  }
  for(const item of userLayers){
    // A new/unsaved placement must stay visible even when its target tier is hidden,
    // otherwise it looks as if upload failed. Canonical lower tiers remain visible
    // as read-only context while Region Definer edits the selected tier.
    const regionTier=currentRegionTierIndex();
    const regionalLayerVisible=!item.canonicalSource||regionSourceLayerVisible(item.tier,item.layer);
    const visible=REGION_DEFINER
      ? (item.canonicalSource?item.tier<=regionTier:item.tier===regionTier)&&regionalLayerVisible
      : (!item.committed||viewerTier==='all'||item.tier===tierByKey(viewerTier).index);
    if(isWorldMapItem(item)){
      item.parallaxX=0;item.parallaxY=0;item.renderOpacity=visible&&!item.zoomPassed?item.opacity:0;refreshUserImage(item);continue;
    }
    const depth=item.tier;
    const panStrength=depth*.022,tiltStrength=depth*.48;
    item.parallaxX=selectionFrozen?0:((-dx*panStrength)+(tiltX*tiltStrength))/Math.max(scale,.00001);
    item.parallaxY=selectionFrozen?0:((-dy*panStrength)+(tiltY*tiltStrength))/Math.max(scale,.00001);
    item.renderOpacity=visible&&!item.zoomPassed?item.opacity:0;refreshUserImage(item);
  }
}
function updateReadouts(){
  stage.dataset.worldId=WORLD_ID;
  stage.dataset.worldSeed=WORLD_SEED;
  stage.dataset.viewerTier=viewerTier;
  stage.dataset.viewerLayer=String(viewerLayer);
  stage.dataset.layerCount=String(BASE_LAYER_COUNT+regionWorldSourceTiles.length+userLayers.length);
  const label=viewerTier==='all'?'All Parallax':tierLabel(tierByKey(viewerTier));
  const worldLabel=DISPLAY_WORLD_NAME?DISPLAY_WORLD_NAME+' world. ':'';
  const continentLabel=CONTINENT_NAME?` Continent ${CONTINENT_NAME}.`:'';
  const regionalLayers=REGION_DEFINER?` Visible World layers ${[...regionWorldLayerSet()].sort((a,b)=>a-b).map(layer=>layer+1).join(', ')||'none'}.`:'';
  stage.setAttribute('aria-label',`Interactive tiered ${worldLabel}viewer.${continentLabel} ${label}. Layer ${viewerLayer}. ${BASE_LAYER_COUNT+regionWorldSourceTiles.length+userLayers.length} total image layers.${regionalLayers} Surface authoring extent ${SURFACE_WORLD_PIXELS} by ${SURFACE_WORLD_PIXELS} pixels. Surface policy ${SURFACE_POLICY}.`);
}
function applyTransform(){
  invalidateRegionCamera();
  world.style.width=naturalWidth+'px';
  world.style.height=naturalHeight+'px';
  world.style.transformOrigin='0 0';
  world.style.transform=REGION_DEFINER
    ? `translate3d(${x}px,${y}px,0) scale(${scale}) rotateX(15deg)`
    : `translate3d(${x}px,${y}px,0) scale(${scale})`;
  if(REGION_DEFINER)syncClaimedRegionContextMask();
  applyParallax();
  updateReadouts();
  scheduleRegionEnhancement();
}
function recomputeMaxViewScale(){
  maxScale=Math.max(minScale*MAX_VIEW_ZOOM_RATIO,8);
}
function fitMap(){
  if(!naturalWidth||!naturalHeight)return;
  if(REGION_DEFINER&&regionClaimedRegion&&regionClaimBounds(regionClaimedRegion)){fitClaimedRegion(regionClaimedRegion);return}
  suspendRegionEnhancement();
  const r=stage.getBoundingClientRect();
  if(r.width<=0||r.height<=0)return;
  viewerSize={width:r.width,height:r.height};
  minScale=Math.min(r.width/naturalWidth,r.height/naturalHeight);
  scale=minScale;
  recomputeMaxViewScale();
  x=fitX=(r.width-naturalWidth*scale)/2;
  y=fitY=(r.height-naturalHeight*scale)/2;
  applyTransform();
}
function zoomAt(cx,cy,factor){
  suspendRegionEnhancement();
  const r=stage.getBoundingClientRect(),sx=cx-r.left,sy=cy-r.top,old=scale,next=clamp(old*factor,MIN_VIEW_SCALE,maxScale);
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
  let lastTouch=-Infinity;
  button.addEventListener('pointerup',event=>{
    if(event.pointerType!=='touch'&&event.pointerType!=='pen')return;
    event.preventDefault();event.stopPropagation();lastTouch=performance.now();fn();
  });
  button.addEventListener('click',event=>{
    if(event.detail!==0&&performance.now()-lastTouch<500)return;
    event.stopPropagation();fn();
  });
}

function renderState(){applyTransform();renderKeyboardKeys()}
const BASE_KEYBOARD_MODES=['Viewer','Tiers','Select','Image','Pixels','Tiles','Sprites','Labels','Litch','CAD','Stylus','Tethers','Metadata'];
function keyboardModes(){
  if(!REGION_DEFINER)return READ_ONLY?['Viewer','Tiers']:CLAIM_ONLY?['Viewer','Tiers','Select']:BASE_KEYBOARD_MODES;
  if(regionClaimPhase==='tier-preview'||regionClaimPhase==='select'||regionClaimPhase==='crop'||regionClaimPhase==='requested')return['Select'];
  if(READ_ONLY)return['Viewer','Tiers'];
  if(CLAIM_ONLY)return['Select'];
  return BASE_KEYBOARD_MODES;
}
function toolKey(label,sub,fn,disabled=false){const b=document.createElement('button');b.type='button';b.disabled=disabled;b.innerHTML=`<strong>${label}</strong><small>${sub}</small>`;b.setAttribute('data-focus-key',label);b.setAttribute('aria-label',label==='⛶'?'Fit map to screen':`${label}: ${sub}`);b.addEventListener('click',fn);return b}
function readoutKey(label,sub){
  const b=document.createElement('button');b.type='button';b.disabled=true;b.className='readout';b.innerHTML=`<strong>${label}</strong><small>${sub}</small>`;b.setAttribute('aria-label',`${label}: ${sub}`);return b;
}
function postRegionMessage(type,payload={}){
  if(!REGION_DEFINER||window.parent===window)return false;
  try{window.parent.postMessage({source:'shaelvien-regiondefiner',type,...payload},location.origin);return true}catch{return false}
}
function currentRegionTierIndex(){return tierByKey(viewerTier==='all'?'sea':viewerTier).index}
function normalizeRegionGridShape(value){return String(value||'').toLowerCase()==='hex'?'hex':'square'}
function regionCellRow(cell){return Math.floor(cell/REGION_GRID_COLUMNS)}
function regionCellColumn(cell){return cell%REGION_GRID_COLUMNS}
function regionCellCenter(cell,shape=regionGridShape){
  const row=regionCellRow(cell),column=regionCellColumn(cell);
  const offset=normalizeRegionGridShape(shape)==='hex'&&(row%2)?0.5:0;
  return{x:clamp((column+0.5+offset)/REGION_GRID_COLUMNS,0,1),y:clamp((row+0.5)/REGION_GRID_ROWS,0,1)};
}
function regionCellFromPoint(x,y,shape=regionGridShape){
  const row=clamp(Math.floor(clamp(y,0,.999999)*REGION_GRID_ROWS),0,REGION_GRID_ROWS-1);
  const offset=normalizeRegionGridShape(shape)==='hex'&&(row%2)?0.5:0;
  const column=clamp(Math.floor((clamp(x,0,.999999)*REGION_GRID_COLUMNS)-offset),0,REGION_GRID_COLUMNS-1);
  return row*REGION_GRID_COLUMNS+column;
}
function regionActiveCellSet(){
  const cells=regionClaimedRegion?.selectedCells;
  return Array.isArray(cells)&&cells.length?new Set(cells.map(Number).filter(Number.isInteger)):null;
}
function nearestAllowedRegionCell(cell,allowed){
  if(!allowed||allowed.has(cell))return cell;
  const target=regionCellCenter(cell),cells=[...allowed];
  let best=cell,bestDistance=Infinity;
  for(const candidate of cells){
    const center=regionCellCenter(candidate),dx=center.x-target.x,dy=center.y-target.y,d=(dx*dx)+(dy*dy);
    if(d<bestDistance){bestDistance=d;best=candidate}
  }
  return best;
}
function snapRegionPoint(x,y){
  if(!REGION_DEFINER)return{x:clamp(x,0,1),y:clamp(y,0,1)};
  let cell=regionCellFromPoint(x,y);
  cell=nearestAllowedRegionCell(cell,regionActiveCellSet());
  return regionCellCenter(cell);
}
function clearRegionWorldSource(){
  for(const item of regionWorldSourceTiles)item.node?.remove();
  regionWorldSourceTiles.splice(0,regionWorldSourceTiles.length);
  for(const item of regionWorldTierImages)item.node?.remove();
  regionWorldTierImages.splice(0,regionWorldTierImages.length);
  for(let index=userLayers.length-1;index>=0;index--){
    const item=userLayers[index];
    if(!item?.canonicalSource)continue;
    stopSpriteMotion(item);
    item.node?.remove();
    userLayers.splice(index,1);
  }
  regionWorldSourceOcean?.remove();regionWorldSourceOcean=null;
  regionWorldSourceMeta=null;
}
function discardCanonicalHydrationItem(item){
  if(!item)return;
  stopSpriteMotion(item);
  item.node?.remove();
  const index=userLayers.indexOf(item);
  if(index>=0)userLayers.splice(index,1);
}
async function hydrateCanonicalRegionLayers(sourceLayers,activeRegionId,revision){
  const tasks=sourceLayers.map(async raw=>{
    const belongsToActiveRegion=!!activeRegionId&&String(raw?.regionId||'')===activeRegionId;
    const editable=ACCESS_MODE==='edit'&&belongsToActiveRegion;
    const item=await attachRestoredLayer(raw,{sourceLocked:!editable,regionOverlay:belongsToActiveRegion,canonicalSource:true});
    if(!item)return null;
    if(revision!==canonicalHydrationRevision){
      discardCanonicalHydrationItem(item);
      return null;
    }
    // Do not wait for every canonical asset before making already-hydrated layers
    // visible. Region Definer is a viewer over the live World Builder map.
    updateLayerOrder();
    applyParallax();
    refreshRegionTierPreview();
    return item;
  });
  const results=await Promise.allSettled(tasks);
  if(revision!==canonicalHydrationRevision)return 0;
  return results.reduce((count,result)=>count+(result.status==='fulfilled'&&result.value?1:0),0);
}
function regionSourceNumber(value,fallback=0){
  const n=Number(value);return Number.isFinite(n)?n:fallback;
}
function applyDatabaseTierImages(tierImages){
  // WORLDSOURCE is authoritative for the canonical tier image references.
  // Never blank a working plane while validating a database URL: probe first,
  // then promote the proven source onto the same World Builder plane.
  if(!Array.isArray(tierImages)||!tierImages.length){
    stage.dataset.canonicalPlaneSource=BASE_WORLD_ASSETS.length?'worldbuilder-shared':'none';
    return;
  }
  stage.dataset.databaseTierImageCount=String(tierImages.length);
  tierImages.slice(0,CANONICAL_PLANE_KEYS.length).forEach((src,tier)=>{
    src=String(src||'').trim();if(!src)return;
    const key=CANONICAL_PLANE_KEYS[tier],node=planeByKey[key];if(!node)return;
    let resolved=src;try{resolved=new URL(src,location.href).href}catch{}
    node.dataset.databaseSource='pending';
    const current=String(node.currentSrc||node.src||'');
    if(current===resolved&&layerReady[key]){
      node.dataset.databaseSource='true';
      node.dataset.referenceOnly='false';
      regionCanonicalTierImages[tier]=resolved;
      stage.dataset.canonicalPlaneSource='database';
      refreshRegionTierPreview();
      return;
    }

    const probe=new Image();
    probe.onload=()=>{
      regionCanonicalTierImages[tier]=resolved;
      node.dataset.databaseSource='true';
      node.dataset.referenceOnly='false';
      stage.dataset.canonicalPlaneSource='database';
      if(String(node.currentSrc||node.src||'')!==resolved){
        node.addEventListener('load',()=>{
          layerReady[key]=true;
          if(key==='surface'){
            naturalWidth=node.naturalWidth||SURFACE_WORLD_PIXELS;
            naturalHeight=node.naturalHeight||SURFACE_WORLD_PIXELS;
            stage.dataset.surfacePixelWidth=String(naturalWidth);
            stage.dataset.surfacePixelHeight=String(naturalHeight);
            loading.hidden=true;fitMap();
          }
          renderState();
          refreshRegionTierPreview();
        },{once:true});
        node.src=resolved;
      }else{
        layerReady[key]=true;
        renderState();
        refreshRegionTierPreview();
      }
    };
    probe.onerror=()=>{
      node.dataset.databaseSource='error';
      stage.dataset.canonicalPlaneFallback='worldbuilder-shared';
      // Keep the already configured/loaded shared World Builder plane. The preview
      // uses the same fallback rather than turning into an empty black tier.
      if(!regionCanonicalTierImages[tier]&&BASE_WORLD_ASSETS[tier])
        regionCanonicalTierImages[tier]=ASSET_ROOT+BASE_WORLD_ASSETS[tier].file;
      refreshRegionTierPreview();
      if(key==='surface'&&!layerReady.surface&&!(BASE_WORLD_ASSETS.length)){
        loading.hidden=false;loading.textContent='MAP IMAGE UNAVAILABLE';
      }
    };
    probe.src=resolved;
  });
}
async function applyCanonicalWorldBuilderSnapshot(state,options={}){
  const regionMode=options.region===true;
  if(!state||typeof state!=='object')return{loaded:false,sourceLayers:[],tierImages:[],hydration:Promise.resolve(0)};
  const stateWorldId=String(state.worldId||'');
  if(stateWorldId&&stateWorldId!==String(WORLD_ID||''))return{loaded:false,sourceLayers:[],tierImages:[],hydration:Promise.resolve(0)};

  const sourceLayers=Array.isArray(state.userLayers)?state.userLayers:[];
  const tierImages=Array.isArray(state.tierImages)?state.tierImages.map(String).filter(Boolean):[];
  const sourcePixelWidth=Math.max(1,Math.trunc(regionSourceNumber(state.sourcePixelWidth,SURFACE_WORLD_PIXELS)));
  const sourcePixelHeight=Math.max(1,Math.trunc(regionSourceNumber(state.sourcePixelHeight,SURFACE_WORLD_PIXELS)));
  if(sourcePixelWidth>1&&sourcePixelHeight>1){
    naturalWidth=sourcePixelWidth;
    naturalHeight=sourcePixelHeight;
  }

  applyDatabaseTierImages(tierImages);

  if(regionMode){
    const revision=Math.trunc(Number(options.revision)||canonicalHydrationRevision);
    const activeRegionId=String(options.activeRegionId||'').trim();
    const hydration=hydrateCanonicalRegionLayers(sourceLayers,activeRegionId,revision);
    return{loaded:true,sourceLayers,tierImages,hydration};
  }

  userLayers.splice(0,userLayers.length);
  world.querySelectorAll('.user-image-placement,.progressive-parallax-placement').forEach(node=>node.remove());
  for(const raw of sourceLayers)await attachRestoredLayer(raw);
  return{loaded:true,sourceLayers,tierImages,hydration:Promise.resolve(sourceLayers.length)};
}

function regionSourceCropStyle(image,tile){
  const sourceWidth=Math.max(0,Math.trunc(regionSourceNumber(tile.sourceWidth,0)));
  const sourceHeight=Math.max(0,Math.trunc(regionSourceNumber(tile.sourceHeight,0)));
  const cropX=Math.max(0,Math.trunc(regionSourceNumber(tile.cropX,0)));
  const cropY=Math.max(0,Math.trunc(regionSourceNumber(tile.cropY,0)));
  const cropWidth=Math.max(0,Math.trunc(regionSourceNumber(tile.cropWidth,0)));
  const cropHeight=Math.max(0,Math.trunc(regionSourceNumber(tile.cropHeight,0)));
  if(sourceWidth>0&&sourceHeight>0&&cropWidth>0&&cropHeight>0){
    image.style.width=`${(sourceWidth*100/cropWidth).toFixed(5)}%`;
    image.style.height=`${(sourceHeight*100/cropHeight).toFixed(5)}%`;
    image.style.left=`${(-cropX*100/cropWidth).toFixed(5)}%`;
    image.style.top=`${(-cropY*100/cropHeight).toFixed(5)}%`;
    image.style.maxWidth='none';image.style.maxHeight='none';image.style.objectFit='fill';
  }else{
    image.style.width='100%';image.style.height='100%';image.style.left='0';image.style.top='0';image.style.objectFit='cover';
  }
}
async function renderRegionWorldSource(payload){
  if(!REGION_DEFINER)return;
  const envelope=payload&&typeof payload==='object'?payload:{};
  let snapshot=envelope.state&&typeof envelope.state==='object'?envelope.state:envelope;
  let tiles=Array.isArray(snapshot.tiles)?snapshot.tiles:Array.isArray(envelope.tiles)?envelope.tiles:[];
  let sourceLayers=Array.isArray(snapshot.userLayers)?snapshot.userLayers:[];
  let tierImages=Array.isArray(snapshot.tierImages)?snapshot.tierImages.map(String).filter(Boolean):[];
  const databaseHasRenderableMap=BASE_WORLD_ASSETS.length>0||tiles.length>0||sourceLayers.length>0||tierImages.length>0;

  if(!databaseHasRenderableMap&&envelope.canPromoteWorldSource===true&&!envelope.recoveredWorldBuilderCache){
    const localState=await readSavedWorldBuilder(WORLD_SOURCE_SAVE_KEY).catch(()=>null);
    const localMatches=localState&&typeof localState==='object'
      &&String(localState.worldId||'')===String(WORLD_ID||'')
      &&String(localState.format||'')==='RIST_WORLDBUILDER_PROTOTYPE';
    const localRenderable=localMatches&&(
      (Array.isArray(localState.tierImages)&&localState.tierImages.length>0)
      ||(Array.isArray(localState.userLayers)&&localState.userLayers.length>0)
      ||(Array.isArray(localState.tiles)&&localState.tiles.length>0)
    );
    if(localRenderable){
      stage.dataset.worldSource='worldbuilder-recovery-cache';
      postRegionMessage('promote-world-source',{state:localState});
      return renderRegionWorldSource({...envelope,state:localState,recoveredWorldBuilderCache:true});
    }
  }

  const hydrationRevision=++canonicalHydrationRevision;
  clearRegionWorldSource();
  regionWorldSourceMeta={
    worldId:String(envelope.worldId||snapshot.worldId||WORLD_ID||''),
    worldName:String(envelope.worldName||snapshot.worldName||WORLD_NAME||DISPLAY_WORLD_NAME||'World'),
    gridColumns:Math.max(1,Math.trunc(regionSourceNumber(snapshot.gridColumns??envelope.gridColumns,REGION_GRID_COLUMNS))),
    gridRows:Math.max(1,Math.trunc(regionSourceNumber(snapshot.gridRows??envelope.gridRows,REGION_GRID_ROWS))),
    gridStyle:normalizeRegionGridShape(snapshot.gridStyle||envelope.gridStyle||'square'),
    planeIndex:Math.trunc(regionSourceNumber(snapshot.planeIndex??envelope.planeIndex,0)),
    updatedAtUtc:String(envelope.updatedAtUtc||'')
  };
  const firstSizedTile=tiles.find(raw=>regionSourceNumber(raw?.sourceWidth,0)>1&&regionSourceNumber(raw?.sourceHeight,0)>1);
  const sourcePixelWidth=Math.max(1,Math.trunc(regionSourceNumber(firstSizedTile?.sourceWidth,snapshot.sourcePixelWidth||envelope.sourcePixelWidth||0)));
  const sourcePixelHeight=Math.max(1,Math.trunc(regionSourceNumber(firstSizedTile?.sourceHeight,snapshot.sourcePixelHeight||envelope.sourcePixelHeight||0)));
  if(sourcePixelWidth>1&&sourcePixelHeight>1){
    naturalWidth=sourcePixelWidth;
    naturalHeight=sourcePixelHeight;
  }
  if(!envelope.recoveredWorldBuilderCache)stage.dataset.worldSource='database';
  const activeRegionId=String(envelope.activeRegionId||REQUESTED_REGION_ID||pendingClaimedRegionId||'').trim();
  const canonical=await applyCanonicalWorldBuilderSnapshot(snapshot,{
    region:true,
    activeRegionId,
    revision:hydrationRevision
  });
  stage.dataset.renderer='worldbuilder-replica';
  sourceLayers=canonical.sourceLayers;
  tierImages=canonical.tierImages;
  if(tierImages.length){
    tierImages.slice(0,CANONICAL_PLANE_KEYS.length).forEach((src,index)=>{
      const value=String(src||'').trim();if(value&&!regionCanonicalTierImages[index])regionCanonicalTierImages[index]=value;
    });
  }
  const sharedBaseMap=BASE_WORLD_ASSETS.length>0||tierImages.length>0;
  // Region Definer tier preview already proves these canonical image URLs can
  // render in this browser. Keep the exact same sources mounted in the actual
  // definition viewer as a fallback representation of the shared world planes.
  // This is rendering only: WORLDSOURCE remains the single source of truth.
  const renderedTierImages=regionTierPreviewSources().slice(0,TIERS.length);
  if(!sharedBaseMap&&!renderedTierImages.length&&!tiles.length&&!sourceLayers.length){
    const ocean=document.createElement('div');ocean.className='region-world-source-ocean';ocean.setAttribute('aria-hidden','true');
    world.insertBefore(ocean,world.firstChild);regionWorldSourceOcean=ocean;
  }
  renderedTierImages.slice(0,TIERS.length).forEach((src,tier)=>{
    if(!src)return;
    const image=document.createElement('img');
    image.className='region-world-source-tier-image';
    image.src=src;
    image.alt='';
    image.draggable=false;
    image.addEventListener('load',()=>{
      if(sourcePixelWidth>1&&sourcePixelHeight>1)return;
      if(image.naturalWidth>1&&image.naturalHeight>1){
        naturalWidth=image.naturalWidth;
        naturalHeight=image.naturalHeight;
        fitMap();
        applyTransform();
      }
    },{once:true});
    image.dataset.tier=String(tier);
    image.dataset.sourceLocked='true';
    image.style.zIndex=String(tierStackBase(tier)-20);
    world.appendChild(image);
    regionWorldTierImages.push({node:image,tier,src});
  });
  tiles.forEach((raw,index)=>{
    const tier=clamp(Math.trunc(regionSourceNumber(raw.tierIndex,0)),0,TIERS.length-1);
    const layer=clamp(Math.trunc(regionSourceNumber(raw.layerOffset,0)),0,9);
    const placementZoom=Math.max(regionSourceNumber(raw.placementZoom,1),1/REGION_GRID_COLUMNS);
    const width=1/REGION_GRID_COLUMNS/placementZoom,height=1/REGION_GRID_ROWS/placementZoom;
    const node=document.createElement('div');node.className='region-world-source-tile';
    node.style.left=`${(clamp(regionSourceNumber(raw.x,0),0,1)*100).toFixed(5)}%`;
    node.style.top=`${(clamp(regionSourceNumber(raw.y,0),0,1)*100).toFixed(5)}%`;
    node.style.width=`${(width*100).toFixed(5)}%`;node.style.height=`${(height*100).toFixed(5)}%`;
    node.style.zIndex=String(tierStackBase(tier)+layer+(index/10000));
    node.style.transform=`rotate(${Math.trunc(regionSourceNumber(raw.rotationQuarterTurns,0))*90}deg)`;
    node.dataset.tier=String(tier);node.dataset.layer=String(layer);node.dataset.sourceLocked='true';
    node.setAttribute('aria-label',String(raw.name||'Locked world source'));
    const frame=document.createElement('span');frame.className='region-world-source-crop';
    const image=document.createElement('img');image.src=String(raw.image||'');image.alt='';image.draggable=false;
    regionSourceCropStyle(image,raw);frame.appendChild(image);node.appendChild(frame);world.appendChild(node);
    regionWorldSourceTiles.push({node,image,tier,layer,index,id:String(raw.id||''),name:String(raw.name||''),assetKind:String(raw.assetKind||'tile')});
  });
  stage.dataset.canonicalLayerCount=String(sourceLayers.length);
  stage.dataset.canonicalTierImageCount=String(tierImages.length);
  // Same WorldBuilder snapshot hydration; RegionDefiner adds only permission/crop view policy.
  const canonicalHydration=canonical.hydration;
  updateLayerOrder();
  const authoredCount=tiles.length+sourceLayers.length;
  const hasCanonicalMap=sharedBaseMap||renderedTierImages.length||authoredCount;
  world.dataset.emptyWorld=hasCanonicalMap?'false':'true';
  loading.hidden=true;
  updateRegionWorldSourceVisibility();
  fitMap();
  updateReadouts();renderKeyboardKeys();
  if(regionClaimPhase==='tier-preview'){
    showRegionTierPreview();
    announce(hasCanonicalMap
      ?'Canonical world map loaded. Swipe through the world tiers, then choose the tier to define a region.'
      :'The canonical world map has not been saved yet. Save it in World Builder first.');
  }else{
    announce(hasCanonicalMap
      ?`${regionWorldSourceMeta.worldName} canonical map loaded. Viewer perspective and permissions are active.`
      :`${regionWorldSourceMeta.worldName} has no saved canonical map yet.`);
  }
  void canonicalHydration.then(count=>{
    if(hydrationRevision!==canonicalHydrationRevision)return;
    stage.dataset.hydratedCanonicalLayerCount=String(count);
    updateLayerOrder();
    applyParallax();
    updateReadouts();
    renderKeyboardKeys();
  }).catch(error=>{
    if(hydrationRevision!==canonicalHydrationRevision)return;
    stage.dataset.canonicalHydrationError=String(error?.message||error||'unknown error').slice(0,160);
  });
}
function updateRegionWorldSourceVisibility(){
  if(!REGION_DEFINER)return;
  const tier=currentRegionTierIndex();
  if(regionWorldSourceOcean)regionWorldSourceOcean.style.opacity=regionWorldTierImages.length?(tier===0?'.18':'.08'):(tier===0?'1':'.32');
  for(const item of regionWorldTierImages)item.node.style.opacity=item.tier<=tier?'1':'0';
  for(const item of regionWorldSourceTiles){
    const visible=item.tier<=tier&&regionSourceLayerVisible(item.tier,item.layer);
    item.node.style.display=visible?'block':'none';
  }
}
function setRegionGridShape(shape){
  if(!REGION_DEFINER)return;
  if(regionClaimedRegion&&(regionClaimPhase==='saved'||regionClaimPhase==='build')){announce('This region grid is fixed by its saved claim. Start a new claim to choose a different grid.');return}
  regionGridShape=normalizeRegionGridShape(shape);
  updateRegionSelectionOverlay();renderKeyboardKeys();
  announce(`${regionGridShape==='hex'?'Hex':'Square'} grid selected for region selection and placement.`);
}
function cycleRegionGridShape(){setRegionGridShape(regionGridShape==='square'?'hex':'square')}
function regionWorldLayerSet(tier=currentRegionTierIndex()){
  tier=clamp(Math.trunc(Number(tier)||0),0,TIERS.length-1);
  return regionWorldLayerVisibility[tier];
}
function regionSourceLayerVisible(tier,layer){
  if(!REGION_DEFINER)return true;
  const set=regionWorldLayerSet(tier);
  return set.has(clamp(Math.trunc(Number(layer)||0),0,9));
}
function serializeRegionWorldLayerVisibility(){
  return regionWorldLayerVisibility.map(set=>[...set].sort((a,b)=>a-b));
}
function restoreRegionWorldLayerVisibility(raw){
  if(!Array.isArray(raw))return;
  for(let tier=0;tier<Math.min(raw.length,regionWorldLayerVisibility.length);tier++){
    if(!Array.isArray(raw[tier]))continue;
    const next=new Set(raw[tier].map(Number).filter(value=>Number.isInteger(value)&&value>=0&&value<10));
    regionWorldLayerVisibility[tier]=next;
  }
}
function setRegionWorldLayersVisible(enabled){
  if(!REGION_DEFINER)return;
  const set=regionWorldLayerSet();set.clear();
  if(enabled)for(let layer=0;layer<10;layer++)set.add(layer);
  applyParallax();renderKeyboardKeys();
  announce(enabled
    ? `All World layers are visible on Tier ${currentRegionTierIndex()+1}.`
    : `All World layers are hidden on Tier ${currentRegionTierIndex()+1}. Regional overlays remain visible.`);
}
function toggleRegionWorldLayer(layer){
  if(!REGION_DEFINER)return;
  layer=clamp(Math.trunc(Number(layer)||0),0,9);
  const set=regionWorldLayerSet(),visible=!set.has(layer);
  if(visible)set.add(layer);else set.delete(layer);
  applyParallax();renderKeyboardKeys();
  announce(`World layer ${layer+1} ${visible?'shown':'hidden'} on Tier ${currentRegionTierIndex()+1}.`);
}
function regionWorldLayerKey(layer){
  const visible=regionSourceLayerVisible(currentRegionTierIndex(),layer);
  const button=toolKey(`W${layer+1}${visible?' ✓':''}`,visible?'World layer visible':'World layer hidden',()=>toggleRegionWorldLayer(layer));
  button.setAttribute('aria-pressed',String(visible));
  return button;
}
function clearRegionSelection(announceChange=true){
  if(!REGION_DEFINER)return;
  regionSelectedCells.clear();updateRegionSelectionOverlay();renderKeyboardKeys();
  if(announceChange)announce('Region selection cleared.');
}
function toggleRegionSelectionMode(){
  if(!REGION_DEFINER||READ_ONLY||regionClaimPhase!=='select')return;
  regionSelectionEnabled=!regionSelectionEnabled;
  pointers.clear();panStart=pinchStart=null;stage.classList.remove('dragging');
  applyParallax();updateRegionSelectionOverlay();renderKeyboardKeys();
  announce(regionSelectionEnabled?'Selection locked. Zoom, pan, and parallax are frozen. Unselected hexes are black and white; tap hexes to select them.':'Selection released. Map zoom, pan, and parallax are available again.');
}
function toggleRegionCell(cell){
  if(!REGION_DEFINER||READ_ONLY||keyboardMode!=='Select'||!regionSelectionEnabled||regionClaimPhase!=='select')return;
  cell=Math.trunc(Number(cell));if(cell<0||cell>=REGION_GRID_COLUMNS*REGION_GRID_ROWS)return;
  if(!regionSelectedCells.delete(cell))regionSelectedCells.add(cell);
  updateRegionSelectionOverlay();renderKeyboardKeys();
  announce(`${regionSelectedCells.size} region tile${regionSelectedCells.size===1?'':'s'} selected on Tier ${currentRegionTierIndex()+1}.`);
}
function regionHexNeighbors(cell){
  const c=regionCellColumn(cell),r=regionCellRow(cell),odd=c&1;
  return [[c-1,r-1+odd],[c-1,r+odd],[c,r-1],[c,r+1],[c+1,r-1+odd],[c+1,r+odd]]
    .filter(([x,y])=>x>=0&&x<REGION_GRID_COLUMNS&&y>=0&&y<REGION_GRID_ROWS)
    .map(([x,y])=>y*REGION_GRID_COLUMNS+x);
}
function enclosedRegionCells(){
  if(regionGridShape!=='hex'||regionSelectedCells.size<6)return[];
  const outside=new Set(),queue=[];
  for(let cell=0;cell<REGION_GRID_COLUMNS*REGION_GRID_ROWS;cell++){
    const c=regionCellColumn(cell),r=regionCellRow(cell);
    if((c===0||r===0||c===REGION_GRID_COLUMNS-1||r===REGION_GRID_ROWS-1)&&!regionSelectedCells.has(cell)){
      outside.add(cell);queue.push(cell);
    }
  }
  while(queue.length){
    const cell=queue.shift();
    for(const next of regionHexNeighbors(cell))if(!regionSelectedCells.has(next)&&!outside.has(next)){outside.add(next);queue.push(next)}
  }
  const inside=[];
  for(let cell=0;cell<REGION_GRID_COLUMNS*REGION_GRID_ROWS;cell++)if(!regionSelectedCells.has(cell)&&!outside.has(cell))inside.push(cell);
  return inside;
}
function claimRegionSelection(){
  if(!regionSelectedCells.size){announce('Select at least one hex before claiming.');return}
  const enclosed=enclosedRegionCells();
  if(enclosed.length){
    const whole=window.confirm(`Your selected hexes close a loop around ${enclosed.length} additional tile${enclosed.length===1?'':'s'}.\n\nOK = claim the whole enclosed area\nCancel = claim only the selected border`);
    if(whole)for(const cell of enclosed)regionSelectedCells.add(cell);
  }
  regionSelectionEnabled=false;
  previewRegionCrop();
}
function regionCellsForTier(){
  const tier=currentRegionTierIndex(),map=new Map();
  for(const region of regionCatalog){
    if(Math.trunc(Number(region?.tierIndex)||0)!==tier)continue;
    for(const cell of Array.isArray(region?.selectedCells)?region.selectedCells:[]){
      const key=Math.trunc(Number(cell));if(key<0||key>=REGION_GRID_COLUMNS*REGION_GRID_ROWS)continue;
      if(!map.has(key))map.set(key,[]);
      map.get(key).push(String(region?.name||'Region'));
    }
  }
  return map;
}
function regionCellCoordinateText(cell){
  return `column ${regionCellColumn(cell)}, row ${regionCellRow(cell)}, cell ${cell}`;
}
function regionTopTileDescription(cell){
  const column=regionCellColumn(cell),row=regionCellRow(cell);
  const px=(column+.5)/REGION_GRID_COLUMNS,py=(row+.5)/REGION_GRID_ROWS;
  const authored=[...userLayers].reverse().find(item=>{
    if(item.kind==='label')return false;
    const footprint=Math.max(1,Math.trunc(Number(item.footprint)||1)),half=(footprint/REGION_GRID_COLUMNS)/2;
    return Math.abs(Number(item.x)-px)<=half&&Math.abs(Number(item.y)-py)<=half;
  });
  if(authored)return String(authored.name||authored.folder||authored.kind||'authored terrain').trim();
  const source=[...regionWorldSourceTiles].reverse().find(item=>{
    const ix=Number(item.x),iy=Number(item.y),span=Math.max(1,Number(item.footprint)||1)/REGION_GRID_COLUMNS;
    return px>=ix&&px<=ix+span&&py>=iy&&py<=iy+span;
  });
  return source?String(source.name||source.folder||'world terrain').trim():'canonical world terrain';
}
function regionCellAccessibilityText(cell){
  return `${regionCellCoordinateText(cell)}. Top tile beneath: ${regionTopTileDescription(cell)}.`;
}
function ensureRegionSelectionOverlay(){
  if(!REGION_DEFINER)return null;
  if(regionSelectionOverlay?.isConnected)return regionSelectionOverlay;
  const overlay=document.createElement('div');overlay.className='region-definition-grid hex';overlay.setAttribute('aria-label','Region definition grid');overlay.setAttribute('role','grid');
  for(let cell=0;cell<REGION_GRID_COLUMNS*REGION_GRID_ROWS;cell++){
    const button=document.createElement('button');button.type='button';button.className='region-definition-cell';button.dataset.cell=String(cell);
    const column=cell%REGION_GRID_COLUMNS,row=Math.floor(cell/REGION_GRID_COLUMNS);
    button.dataset.coordinate=regionCellCoordinateText(cell);
    button.dataset.terrainDescription=regionTopTileDescription(cell);
    button.setAttribute('aria-label',regionCellAccessibilityText(cell));
    button.setAttribute('role','gridcell');
    button.addEventListener('pointerdown',event=>{if(keyboardMode==='Select'&&regionSelectionEnabled){event.preventDefault();event.stopPropagation()}});
    button.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();toggleRegionCell(cell)});
    overlay.appendChild(button);
  }
  world.appendChild(overlay);regionSelectionOverlay=overlay;updateRegionSelectionOverlay();return overlay;
}
function updateRegionSelectionOverlay(){
  if(!REGION_DEFINER)return;
  const overlay=ensureRegionSelectionOverlay();if(!overlay)return;
  const selecting=regionClaimPhase==='select';
  const active=keyboardMode==='Select'&&!keyboard.hidden&&!READ_ONLY&&regionSelectionEnabled&&selecting;
  overlay.classList.toggle('active',active);
  overlay.classList.toggle('square',regionGridShape==='square');
  overlay.classList.toggle('hex',regionGridShape==='hex');
  overlay.dataset.tier=String(currentRegionTierIndex());
  overlay.dataset.gridShape=regionGridShape;
  overlay.setAttribute('aria-hidden',String(!active&&!regionCropPreview));
  const existing=regionCellsForTier();
  // Flat-top hexes overlap horizontally by 25% and alternate columns shift
  // vertically by half a hex. This keeps the coordinate lattice aligned
  // instead of incorrectly shifting alternate rows sideways.
  const cellWidth=100/(REGION_GRID_COLUMNS*.75+.25),cellHeight=100/(REGION_GRID_ROWS+.5);
  for(const button of overlay.children){
    const cell=Math.trunc(Number(button.dataset.cell)),row=regionCellRow(cell),column=regionCellColumn(cell);
    const selected=regionSelectedCells.has(cell),names=existing.get(cell)||[];
    button.classList.toggle('selected',selected);
    button.classList.toggle('existing',names.length>0);
    button.setAttribute('aria-selected',String(selected));
    button.dataset.coordinate=regionCellCoordinateText(cell);
    button.dataset.terrainDescription=regionTopTileDescription(cell);
    const accessible=regionCellAccessibilityText(cell);
    button.setAttribute('aria-label',accessible);
    button.title=names.length?`${accessible} Existing: ${names.join(', ')}`:accessible;
    if(regionGridShape==='hex'){
      button.style.left=`${column*cellWidth*.75}%`;
      button.style.top=`${(row+(column%2?0.5:0))*cellHeight}%`;
      button.style.width=`${cellWidth*1.01}%`;
      button.style.height=`${cellHeight*1.01}%`;
    }else{
      button.style.left='';button.style.top='';button.style.width='';button.style.height='';
    }
  }
  stage.classList.toggle('region-crop-preview',!!regionCropPreview);
}
function regionNameInput(){
  const input=document.createElement('input');input.type='text';input.className='region-name-input';input.maxLength=80;input.value=regionNameDraft;input.placeholder='Region name';input.setAttribute('aria-label','Region name');
  input.addEventListener('input',()=>{regionNameDraft=input.value.slice(0,80)});
  input.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();event.stopPropagation();createRegionDefinition()}});
  return input;
}
function clearRegionMask(refit=true){
  if(!REGION_DEFINER)return;
  regionClaimMaskUrl='';
  world.style.maskImage='none';world.style.webkitMaskImage='none';
  world.style.maskSize='';world.style.webkitMaskSize='';world.style.maskRepeat='';world.style.webkitMaskRepeat='';
  stage.classList.remove('region-cropped');delete stage.dataset.cropMode;delete stage.dataset.regionContext;
  if(refit&&naturalWidth&&naturalHeight)fitMap();
}
let regionClaimOutline=null;
function syncClaimedRegionOutline(region){
  if(!REGION_DEFINER)return;
  if(!region){
    regionClaimOutline?.remove();regionClaimOutline=null;return;
  }
  const bounds=regionClaimBounds(region);if(!bounds)return;
  if(!regionClaimOutline){
    regionClaimOutline=document.createElement('div');
    regionClaimOutline.className='region-claim-outline';
    regionClaimOutline.setAttribute('aria-hidden','true');
    world.appendChild(regionClaimOutline);
  }
  regionClaimOutline.style.left=`${(bounds.minX/REGION_GRID_COLUMNS)*100}%`;
  regionClaimOutline.style.top=`${(bounds.minY/REGION_GRID_ROWS)*100}%`;
  regionClaimOutline.style.width=`${(bounds.width/REGION_GRID_COLUMNS)*100}%`;
  regionClaimOutline.style.height=`${(bounds.height/REGION_GRID_ROWS)*100}%`;
  regionClaimOutline.dataset.label=String(region?.name||'YOUR CLAIM').toUpperCase();
}
function clearClaimedRegionCrop(refit=true){
  if(!REGION_DEFINER)return;
  regionClaimedRegion=null;pendingClaimedRegionId='';syncClaimedRegionOutline(null);
  clearRegionMask(refit);
}
function regionMaskSvg(region){
  const cells=Array.isArray(region?.selectedCells)?region.selectedCells.map(Number).filter(Number.isInteger):[];
  const shape=normalizeRegionGridShape(region?.gridShape||regionGridShape);
  const figures=[];
  for(const cell of cells){
    const row=regionCellRow(cell),column=regionCellColumn(cell);
    if(shape==='hex'){
      const x=column*.75,y=row+(column%2?0.5:0);
      figures.push(`<polygon points="${x+0.25},${y} ${x+0.75},${y} ${x+1},${y+0.5} ${x+0.75},${y+1} ${x+0.25},${y+1} ${x},${y+0.5}" fill="white"/>`);
    }else figures.push(`<rect x="${column}" y="${row}" width="1" height="1" fill="white"/>`);
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${REGION_GRID_COLUMNS} ${REGION_GRID_ROWS}" preserveAspectRatio="none">${figures.join('')}</svg>`;
}
function regionClaimBounds(region){
  const cells=Array.isArray(region?.selectedCells)?region.selectedCells.map(Number).filter(Number.isInteger):[];
  if(!cells.length)return null;
  const shape=normalizeRegionGridShape(region?.gridShape||regionGridShape);
  let minX=Infinity,minY=Infinity,maxX=-Infinity,maxY=-Infinity;
  for(const cell of cells){
    const row=regionCellRow(cell),column=regionCellColumn(cell);
    if(shape==='hex'){
      const hx=column*.75,hy=row+(column%2?0.5:0);
      minX=Math.min(minX,hx);maxX=Math.max(maxX,hx+1);
      minY=Math.min(minY,hy);maxY=Math.max(maxY,hy+1);
    }else{
      minX=Math.min(minX,column);maxX=Math.max(maxX,column+1);
      minY=Math.min(minY,row);maxY=Math.max(maxY,row+1);
    }
  }
  minX=clamp(minX,0,REGION_GRID_COLUMNS);maxX=clamp(maxX,0,REGION_GRID_COLUMNS);
  minY=clamp(minY,0,REGION_GRID_ROWS);maxY=clamp(maxY,0,REGION_GRID_ROWS);
  return{minX,minY,maxX,maxY,width:Math.max(1,maxX-minX),height:Math.max(1,maxY-minY)};
}
function fitClaimedRegion(region){
  const bounds=regionClaimBounds(region);if(!bounds||!naturalWidth||!naturalHeight)return;
  suspendRegionEnhancement();
  const r=stage.getBoundingClientRect(),cropX=(bounds.minX/REGION_GRID_COLUMNS)*naturalWidth,cropY=(bounds.minY/REGION_GRID_ROWS)*naturalHeight;
  const cropW=(bounds.width/REGION_GRID_COLUMNS)*naturalWidth,cropH=(bounds.height/REGION_GRID_ROWS)*naturalHeight;
  const tiltHeight=cropH*Math.cos(15*Math.PI/180);
  scale=Math.min(r.width/Math.max(cropW,1),r.height/Math.max(tiltHeight,1))*.92;
  scale=clamp(scale,MIN_VIEW_SCALE,Math.max(maxScale,scale));
  const centerX=cropX+(cropW/2),centerY=cropY+(cropH/2);
  x=fitX=(r.width/2)-(centerX*scale);
  y=fitY=(r.height/2)-(centerY*scale);
  applyTransform();
}
function claimedRegionFitScale(region){
  const bounds=regionClaimBounds(region);if(!bounds||!naturalWidth||!naturalHeight)return 0;
  const r=stage.getBoundingClientRect();
  if(r.width<=0||r.height<=0)return 0;
  const cropW=(bounds.width/REGION_GRID_COLUMNS)*naturalWidth,cropH=(bounds.height/REGION_GRID_ROWS)*naturalHeight;
  const tiltHeight=cropH*Math.cos(15*Math.PI/180);
  return Math.min(r.width/Math.max(cropW,1),r.height/Math.max(tiltHeight,1))*.92;
}
function syncClaimedRegionContextMask(){
  if(!REGION_DEFINER||!regionClaimedRegion||!regionClaimMaskUrl)return;
  const focusScale=claimedRegionFitScale(regionClaimedRegion);
  if(!(focusScale>0))return;
  // Region Definer is a permission-scoped view of the same canonical world.
  // Close work keeps the claim isolated; zooming out restores the surrounding
  // world so the claimed zone remains visibly connected to Endemar.
  const threshold=Math.max(minScale*2.5,focusScale*.48);
  const focused=scale>threshold;
  if(focused){
    world.style.maskImage=regionClaimMaskUrl;world.style.webkitMaskImage=regionClaimMaskUrl;
    stage.dataset.regionContext='region';stage.dataset.cropMode='visibility-mask';
  }else{
    world.style.maskImage='none';world.style.webkitMaskImage='none';
    stage.dataset.regionContext='world';stage.dataset.cropMode='world-context';
  }
}
function applyRegionMask(region,cropMode='visibility-mask',saved=false){
  if(!REGION_DEFINER||!region)return false;
  const bounds=regionClaimBounds(region);
  if(!bounds){
    clearRegionMask(false);
    stage.dataset.cropMode='invalid-empty-region';
    return false;
  }
  const svg=regionMaskSvg(region),url=`url("data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}")`;
  regionClaimMaskUrl=url;
  world.style.maskImage=url;world.style.webkitMaskImage=url;
  world.style.maskSize='100% 100%';world.style.webkitMaskSize='100% 100%';
  world.style.maskRepeat='no-repeat';world.style.webkitMaskRepeat='no-repeat';
  stage.classList.toggle('region-cropped',!!saved);stage.dataset.cropMode=cropMode;stage.dataset.regionContext='region';
  requestAnimationFrame(()=>fitClaimedRegion(region));
  return true;
}
function applyClaimedRegionCrop(region){
  if(!REGION_DEFINER||!region)return;
  regionClaimedRegion=region;pendingClaimedRegionId=String(region.id||'');
  stage.classList.remove('region-tier-previewing','region-selection-only');
  regionGridShape=normalizeRegionGridShape(region.gridShape||regionGridShape);
  const savedTier=clamp(Math.trunc(Number(region.tierIndex)||0),0,TIERS.length-1);
  viewerTier=tierByIndex(savedTier).key;viewerLayer=0;updateTierButton();renderTierMenu();updateRegionWorldSourceVisibility();
  regionCropPreview=false;regionSelectionEnabled=false;syncClaimedRegionOutline(region);updateRegionSelectionOverlay();
  const editableExisting=REGION_FLOW==='existing'&&ACCESS_MODE==='edit';
  regionClaimPhase=editableExisting?'build':'saved';
  stage.classList.toggle('region-build-mode',editableExisting);
  if(editableExisting)keyboardMode='Tiles';
  if(!applyRegionMask(region,'visibility-mask',true))requestAnimationFrame(()=>fitMap());
  if(editableExisting)queueMicrotask(()=>{renderKeyboardTabs();renderKeyboardKeys();if(keyboard.hidden)openKeyboard()});
}
function ensureRegionTierPreview(){
  if(!REGION_DEFINER)return null;
  if(regionTierPreview?.isConnected)return regionTierPreview;
  const panel=document.createElement('section');
  panel.className='region-tier-preview';
  panel.hidden=true;
  panel.setAttribute('role','dialog');
  panel.setAttribute('aria-modal','true');
  panel.setAttribute('aria-label','Choose a world tier for the new region');
  panel.innerHTML=`
    <div class="region-tier-preview-copy">
      <small>${CLAIM_ONLY?'CLAIM REGION':'NEW REGION'} · WORLD SOURCE</small>
      <strong data-tier-title>TIER 1 · SEA LEVEL</strong>
      <span data-tier-help>Swipe left or right across the map to preview tiers.</span>
    </div>
    <div class="region-tier-preview-map" data-tier-map aria-hidden="true">
      <div class="region-tier-preview-map-stack">
        <img data-tier-image="0" alt="" draggable="false" />
        <img data-tier-image="1" alt="" draggable="false" />
        <img data-tier-image="2" alt="" draggable="false" />
      </div>
      <span class="region-tier-preview-status" data-tier-map-status>LOADING WORLD TIER…</span>
    </div>
    <div class="region-tier-preview-actions">
      <button type="button" data-tier-prev aria-label="Previous tier">‹</button>
      <div class="region-tier-preview-dots" data-tier-dots aria-hidden="true"></div>
      <button type="button" data-tier-next aria-label="Next tier">›</button>
    </div>
    <button type="button" class="region-tier-preview-select" data-tier-select>SELECT THIS TIER</button>`;
  stage.appendChild(panel);
  panel.querySelector('[data-tier-prev]')?.addEventListener('click',()=>stepRegionTierPreview(-1));
  panel.querySelector('[data-tier-next]')?.addEventListener('click',()=>stepRegionTierPreview(1));
  panel.querySelector('[data-tier-select]')?.addEventListener('click',confirmRegionTierPreview);
  panel.querySelectorAll('[data-tier-image]').forEach(image=>{
    image.addEventListener('load',()=>{image.dataset.loaded='true';refreshRegionTierPreviewImages()});
    image.addEventListener('error',()=>{
      const tier=clamp(Math.trunc(Number(image.dataset.tierImage)||0),0,CANONICAL_PLANE_KEYS.length-1);
      const key=CANONICAL_PLANE_KEYS[tier],liveNode=planeByKey[key];
      const fallback=String(liveNode?.currentSrc||liveNode?.src||(BASE_WORLD_ASSETS[tier]?ASSET_ROOT+BASE_WORLD_ASSETS[tier].file:'')).trim();
      if(fallback&&image.dataset.fallbackTried!=='true'&&String(image.src||'')!==fallback){
        image.dataset.fallbackTried='true';image.src=fallback;return;
      }
      image.dataset.loadError='true';refreshRegionTierPreviewImages();
    });
  });
  panel.addEventListener('pointerdown',event=>{
    if(event.target instanceof Element&&event.target.closest('button'))return;
    regionTierPreviewPointer={id:event.pointerId,x:event.clientX,y:event.clientY};
    try{panel.setPointerCapture(event.pointerId)}catch{}
  });
  panel.addEventListener('pointerup',event=>{
    if(!regionTierPreviewPointer||regionTierPreviewPointer.id!==event.pointerId)return;
    const dx=event.clientX-regionTierPreviewPointer.x,dy=event.clientY-regionTierPreviewPointer.y;
    regionTierPreviewPointer=null;
    if(Math.abs(dx)>48&&Math.abs(dx)>Math.abs(dy)*1.15)stepRegionTierPreview(dx<0?1:-1);
  });
  panel.addEventListener('pointercancel',()=>{regionTierPreviewPointer=null});
  regionTierPreview=panel;
  refreshRegionTierPreview();
  return panel;
}
function regionTierPreviewSources(){
  const worldMap=customWorldMap();
  const worldMapSrc=worldMap?String(worldMap.transparent&&worldMap.transparentSrc?worldMap.transparentSrc:worldMap.originalSrc||'').trim():'';
  return CANONICAL_PLANE_KEYS.map((key,index)=>{
    if(index===0&&worldMapSrc)return worldMapSrc;
    const node=planeByKey[key];
    const live=String(node?.currentSrc||node?.src||'').trim();
    return String(regionCanonicalTierImages[index]||live||(BASE_WORLD_ASSETS[index]?ASSET_ROOT+BASE_WORLD_ASSETS[index].file:'')).trim();
  });
}
function refreshRegionTierPreviewImages(){
  const panel=regionTierPreview;if(!panel?.isConnected)return;
  const current=currentRegionTierIndex(),sources=regionTierPreviewSources();
  let anyVisibleLoaded=false,visibleExpected=0,visibleErrors=0;
  panel.querySelectorAll('[data-tier-image]').forEach(image=>{
    const tier=clamp(Math.trunc(Number(image.dataset.tierImage)||0),0,TIERS.length-1);
    const visible=tier<=current,src=String(sources[tier]||'');
    image.hidden=!visible;
    image.style.opacity=visible?'1':'0';
    if(visible){
      visibleExpected++;
      if(src&&String(image.currentSrc||image.src||'')!==src){
        image.dataset.loaded='false';image.dataset.loadError='false';image.dataset.fallbackTried='false';image.src=src;
      }
      if(image.complete&&image.naturalWidth>1){image.dataset.loaded='true';anyVisibleLoaded=true}
      if(image.dataset.loadError==='true')visibleErrors++;
    }
  });
  const status=panel.querySelector('[data-tier-map-status]');
  if(status){
    if(anyVisibleLoaded){status.hidden=true;status.textContent=''}
    else{
      status.hidden=false;
      status.textContent=visibleExpected>0&&visibleErrors>=visibleExpected
        ? 'WORLD TIER IMAGE UNAVAILABLE'
        : 'LOADING WORLD TIER…';
    }
  }
  panel.dataset.previewTier=String(current);
}
function refreshRegionTierPreview(){
  const panel=ensureRegionTierPreview();if(!panel)return;
  const tier=tierByKey(viewerTier==='all'?'sea':viewerTier);
  const title=panel.querySelector('[data-tier-title]');
  if(title)title.textContent=`TIER ${tier.index+1} · ${tierLabel(tier).toUpperCase()}`;
  const dots=panel.querySelector('[data-tier-dots]');
  if(dots)dots.innerHTML=TIERS.map(item=>`<i class="${item.index===tier.index?'active':''}"></i>`).join('');
  refreshRegionTierPreviewImages();
}
function stepRegionTierPreview(delta){
  if(!REGION_DEFINER)return;
  const current=currentRegionTierIndex();
  const next=(current+Number(delta)+TIERS.length)%TIERS.length;
  setViewerTier(TIERS[next].key);
  fitMap();
  refreshRegionTierPreview();
}
function showRegionTierPreview(){
  if(!REGION_DEFINER||READ_ONLY)return;
  regionClaimPhase='tier-preview';regionSelectionEnabled=false;regionCropPreview=false;
  regionSelectedCells.clear();regionNameDraft='';
  clearClaimedRegionCrop(false);
  viewerLayer=0;
  if(viewerTier==='all')viewerTier='sea';
  updateTierButton();renderTierMenu();updateRegionWorldSourceVisibility();fitMap();updateRegionSelectionOverlay();
  stage.classList.add('region-tier-previewing');stage.classList.remove('region-selection-only','region-build-mode');
  stage.dataset.regionEntry='tier-preview';
  const panel=ensureRegionTierPreview();if(panel){panel.hidden=false;refreshRegionTierPreview()}
  if(!keyboard.hidden)closeKeyboard();
}
function hideRegionTierPreview(){
  if(regionTierPreview)regionTierPreview.hidden=true;
  stage.classList.remove('region-tier-previewing');
  stage.dataset.regionEntry='selection';
}
function confirmRegionTierPreview(){
  if(!REGION_DEFINER||READ_ONLY)return;
  chooseRegionClaimTier(viewerTier==='all'?'sea':viewerTier);
}
function startRegionClaim(){
  if(!REGION_DEFINER||READ_ONLY)return;
  pendingClaimedRegionId='';regionClaimedRegion=null;
  viewerTier='sea';viewerLayer=0;
  showRegionTierPreview();
  renderKeyboardTabs();renderKeyboardKeys();
  announce(`${CLAIM_ONLY?'Claim Region':'New Region'}. Swipe through the world tiers and select one.`);
}
function chooseRegionClaimTier(key){
  if(!REGION_DEFINER)return;
  hideRegionTierPreview();
  setViewerTier(key);
  regionClaimPhase='select';regionSelectionEnabled=false;regionCropPreview=false;regionSelectedCells.clear();
  keyboardMode='Select';
  stage.classList.add('region-selection-only');stage.classList.remove('region-build-mode');
  // Refit after the modal preview disappears and explicitly re-apply the
  // canonical tier visibility. Mobile browsers can otherwise retain the preview
  // frame while the underlying transformed world remains outside the viewport.
  updateRegionWorldSourceVisibility();
  fitMap();
  applyParallax();
  updateRegionSelectionOverlay();renderKeyboardTabs();renderKeyboardKeys();
  if(keyboard.hidden)openKeyboard();
  announce(`Tier ${currentRegionTierIndex()+1}, ${tierLabel(tierByKey(viewerTier))}, selected. Position and zoom the map, then press Select to freeze the view and choose hexes.`);
}
function cancelRegionClaim(){
  if(!REGION_DEFINER)return;
  showRegionTierPreview();
  renderKeyboardTabs();renderKeyboardKeys();
  announce('Region selection cleared. Choose a tier again.');
}
function previewRegionCrop(){
  if(!REGION_DEFINER||regionClaimPhase!=='select'||!regionSelectedCells.size)return;
  const preview={
    selectedCells:[...regionSelectedCells].sort((a,b)=>a-b),
    gridShape:regionGridShape,
    tierIndex:currentRegionTierIndex()
  };
  regionClaimPhase='crop';regionCropPreview=true;regionSelectionEnabled=false;
  stage.classList.add('region-selection-only');
  updateRegionSelectionOverlay();
  applyRegionMask(preview,'selection-preview',false);
  renderKeyboardKeys();
  announce(`Crop preview ready for ${regionSelectedCells.size} selected ${regionGridShape} tile${regionSelectedCells.size===1?'':'s'}. Name this regional map, then save it.`);
}
function returnToRegionSelection(){
  if(!REGION_DEFINER)return;
  clearRegionMask(false);
  regionClaimPhase='select';regionCropPreview=false;regionSelectionEnabled=true;stage.classList.add('region-selection-only');
  updateRegionSelectionOverlay();fitMap();renderKeyboardKeys();
  announce('Region selection reopened.');
}
async function persistRegionClaimWorkspace(){
  // Region claims persist as authority metadata. The map itself is never copied:
  // RegionDefiner edits the one canonical database map through saveRegionMapToDatabase().
  return;
}
function createRegionDefinition(){
  if(!REGION_DEFINER||READ_ONLY||regionCreatePending)return;
  if(regionClaimPhase!=='crop'){announce('Preview the crop before saving the region.');return}
  const name=String(regionNameDraft||'').trim();
  if(!name){announce('Name the region before saving or requesting it.');return}
  if(!regionSelectedCells.size){announce('Select at least one world tile for the region.');return}
  regionCreatePending=true;renderKeyboardKeys();
  const payload={
    name,
    cells:[...regionSelectedCells].sort((a,b)=>a-b),
    tierIndex:currentRegionTierIndex(),
    sourceLayerOffsets:[...regionWorldLayerSet()].sort((a,b)=>a-b),
    gridShape:regionGridShape
  };
  const sent=postRegionMessage(CLAIM_ONLY?'request-claim':'create-region',payload);
  if(!sent){regionCreatePending=false;renderKeyboardKeys();announce('Region persistence bridge is unavailable.');return}
  announce(CLAIM_ONLY?'Sending the selected world footprint to the GM for permission review.':`Saving ${name}. This defines the regional view and authority only; the canonical world map remains intact.`);
}
function buildClaimedRegion(){
  if(!REGION_DEFINER||!regionClaimedRegion||CLAIM_ONLY)return;
  regionClaimPhase='build';regionSelectionEnabled=false;regionCropPreview=false;keyboardMode='Tiles';
  stage.classList.add('region-build-mode');stage.classList.remove('region-selection-only','region-tier-previewing');
  renderKeyboardTabs();renderKeyboardKeys();updateRegionSelectionOverlay();
  announce(`Building ${regionClaimedRegion.name||'region'}. ${regionGridShape==='hex'?'Hex':'Square'} placement snapping is active.`);
}
function renderRegionSelectKeyboard(){
  const visibleWorldLayers=[...regionWorldLayerSet()].sort((a,b)=>a-b);
  if(regionClaimPhase==='tier-preview'){
    keyboardKeys.append(
      readoutKey(CLAIM_ONLY?'CLAIM REGION':'NEW REGION','choose a world tier first'),
      readoutKey(`TIER ${currentRegionTierIndex()+1}`,tierLabel(tierByIndex(currentRegionTierIndex()))),
      toolKey('CHOOSE TIER','return to swipe preview',showRegionTierPreview)
    );return;
  }
  if(regionClaimPhase==='idle'){
    keyboardKeys.append(
      readoutKey('REGION','no active region'),
      toolKey(regionWorldSourceMeta?'NEW REGION':'LOADING…',regionWorldSourceMeta?'choose a Tier and select the map':'waiting for selected world',startRegionClaim,!regionWorldSourceMeta),
      readoutKey(`${regionCatalog.length} SAVED`,'defined regions')
    );return;
  }
  if(regionClaimPhase==='select'){
    keyboardKeys.append(
      toolKey(regionSelectionEnabled?'DESELECT':'SELECT',regionSelectionEnabled?'unlock map zoom and pan':'freeze map and select hexes',toggleRegionSelectionMode),
      toolKey('CLAIM',regionSelectedCells.size?'claim selected coordinates':'select hexes first',claimRegionSelection,!regionSelectedCells.size),
      toolKey('−','zoom',()=>zoomCenter(1/1.22),regionSelectionEnabled),
      toolKey('+','zoom',()=>zoomCenter(1.22),regionSelectionEnabled),
      toolKey('⛶','fit map',fitMap,regionSelectionEnabled),
      readoutKey(`TIER ${currentRegionTierIndex()+1}`,tierLabel(tierByIndex(currentRegionTierIndex()))),
      readoutKey(regionGridShape.toUpperCase(),'selection grid'),
      readoutKey(`${regionSelectedCells.size} TILES`,regionSelectedCells.size?'selected footprint':'select at least 1'),
      readoutKey(`${visibleWorldLayers.length}/10 WORLD`,'source layers included'),
      toolKey(regionGridShape==='square'?'SQUARE ✓':'HEX ✓','change selection grid',cycleRegionGridShape),
      toolKey('CLEAR','selection',()=>clearRegionSelection(true),!regionSelectedCells.size),
      toolKey('CHOOSE TIER','restart tier preview',showRegionTierPreview),
      toolKey('CLAIM','claim selected coordinates',claimRegionSelection,!regionSelectedCells.size)
    );return;
  }
  if(regionClaimPhase==='crop'){
    keyboardKeys.append(
      regionNameInput(),
      readoutKey(`TIER ${currentRegionTierIndex()+1}`,tierLabel(tierByIndex(currentRegionTierIndex()))),
      readoutKey(`${regionSelectedCells.size} TILES`,'crop footprint'),
      readoutKey(regionGridShape.toUpperCase(),'region grid'),
      toolKey('BACK','edit selected tiles',returnToRegionSelection),
      toolKey(regionCreatePending?(CLAIM_ONLY?'SENDING…':'SAVING…'):(CLAIM_ONLY?'REQUEST':'SAVE REGION'),CLAIM_ONLY?'send to GM for permission review':'crop and save selected map',createRegionDefinition,READ_ONLY||regionCreatePending||!regionSelectedCells.size)
    );return;
  }
  if(regionClaimPhase==='requested'){
    keyboardKeys.append(
      readoutKey('REQUEST SENT','GM approval required'),
      readoutKey(`TIER ${currentRegionTierIndex()+1}`,tierLabel(tierByIndex(currentRegionTierIndex()))),
      readoutKey(`${regionSelectedCells.size} TILES`,'requested footprint'),
      toolKey('NEW REQUEST','select another portion',startRegionClaim)
    );return;
  }
  const region=regionClaimedRegion;
  keyboardKeys.append(
    readoutKey(String(region?.name||'REGION').toUpperCase(),regionClaimPhase==='build'?'building regional map':'saved cropped region'),
    readoutKey(`TIER ${Math.trunc(Number(region?.tierIndex)||currentRegionTierIndex())+1}`,tierLabel(tierByIndex(Math.trunc(Number(region?.tierIndex)||currentRegionTierIndex())))),
    readoutKey(normalizeRegionGridShape(region?.gridShape||regionGridShape).toUpperCase(),'placement grid'),
    readoutKey(`${Array.isArray(region?.selectedCells)?region.selectedCells.length:0} TILES`,'full regional map'),
    toolKey(regionClaimPhase==='build'?'BUILDING ✓':'BUILD REGION','open regional assets',buildClaimedRegion,READ_ONLY||CLAIM_ONLY),
    toolKey('NEW REGION','define another region',startRegionClaim,READ_ONLY)
  );
}
async function handleRegionHostMessage(event){
  if(!REGION_DEFINER||event.origin!==location.origin||event.source!==window.parent)return;
  const data=event.data;if(!data||data.source!=='shaelvien-regiondefiner-host')return;
  if(data.type==='bridge-ready'){postRegionMessage('ready');return}
  if(data.type==='world-source'){
    await renderRegionWorldSource(data.worldSource||{});
    return;
  }
  if(data.type==='map-load-error'){
    if(BASE_WORLD_ASSETS.length){
      loading.hidden=true;
      announce('The canonical base map is visible. Database-authored layers are temporarily unavailable.');
    }else{
      loading.hidden=false;
      loading.textContent='MAP DATABASE UNAVAILABLE';
      announce(String(data.message||'Canonical map database is unavailable.'));
    }
    return;
  }
  if(data.type==='catalog-error'){
    announce('The map is available, but Region permissions could not be refreshed yet.');
    return;
  }
  if(data.type==='catalog'){
    regionCatalog=Array.isArray(data.regions)?data.regions:[];
    if(pendingClaimedRegionId&&!regionClaimedRegion){
      const claimed=regionCatalog.find(region=>String(region?.id||'')===pendingClaimedRegionId);
      if(claimed)applyClaimedRegionCrop(claimed)
    }
    updateRegionSelectionOverlay();renderKeyboardKeys();return;
  }
  if(data.type==='region-created'){
    regionCreatePending=false;
    if(data.region)regionCatalog=[...regionCatalog.filter(r=>String(r?.id)!==String(data.region.id)),data.region];
    const claimed=data.region;
    const savedName=String(claimed?.name||regionNameDraft||'Region');
    regionNameDraft='';regionClaimPhase='saved';
    if(claimed)applyClaimedRegionCrop(claimed);
    regionSelectedCells.clear();updateRegionSelectionOverlay();renderKeyboardKeys();
    await persistRegionClaimWorkspace();
    announce(`${savedName} saved. The viewer now hides everything outside the region; the underlying canonical world map is unchanged.`);return;
  }
  if(data.type==='map-region-saved'||data.type==='map-region-save-error'){
    const requestId=String(data.requestId||''),waiter=regionMapSaveWaiters.get(requestId);
    if(!waiter)return;
    clearTimeout(waiter.timeout);regionMapSaveWaiters.delete(requestId);
    if(data.type==='map-region-saved'&&data.result?.success!==false)waiter.resolve(data.result||true);
    else waiter.reject(new Error(String(data.message||'Canonical world map save failed.')));
    return;
  }
  if(data.type==='claim-requested'){
    regionCreatePending=false;
    const result=data.result||{};
    if(result.success){
      regionClaimPhase='requested';regionCropPreview=false;regionSelectionEnabled=false;updateRegionSelectionOverlay();renderKeyboardKeys();
      announce(String(result.message||'Claim request sent to the GM. No build authority has been granted yet.'));
    }else{
      renderKeyboardKeys();announce(String(result.message||'The claim request was not accepted. Nothing was granted.'));
    }
    return;
  }
  if(data.type==='error'){regionCreatePending=false;renderKeyboardKeys();announce(String(data.message||'Region operation failed.'))}
}
if(REGION_DEFINER){
  window.addEventListener('message',handleRegionHostMessage);
  // Build the tier chooser immediately from the canonical/base tier sources. The
  // database message may refine those images/layers later, but it must not gate
  // the first visible step of the new-region workflow.
  if(REGION_FLOW==='new'&&!READ_ONLY)showRegionTierPreview();
  queueMicrotask(()=>{ensureRegionSelectionOverlay();postRegionMessage('ready')});
}else if(LIVE_WORLDBUILDER&&window.parent!==window){
  window.addEventListener('message',handleWorldBuilderHostMessage);
  queueMicrotask(()=>postWorldBuilderHostMessage('ready'));
}
function tierDisplay(index){const tier=tierByIndex(clamp(Math.trunc(Number(index)||0),0,TIERS.length-1));return{number:tier.index+1,label:tierLabel(tier)}}
function layerDisplay(index){return clamp(Math.trunc(Number(index)||0),0,9)+1}
function selectedPositionSummary(item){
  if(!item)return{tier:1,tierLabel:tierLabel(TIERS[0]),layer:1,x:'0.000',y:'0.000'};
  const tier=tierDisplay(item.tier);
  return{tier:tier.number,tierLabel:tier.label,layer:layerDisplay(item.layer),x:(Number(item.x)||0).toFixed(3),y:(Number(item.y)||0).toFixed(3)};
}
function personalSessionToken(){
  try{
    const parentToken=window.parent&&window.parent!==window?window.parent.ristAuth?.sessionInfo?.().token:'';
    return String(parentToken||sessionStorage.getItem('rist.session')||'');
  }catch{return String(sessionStorage.getItem('rist.session')||'')}
}
async function personalAuthConfig(){
  if(personalAuthConfigPromise)return personalAuthConfigPromise;
  personalAuthConfigPromise=(async()=>{
    const response=await fetch('../auth-config.json',{cache:'no-store'});
    if(!response.ok)throw new Error('Account storage configuration unavailable');
    const config=await response.json(),base=String(config?.apiBaseUrl||config?.ApiBaseUrl||'').replace(/\/$/,'');
    if(!/^https?:\/\//i.test(base))throw new Error('Account storage is not configured');
    return{base};
  })();
  try{return await personalAuthConfigPromise}catch(error){personalAuthConfigPromise=null;throw error}
}
async function personalApi(path,options={}){
  const token=personalSessionToken();
  if(!token)throw new Error('Log in to use your personal Uploads folders');
  const {base}=await personalAuthConfig();
  const headers=new Headers(options.headers||{});headers.set('Authorization',`Bearer ${token}`);
  const response=await fetch(base+path,{...options,headers,cache:'no-store'});
  if(response.status===401)throw new Error('Your login expired. Log in again');
  if(!response.ok){
    let message='Personal storage request failed';
    try{const payload=await response.json();message=String(payload?.error||payload?.Error||message)}catch{}
    throw new Error(message);
  }
  return response;
}
function personalSafeFileName(name){
  const base=String(name||'asset.png').split(/[\\/]/).pop()||'asset.png';
  const cleaned=base.replace(/[^a-z0-9._-]+/gi,'-').replace(/^-+|-+$/g,'');
  return cleaned||'asset.png';
}
function personalPathSegment(value){
  const segment=String(value||'custom').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');
  return segment||'custom';
}
function personalEntryValue(entry,name,fallback=null){
  if(!entry||typeof entry!=='object')return fallback;
  const camel=name.charAt(0).toLowerCase()+name.slice(1);
  return entry[name]??entry[camel]??fallback;
}
async function personalDownloadUrl(key){
  const response=await personalApi('/storage/download?key='+encodeURIComponent(key));
  const payload=await response.json();
  return String(payload?.url||payload?.Url||'');
}
async function readPersonalCatalog(){
  try{
    const url=await personalDownloadUrl(PERSONAL_ASSET_INDEX_KEY);
    if(!url)return{Items:[],UpdatedAtUtc:new Date().toISOString()};
    const response=await fetch(url,{cache:'no-store'});
    if(!response.ok)return{Items:[],UpdatedAtUtc:new Date().toISOString()};
    const payload=await response.json();
    const items=Array.isArray(payload?.Items)?payload.Items:Array.isArray(payload?.items)?payload.items:[];
    return{...payload,Items:items};
  }catch(error){
    if(/not found|404/i.test(String(error?.message||error)))return{Items:[],UpdatedAtUtc:new Date().toISOString()};
    throw error;
  }
}
async function uploadPersonalBlob(key,blob,contentType){
  const prepare=await personalApi('/storage/upload',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({key,contentType})
  });
  const post=await prepare.json(),url=String(post?.url||post?.Url||''),fields=post?.fields||post?.Fields||{};
  if(!url)throw new Error('Personal upload could not be prepared');
  const form=new FormData();
  Object.entries(fields).forEach(([field,value])=>form.append(field,String(value)));
  form.append('file',blob,personalSafeFileName(key));
  const result=await fetch(url,{method:'POST',body:form});
  if(!result.ok)throw new Error('Personal upload failed');
}
async function writePersonalCatalog(catalog){
  const payload={...catalog,Items:Array.isArray(catalog?.Items)?catalog.Items:[],UpdatedAtUtc:new Date().toISOString()};
  await uploadPersonalBlob(PERSONAL_ASSET_INDEX_KEY,new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}),'application/json');
  return payload;
}
function normalizePersonalAsset(entry,url=''){
  const key=String(personalEntryValue(entry,'Key','')),category=String(personalEntryValue(entry,'Category','Tiles'));
  const kind=String(personalEntryValue(entry,'AssetKind',category==='Sprites'?'sprite':'image')).toLowerCase();
  return{
    key,name:String(personalEntryValue(entry,'Name',key.split('/').pop()||'Upload')),
    category,folder:String(personalEntryValue(entry,'Folder','Custom')),assetKind:kind,url,
    uploadedAt:String(personalEntryValue(entry,'UploadedAtUtc','')),
    columns:Math.max(1,Number(personalEntryValue(entry,'SpriteColumns',1))||1),
    rows:Math.max(1,Number(personalEntryValue(entry,'SpriteRows',1))||1),
    frameCount:Math.max(1,Number(personalEntryValue(entry,'FrameCount',1))||1),
    fps:Math.max(0,Number(personalEntryValue(entry,'FramesPerSecond',0))||0),
    sourceWidth:Math.max(0,Number(personalEntryValue(entry,'SourceWidth',0))||0),
    sourceHeight:Math.max(0,Number(personalEntryValue(entry,'SourceHeight',0))||0),
    cropX:Math.max(0,Number(personalEntryValue(entry,'CropX',0))||0),
    cropY:Math.max(0,Number(personalEntryValue(entry,'CropY',0))||0),
    cropWidth:Math.max(0,Number(personalEntryValue(entry,'CropWidth',0))||0),
    cropHeight:Math.max(0,Number(personalEntryValue(entry,'CropHeight',0))||0),
    whiteTransparent:!!personalEntryValue(entry,'WhiteTransparent',false)
  };
}
async function ensurePersonalAssets(force=false){
  if(personalAssetLoading)return personalAssets;
  if(personalAssets.length&&!force)return personalAssets;
  personalAssetLoading=true;personalAssetError='';renderKeyboardKeys();
  try{
    const catalog=await readPersonalCatalog();
    const entries=[...(catalog.Items||[])].sort((a,b)=>String(personalEntryValue(b,'UploadedAtUtc','')).localeCompare(String(personalEntryValue(a,'UploadedAtUtc','')))).slice(0,300);
    const hydrated=await Promise.all(entries.map(async entry=>{
      const key=String(personalEntryValue(entry,'Key',''));if(!key)return null;
      try{return normalizePersonalAsset(entry,await personalDownloadUrl(key))}catch{return normalizePersonalAsset(entry,'')}
    }));
    personalAssets=hydrated.filter(asset=>asset?.key&&asset.url);
    return personalAssets;
  }catch(error){
    personalAssetError=String(error?.message||error||'Personal uploads unavailable');
    return personalAssets;
  }finally{personalAssetLoading=false;renderKeyboardKeys()}
}
function trackPersonalUpload(promise){
  pendingPersonalUploads.add(promise);
  promise.then(()=>pendingPersonalUploads.delete(promise),()=>pendingPersonalUploads.delete(promise));
  return promise;
}
async function saveFileToPersonalLibrary(file,metadata={}){
  if(!file||Number(file.size||0)<=0)throw new Error('The upload is empty');
  if(Number(file.size||0)>PERSONAL_ASSET_MAX_BYTES)throw new Error('Personal uploads are limited to 20 MB each');
  const category=String(metadata.category||'Images'),folder=String(metadata.folder||`My ${category}`);
  const safe=personalSafeFileName(file?.name||'asset.png');
  const key=`uploads/${personalPathSegment(category)}/${personalPathSegment(folder)}/${crypto.randomUUID?.()||Date.now()}-${safe}`;
  await uploadPersonalBlob(key,file,file.type||'application/octet-stream');
  const catalog=await readPersonalCatalog(),items=[...(catalog.Items||[])];
  const entry={
    Key:key,Name:String(metadata.name||String(file?.name||'Upload').replace(/\.[^.]+$/,'')),Category:category,Folder:folder,
    UploadedAtUtc:new Date().toISOString(),AssetKind:String(metadata.assetKind||'image'),
    SpriteColumns:Math.max(1,Math.trunc(Number(metadata.columns)||1)),SpriteRows:Math.max(1,Math.trunc(Number(metadata.rows)||1)),
    FrameCount:Math.max(1,Math.trunc(Number(metadata.frameCount)||1)),FramesPerSecond:Math.max(0,Number(metadata.fps)||0),
    SourceWidth:Math.max(0,Math.trunc(Number(metadata.sourceWidth)||0)),SourceHeight:Math.max(0,Math.trunc(Number(metadata.sourceHeight)||0)),
    CropX:Math.max(0,Math.trunc(Number(metadata.cropX)||0)),CropY:Math.max(0,Math.trunc(Number(metadata.cropY)||0)),
    CropWidth:Math.max(0,Math.trunc(Number(metadata.cropWidth)||0)),CropHeight:Math.max(0,Math.trunc(Number(metadata.cropHeight)||0)),
    WhiteTransparent:!!metadata.whiteTransparent
  };
  items.push(entry);await writePersonalCatalog({...catalog,Items:items});
  const asset=normalizePersonalAsset(entry,await personalDownloadUrl(key));
  personalAssets=[asset,...personalAssets.filter(existing=>existing.key!==key)];
  renderKeyboardKeys();
  return asset;
}
function personalExtensionForType(type){
  switch(String(type||'').toLowerCase()){
    case 'image/jpeg':return '.jpg';
    case 'image/webp':return '.webp';
    case 'image/gif':return '.gif';
    default:return '.png';
  }
}
async function promoteRestoredLayerToPersonal(item){
  if(!item||item.personalAssetKey||item.assetId)return null;
  const source=String(item.kind==='sprite'?(item.spriteSheetSrc||''):(item.originalSrc||''));
  if(!source.startsWith('data:image/'))return null;
  const blob=await (await fetch(source)).blob();
  const base=personalSafeFileName(item.name|| (item.kind==='sprite'?'Saved sprite':'Saved image')).replace(/\.[^.]+$/,'');
  const file=new File([blob],base+personalExtensionForType(blob.type),{type:blob.type||'image/png'});
  const category=item.kind==='sprite'?'Sprites':'Images',folder=item.kind==='sprite'?'My Sprites':'My Images';
  const asset=await saveFileToPersonalLibrary(file,{
    category,folder,assetKind:item.kind==='sprite'?'sprite':'image',name:item.name||base,
    columns:item.spriteColumns||1,rows:item.spriteRows||1,frameCount:item.spriteFrameCount||1,fps:item.spriteFps||0,
    sourceWidth:item.spriteSourceWidth||0,sourceHeight:item.spriteSourceHeight||0,cropX:item.spriteCropX||0,cropY:item.spriteCropY||0,
    cropWidth:item.spriteCropWidth||0,cropHeight:item.spriteCropHeight||0,whiteTransparent:item.spriteWhiteTransparent!==false
  });
  item.assetId=`private:${asset.key}`;item.personalAssetKey=asset.key;
  announce(`${item.name||'Saved upload'} migrated into ${folder}.`);
  return asset;
}
function personalAssetsFor(type){
  if(type==='Sprites')return personalAssets.filter(asset=>asset.assetKind==='sprite'||asset.category==='Sprites');
  if(type==='Images')return personalAssets.filter(asset=>asset.category==='Images'&&asset.assetKind!=='sprite');
  if(type==='Tiles')return personalAssets.filter(asset=>asset.category==='Tiles');
  if(type==='Uploads')return personalAssets.filter(asset=>asset.category!=='Images'&&asset.category!=='Sprites');
  return personalAssets;
}
function openPersonalFolder(type){personalFolderType=type;personalAssetPage=0;void ensurePersonalAssets();renderKeyboardKeys()}
function closePersonalFolder(){personalFolderType=null;personalAssetPage=0;renderKeyboardKeys()}
function personalPageAssets(type){
  const assets=personalAssetsFor(type),pages=Math.max(1,Math.ceil(assets.length/PERSONAL_ASSET_PAGE_SIZE));
  personalAssetPage=clamp(personalAssetPage,0,pages-1);
  return{assets:assets.slice(personalAssetPage*PERSONAL_ASSET_PAGE_SIZE,(personalAssetPage+1)*PERSONAL_ASSET_PAGE_SIZE),pages,total:assets.length};
}
function placePersonalImage(asset){
  if(READ_ONLY){announce('World reference mode is view only.');return;}
  if(!asset?.url)return;
  const placementRole=currentAssetPlacementRole(),rawPoint=viewerCenterPosition(),point=REGION_DEFINER?snapRegionPoint(rawPoint.x,rawPoint.y):rawPoint,address=placementAddress(currentTierIndex(),1);
  const item={
    id:`private-image:${crypto.randomUUID?.()||Date.now()}`,assetId:`private:${asset.key}`,personalAssetKey:asset.key,name:asset.name,kind:'image',libraryTile:false,sourceLocked:false,regionOverlay:REGION_DEFINER,regionId:REGION_DEFINER?activeRegionMapId():'',
    placementRole,fullWorld:placementRole==='world-map',
    originalSrc:asset.url,transparentSrc:asset.url,transparent:false,x:placementRole==='world-map'?.5:point.x,y:placementRole==='world-map'?.5:point.y,tier:placementRole==='world-map'?0:address.tier,layer:placementRole==='world-map'?0:address.layer,
    size:1,rotation:0,opacity:1,committed:false,renderOpacity:1,zoomPassed:false,zoomPassScale:null,node:null
  };
  if(isWorldMapItem(item))removeCustomWorldMap(item);
  const node=document.createElement('img');node.className=`user-image-placement${isWorldMapItem(item)?' full-world-placement':''}`;node.alt=item.name;node.draggable=false;item.node=node;
  node.addEventListener('pointerdown',event=>beginImageDrag(event,item));node.addEventListener('pointermove',moveImageDrag);node.addEventListener('pointerup',endImageDrag);node.addEventListener('pointercancel',endImageDrag);
  userLayers.push(item);world.appendChild(node);world.dataset.emptyWorld='false';void primeCollisionMask(asset.url);updateLayerOrder();refreshUserImage(item);selectUserImage(item);
  personalFolderType=null;keyboardMode='Image';openKeyboard();renderKeyboardTabs();renderKeyboardKeys();applyParallax();scheduleRegionEnhancement(30);
  if(isWorldMapItem(item)){assetPlacementRole='layer';announce(`${item.name} is now the Sea Level World Map at 100% by 100%.`)}
  else announce(`${item.name} placed from My Images as an adjustable layer. Save commits this instance.`);
}
async function placePersonalSprite(asset){
  if(READ_ONLY){announce('World reference mode is view only.');return;}
  if(!asset?.url)return;
  const item=await placeSpriteDefinition({
    id:`private-sprite:${crypto.randomUUID?.()||Date.now()}`,assetId:`private:${asset.key}`,name:asset.name,sheetSrc:asset.url,
    columns:asset.columns,rows:asset.rows,frameCount:asset.frameCount,fps:asset.fps||6,sourceWidth:asset.sourceWidth,sourceHeight:asset.sourceHeight,
    cropX:asset.cropX,cropY:asset.cropY,cropWidth:asset.cropWidth,cropHeight:asset.cropHeight,whiteTransparent:asset.whiteTransparent
  });
  item.personalAssetKey=asset.key;personalFolderType=null;return item;
}
function placePersonalTile(asset){
  if(READ_ONLY){announce('World reference mode is view only.');return;}
  if(!asset?.url)return;
  placeLibraryTile({id:`private:${asset.key}`,name:asset.name,image:asset.url});
  if(selectedImage)selectedImage.personalAssetKey=asset.key;
  personalFolderType=null;
}
function personalAssetKey(asset,type){
  const button=document.createElement('button');button.type='button';button.className='library-tile-key';button.setAttribute('aria-label',`${asset.name}. Personal ${type.toLowerCase()} upload.`);
  const image=document.createElement('img');image.src=asset.url;image.alt='';image.loading='lazy';image.decoding='async';image.draggable=false;image.style.width='100%';image.style.height='100%';image.style.objectFit='cover';
  const label=document.createElement('small');label.textContent=asset.name;button.append(image,label);
  button.addEventListener('click',()=>{if(type==='Sprites')void placePersonalSprite(asset);else if(type==='Images')placePersonalImage(asset);else placePersonalTile(asset)});
  return button;
}
function renderPersonalFolder(type,title){
  if(type==='Images'||type==='Tiles')appendPlacementRoleControls();
  if(personalAssetLoading){keyboardKeys.append(toolKey('‹','Back',closePersonalFolder),toolKey('LOADING',title,()=>{},true));return}
  if(personalAssetError&&!personalAssets.length){
    keyboardKeys.append(toolKey('‹','Back',closePersonalFolder),toolKey('RETRY',title,()=>{personalAssetError='';void ensurePersonalAssets(true)}),toolKey('ERROR',personalAssetError,()=>{},true));return;
  }
  const page=personalPageAssets(type);
  keyboardKeys.append(toolKey('‹','Back',closePersonalFolder),toolKey(title,`${page.total} upload${page.total===1?'':'s'} · Page ${personalAssetPage+1}/${page.pages}`,()=>{},true));
  page.assets.forEach(asset=>keyboardKeys.append(personalAssetKey(asset,type)));
  if(!page.assets.length)keyboardKeys.append(toolKey('EMPTY','No personal uploads yet',()=>{},true));
  if(page.pages>1)keyboardKeys.append(
    toolKey('‹','Previous',()=>{personalAssetPage=(personalAssetPage-1+page.pages)%page.pages;renderKeyboardKeys()}),
    toolKey('›','Next',()=>{personalAssetPage=(personalAssetPage+1)%page.pages;renderKeyboardKeys()})
  );
}
function tileLibraryAsset(raw){
  return{
    id:String(raw?.id||raw?.Id||''),
    name:String(raw?.name||raw?.Name||'Asset'),
    image:String(raw?.image||raw?.Image||''),
    layer:String(raw?.layer||raw?.Layer||''),
    directory:String(raw?.directory||raw?.Directory||''),
    folder:String(raw?.folder||raw?.Folder||''),
    kind:String(raw?.assetKind||raw?.AssetKind||'tile').toLowerCase(),
    scale:String(raw?.layer||raw?.Layer||'').toUpperCase()
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
      asset.id&&asset.image&&asset.kind!=='sprite'&&asset.scale===ASSET_SCALE&&(REGION_DEFINER||asset.directory.toLowerCase()==='terrain')
    );
    if(!tileCatalog.length)throw new Error(`No ${ASSET_SCALE.toLowerCase()} tiles are registered.`);
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
  if(READ_ONLY){announce('World reference mode is view only.');return;}
  if(!asset?.image)return;
  const placementRole=currentAssetPlacementRole(),rawPoint=viewerCenterPosition(),point=REGION_DEFINER?snapRegionPoint(rawPoint.x,rawPoint.y):rawPoint,address=placementAddress(currentTierIndex(),1),item={
    id:`library:${asset.id}:${crypto.randomUUID?.()||Date.now()}`,
    assetId:asset.id,name:asset.name,libraryTile:true,sourceLocked:false,regionOverlay:REGION_DEFINER,regionId:REGION_DEFINER?activeRegionMapId():'',
    placementRole,fullWorld:placementRole==='world-map',
    originalSrc:asset.image,transparentSrc:asset.image,transparent:false,
    x:placementRole==='world-map'?.5:point.x,y:placementRole==='world-map'?.5:point.y,tier:placementRole==='world-map'?0:address.tier,layer:placementRole==='world-map'?0:address.layer,
    size:1,rotation:0,opacity:1,committed:false,renderOpacity:1,zoomPassed:false,zoomPassScale:null,node:null
  };
  if(isWorldMapItem(item))removeCustomWorldMap(item);
  const node=document.createElement('img');node.className=`user-image-placement library-tile-placement${isWorldMapItem(item)?' full-world-placement':''}`;node.alt=asset.name;node.draggable=false;item.node=node;
  node.addEventListener('pointerdown',event=>beginImageDrag(event,item));node.addEventListener('pointermove',moveImageDrag);node.addEventListener('pointerup',endImageDrag);node.addEventListener('pointercancel',endImageDrag);
  userLayers.push(item);world.appendChild(node);world.dataset.emptyWorld='false';void primeCollisionMask(asset.image);updateLayerOrder();refreshUserImage(item);selectUserImage(item);
  keyboardMode='Image';openKeyboard();renderKeyboardTabs();renderKeyboardKeys();applyParallax();scheduleRegionEnhancement(30);
  if(isWorldMapItem(item)){assetPlacementRole='layer';announce(`${asset.name} is now the Sea Level World Map at 100% by 100%. Future images and tiles default to adjustable layers.`)}
  else announce(REGION_DEFINER?`${asset.name} placed inside ${regionClaimedRegion?.name||'the claimed region'} and snapped to its grid.`:`${asset.name} placed at the viewer center as an adjustable layer above Sea Level.`);
}
function libraryTileKey(asset){
  const button=document.createElement('button'),role=currentAssetPlacementRole();button.type='button';button.className='library-tile-key';button.setAttribute('aria-label',`${asset.name}. Tap to place this tile as ${role==='world-map'?'the full Sea Level World Map':'an adjustable layer'}.`);
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
    folder:String(raw?.folder||raw?.Folder||'Sprites'),kind:String(raw?.assetKind||raw?.AssetKind||'sprite').toLowerCase(),scale:String(raw?.layer||raw?.Layer||'').toUpperCase(),
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
    const raw=await response.json();spriteCatalog=(Array.isArray(raw)?raw:[]).map(spriteLibraryAsset).filter(asset=>asset.id&&asset.image&&asset.kind==='sprite'&&asset.scale===ASSET_SCALE);
    if(!spriteCatalog.length)throw new Error(`No registered ${ASSET_SCALE.toLowerCase()} sprites found.`);
    if(spriteLibraryFolder&&!spriteCatalog.some(asset=>asset.folder===spriteLibraryFolder))spriteLibraryFolder=null;spriteLibraryPage=0;
  }catch(error){spriteCatalog=[];spriteLibraryError=String(error?.message||error||'Sprite library unavailable.')}
  finally{spriteLibraryLoading=false;if(keyboardMode==='Sprites')renderKeyboardKeys()}
}
function spriteLibraryFolders(){return[...new Set(spriteCatalog.map(asset=>asset.folder).filter(Boolean))].sort((a,b)=>a.localeCompare(b))}
function currentSpriteLibraryAssets(){return spriteLibraryFolder?spriteCatalog.filter(asset=>asset.folder===spriteLibraryFolder):[]}
function spriteLibraryPageCount(){return Math.max(1,Math.ceil(currentSpriteLibraryAssets().length/SPRITE_LIBRARY_PAGE_SIZE))}
function spriteLibraryPageAssets(){spriteLibraryPage=clamp(spriteLibraryPage,0,spriteLibraryPageCount()-1);const start=spriteLibraryPage*SPRITE_LIBRARY_PAGE_SIZE;return currentSpriteLibraryAssets().slice(start,start+SPRITE_LIBRARY_PAGE_SIZE)}
async function placeSpriteDefinition(definition){
  if(READ_ONLY)throw new Error('World reference mode is view only.');
  const point=viewerCenterPosition(),address=placementAddress(currentTierIndex(),1);
  const extractOptions={
    columns:definition.columns,rows:definition.rows,frameCount:definition.frameCount,
    sourceWidth:definition.sourceWidth||0,sourceHeight:definition.sourceHeight||0,cropX:definition.cropX||0,cropY:definition.cropY||0,
    cropWidth:definition.cropWidth||0,cropHeight:definition.cropHeight||0,whiteTransparent:definition.whiteTransparent!==false
  };
  announce(`Preparing frame 1 of ${definition.name||'sprite'} for placement.`);
  const firstFrame=await extractSpriteFrame(definition.sheetSrc,extractOptions,0);
  const item={
    id:definition.id||crypto.randomUUID?.()||String(Date.now()),assetId:definition.assetId||null,name:definition.name||'Sprite',kind:'sprite',libraryTile:false,sourceLocked:false,regionOverlay:REGION_DEFINER,regionId:REGION_DEFINER?activeRegionMapId():'',
    spriteSheetSrc:definition.sheetSrc,spriteColumns:definition.columns,spriteRows:definition.rows,spriteFrameCount:Math.max(1,Number(definition.frameCount)||1),spriteFps:Math.max(1,Number(definition.fps)||6),
    spriteSourceWidth:definition.sourceWidth||null,spriteSourceHeight:definition.sourceHeight||null,spriteCropX:definition.cropX||0,spriteCropY:definition.cropY||0,
    spriteCropWidth:definition.cropWidth||null,spriteCropHeight:definition.cropHeight||null,spriteWhiteTransparent:definition.whiteTransparent!==false,
    frameSources:[firstFrame],currentFrame:0,playing:false,spriteReady:false,originalSrc:firstFrame,transparentSrc:firstFrame,transparent:true,
    x:point.x,y:point.y,tier:address.tier,layer:address.layer,size:1,rotation:0,opacity:1,committed:false,renderOpacity:1,zoomPassed:false,zoomPassScale:null,node:null
  };
  const node=document.createElement('img');node.className='user-image-placement sprite-placement';node.alt=item.name;node.draggable=false;item.node=node;
  node.addEventListener('pointerdown',event=>beginImageDrag(event,item));node.addEventListener('pointermove',moveImageDrag);node.addEventListener('pointerup',endImageDrag);node.addEventListener('pointercancel',endImageDrag);
  userLayers.push(item);world.appendChild(node);void primeCollisionMask(firstFrame);updateLayerOrder();refreshUserImage(item);selectUserImage(item);
  keyboardMode='Image';openKeyboard();renderKeyboardTabs();renderKeyboardKeys();applyParallax();scheduleRegionEnhancement(30);
  announce(`${item.name} placed using frame 1. It stays above the map while positioning; Save commits it to Tier ${selectedPositionSummary(item).tier}, Layer ${selectedPositionSummary(item).layer} and begins motion.`);

  item.spriteReadyPromise=extractSpriteFrames(definition.sheetSrc,extractOptions).then(frames=>{
    if(!item.node?.isConnected||!frames.length)return item;
    item.frameSources=frames;item.spriteFrameCount=frames.length;item.spriteReady=true;item.currentFrame=0;
    item.originalSrc=frames[0];item.transparentSrc=frames[0];refreshUserImage(item);
    frames.forEach(frame=>void primeCollisionMask(frame));
    if(item.committed&&frames.length>1)startSpriteMotion(item);
    announce(`${item.name} sprite set ready with ${frames.length} frames.`);
    return item;
  }).catch(error=>{
    item.spriteReady=false;item.spriteLoadError=String(error?.message||error||'frame preparation failed');
    announce(`${item.name} was placed with frame 1, but animation preparation failed: ${item.spriteLoadError}`);
    return item;
  });
  return item;
}
async function placeUploadedSprite(file){
  if(READ_ONLY){announce('World reference mode is view only.');return;}
  if(!file?.type?.startsWith('image/')){announce('Choose a sprite sheet image.');return}
  try{
    const sheetSrc=await fileDataUrl(file),columns=clamp(Math.trunc(Number(spriteColumns.value)||3),1,16),rows=clamp(Math.trunc(Number(spriteRows.value)||2),1,16);
    const frameCount=clamp(Math.trunc(Number(spriteFrameCount.value)||columns*rows),1,columns*rows),fps=clamp(Number(spriteFps.value)||6,1,30);
    const item=await placeSpriteDefinition({name:file.name||'Uploaded sprite',sheetSrc,columns,rows,frameCount,fps,whiteTransparent:true});
    item.personalUploadPromise=trackPersonalUpload(
      saveFileToPersonalLibrary(file,{
        category:'Sprites',folder:'My Sprites',assetKind:'sprite',name:String(file.name||'Uploaded sprite').replace(/\.[^.]+$/,''),
        columns,rows,frameCount,fps,whiteTransparent:true
      }).then(asset=>{
        item.assetId=`private:${asset.key}`;item.personalAssetKey=asset.key;
        announce(`${item.name} added to My Sprites.`);return asset;
      }).catch(error=>{announce(`${item.name} is placed, but My Sprites could not save it: ${String(error?.message||error)}`);return null})
    );
    closeSpriteUpload(false);
    keyboardMode='Image';openKeyboard();renderKeyboardTabs();renderKeyboardKeys();selectUserImage(item);
  }catch(error){announce(`Sprite upload failed: ${String(error?.message||error||'unknown error')}`)}
}
async function placeLibrarySprite(asset){
  if(READ_ONLY){announce('World reference mode is view only.');return;}
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
function renderKeyboardTabs(){RistViewerInput.preserveFocus(keyboardTabs,renderKeyboardTabsContent,keyboardToggle)}
function renderKeyboardTabsContent(){const modes=keyboardModes();if(!modes.includes(keyboardMode))keyboardMode=modes[0];keyboardTabs.replaceChildren();modes.forEach(mode=>{const b=document.createElement('button');b.type='button';b.role='tab';b.setAttribute('data-focus-key',mode);b.textContent=mode;b.classList.toggle('active',mode===keyboardMode);b.setAttribute('aria-selected',String(mode===keyboardMode));b.addEventListener('click',()=>{if(mode!==keyboardMode)personalFolderType=null;keyboardMode=mode;renderKeyboardTabs();renderKeyboardKeys();announce(`${mode} keyboard opened.`)});keyboardTabs.append(b)})}
function renderKeyboardKeys(){RistViewerInput.preserveFocus(keyboardKeys,renderKeyboardKeysContent,keyboardToggle)}
function renderKeyboardKeysContent(){
  if(!keyboardKeys)return;
  keyboardKeys.replaceChildren();
  if(REGION_DEFINER)updateRegionSelectionOverlay();
  if(keyboardMode==='Viewer'){
    keyboardKeys.append(
      toolKey('−','zoom',()=>zoomCenter(1/1.22)),
      toolKey('+','zoom',()=>zoomCenter(1.22)),
      toolKey('⛶','camera',fitMap),
      toolKey('⌁','reset tilt',resetTilt)
    );
    if(REGION_DEFINER)keyboardKeys.append(
      readoutKey(regionClaimedRegion?'REGION':'WORLD MAP',regionClaimedRegion?'claimed full map':'claim source'),
      regionClaimedRegion
        ? readoutKey(regionGridShape.toUpperCase(),'saved placement grid')
        : toolKey(regionGridShape==='square'?'SQUARE ✓':'HEX ✓','selection + placement grid',cycleRegionGridShape),
      toolKey(regionClaimedRegion?'REGION':(regionWorldSourceMeta?'CLAIM':'LOADING…'),regionClaimedRegion?'open claimed region':(regionWorldSourceMeta?'open Select tools':'waiting for selected world'),()=>{if(!regionClaimedRegion&&!regionWorldSourceMeta)return;keyboardMode='Select';renderKeyboardTabs();renderKeyboardKeys();announce(regionClaimedRegion?'Claimed Region controls opened.':'Claim Region controls opened.')},!regionClaimedRegion&&!regionWorldSourceMeta)
    );
    return;
  }
  if(keyboardMode==='Tiers'){
    if(!REGION_DEFINER){
      keyboardKeys.append(
        toolKey('≋','All Parallax',()=>setViewerTier('all')),
        toolKey('≈',tierLabel(TIERS[0]),()=>setViewerTier('sea')),
        toolKey('⌁',tierLabel(TIERS[1]),()=>setViewerTier('hills')),
        toolKey('▲',tierLabel(TIERS[2]),()=>setViewerTier('mountains')),
        toolKey('L −','layer',()=>{viewerLayer=clamp(viewerLayer-1,0,9);renderState();announce(`Viewer layer ${viewerLayer+1}.`)}),
        toolKey('L +','layer',()=>{viewerLayer=clamp(viewerLayer+1,0,9);renderState();announce(`Viewer layer ${viewerLayer+1}.`)}),
        toolKey('NAME','tier',renameViewerTier,viewerTier==='all'||READ_ONLY)
      );return;
    }
    const tierLocked=regionClaimPhase==='select'||regionClaimPhase==='crop'||regionClaimPhase==='saved'||regionClaimPhase==='build';
    if(tierLocked){
      keyboardKeys.append(
        readoutKey(`TIER ${currentRegionTierIndex()+1}`,`${tierLabel(tierByIndex(currentRegionTierIndex()))} · claim locked`),
        toolKey('WORK L −',`Layer ${viewerLayer+1}`,()=>{viewerLayer=clamp(viewerLayer-1,0,9);renderState();announce(`Viewer layer ${viewerLayer+1}.`)}),
        toolKey('WORK L +',`Layer ${viewerLayer+1}`,()=>{viewerLayer=clamp(viewerLayer+1,0,9);renderState();announce(`Viewer layer ${viewerLayer+1}.`)})
      );
    }else{
      keyboardKeys.append(
        toolKey(`≈${viewerTier==='sea'?' ✓':''}`,tierLabel(TIERS[0]),()=>setViewerTier('sea')),
        toolKey(`⌁${viewerTier==='hills'?' ✓':''}`,tierLabel(TIERS[1]),()=>setViewerTier('hills')),
        toolKey(`▲${viewerTier==='mountains'?' ✓':''}`,tierLabel(TIERS[2]),()=>setViewerTier('mountains'))
      );
    }
    keyboardKeys.append(
      toolKey('WORLD ALL','show source layers',()=>setRegionWorldLayersVisible(true)),
      toolKey('WORLD NONE','hide source layers',()=>setRegionWorldLayersVisible(false))
    );
    for(let layer=0;layer<10;layer++)keyboardKeys.append(regionWorldLayerKey(layer));
    if(regionClaimPhase==='select'||regionClaimPhase==='crop')keyboardKeys.append(toolKey('‹','back to claim',()=>{keyboardMode='Select';renderKeyboardTabs();renderKeyboardKeys();announce('Claim Region controls reopened.')}));    
    return;
  }
  if(keyboardMode==='Tiles'){
    if(personalFolderType==='Tiles'){renderPersonalFolder('Tiles','MY TILES');return}
    if(personalFolderType==='Uploads'){renderPersonalFolder('Uploads','MY ASSETS');return}
    appendPlacementRoleControls();
    if(!tileCatalog.length&&!tileLibraryLoading&&!tileLibraryError)void ensureTileLibrary();
    if(tileLibraryLoading){keyboardKeys.append(toolKey('MY TILES','Personal folder',()=>openPersonalFolder('Tiles')),toolKey('MY ASSETS','Other uploads',()=>openPersonalFolder('Uploads')),toolKey('LOADING','World tile library',()=>{},true));return}
    if(tileLibraryError){
      keyboardKeys.append(
        toolKey('MY TILES','Personal folder',()=>openPersonalFolder('Tiles')),
        toolKey('MY ASSETS','Other uploads',()=>openPersonalFolder('Uploads')),
        toolKey('RETRY','Tile library',()=>{tileLibraryError='';void ensureTileLibrary(true)}),
        toolKey('ERROR',tileLibraryError,()=>{},true)
      );return;
    }
    if(!tileLibraryFolder){
      const folders=tileLibraryFolders();
      keyboardKeys.append(
        toolKey('MY TILES','Personal folder',()=>openPersonalFolder('Tiles')),
        toolKey('MY ASSETS','Other uploads',()=>openPersonalFolder('Uploads')),
        toolKey(ASSET_SCALE,REGION_DEFINER?'Regional Asset Library':'Tile Library',()=>{},true)
      );
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
    if(personalFolderType==='Sprites'){renderPersonalFolder('Sprites','MY SPRITES');return}
    if(!spriteCatalog.length&&!spriteLibraryLoading&&!spriteLibraryError)void ensureSpriteLibrary();
    keyboardKeys.append(
      toolKey('UPLOAD','sprite set',openSpriteUpload),
      toolKey('MY SPRITES','Personal folder',()=>openPersonalFolder('Sprites')),
      toolKey(ASSET_SCALE,'Sprite library filter',()=>{},true)
    );
    if(selectedImage?.kind==='sprite'){
      keyboardKeys.append(
        toolKey('FPS −',`${Math.max(1,Number(selectedImage.spriteFps)||6)} fps`,()=>{selectedImage.spriteFps=clamp((Number(selectedImage.spriteFps)||6)-1,1,30);if(selectedImage.playing)startSpriteMotion(selectedImage);renderKeyboardKeys()}),
        toolKey('FPS +',`${Math.max(1,Number(selectedImage.spriteFps)||6)} fps`,()=>{selectedImage.spriteFps=clamp((Number(selectedImage.spriteFps)||6)+1,1,30);if(selectedImage.playing)startSpriteMotion(selectedImage);renderKeyboardKeys()}),
        toolKey(selectedImage.playing?'PAUSE':'PLAY','motion',()=>{if(selectedImage.playing)stopSpriteMotion(selectedImage);else if(selectedImage.committed)startSpriteMotion(selectedImage);else announce('Save the sprite first to begin world motion.');renderKeyboardKeys()})
      );
    }
    if(spriteLibraryLoading){keyboardKeys.append(toolKey('LOADING','Sprite library',()=>{},true));return}
    if(spriteLibraryError){
      if(REGION_DEFINER&&/^No registered region sprites/i.test(spriteLibraryError)){
        keyboardKeys.append(toolKey('EMPTY','No regional sprites registered yet',()=>{},true));return;
      }
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
    if(personalFolderType==='Images'){renderPersonalFolder('Images','MY IMAGES');return}
    if(!selectedImage){
      appendPlacementRoleControls();
      keyboardKeys.append(
        toolKey('UPLOAD','image',openImageUpload),
        toolKey('MY IMAGES','Personal folder',()=>openPersonalFolder('Images'))
      );return;
    }
    if(isWorldMapItem(selectedImage)){
      keyboardKeys.append(
        readoutKey('WORLD MAP','Sea Level · 100% × 100%'),
        readoutKey('BASE','full world footprint'),
        toolKey('OP −','opacity',()=>{selectedImage.opacity=clamp(selectedImage.opacity-.1,.1,1);refreshUserImage(selectedImage)}),
        toolKey('OP +','opacity',()=>{selectedImage.opacity=clamp(selectedImage.opacity+.1,.1,1);refreshUserImage(selectedImage)}),
        toolKey(selectedImage.transparent?'TRANS ✓':'TRANS','background',()=>{selectedImage.transparent=!selectedImage.transparent;refreshUserImage(selectedImage);renderKeyboardKeys()}),
        toolKey('MY IMAGES','Personal folder',()=>{deselectUserImage(false);openPersonalFolder('Images')}),
        toolKey('DELETE','world map',removeSelectedImage)
      );return;
    }
    const pos=selectedPositionSummary(selectedImage);
    keyboardKeys.append(
      readoutKey(`TIER ${pos.tier}`,pos.tierLabel),
      readoutKey(`LAYER ${pos.layer}`,'current layer'),
      readoutKey(`X ${pos.x}`,'world position'),
      readoutKey(`Y ${pos.y}`,'world position'),
      toolKey('SIZE −',`${selectedImage.size.toFixed(selectedImage.size<2?1:2)}×`,()=>adjustSelectedSize(-1),selectedImage.size<=.2),
      toolKey('SIZE +',`${selectedImage.size.toFixed(selectedImage.size<2?1:2)}×`,()=>adjustSelectedSize(1),selectedImage.size>=20),
      toolKey('↺','rotate',()=>{selectedImage.rotation-=15;refreshUserImage(selectedImage)}),
      toolKey('↻','rotate',()=>{selectedImage.rotation+=15;refreshUserImage(selectedImage)}),
      toolKey('OP −','opacity',()=>{selectedImage.opacity=clamp(selectedImage.opacity-.1,.1,1);refreshUserImage(selectedImage)}),
      toolKey('OP +','opacity',()=>{selectedImage.opacity=clamp(selectedImage.opacity+.1,.1,1);refreshUserImage(selectedImage)}),
      toolKey(selectedImage.transparent?'TRANS ✓':'TRANS','background',()=>{selectedImage.transparent=!selectedImage.transparent;refreshUserImage(selectedImage);renderKeyboardKeys()}),
      toolKey('TIER −',`T${pos.tier} · ${pos.tierLabel}`,()=>moveSelectedTier(-1),REGION_DEFINER||selectedImage.tier<=0),
      toolKey('TIER +',`T${pos.tier} · ${pos.tierLabel}`,()=>moveSelectedTier(1),REGION_DEFINER||selectedImage.tier>=TIERS.length-1),
      toolKey('LAYER −',`L${pos.layer}`,()=>moveSelectedLayer(-1),selectedImage.tier<=0&&selectedImage.layer<=0),
      toolKey('LAYER +',`L${pos.layer}`,()=>moveSelectedLayer(1),selectedImage.tier>=TIERS.length-1&&selectedImage.layer>=9),
      toolKey('MY IMAGES','Personal folder',()=>{deselectUserImage(false);openPersonalFolder('Images')}),
      toolKey('DELETE','image',removeSelectedImage)
    );return;
  }
  if(keyboardMode==='Select'){
    if(REGION_DEFINER){renderRegionSelectKeyboard();return}
    const items=selectablePlacedContent();
    keyboardKeys.append(
      toolKey('‹','previous image',()=>cyclePlacedSelection(-1),!items.length),
      toolKey('›','next image',()=>cyclePlacedSelection(1),!items.length),
      placedContentSelect(),
      toolKey('EDIT','selected content',()=>{if(!selectedImage)return;keyboardMode=selectedImage.kind==='label'?'Labels':'Image';renderKeyboardTabs();renderKeyboardKeys();announce(`${selectedImage.kind==='label'?'Label':'Image'} editing controls opened.`)},!selectedImage),
      toolKey('CLEAR','selection',()=>deselectUserImage(true),!selectedImage)
    );return;
  }
  if(keyboardMode==='Labels'){renderLabelsKeyboard();return}
  const sets={Pixels:['Select','Paint','Erase','Fill'],Litch:['Light','Shadow','Intensity','Falloff'],CAD:['Line','Shape','Measure','Snap'],Stylus:['Draw','Pressure','Erase','Sample'],Tethers:['Link','Unlink','Anchor','Trace'],Metadata:['Inspect','Identity','Provenance','Relations']};
  (sets[keyboardMode]||['Inspect']).forEach(name=>keyboardKeys.append(toolKey(name,keyboardMode.toLowerCase(),()=>setTool(name))));
}
function openKeyboard(){keyboard.hidden=false;stage.classList.add('keyboard-open');keyboardToggle.setAttribute('aria-expanded','true');keyboardToggle.setAttribute('aria-label',REGION_DEFINER?'Close Region Definer keyboard':'Close World Builder keyboard');renderKeyboardTabs();renderKeyboardKeys();if(REGION_DEFINER)updateRegionSelectionOverlay();announce(`${keyboardMode} keyboard opened over viewer. Viewer size unchanged.`)}
function closeKeyboard(){const restoreFocus=keyboard.contains(document.activeElement);keyboard.hidden=true;stage.classList.remove('keyboard-open');keyboardToggle.setAttribute('aria-expanded','false');keyboardToggle.setAttribute('aria-label',REGION_DEFINER?'Open Region Definer keyboard':'Open World Builder keyboard');if(REGION_DEFINER)updateRegionSelectionOverlay();if(restoreFocus)keyboardToggle.focus();announce('Keyboard hidden. Viewer unobstructed.')}

BASE_WORLD_ASSETS.forEach(asset=>{
  const node=planeByKey[asset.key];
  node.addEventListener('load',()=>{
    layerReady[asset.key]=true;
    if(asset.key!=='surface')void primeCollisionMask(collisionSource(node));
    if(asset.key==='surface'&&node.dataset.derivedUpscale!=='1'){
      naturalWidth=SURFACE_WORLD_PIXELS;
      naturalHeight=SURFACE_WORLD_PIXELS;
      stage.dataset.surfacePixelWidth=String(SURFACE_WORLD_PIXELS);
      stage.dataset.surfacePixelHeight=String(SURFACE_WORLD_PIXELS);
      loading.hidden=true;
      fitMap();
      if(upscaleEnabled&&!upscaleStarted){upscaleStarted=true;void applyUpscalePreference()}
      scheduleRegionEnhancement(60);
      if(!REGION_DEFINER)void restoreSavedWorldBuilder();
      else refreshRegionTierPreview();
    }else{
      if(asset.key==='surface')loading.hidden=true;
      renderState();
      if(REGION_DEFINER)refreshRegionTierPreview();
    }
  });
  node.addEventListener('error',()=>{
    layerReady[asset.key]=false;
    if(asset.key==='surface'){loading.hidden=false;loading.textContent='WORLD MAP ASSET UNAVAILABLE'}
    renderState();
    if(REGION_DEFINER)refreshRegionTierPreview();
  });
  node.src=ASSET_ROOT+asset.file;
});

if(!BASE_WORLD_ASSETS.length){
  naturalWidth=SURFACE_WORLD_PIXELS;
  naturalHeight=SURFACE_WORLD_PIXELS;
  stage.dataset.surfacePixelWidth=String(SURFACE_WORLD_PIXELS);
  stage.dataset.surfacePixelHeight=String(SURFACE_WORLD_PIXELS);
  stage.dataset.seaLevelReference='ocean';
  world.dataset.emptyWorld='true';
  // Empty worlds begin with a non-authoritative ocean reference instead of a
  // black canvas. It occupies Sea Level at 100% × 100%, remains replaceable,
  // and is intentionally not serialized as authored world content.
  world.style.background='radial-gradient(circle at 50% 42%,rgba(28,96,124,.72),rgba(2,22,34,.98) 74%)';
  if(surface){
    surface.dataset.referenceOnly='true';
    surface.alt='Sea level ocean reference';
    surface.style.objectFit='cover';
    surface.addEventListener('load',()=>{
      if(surface.dataset.referenceOnly!=='true')return;
      layerReady.surface=true;
      stage.dataset.seaLevelReference='ocean-image';
      loading.hidden=true;
      renderState();
      if(REGION_DEFINER)refreshRegionTierPreview();
    },{once:true});
    surface.addEventListener('error',()=>{
      if(surface.dataset.referenceOnly!=='true')return;
      layerReady.surface=false;
      stage.dataset.seaLevelReference='ocean-gradient';
      renderState();
    },{once:true});
    surface.src=DEFAULT_SEA_LEVEL_REFERENCE;
  }
  fitMap();
  if(!REGION_DEFINER)void restoreSavedWorldBuilder();
  if(REGION_DEFINER){
    loading.hidden=false;loading.textContent='LOADING SELECTED WORLD MAP…';
    announce('Sea Level ocean reference ready while the selected world map loads.');
  }else{
    loading.hidden=true;
    announce('Sea Level ocean reference ready. Add images or tiles above it, or replace it as the World Map.');
  }
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
  // HOME is an in-session transition back to the authenticated Shaelvien landing
  // page. Never reload /Game here: a reload re-enters the Press Start launch gate.
  const sent=REGION_DEFINER?postRegionMessage('home'):postWorldBuilderHostMessage('home');
  if(sent)return;
  try{localStorage.setItem('rist.shell.workspace.v1','hub')}catch{}
  announce('Home is waiting for the Shaelvien launcher connection. Please try again.');
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

persistentSave?.addEventListener('click',()=>{
  if(REGION_DEFINER&&(regionClaimPhase==='select'||regionClaimPhase==='crop')){createRegionDefinition();return}
  void saveWorldBuilder();
});
bindTap($('fit'),fitMap);
bindTap($('zoomIn'),()=>zoomCenter(1.22));
bindTap($('zoomOut'),()=>zoomCenter(1/1.22));
$('home').addEventListener('click',goHome);
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
imagePlacementRole?.addEventListener('change',()=>{assetPlacementRole=requestedPlacementRole(imagePlacementRole.value);syncImagePlacementRole();announce(assetPlacementRole==='world-map'?'World Map selected. This image will fill Sea Level at 100% by 100%.':'Adjustable Layer selected. This image will sit above the Sea Level world map.')});
imageBrowse.addEventListener('click',()=>imageFile.click());
imageFile.addEventListener('change',()=>{const file=imageFile.files?.[0];if(file)void placeUploadedImage(file);imageFile.value=''});
imageDropzone.addEventListener('click',event=>{if(event.target===imageDropzone)imageFile.click()});
imageDropzone.addEventListener('keydown',event=>{if(event.target===imageDropzone&&(event.key==='Enter'||event.key===' ')){event.preventDefault();imageFile.click()}});
for(const type of ['dragenter','dragover'])imageDropzone.addEventListener(type,event=>{event.preventDefault();event.stopPropagation();imageDropzone.classList.add('dragover')});
for(const type of ['dragleave','drop'])imageDropzone.addEventListener(type,event=>{event.preventDefault();event.stopPropagation();imageDropzone.classList.remove('dragover')});
imageDropzone.addEventListener('drop',event=>{const file=[...(event.dataTransfer?.files||[])].find(f=>f.type.startsWith('image/'));if(file)void placeUploadedImage(file)});
bindTap(spriteUploadClose,closeSpriteUpload);
spriteBrowse.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();spriteFile.click()}});
spriteFile.addEventListener('change',()=>{const file=spriteFile.files?.[0];if(file)void placeUploadedSprite(file);spriteFile.value=''});
spriteColumns.addEventListener('input',syncSpriteFrameCount);spriteRows.addEventListener('input',syncSpriteFrameCount);
spriteDropzone.addEventListener('click',event=>{if(event.target===spriteDropzone)spriteFile.click()});
spriteDropzone.addEventListener('keydown',event=>{if(event.target===spriteDropzone&&(event.key==='Enter'||event.key===' ')){event.preventDefault();spriteFile.click()}});
for(const type of ['dragenter','dragover'])spriteDropzone.addEventListener(type,event=>{event.preventDefault();event.stopPropagation();spriteDropzone.classList.add('dragover')});
for(const type of ['dragleave','drop'])spriteDropzone.addEventListener(type,event=>{event.preventDefault();event.stopPropagation();spriteDropzone.classList.remove('dragover')});
spriteDropzone.addEventListener('drop',event=>{const file=[...(event.dataTransfer?.files||[])].find(f=>f.type.startsWith('image/'));if(file)void placeUploadedSprite(file)});
$('keyboardClose').addEventListener('click',closeKeyboard);

stage.addEventListener('wheel',e=>{
  if(REGION_DEFINER&&regionClaimPhase==='select'&&regionSelectionEnabled)return;
  if(e.target instanceof Element&&e.target.closest('[data-ui]'))return;
  if(!e.deltaY)return;
  e.preventDefault();
  const unit=e.deltaMode===1?16:e.deltaMode===2?stage.clientHeight:1;
  zoomAt(e.clientX,e.clientY,Math.exp(-clamp(e.deltaY*unit,-240,240)*.0015));
},{passive:false});
stage.addEventListener('pointerdown',e=>{
  if(REGION_DEFINER&&regionClaimPhase==='select'&&regionSelectionEnabled)return;
  if(e.target instanceof Element&&e.target.closest('[data-ui]'))return;
  if(e.target instanceof Element&&e.target.closest('button,input,select,textarea,a[href],[contenteditable]:not([contenteditable="false"])'))return;
  if(e.pointerType==='mouse'&&e.button!==0)return;
  if(!(e.target instanceof Element&&e.target.closest('.user-image-placement')))deselectUserImage(false);
  suspendRegionEnhancement();
  if(e.pointerType==='mouse')stage.focus({preventScroll:true});
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
    const oldScale=scale,nextScale=clamp(pinchStart.scale*(d/pinchStart.distance),MIN_VIEW_SCALE,maxScale);
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
  if(!pointers.has(e.pointerId))return;
  pointers.delete(e.pointerId);
  if(!pointers.size){panStart=pinchStart=null;stage.classList.remove('dragging');scheduleRegionEnhancement(45)}
  else if(pointers.size===1){const[r]=[...pointers.values()];panStart={pointerX:r.x,pointerY:r.y,x,y};pinchStart=null}
  if(stage.hasPointerCapture?.(e.pointerId))stage.releasePointerCapture(e.pointerId);
}
stage.addEventListener('pointerup',release);
stage.addEventListener('pointercancel',release);
stage.addEventListener('lostpointercapture',event=>{release(event);endImageDrag(event)});
window.addEventListener('blur',()=>{
  for(const pointerId of [...pointers.keys()])release({pointerId});
  if(imageDrag)endImageDrag({pointerId:imageDrag.id});
});
// Observe the actual host, including its first nonzero layout, without resetting
// the user's zoom or world point under the viewport center on every resize.
function resizeViewer(){
  const rect=stage.getBoundingClientRect(),next={width:rect.width,height:rect.height};
  if(next.width<=0||next.height<=0)return;
  const camera=RistViewerInput.resizeCamera({x,y,fitX,fitY,scale},viewerSize,next);
  viewerSize=next;
  if(!camera){fitMap();return}
  ({x,y,fitX,fitY}=camera);
  applyTransform();scheduleRegionEnhancement(80);
}
const viewerResizeObserver=new ResizeObserver(resizeViewer);
viewerResizeObserver.observe(stage);
RistViewerInput.install({stage,document,
  pan:(dx,dy)=>{x+=dx;y+=dy;applyTransform()},zoom:zoomCenter,fit:fitMap,
  tiers:()=>tierToggle.click(),settings:openViewerSettings,
  upload:()=>{if(!imageUploadToggle.disabled)openImageUpload()},
  keyboard:()=>{openKeyboard();$('keyboardClose').focus()},
  modal:()=>[viewerSettingsPanel,spriteUploadPanel,imageUploadPanel].find(panel=>!panel.hidden)
});
document.addEventListener('keydown',e=>{if(e.key!=='Escape')return;if(!tierMenu.hidden){closeTierMenu();tierToggle.focus();return}if(!viewerSettingsPanel.hidden){closeViewerSettings();return}if(!spriteUploadPanel.hidden){closeSpriteUpload();return}if(!imageUploadPanel.hidden){closeImageUpload();return}if(!keyboard.hidden)closeKeyboard()});

window.ShaelvienPrototype=Object.freeze({
  world:Object.freeze({id:WORLD_ID,name:DISPLAY_WORLD_NAME,continent:CONTINENT_NAME,seed:WORLD_SEED,surfacePixels:SURFACE_WORLD_PIXELS,surfacePolicy:SURFACE_POLICY}),
  getUpscaleState:()=>({enabled:upscaleEnabled,mode:stage.dataset.upscale||'original'}),
  save:saveWorldBuilder,
  tiers:TIERS,
  baseLayers:BASE_WORLD_ASSETS,
  getViewerState:()=>({
    workspaceMode:WORKSPACE_MODE,assetScale:ASSET_SCALE,mapAuthorityScoped:MAP_AUTHORITY_SCOPED,
    viewerTier,viewerLayer,
    layerCount:BASE_LAYER_COUNT+regionWorldSourceTiles.length+userLayers.length,
    userLayers:userLayers.map(item=>({id:item.id,kind:item.kind||'image',text:item.kind==='label'?item.text:undefined,tier:item.tier,layer:item.layer,x:item.x,y:item.y,size:item.size,rotation:item.rotation,opacity:item.opacity,transparent:item.transparent,committed:!!item.committed,zoomPassed:!!item.zoomPassed})),
    keyboardOpen:!keyboard.hidden,keyboardMode,toolMode,
    tileLibrary:{loaded:tileCatalog.length,folder:tileLibraryFolder,page:tileLibraryPage,count:tileCatalog.length,error:tileLibraryError||null},
    regionDefinition:REGION_DEFINER?{
      tierIndex:currentRegionTierIndex(),
      selectedCells:[...regionSelectedCells],
      savedCount:regionCatalog.length,
      visibleWorldLayers:[...regionWorldLayerSet()].sort((a,b)=>a-b).map(layer=>layer+1)
    }:null,
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
