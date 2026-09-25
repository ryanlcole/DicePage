(() => {
'use strict';
const QUERY=new URLSearchParams(location.search);
const LIVE_WORLDBUILDER=QUERY.get('live-worldbuilder')==='1';
const WORKSPACE_MODE=String(QUERY.get('mode')||'worldbuilder').toLowerCase();
const IMMERSION_BUILDER=WORKSPACE_MODE==='immersion';
const LOCAL_DEFINER=WORKSPACE_MODE==='localdefiner';
const REGION_DEFINER=WORKSPACE_MODE==='regiondefiner'||LOCAL_DEFINER;
const REPRESENTATION_ANGLE_DEGREES=LOCAL_DEFINER?30:REGION_DEFINER?15:0;
const REGION_FLOW=String(QUERY.get('regionFlow')||'').toLowerCase();
const REQUESTED_REGION_ID=String(QUERY.get('regionId')||'');
const REQUESTED_LOCAL_ID=String(QUERY.get('localId')||'');
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
const ASSET_SCALE=LOCAL_DEFINER?'LOCAL':REGION_DEFINER?'REGION':'WORLD';
const SURFACE_WORLD_PIXELS=Math.max(2048,Math.min(32768,Math.trunc(Number(QUERY.get('surfacePixels'))||2048)));
const MIN_VIEW_SCALE=1e-6;
const ASSET_ROOT='https://d2d6rnm6fnsp89.cloudfront.net/library/terrains/standard/world/whole_maps/geonaph/';
const DEFAULT_SEA_LEVEL_REFERENCE='https://d2d6rnm6fnsp89.cloudfront.net/tilesets/world/terrain/ocean/ocean-067/tile-03-03.jpg';
const TIERS=Object.freeze([
  Object.freeze({key:'sea',label:'Sea Level',index:0,glyph:'≈'}),
  Object.freeze({key:'hills',label:'Hills / Low Clouds',index:1,glyph:'⌁'}),
  Object.freeze({key:'mountains',label:'Mountains / Weather',index:2,glyph:'▲'})
]);
const BASE_WORLD_ASSETS=Object.freeze(IS_GEONAPH_SEED&&REGION_FLOW!=='existing'?[
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
const IMAGE_ENGINE=window.ReLiCImageEngine||null;
const stage=$('stage'),world=$('world'),surface=$('surfacePlane'),highlands=$('highlandsPlane'),mountains=$('mountainPlane'),loading=$('loading'),battle=$('battleInstance'),battleText=$('battleText'),keyboard=$('viewerKeyboard'),keyboardToggle=$('keyboardToggle'),persistentSave=$('persistentSave'),regionPersistenceStatus=$('regionPersistenceStatus'),imageUploadToggle=$('imageUploadToggle'),tierToggle=$('tierToggle'),tierGlyph=$('tierGlyph'),tierMenu=$('tierMenu'),settingsToggle=$('settingsToggle'),viewerSettingsPanel=$('viewerSettingsPanel'),viewerSettingsClose=$('viewerSettingsClose'),settingsFit=$('settingsFit'),settingsResetTilt=$('settingsResetTilt'),settingsUpscale=$('settingsUpscale'),settingsUpscaleLabel=$('settingsUpscaleLabel'),settingsStartMenu=$('settingsStartMenu'),imageUploadPanel=$('imageUploadPanel'),imageUploadClose=$('imageUploadClose'),imagePlacementRole=$('imagePlacementRole'),imagePlacementHint=$('imagePlacementHint'),imagePositionGrid=$('imagePositionGrid'),imageDropzone=$('imageDropzone'),imageBrowse=$('imageBrowse'),imageFile=$('imageFile'),imageX=$('imageX'),imageY=$('imageY'),imageTier=$('imageTier'),imageLayer=$('imageLayer'),imageTransparency=$('imageTransparency'),spriteUploadPanel=$('spriteUploadPanel'),spriteUploadClose=$('spriteUploadClose'),spriteDropzone=$('spriteDropzone'),spriteBrowse=$('spriteBrowse'),spriteFile=$('spriteFile'),spriteColumns=$('spriteColumns'),spriteRows=$('spriteRows'),spriteFps=$('spriteFps'),spriteFrameCount=$('spriteFrameCount'),spriteMotionOnly=$('spriteMotionOnly'),keyboardTabs=$('keyboardTabs'),keyboardKeys=$('keyboardKeys'),live=$('live');
if(READ_ONLY){
  stage.classList.add('read-only');stage.setAttribute('aria-readonly','true');stage.dataset.access='view';
  persistentSave.disabled=true;persistentSave.title='Read-only world reference';
  imageUploadToggle.disabled=true;imageUploadToggle.title='Read-only world reference';
  const banner=document.createElement('div');banner.className='read-only-reference';banner.textContent=IMMERSION_BUILDER?'IMMERSIONBUILDER · ZOOM TRANSITION AUTHORING':'VIEW ONLY · WORLD REFERENCE';banner.setAttribute('role','status');stage.appendChild(banner);
}else if(CLAIM_ONLY){
  stage.dataset.access='claim';
  persistentSave.disabled=true;persistentSave.title='Claim requests do not directly edit the world';
  imageUploadToggle.disabled=true;imageUploadToggle.title='Wait for GM approval before building';
  const banner=document.createElement('div');banner.className='claim-request-reference';banner.textContent='CLAIM REQUEST MODE · GM APPROVAL REQUIRED';banner.setAttribute('role','status');stage.appendChild(banner);
}else stage.dataset.access='edit';
if(REGION_DEFINER){
  document.title=LOCAL_DEFINER?'Shaelvien Local Definer':'Shaelvien Region Definer';
  stage.classList.add('region-definer-mode');
  if(LOCAL_DEFINER)stage.classList.add('local-definer-mode');
  stage.dataset.workspace=LOCAL_DEFINER?'localdefiner':'regiondefiner';
  stage.dataset.mapAuthority=LOCAL_DEFINER?'local-object-anchor':'region-scoped';
  stage.dataset.representationAngle=String(REPRESENTATION_ANGLE_DEGREES);
  keyboard?.setAttribute('aria-label',LOCAL_DEFINER?'Local Definer contextual keyboard':'Region Definer contextual keyboard');
  keyboardToggle?.setAttribute('aria-label',LOCAL_DEFINER?'Open Local Definer keyboard':'Open Region Definer keyboard');
  persistentSave.title=LOCAL_DEFINER?'Local definitions are saved from selected objects':'Save authorized changes to the canonical map';
  persistentSave.setAttribute('aria-label',LOCAL_DEFINER?'Save selected Local object':'Save authorized region changes to the canonical map');
  if(LOCAL_DEFINER)persistentSave.hidden=true;
  if(LOCAL_DEFINER)imageUploadToggle.hidden=true;else imageUploadToggle?.setAttribute('aria-label','Add regional image');
  const banner=document.createElement('div');banner.className='region-mode-reference';banner.textContent=LOCAL_DEFINER?'LOCAL DEFINER · REGION → ASSET → LOCAL · 30° VIEW':'REGION DEFINER · CANONICAL MAP · 15° VIEW';banner.setAttribute('role','status');stage.appendChild(banner);
  // A new-region flow is tier choice first. Hide viewer chrome from the first JS paint
  // instead of exposing the canonical viewer while the database source hydrates.
  if(!LOCAL_DEFINER&&REGION_FLOW==='new'&&!READ_ONLY){
    stage.classList.add('region-tier-previewing');
    stage.dataset.regionEntry='tier-preview';
  }
}
const planeByKey={surface,highlands,mountains};
const CANONICAL_PLANE_KEYS=Object.freeze(['surface','highlands','mountains']);
const layerReady={surface:false,highlands:false,mountains:false};
const pointers=new Map();
let viewerSize=null;
let naturalWidth=1,naturalHeight=1,scale=1,minScale=.1,maxScale=12,x=0,y=0,fitX=0,fitY=0,panStart=null,pinchStart=null,keyboardMode=REGION_DEFINER&&REGION_FLOW==='new'?'Select':'Viewer',toolMode='Inspect',assetInteractionMode='select',tiltBaseline=null,tiltTargetX=0,tiltTargetY=0,tiltX=0,tiltY=0,tiltFrame=0,selectedImage=null,imageDrag=null,assetResizeOverlay=null,assetResizeDrag=null,viewerTier=REGION_DEFINER?'sea':'all',viewerLayer=0,upscaleStarted=false;
const userLayers=[];
let spriteChainTarget=null;
let regionEditLayer=null;
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
let localCatalog=[],localCreatePending=false,localNameDraft='',localNameAnchorId='',activeLocal=null,localAnchorItem=null,localEditLayer=null,localTierIndex=0,localLayerIndex=1,localPersistenceDbCount=null,localRegionPreview=null,localRegionPreviewPointer=null,localRegionPreviewIndex=0,localRegionSelectPending=false,localRegionEditable=false,requestedLocalOpenPending=false,localRegionSourceReady=false;
let regionGridShape='hex',regionClaimPhase=REGION_DEFINER&&REGION_FLOW==='new'?'tier-preview':'idle',regionCropPreview=false,regionClaimedRegion=null,pendingClaimedRegionId=REQUESTED_REGION_ID;
let regionWorldSourceMeta=null;
let regionClaimMaskUrl='';
const regionWorldSourceTiles=[];
const regionWorldTierImages=[];
let regionWorldSourceOcean=null;
let regionCanonicalTierImages=BASE_WORLD_ASSETS.map(asset=>ASSET_ROOT+asset.file);
let regionTierPreview=null,regionTierPreviewPointer=null;
let canonicalHydrationRevision=0;
let regionProjectionLoaded=false,regionRasterIndexMissing=false,regionTierIndex=0,regionLayerIndex=1,regionPersistenceDbCount=null;
function regionWorldLayer(item){return clamp(Math.trunc(Number(item?.worldLayer??item?.layer??0)||0),0,9)}
function regionOverlayTier(item){return Math.max(0,Math.trunc(Number(item?.regionTier??0)||0))}
function regionOverlayLayer(item){return clamp(Math.trunc(Number(item?.regionLayer??1)||1),1,9)}
function nestedVerticalAddress(item={}){
  return{
    worldTier:Math.max(0,Math.trunc(Number(item?.worldTier??item?.tier??regionClaimedRegion?.tierIndex??0)||0)),
    worldLayer:regionWorldLayer(item),
    regionTier:regionOverlayTier(item),
    regionLayer:regionOverlayLayer(item),
    localTier:Math.max(0,Math.trunc(Number(item?.localTier??0)||0)),
    localLayer:clamp(Math.trunc(Number(item?.localLayer??0)||0),0,9),
    instanceTier:Math.max(0,Math.trunc(Number(item?.instanceTier??0)||0)),
    instanceLayer:clamp(Math.trunc(Number(item?.instanceLayer??0)||0),0,9)
  };
}
function regionZ100(worldLayer,regionLayer){
  return clamp(Math.trunc(Number(worldLayer)||0),0,9)*100+clamp(Math.trunc(Number(regionLayer)||1),1,9);
}
function regionZLabel(itemOrWorldLayer,overlayLayer){
  const z=typeof itemOrWorldLayer==='object'
    ?regionZ100(regionWorldLayer(itemOrWorldLayer),regionOverlayLayer(itemOrWorldLayer))
    :regionZ100(itemOrWorldLayer,overlayLayer);
  return (z/100).toFixed(2);
}
function applyRegionAddress(item,worldLayer=viewerLayer,overlayLayer=regionLayerIndex){
  if(!REGION_DEFINER||!item?.regionOverlay)return item;
  const parentTier=clamp(Math.trunc(Number(regionClaimedRegion?.tierIndex)||0),0,TIERS.length-1);
  item.tier=parentTier;
  item.worldTier=parentTier;
  item.worldLayer=clamp(Math.trunc(Number(item.worldLayer??worldLayer)||0),0,9);
  item.layer=item.worldLayer;
  item.regionTier=Math.max(0,Math.trunc(Number(item.regionTier??regionTierIndex)||0));
  item.regionLayer=clamp(Math.trunc(Number(item.regionLayer??overlayLayer)||1),1,9);
  item.localTier=Math.max(0,Math.trunc(Number(item.localTier??0)||0));
  item.localLayer=clamp(Math.trunc(Number(item.localLayer??0)||0),0,9);
  item.instanceTier=Math.max(0,Math.trunc(Number(item.instanceTier??0)||0));
  item.instanceLayer=clamp(Math.trunc(Number(item.instanceLayer??0)||0),0,9);
  item.z100=regionZ100(item.worldLayer,item.regionLayer);
  item.parentTierIndex=parentTier;
  item.parallaxMode='anchored';
  item.anchorTier=parentTier;
  return item;
}
function localIsOpen(){return !!(LOCAL_DEFINER&&activeLocal?.id)}
function maybeOpenRequestedLocal(){
  if(!LOCAL_DEFINER||!REQUESTED_LOCAL_ID||localIsOpen()||requestedLocalOpenPending||!localRegionSourceReady)return;
  const local=localCatalog.find(item=>String(item?.id||'')===REQUESTED_LOCAL_ID);
  if(!local)return;
  requestedLocalOpenPending=true;
  if(!postRegionMessage('open-local',{localId:REQUESTED_LOCAL_ID})){
    requestedLocalOpenPending=false;
    announce('Saved Local could not be opened because the Local database bridge is unavailable.');
  }
}
function activeLocalMapId(){return String(activeLocal?.id||'').trim()}
function localAnchorBounds(local=activeLocal){
  if(!local)return null;
  const width=clamp(Number(local.width)||.0001,.0001,1),height=clamp(Number(local.height)||.0001,.0001,1);
  const cx=clamp(Number(local.x)||0,0,1),cy=clamp(Number(local.y)||0,0,1);
  return{
    minX:clamp(cx-width/2,0,1),maxX:clamp(cx+width/2,0,1),
    minY:clamp(cy-height/2,0,1),maxY:clamp(cy+height/2,0,1),
    width,height,cx,cy
  };
}
function localPointToWorld(x,y,local=activeLocal){
  const bounds=localAnchorBounds(local);
  if(!bounds)return{x:clamp(Number(x)||0,0,1),y:clamp(Number(y)||0,0,1)};
  return{
    x:clamp(bounds.minX+clamp(Number(x)||0,0,1)*bounds.width,0,1),
    y:clamp(bounds.minY+clamp(Number(y)||0,0,1)*bounds.height,0,1)
  };
}
function constrainLocalPoint(x,y){
  const bounds=localAnchorBounds();
  if(!bounds)return constrainRegionPoint(x,y);
  return{
    x:clamp(Number(x)||0,bounds.minX,bounds.maxX),
    y:clamp(Number(y)||0,bounds.minY,bounds.maxY)
  };
}
function applyLocalAddress(item,tier=localTierIndex,layer=localLayerIndex){
  if(!LOCAL_DEFINER||!localIsOpen()||!item)return item;
  item.regionOverlay=true;
  item.localOverlay=true;
  item.regionId=String(activeLocal.regionId||activeRegionMapId());
  item.localId=activeLocalMapId();
  item.tier=clamp(Math.trunc(Number(activeLocal.worldTier??activeLocal.tier)||0),0,TIERS.length-1);
  item.worldTier=item.tier;
  item.worldLayer=clamp(Math.trunc(Number(activeLocal.worldLayer??activeLocal.layer)||0),0,9);
  item.layer=item.worldLayer;
  item.regionTier=Math.max(0,Math.trunc(Number(activeLocal.regionTier)||0));
  item.regionLayer=clamp(Math.trunc(Number(activeLocal.regionLayer)||1),1,9);
  item.localTier=Math.max(0,Math.trunc(Number(item.localTier??tier)||0));
  item.localLayer=clamp(Math.trunc(Number(item.localLayer??layer)||1),1,9);
  item.instanceTier=Math.max(0,Math.trunc(Number(item.instanceTier)||0));
  item.instanceLayer=clamp(Math.trunc(Number(item.instanceLayer)||0),0,9);
  item.z100=regionZ100(item.worldLayer,item.regionLayer);
  item.parentTierIndex=item.worldTier;
  item.parallaxMode='anchored';
  item.anchorTier=item.worldTier;
  return item;
}
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
const localMapSaveWaiters=new Map();
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
const alphaComponentCache=new Map();
const COLLISION_MASK_MAX=512;

function stableAssetAspect(item){
  if(item?.kind==='sprite'){
    const width=Number(item.spriteCropWidth)||((Number(item.spriteSourceWidth)||0)/Math.max(1,Number(item.spriteColumns)||1));
    const height=Number(item.spriteCropHeight)||((Number(item.spriteSourceHeight)||0)/Math.max(1,Number(item.spriteRows)||1));
    if(width>0&&height>0)return width/height;
  }
  const node=item?.node;
  if(node?.naturalWidth>0&&node?.naturalHeight>0)return node.naturalWidth/node.naturalHeight;
  return 1;
}
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
  const baseW=naturalWidth*.12,aspect=1/Math.max(stableAssetAspect(item),.00001),baseH=baseW*aspect;
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
  const baseW=naturalWidth*.12,aspect=1/Math.max(stableAssetAspect(item),.00001),baseH=baseW*aspect,size=Math.max(Number(item.size)||1,.00001);
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
function activeRegionOverlayItems(regionId=activeRegionMapId()){
  const id=String(regionId||'');
  return userLayers.filter(item=>item?.regionOverlay&&String(item.regionId||'')===id);
}
function refreshRegionPersistenceStatus(dbCount=regionPersistenceDbCount){
  if(!REGION_DEFINER||!regionPersistenceStatus)return;
  if(!regionDeedIsComplete()&&!REQUESTED_REGION_ID){
    regionPersistenceStatus.hidden=true;return;
  }
  const items=activeRegionOverlayItems();
  const pending=items.filter(item=>item.personalAssetKey&&(
    item.node?.dataset.assetPending==='true'||(!item.renderedSrc&&!item.node?.currentSrc)
  )).length;
  const unsaved=items.filter(item=>item.committed===false).length;
  const hidden=items.filter(item=>{
    if(item.personalAssetKey&&(item.node?.dataset.assetPending==='true'||(!item.renderedSrc&&!item.node?.currentSrc)))return false;
    return !!item.node&&(item.node.hidden||item.node.style.visibility==='hidden'||Number(item.renderOpacity)<=.001);
  }).length;
  const visible=Math.max(0,items.length-pending-hidden);
  const db=dbCount!==null&&dbCount!==undefined&&Number.isFinite(Number(dbCount))
    ?Math.max(0,Math.trunc(Number(dbCount)))
    :'?';
  regionPersistenceStatus.hidden=false;
  regionPersistenceStatus.classList.remove('ok','waiting','hidden-assets','error');
  let text=`DB ${db} · VISIBLE ${visible}`;
  if(pending){text+=` · MY IMAGES WAITING ${pending}`;regionPersistenceStatus.classList.add('waiting')}
  if(hidden){text+=` · HIDDEN ${hidden}`;regionPersistenceStatus.classList.add('hidden-assets')}
  if(unsaved)text+=` · UNSAVED ${unsaved}`;
  if(!pending&&!hidden&&unsaved===0&&db!=='?')regionPersistenceStatus.classList.add('ok');
  regionPersistenceStatus.textContent=text;
  stage.dataset.regionDbCount=String(db);
  stage.dataset.regionVisibleCount=String(visible);
  stage.dataset.regionPendingAssetCount=String(pending);
  stage.dataset.regionHiddenAssetCount=String(hidden);
  stage.dataset.regionUnsavedCount=String(unsaved);
}
function ensureActiveRegionOverlaysShown(regionId=activeRegionMapId()){
  if(!REGION_DEFINER||!regionDeedIsComplete())return;
  const id=String(regionId||'');
  const layer=ensureRegionEditLayer();
  layer.hidden=false;
  for(const item of activeRegionOverlayItems(id)){
    if(item.node)item.node.hidden=false;
  }
}
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
    const expectedIds=userLayers.map(item=>String(item?.id||'')).filter(Boolean);
    regionMapSaveWaiters.set(requestId,{resolve,reject,timeout,expectedIds,regionId,expectedCount:userLayers.length});
    if(!postRegionMessage('save-map-region',{requestId,regionId,userLayers})){
      clearTimeout(timeout);regionMapSaveWaiters.delete(requestId);
      reject(new Error('Region map database bridge is unavailable.'));
    }
  });
}
function saveLocalMapToDatabase(userLayers){
  if(!LOCAL_DEFINER||window.parent===window)return Promise.resolve(false);
  const localId=activeLocalMapId();
  if(!localId)return Promise.reject(new Error('Select or create a Local before saving Local content.'));
  const requestId=crypto.randomUUID?.()||('local-map-'+Date.now()+'-'+Math.random().toString(16).slice(2));
  return new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>{
      localMapSaveWaiters.delete(requestId);
      reject(new Error('Local map save timed out.'));
    },12000);
    const expectedIds=userLayers.map(item=>String(item?.id||'')).filter(Boolean);
    localMapSaveWaiters.set(requestId,{resolve,reject,timeout,expectedIds,localId,expectedCount:userLayers.length});
    if(!postRegionMessage('save-map-local',{requestId,localId,userLayers})){
      clearTimeout(timeout);localMapSaveWaiters.delete(requestId);
      reject(new Error('Local map database bridge is unavailable.'));
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
function itemParallaxMode(item){
  if(REGION_DEFINER)return'anchored';
  return item?.parallaxMode==='anchored'||item?.parallaxMode==='tier'?item.parallaxMode:'tier';
}
function restoredParallaxMode(raw,regionOverlay){
  return raw?.parallaxMode==='anchored'||raw?.parallaxMode==='tier'
    ?raw.parallaxMode
    :(regionOverlay?'anchored':'tier');
}
function itemAnchorTier(item){
  return clamp(Math.trunc(Number(item?.anchorTier??item?.tier)||0),0,TIERS.length-1);
}
function localSaveCandidates(){
  const localId=activeLocalMapId();
  if(!LOCAL_DEFINER||!localId)return[];
  return userLayers.filter(item=>{
    if(!item||item.sourceLocked||!item.localOverlay||!item.node?.isConnected)return false;
    if(String(item.localId||'')!==localId)return false;
    if(localEditLayer&&item.node.parentElement!==localEditLayer)return false;
    item.regionId=String(activeLocal?.regionId||activeRegionMapId());
    item.localId=localId;
    return true;
  });
}
function regionSaveCandidates(){
  if(!REGION_DEFINER)return userLayers;
  if(LOCAL_DEFINER)return localSaveCandidates();
  const regionId=activeRegionMapId();
  if(!regionId)return[];
  // The active edit layer is the UI truth for this deed. Normalize the region
  // identity before filtering so a stale/blank item.regionId cannot make a
  // visible authored object disappear from the save payload.
  return userLayers.filter(item=>{
    if(!item||item.sourceLocked||!item.regionOverlay||item.localOverlay||!item.node?.isConnected)return false;
    if(regionEditLayer&&item.node.parentElement!==regionEditLayer)return false;
    item.regionId=regionId;
    return true;
  });
}
function assetAuthorityResourceId(item){
  if(!item)return'';
  const existing=String(item.authorityResourceId||'').trim();
  if(existing)return existing;
  const id=String(item.id||crypto.randomUUID?.()||Date.now()).trim();
  item.id=id;
  item.authorityResourceId=`asset:${id}`;
  return item.authorityResourceId;
}
function serializableUserLayer(item){
  if(item?.kind==='label'){
    return{
      id:item.id,authorityResourceId:assetAuthorityResourceId(item),regionId:String(item.regionId||''),localId:String(item.localId||''),localOverlay:!!item.localOverlay,name:item.name||item.text||'Label',kind:'label',text:String(item.text||'').slice(0,120),
      x:clamp(Number(item.x)||0,0,1),y:clamp(Number(item.y)||0,0,1),
      tier:clamp(Math.trunc(Number(item.tier)||0),0,TIERS.length-1),
      layer:clamp(Math.trunc(Number(item.layer)||0),0,9),
      worldTier:REGION_DEFINER?nestedVerticalAddress(item).worldTier:undefined,worldLayer:REGION_DEFINER?nestedVerticalAddress(item).worldLayer:undefined,
      regionTier:REGION_DEFINER?nestedVerticalAddress(item).regionTier:undefined,regionLayer:REGION_DEFINER?nestedVerticalAddress(item).regionLayer:undefined,
      localTier:REGION_DEFINER?nestedVerticalAddress(item).localTier:undefined,localLayer:REGION_DEFINER?nestedVerticalAddress(item).localLayer:undefined,
      instanceTier:REGION_DEFINER?nestedVerticalAddress(item).instanceTier:undefined,instanceLayer:REGION_DEFINER?nestedVerticalAddress(item).instanceLayer:undefined,
      z100:REGION_DEFINER?regionZ100(regionWorldLayer(item),regionOverlayLayer(item)):undefined,parallaxMode:itemParallaxMode(item),anchorTier:itemAnchorTier(item),rotation:Number(item.rotation)||0,opacity:clamp(Number(item.opacity)||1,.01,1),
      fontSize:clamp(Number(item.fontSize)||48,12,180),bold:!!item.bold,italic:!!item.italic,color:String(item.color||LABEL_COLORS[0]),
      textAlign:['left','center','right'].includes(item.textAlign)?item.textAlign:'center',letterSpacing:clamp(Number(item.letterSpacing)||0,-2,12),
      plate:!!item.plate,offsetX:clamp(Number(item.offsetX)||0,-400,400),offsetY:clamp(Number(item.offsetY)||0,-400,400),positionLocked:!!item.positionLocked,stackPin:item.stackPin==='front'?'front':'',committed:true
    };
  }
  return{
    id:item.id,authorityResourceId:assetAuthorityResourceId(item),regionId:String(item.regionId||''),localId:String(item.localId||''),localOverlay:!!item.localOverlay,assetId:item.assetId||null,personalAssetKey:item.personalAssetKey||null,name:item.name||'',libraryTile:!!item.libraryTile,kind:item.kind||'image',
    placementRole:isWorldMapItem(item)?'world-map':'layer',fullWorld:isWorldMapItem(item),
    // Personal-library URLs are short-lived capabilities. Persist only the stable
    // asset identity; reload resolves a fresh URL after authenticated storage is ready.
    originalSrc:item.personalAssetKey?'':(item.originalSrc||''),transparentSrc:item.personalAssetKey?'':(item.transparentSrc||''),transparent:!!item.transparent,alphaCrop:normalizeAlphaCrop(item.alphaCrop),alphaComponentSeed:normalizeAlphaSeed(item.alphaComponentSeed),linkGroupId:String(item.linkGroupId||''),linkGroupIndex:Number.isFinite(Number(item.linkGroupIndex))?Math.trunc(Number(item.linkGroupIndex)):null,linkGroupCount:Number.isFinite(Number(item.linkGroupCount))?Math.trunc(Number(item.linkGroupCount)):null,
    spriteSheetSrc:item.personalAssetKey?null:(item.spriteSheetSrc||null),spriteColumns:item.spriteColumns||null,spriteRows:item.spriteRows||null,
    spriteFrameCount:item.spriteFrameCount||null,spriteFps:item.spriteFps||null,spriteSourceWidth:item.spriteSourceWidth||null,
    spriteSourceHeight:item.spriteSourceHeight||null,spriteCropX:item.spriteCropX||0,spriteCropY:item.spriteCropY||0,
    spriteCropWidth:item.spriteCropWidth||null,spriteCropHeight:item.spriteCropHeight||null,spriteWhiteTransparent:item.spriteWhiteTransparent!==false,spriteMotionOnly:!!item.spriteMotionOnly,spriteChainId:item.spriteChainId||null,
    spritePages:item.kind==='sprite'&&Array.isArray(item.spritePages)?item.spritePages.map((page,index)=>({
      index,
      personalAssetKey:page.personalAssetKey||null,assetId:page.assetId||null,name:page.name||`Sprite page ${index+1}`,
      sheetSrc:page.personalAssetKey?'':String(page.sheetSrc||''),
      columns:page.columns||item.spriteColumns||1,rows:page.rows||item.spriteRows||1,frameCount:page.frameCount||1,
      sourceWidth:page.sourceWidth||0,sourceHeight:page.sourceHeight||0,cropX:page.cropX||0,cropY:page.cropY||0,
      cropWidth:page.cropWidth||0,cropHeight:page.cropHeight||0,whiteTransparent:page.whiteTransparent!==false
    })):null,
    x:clamp(Number(item.x)||0,0,1),y:clamp(Number(item.y)||0,0,1),
    tier:clamp(Math.trunc(Number(item.tier)||0),0,TIERS.length-1),
    layer:clamp(Math.trunc(Number(item.layer)||0),0,9),
    worldTier:REGION_DEFINER?nestedVerticalAddress(item).worldTier:undefined,worldLayer:REGION_DEFINER?nestedVerticalAddress(item).worldLayer:undefined,
    regionTier:REGION_DEFINER?nestedVerticalAddress(item).regionTier:undefined,regionLayer:REGION_DEFINER?nestedVerticalAddress(item).regionLayer:undefined,
    localTier:REGION_DEFINER?nestedVerticalAddress(item).localTier:undefined,localLayer:REGION_DEFINER?nestedVerticalAddress(item).localLayer:undefined,
    instanceTier:REGION_DEFINER?nestedVerticalAddress(item).instanceTier:undefined,instanceLayer:REGION_DEFINER?nestedVerticalAddress(item).instanceLayer:undefined,
    z100:REGION_DEFINER?regionZ100(regionWorldLayer(item),regionOverlayLayer(item)):undefined,parallaxMode:itemParallaxMode(item),anchorTier:itemAnchorTier(item),size:clamp(Number(item.size)||1,.05,20),
    rotation:Number(item.rotation)||0,opacity:clamp(Number(item.opacity)||1,.01,1),positionLocked:!!item.positionLocked,stackPin:item.stackPin==='front'?'front':'',committed:true
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
    const authoredRegionLayers=REGION_DEFINER
      ? userLayers.filter(item=>item&&!item.sourceLocked&&item.regionOverlay&&(!LOCAL_DEFINER||item.localOverlay)&&item.node?.isConnected)
      : [];
    const editableLayers=REGION_DEFINER?regionSaveCandidates():userLayers;
    if(REGION_DEFINER&&authoredRegionLayers.length>0&&editableLayers.length===0){
      throw new Error(`${LOCAL_DEFINER?'Local':'Region'} save payload was empty while ${authoredRegionLayers.length} authored object${authoredRegionLayers.length===1?' is':'s are'} still on the map.`);
    }
    const serializedLayers=editableLayers.map(serializableUserLayer);
    const state=REGION_DEFINER?null:worldBuilderSourceState(editableLayers);
    if(LOCAL_DEFINER){
      const verification=await saveLocalMapToDatabase(serializedLayers);
      if(!verification?.verified)throw new Error('Local save could not be verified after writing.');
      localPersistenceDbCount=verification.persistedIds.length;
    }else if(REGION_DEFINER){
      const verification=await saveRegionMapToDatabase(serializedLayers);
      if(!verification?.verified)throw new Error('Region save could not be verified after writing.');
      regionPersistenceDbCount=verification.persistedIds.length;
    }else{
      if(LIVE_WORLDBUILDER&&window.parent!==window)await saveWorldSourceToDatabase(state);
      await writeSavedWorldBuilder(state,WORLD_SOURCE_SAVE_KEY);
    }
    for(const item of editableLayers){
      item.committed=true;refreshUserImage(item);
      if(item.kind==='sprite'&&Array.isArray(item.frameSources)&&item.frameSources.length>1)startSpriteMotion(item);
    }
    updateLayerOrder();applyParallax();
    if(REGION_DEFINER){ensureActiveRegionOverlaysShown();refreshRegionPersistenceStatus()}
    deselectUserImage(false);
    persistentSave.classList.add('saved');
    setTimeout(()=>persistentSave?.classList.remove('saved'),900);
    announce(REGION_DEFINER
      ? `Saved ${serializedLayers.length} regional overlay${serializedLayers.length===1?'':'s'} on locked World Tier ${Number(regionClaimedRegion?.tierIndex||0)+1}.`
      : `World Builder saved. ${serializedLayers.length} placed item${serializedLayers.length===1?'':'s'} committed. Use Select or the matching keyboard to edit saved content.`);
    return true;
  }catch(error){
    if(REGION_DEFINER&&regionPersistenceStatus){
      regionPersistenceStatus.hidden=false;
      regionPersistenceStatus.classList.remove('ok','waiting','hidden-assets');
      regionPersistenceStatus.classList.add('error');
      regionPersistenceStatus.textContent='SAVE FAILED · '+String(error?.message||error||'unknown error');
    }
    announce(`Save failed: ${String(error?.message||error||'unknown error')}`);
    return false;
  }finally{
    persistentSave.disabled=false;persistentSave.classList.remove('saving');
  }
}
async function attachRestoredLayer(raw,options={}){
  const sourceLocked=!!options.sourceLocked,regionOverlay=!!options.regionOverlay,localOverlay=!!options.localOverlay,canonicalSource=!!options.canonicalSource;
  const restoredLocalId=String(options.localId||raw?.localId||'');
  const kind=String(raw?.kind||'image').toLowerCase();
  const personalAssetKey=String(raw?.personalAssetKey||'').trim();
  const savedPersonalFallback=String(raw?.originalSrc||raw?.transparentSrc||raw?.spriteSheetSrc||'');
  const freshPersonalSrc=personalAssetKey
    ? await resolvePersonalAssetSource(personalAssetKey,savedPersonalFallback)
    : '';
  if(kind==='label'){
    const item={
      id:String(raw.id||`label:${crypto.randomUUID?.()||Date.now()}`),authorityResourceId:String(raw.authorityResourceId||''),regionId:String(raw.regionId||''),localId:restoredLocalId,localOverlay:localOverlay||!!raw.localOverlay,kind:'label',name:String(raw.name||raw.text||'Label'),text:String(raw.text||raw.name||'Label').slice(0,120),sourceLocked,regionOverlay,canonicalSource,
      x:clamp(Number(raw.x)||0,0,1),y:clamp(Number(raw.y)||0,0,1),tier:clamp(Math.trunc(Number(raw.tier)||0),0,TIERS.length-1),
      layer:clamp(Math.trunc(Number(raw.layer)||0),0,9),
      worldTier:REGION_DEFINER?Math.max(0,Math.trunc(Number(raw.worldTier??raw.tier)||0)):undefined,
      worldLayer:REGION_DEFINER?clamp(Math.trunc(Number(raw.worldLayer??raw.layer)||0),0,9):undefined,
      regionTier:REGION_DEFINER?Math.max(0,Math.trunc(Number(raw.regionTier)||0)):undefined,
      regionLayer:REGION_DEFINER?clamp(Math.trunc(Number(raw.regionLayer)||1),1,9):undefined,
      localTier:REGION_DEFINER?Math.max(0,Math.trunc(Number(raw.localTier)||0)):undefined,
      localLayer:REGION_DEFINER?clamp(Math.trunc(Number(raw.localLayer)||0),0,9):undefined,
      instanceTier:REGION_DEFINER?Math.max(0,Math.trunc(Number(raw.instanceTier)||0)):undefined,
      instanceLayer:REGION_DEFINER?clamp(Math.trunc(Number(raw.instanceLayer)||0),0,9):undefined,
      z100:REGION_DEFINER?Math.trunc(Number(raw.z100)||0):undefined,rotation:Number(raw.rotation)||0,opacity:clamp(Number(raw.opacity)||1,.01,1),
      fontSize:clamp(Number(raw.fontSize)||48,12,180),bold:!!raw.bold,italic:!!raw.italic,color:String(raw.color||LABEL_COLORS[0]),
      textAlign:['left','center','right'].includes(raw.textAlign)?raw.textAlign:'center',letterSpacing:clamp(Number(raw.letterSpacing)||0,-2,12),
      plate:!!raw.plate,offsetX:clamp(Number(raw.offsetX)||0,-400,400),offsetY:clamp(Number(raw.offsetY)||0,-400,400),positionLocked:!!raw.positionLocked,stackPin:raw.stackPin==='front'?'front':'',
      parallaxMode:restoredParallaxMode(raw,regionOverlay),anchorTier:clamp(Math.trunc(Number(raw.anchorTier??raw.tier)||0),0,TIERS.length-1),
      committed:raw.committed!==false,renderOpacity:1,parallaxX:0,parallaxY:0,node:null
    };
    const node=document.createElement('div');node.className='user-image-placement user-label-placement';node.setAttribute('role','text');node.setAttribute('aria-label',`World label: ${item.text}`);item.node=node;
    node.addEventListener('pointerdown',event=>beginImageDrag(event,item));node.addEventListener('pointermove',moveImageDrag);node.addEventListener('pointerup',endImageDrag);node.addEventListener('pointercancel',endImageDrag);
    assetAuthorityResourceId(item);assetAuthorityResourceId(item);userLayers.push(item);mountUserPlacement(item);refreshUserLabel(item);return item;
  }
  const isSprite=kind==='sprite';
  const rawSpritePages=isSprite&&Array.isArray(raw?.spritePages)?raw.spritePages:[];
  if(!freshPersonalSrc&&!raw?.originalSrc&&!raw?.spriteSheetSrc&&!personalAssetKey&&!rawSpritePages.length)return null;
  let frameSources=[],resolvedSpritePages=[];
  if(isSprite){
    try{
      if(rawSpritePages.length){
        for(let index=0;index<rawSpritePages.length;index++){
          const pageRaw=rawSpritePages[index]||{};
          const key=String(pageRaw.personalAssetKey||'').trim();
          const fallback=String(pageRaw.sheetSrc||'');
          const sheetSrc=key?await resolvePersonalAssetSource(key,fallback):fallback;
          if(!sheetSrc)continue;
          resolvedSpritePages.push(normalizedSpritePage({...pageRaw,sheetSrc,personalAssetKey:key||null},index));
        }
      }else{
        const sheet=String(freshPersonalSrc||raw.spriteSheetSrc||raw.originalSrc||'');
        if(sheet)resolvedSpritePages=[normalizedSpritePage({
          name:raw.name||'Sprite page 1',sheetSrc:sheet,personalAssetKey:personalAssetKey||null,assetId:raw.assetId||null,
          columns:raw.spriteColumns||1,rows:raw.spriteRows||1,frameCount:raw.spriteFrameCount||1,
          sourceWidth:raw.spriteSourceWidth||0,sourceHeight:raw.spriteSourceHeight||0,
          cropX:raw.spriteCropX||0,cropY:raw.spriteCropY||0,cropWidth:raw.spriteCropWidth||0,cropHeight:raw.spriteCropHeight||0,
          whiteTransparent:raw.spriteWhiteTransparent!==false
        },0)];
      }
      frameSources=await extractSpriteChainFrames(resolvedSpritePages,{motionOnly:raw.spriteMotionOnly===true});
    }catch{
      const fallback=String(raw.originalSrc||freshPersonalSrc||raw.spriteSheetSrc||'');
      if(fallback)frameSources=[fallback];
    }
  }
  const firstPage=resolvedSpritePages[0]||null;
  const first=isSprite?(frameSources[0]||String(firstPage?.sheetSrc||freshPersonalSrc||raw.originalSrc||raw.spriteSheetSrc||'')):String(freshPersonalSrc||raw.originalSrc||'');
  const restoredTransparentSrc=!isSprite&&first
    ?await preparedImageSource(first,{transparent:!!raw.transparent,alphaCrop:raw.alphaCrop,alphaComponentSeed:raw.alphaComponentSeed}).catch(()=>String(raw.transparentSrc||first))
    :first;
  const item={
    id:String(raw.id||crypto.randomUUID?.()||Date.now()),authorityResourceId:String(raw.authorityResourceId||''),regionId:String(raw.regionId||''),localId:restoredLocalId,localOverlay:localOverlay||!!raw.localOverlay,assetId:raw.assetId||null,personalAssetKey:raw.personalAssetKey||null,name:String(raw.name||''),libraryTile:!!raw.libraryTile,kind:isSprite?'sprite':'image',sourceLocked,regionOverlay,canonicalSource,
    placementRole:storedPlacementRole(raw),fullWorld:storedPlacementRole(raw)==='world-map',
    originalSrc:first,transparentSrc:isSprite?String(first||freshPersonalSrc||raw.transparentSrc||''):String(restoredTransparentSrc||first||raw.transparentSrc||''),transparent:isSprite?true:!!raw.transparent,
    alphaCrop:isSprite?null:normalizeAlphaCrop(raw.alphaCrop),alphaComponentSeed:isSprite?null:normalizeAlphaSeed(raw.alphaComponentSeed),
    linkGroupId:String(raw.linkGroupId||''),linkGroupIndex:Number.isFinite(Number(raw.linkGroupIndex))?Math.trunc(Number(raw.linkGroupIndex)):null,linkGroupCount:Number.isFinite(Number(raw.linkGroupCount))?Math.trunc(Number(raw.linkGroupCount)):null,
    spritePages:isSprite?resolvedSpritePages:null,
    spriteSheetSrc:isSprite?String(firstPage?.sheetSrc||freshPersonalSrc||raw.spriteSheetSrc||raw.originalSrc||''):null,
    spriteColumns:isSprite?(Number(firstPage?.columns)||Number(raw.spriteColumns)||1):null,spriteRows:isSprite?(Number(firstPage?.rows)||Number(raw.spriteRows)||1):null,
    spriteFrameCount:isSprite?(frameSources.length||Number(raw.spriteFrameCount)||1):null,spriteFps:isSprite?clamp(Number(raw.spriteFps)||6,1,60):null,
    spriteSourceWidth:isSprite?(Number(firstPage?.sourceWidth)||Number(raw.spriteSourceWidth)||null):null,spriteSourceHeight:isSprite?(Number(firstPage?.sourceHeight)||Number(raw.spriteSourceHeight)||null):null,
    spriteCropX:isSprite?(Number(firstPage?.cropX)||Number(raw.spriteCropX)||0):0,spriteCropY:isSprite?(Number(firstPage?.cropY)||Number(raw.spriteCropY)||0):0,
    spriteCropWidth:isSprite?(Number(firstPage?.cropWidth)||Number(raw.spriteCropWidth)||null):null,spriteCropHeight:isSprite?(Number(firstPage?.cropHeight)||Number(raw.spriteCropHeight)||null):null,
    spriteWhiteTransparent:isSprite?(firstPage?firstPage.whiteTransparent!==false:raw.spriteWhiteTransparent!==false):raw.spriteWhiteTransparent!==false,spriteMotionOnly:raw.spriteMotionOnly===true,spriteChainId:String(raw.spriteChainId||''),
    frameSources,currentFrame:0,playing:false,
    x:clamp(Number(raw.x)||0,0,1),y:clamp(Number(raw.y)||0,0,1),tier:clamp(Math.trunc(Number(raw.tier)||0),0,TIERS.length-1),
    layer:clamp(Math.trunc(Number(raw.layer)||0),0,9),
    worldTier:REGION_DEFINER?Math.max(0,Math.trunc(Number(raw.worldTier??raw.tier)||0)):undefined,
    worldLayer:REGION_DEFINER?clamp(Math.trunc(Number(raw.worldLayer??raw.layer)||0),0,9):undefined,
    regionTier:REGION_DEFINER?Math.max(0,Math.trunc(Number(raw.regionTier)||0)):undefined,
    regionLayer:REGION_DEFINER?clamp(Math.trunc(Number(raw.regionLayer)||1),1,9):undefined,
    localTier:REGION_DEFINER?Math.max(0,Math.trunc(Number(raw.localTier)||0)):undefined,
    localLayer:REGION_DEFINER?clamp(Math.trunc(Number(raw.localLayer)||0),0,9):undefined,
    instanceTier:REGION_DEFINER?Math.max(0,Math.trunc(Number(raw.instanceTier)||0)):undefined,
    instanceLayer:REGION_DEFINER?clamp(Math.trunc(Number(raw.instanceLayer)||0),0,9):undefined,
    z100:REGION_DEFINER?Math.trunc(Number(raw.z100)||0):undefined,size:clamp(Number(raw.size)||1,.05,20),rotation:Number(raw.rotation)||0,
    opacity:clamp(Number(raw.opacity)||1,.01,1),positionLocked:!!raw.positionLocked,stackPin:raw.stackPin==='front'?'front':'',parallaxMode:restoredParallaxMode(raw,regionOverlay),anchorTier:clamp(Math.trunc(Number(raw.anchorTier??raw.tier)||0),0,TIERS.length-1),committed:raw.committed!==false,renderOpacity:1,zoomPassed:false,zoomPassScale:null,node:null
  };
  const node=document.createElement('img');node.className=`user-image-placement${item.libraryTile?' library-tile-placement':''}${isSprite?' sprite-placement':''}${isWorldMapItem(item)?' full-world-placement':''}`;node.alt=item.name||(isSprite?'Placed sprite':'Placed image');node.draggable=false;item.node=node;
  node.addEventListener('pointerdown',event=>beginImageDrag(event,item));node.addEventListener('pointermove',moveImageDrag);node.addEventListener('pointerup',endImageDrag);node.addEventListener('pointercancel',endImageDrag);
  node.addEventListener('load',()=>{item.node.dataset.assetPending='false';item.node.style.visibility='';refreshUserImage(item);applyParallax();scheduleRegionEnhancement(30)},{once:true});
  node.addEventListener('error',()=>{if(item.personalAssetKey)schedulePersonalAssetHydration(item,0)});
  userLayers.push(item);mountUserPlacement(item);refreshUserImage(item);
  if(item.personalAssetKey&&!first)schedulePersonalAssetHydration(item,0);
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
function currentTierIndex(){return REGION_DEFINER&&regionDeedIsComplete()?clamp(Math.trunc(Number(regionClaimedRegion?.tierIndex)||0),0,TIERS.length-1):(viewerTier==='all'?0:tierByKey(viewerTier).index)}
function tierStackBase(tier){return 100+(clamp(Math.trunc(Number(tier)||0),0,TIERS.length-1)*100)}
function ensureRegionEditLayer(){
  if(!REGION_DEFINER)return world;
  if(regionEditLayer?.isConnected)return regionEditLayer;
  const layer=document.createElement('div');
  layer.className='region-edit-layer';
  layer.setAttribute('aria-label','Editable regional objects above locked selected world tier');
  layer.dataset.authority='region';
  layer.hidden=true;
  world.appendChild(layer);
  regionEditLayer=layer;
  return layer;
}
function ensureLocalEditLayer(){
  if(!LOCAL_DEFINER)return ensureRegionEditLayer();
  if(localEditLayer?.isConnected)return localEditLayer;
  const layer=document.createElement('div');
  layer.className='region-edit-layer local-edit-layer';
  layer.setAttribute('aria-label','Editable Local objects above locked selected Region asset');
  layer.dataset.authority='local';
  layer.hidden=true;
  world.appendChild(layer);
  localEditLayer=layer;
  return layer;
}
function mountUserPlacement(item){
  // Local content inherits the selected Region anchor's canonical X/Y space and
  // only adds Local tier/layer depth. The camera may crop/zoom; coordinates do not.
  if(LOCAL_DEFINER&&localIsOpen()&&!item.sourceLocked&&!item.canonicalSource&&!item.localAnchor){
    item.localOverlay=true;
    item.localId=activeLocalMapId();
    applyLocalAddress(item,item.localTier??localTierIndex,item.localLayer??localLayerIndex);
  }else if(REGION_DEFINER&&item.regionOverlay){
    applyRegionAddress(item,item.worldLayer??item.layer,item.regionLayer??regionLayerIndex);
  }
  if(!item.parallaxMode)item.parallaxMode='anchored';
  if(item.anchorTier==null)item.anchorTier=item.tier;
  const parent=item.localOverlay?ensureLocalEditLayer():(REGION_DEFINER&&item.regionOverlay?ensureRegionEditLayer():world);
  parent.appendChild(item.node);
}
function syncRegionEditLayer(){
  if(!REGION_DEFINER)return;
  const layer=ensureRegionEditLayer(),deed=regionClaimedRegion;
  const parentTier=clamp(Math.trunc(Number(deed?.tierIndex)||0),0,TIERS.length-1);
  const active=regionDeedIsComplete();
  layer.dataset.regionId=String(deed?.id||'');
  layer.dataset.tier=String(parentTier);
  layer.dataset.worldZ=String(viewerLayer);
  layer.dataset.regionTier=String(regionTierIndex);
  layer.dataset.regionLayer=String(regionLayerIndex);
  layer.style.zIndex='';
  layer.hidden=!active;
  const localAnchorId=LOCAL_DEFINER&&localIsOpen()?String(activeLocal?.anchorObjectId||''):'';
  for(const item of userLayers){
    if(!item.regionOverlay||!item.node)continue;
    if(LOCAL_DEFINER&&localIsOpen()){
      if(item.localOverlay)continue;
      item.node.hidden=!active||String(item.regionId||'')!==String(deed?.id||'')||String(item.id||'')!==localAnchorId;
    }else{
      item.node.hidden=!active||String(item.regionId||'')!==String(deed?.id||'');
    }
  }
  if(active&&!LOCAL_DEFINER)refreshRegionPersistenceStatus();
}
function syncLocalEditLayer(){
  if(!LOCAL_DEFINER)return;
  const layer=ensureLocalEditLayer(),localId=activeLocalMapId(),active=localIsOpen();
  layer.dataset.localId=localId;
  layer.dataset.regionId=String(activeLocal?.regionId||'');
  layer.dataset.localTier=String(localTierIndex);
  layer.dataset.localLayer=String(localLayerIndex);
  layer.hidden=!active;
  for(const item of userLayers){
    if(!item.localOverlay||!item.node)continue;
    item.node.hidden=!active||String(item.localId||'')!==localId;
  }
}
function updateLayerOrder(){
  // Tier is the committed parallax/depth boundary. Unsaved placements float above
  // the stack only while the user is positioning them; Save drops them into truth.
  surface.style.zIndex=String(tierStackBase(0));
  highlands.style.zIndex=String(tierStackBase(1));
  mountains.style.zIndex=String(tierStackBase(2));
  userLayers.forEach((item,index)=>{
    item.stackOrder=index;
    const committedZ=tierStackBase(item.tier)+1+clamp(Math.trunc(Number(item.layer)||0),0,9)+(index/100);
    const regionZ=item.regionOverlay?regionZ100(regionWorldLayer(item),regionOverlayLayer(item)):regionWorldLayer(item)*100;
    const localZ=item.localOverlay
      ?(regionZ*10000)+(Math.max(0,Math.trunc(Number(item.localTier)||0))*1000)+(clamp(Math.trunc(Number(item.localLayer)||1),1,9)*100)
        +(Math.max(0,Math.trunc(Number(item.instanceTier)||0))*10)+clamp(Math.trunc(Number(item.instanceLayer)||0),0,9)
      :regionZ;
    item.node.style.zIndex=String(REGION_DEFINER
      ? (LOCAL_DEFINER&&item.localOverlay?localZ:regionZ)+(index/1000)
      : isWorldMapItem(item)?tierStackBase(0)+1:(item.committed?committedZ:1000+(index/100)));
    item.node.dataset.tier=String(item.tier);
    item.node.dataset.layer=String(item.layer);
    if(REGION_DEFINER){
      item.node.dataset.worldTier=String(item.worldTier??item.tier??0);
      item.node.dataset.worldLayer=String(regionWorldLayer(item));
      item.node.dataset.regionTier=String(item.regionOverlay?regionOverlayTier(item):0);
      item.node.dataset.regionLayer=String(item.regionOverlay?regionOverlayLayer(item):0);
      item.node.dataset.localTier=String(item.localTier??0);
      item.node.dataset.localLayer=String(item.localLayer??0);
      item.node.dataset.instanceTier=String(item.instanceTier??0);
      item.node.dataset.instanceLayer=String(item.instanceLayer??0);
      item.node.dataset.z100=String(item.regionOverlay?regionZ100(regionWorldLayer(item),regionOverlayLayer(item)):regionWorldLayer(item)*100);
    }
    item.node.dataset.placementRole=isWorldMapItem(item)?'world-map':'layer';
    item.node.dataset.placementPreview=item.committed?'false':'true';
  });
  if(REGION_DEFINER)syncRegionEditLayer();
  if(LOCAL_DEFINER)syncLocalEditLayer();
}
function closeTierMenu(){tierMenu.hidden=true;tierToggle.setAttribute('aria-expanded','false')}
function renderTierMenu(){
  tierMenu.replaceChildren();
  const options=REGION_DEFINER&&regionDeedIsComplete()
    ?[tierByIndex(clamp(Math.trunc(Number(regionClaimedRegion?.tierIndex)||0),0,TIERS.length-1))]
    :REGION_DEFINER?[...TIERS]:[{key:'all',label:'All Parallax',glyph:'≋'},...TIERS];
  for(const option of options){
    const button=document.createElement('button');button.type='button';button.role='menuitemradio';button.textContent=option.glyph;button.setAttribute('aria-label',option.key==='all'?option.label:tierLabel(option));
    const selected=REGION_DEFINER&&regionDeedIsComplete()?true:viewerTier===option.key;button.setAttribute('aria-checked',String(selected));button.setAttribute('aria-current',String(selected));
    button.addEventListener('click',()=>{setViewerTier(option.key);closeTierMenu();tierToggle.focus()});tierMenu.appendChild(button);
  }
}
function updateTierButton(){
  if(REGION_DEFINER&&regionDeedIsComplete()){
    const parent=tierByIndex(clamp(Math.trunc(Number(regionClaimedRegion?.tierIndex)||0),0,TIERS.length-1));
    tierGlyph.textContent=parent.glyph;
    tierToggle.setAttribute('aria-label',`${tierLabel(parent)} locked. World layer ${viewerLayer}; Region tier ${regionTierIndex}, layer ${regionLayerIndex}.`);
    return;
  }
  const option=viewerTier==='all'?{label:'All Parallax',glyph:'≋'}:tierByKey(viewerTier);tierGlyph.textContent=option.glyph;tierToggle.setAttribute('aria-label',`${viewerTier==='all'?option.label:tierLabel(option)}. Open tier selector`);
}
function setViewerTier(key){
  if(REGION_DEFINER&&regionDeedIsComplete()){
    announce(`World Tier ${Number(regionClaimedRegion.tierIndex)+1} is fixed by the deed. Use World Layer, Region Tier, and Region Layer controls for nested depth.`);
    return;
  }
  const previous=viewerTier;
  viewerTier=REGION_DEFINER?(key==='all'?'sea':tierByKey(key).key):(key==='all'?'all':tierByKey(key).key);
  viewerLayer=0;
  if(REGION_DEFINER&&previous!==viewerTier){clearRegionSelection(false);deselectUserImage(false);syncRegionEditLayer()}
  updateTierButton();renderTierMenu();applyTransform();scheduleRegionEnhancement(40);renderKeyboardKeys();
  announce(viewerTier==='all'?'All Parallax selected. Zoom blends through all world tiers.':`${tierLabel(tierByKey(viewerTier))} selected${REGION_DEFINER?' for regional definition.':''}`);
}
function adjustSelectedSize(direction){
  if(READ_ONLY)return;
  if(!selectedImage)return;
  if(isWorldMapItem(selectedImage)){announce('World Map always fills 100% by 100% of the world.');return}
  const current=Math.max(.2,Number(selectedImage.size)||1);
  const step=current<2?.1:current<6?.25:.5;
  applySelectedSize(selectedImage,clamp(current+(Math.sign(direction||1)*step),.2,20),{announceChange:true});
  renderKeyboardKeys();
}
function moveSelectedTier(delta){
  if(READ_ONLY||!selectedImage)return;
  const members=linkedSelectionMembers(selectedImage);
  if(LOCAL_DEFINER&&selectedImage.localOverlay){
    const next=Math.max(0,Math.trunc(Number(selectedImage.localTier)||0)+Math.sign(delta));
    for(const member of members)member.localTier=next;
    localTierIndex=next;updateLayerOrder();applyParallax();renderKeyboardKeys();updateTierButton();
    announce(`Local Tier ${next}, Local Layer ${selectedImage.localLayer??0}. ${members.length>1?'Linked pieces remain together. ':''}Local X/Y retained; World projection is derived from the Region anchor.`);return;
  }
  if(REGION_DEFINER){
    const next=clamp(regionWorldLayer(selectedImage)+Math.sign(delta),0,9);
    for(const member of members){member.worldLayer=next;member.layer=next;member.z100=regionZ100(next,regionOverlayLayer(member))}
    viewerLayer=next;updateLayerOrder();applyParallax();renderKeyboardKeys();updateTierButton();
    announce(`World Z ${next}; exact regional Z ${regionZLabel(selectedImage)}.`);return;
  }
  if(isWorldMapItem(selectedImage)){announce('World Map is locked to Sea Level.');return}
  for(const member of members){
    member.tier=clamp(member.tier+delta,0,TIERS.length-1);
    member.parallaxMode=member.tier===itemAnchorTier(member)?'anchored':'tier';
  }
  updateLayerOrder();applyParallax();renderKeyboardKeys();
  const pos=selectedPositionSummary(selectedImage);
  announce(`${members.length>1?'Linked selection':selectedImage.kind==='label'?'Label':selectedImage.kind==='sprite'?'Sprite':'Image'} moved to Tier ${pos.tier}, ${pos.tierLabel}, Layer ${pos.layer}.`);
}
function moveSelectedRegionTier(delta){
  if(READ_ONLY||!selectedImage||!REGION_DEFINER)return;
  if(LOCAL_DEFINER){announce('Region tier is inherited from the selected Local anchor.');return}
  const members=linkedSelectionMembers(selectedImage),next=Math.max(0,regionOverlayTier(selectedImage)+Math.sign(delta));
  for(const member of members)member.regionTier=next;
  regionTierIndex=next;
  updateLayerOrder();applyParallax();renderKeyboardKeys();updateTierButton();
  announce(`Region Tier ${next}, Layer ${regionOverlayLayer(selectedImage)}.`);
}
function moveSelectedLayer(delta){
  if(READ_ONLY||!selectedImage)return;
  if(isWorldMapItem(selectedImage)){announce('World Map is the Sea Level base layer.');return}
  const members=linkedSelectionMembers(selectedImage);
  if(LOCAL_DEFINER&&selectedImage.localOverlay){
    const next=clamp(Math.trunc(Number(selectedImage.localLayer)||0)+Math.sign(delta),0,9);
    for(const member of members)member.localLayer=next;
    localLayerIndex=next;updateLayerOrder();applyParallax();renderKeyboardKeys();updateTierButton();
    announce(`Local Layer ${next}, Local Tier ${selectedImage.localTier||0}. ${members.length>1?'Linked pieces remain together. ':''}Local X/Y retained; World projection is derived from the Region anchor.`);return;
  }
  if(REGION_DEFINER){
    const next=clamp(regionOverlayLayer(selectedImage)+Math.sign(delta),1,9);
    for(const member of members){member.regionLayer=next;member.z100=regionZ100(regionWorldLayer(member),next)}
    regionLayerIndex=next;updateLayerOrder();applyParallax();renderKeyboardKeys();updateTierButton();
    announce(`Region layer ${next}; exact Z ${regionZLabel(selectedImage)}.`);return;
  }
  const maxSceneZ=(TIERS.length*10)-1;
  for(const member of members){
    const currentSceneZ=(member.tier*10)+member.layer,nextSceneZ=clamp(currentSceneZ+delta,0,maxSceneZ);
    member.tier=Math.floor(nextSceneZ/10);member.layer=nextSceneZ%10;
  }
  updateLayerOrder();applyParallax();renderKeyboardKeys();
  const pos=selectedPositionSummary(selectedImage);
  announce(`${members.length>1?'Linked selection':selectedImage.kind==='label'?'Label':selectedImage.kind==='sprite'?'Sprite':'Image'} moved to Tier ${pos.tier}, ${pos.tierLabel}, Layer ${pos.layer}.`);
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
  if(REGION_DEFINER&&regionDeedIsComplete()){
    return{tier:clamp(Math.trunc(Number(regionClaimedRegion?.tierIndex)||0),0,TIERS.length-1),layer:clamp(viewerLayer,0,9)};
  }
  tier=clamp(tier,0,TIERS.length-1);
  const maxSceneZ=(TIERS.length*10)-1,sceneZ=clamp((tier*10)+viewerLayer+layerDelta,0,maxSceneZ);
  return{tier:Math.floor(sceneZ/10),layer:sceneZ%10};
}
function viewerCenterPosition(){
  const r=stage.getBoundingClientRect();
  const wx=((r.width/2)-x)/Math.max(scale,.00001);
  const wy=((r.height/2)-y)/Math.max(scale,.00001);
  const point={x:clamp(wx/Math.max(naturalWidth,1),0,1),y:clamp(wy/Math.max(naturalHeight,1),0,1)};
  return LOCAL_DEFINER&&localIsOpen()?constrainLocalPoint(point.x,point.y):(REGION_DEFINER?constrainRegionPoint(point.x,point.y):point);
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
    :LOCAL_DEFINER&&localIsOpen()
      ?`Image upload opened inside ${activeLocal?.name||'Local'} at Local Tier ${localTierIndex}, Local Layer ${localLayerIndex}. Canonical X/Y remain unchanged.`
      :REGION_DEFINER&&regionDeedIsComplete()
      ?`Image upload opened at World Z ${viewerLayer}, Region layer ${regionLayerIndex}, exact Z ${regionZLabel(viewerLayer,regionLayerIndex)}.`
      :`Image upload opened. Adjustable layer defaults to ${tierLabel(tierByIndex(currentTierIndex()))}.`);
}function closeImageUpload(){imageUploadPanel.hidden=true;stage.classList.remove('image-upload-open');imageUploadToggle.focus()}
function fileDataUrl(file){return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result||''));reader.onerror=()=>reject(reader.error);reader.readAsDataURL(file)})}
function loadDataImage(src){return new Promise((resolve,reject)=>{const img=new Image();if(!String(src).startsWith('data:')&&!String(src).startsWith('blob:'))img.crossOrigin='anonymous';img.onload=()=>resolve(img);img.onerror=reject;img.src=src})}
function openSpriteUpload(target=null){
  if(READ_ONLY){announce('World reference mode is view only.');return;}
  spriteChainTarget=target?.kind==='sprite'?target:null;
  spriteColumns.value=String(spriteChainTarget?.spriteColumns||2);
  spriteRows.value=String(spriteChainTarget?.spriteRows||2);
  spriteFps.value=String(spriteChainTarget?.spriteFps||60);
  spriteFrameCount.value=String((spriteChainTarget?.spriteColumns||2)*(spriteChainTarget?.spriteRows||2));
  if(spriteMotionOnly)spriteMotionOnly.checked=spriteChainTarget?!!spriteChainTarget.spriteMotionOnly:REGION_DEFINER;
  spriteUploadPanel.hidden=false;stage.classList.add('image-upload-open');spriteDropzone.focus();
  announce(spriteChainTarget
    ?`Add one or more sprite pages to ${spriteChainTarget.name}. Pages will play in file order after the existing chain.`
    :'Sprite chain upload opened. Select one or more sheets; they will play in file order as one animation.');
}
function closeSpriteUpload(returnToSprites=true){
  spriteUploadPanel.hidden=true;stage.classList.remove('image-upload-open');spriteChainTarget=null;
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
function isolateSpriteMotion(frameImages,low=32,high=96){
  if(!Array.isArray(frameImages)||frameImages.length<2)return frameImages;
  const count=frameImages.length,pixels=frameImages[0]?.data?.length||0;
  if(!pixels)return frameImages;
  for(let i=0;i<pixels;i+=4){
    let minR=255,minG=255,minB=255,maxR=0,maxG=0,maxB=0,maxA=0;
    for(const frame of frameImages){
      const d=frame.data,r=d[i],g=d[i+1],b=d[i+2],a=d[i+3];
      if(r<minR)minR=r;if(g<minG)minG=g;if(b<minB)minB=b;
      if(r>maxR)maxR=r;if(g>maxG)maxG=g;if(b>maxB)maxB=b;
      if(a>maxA)maxA=a;
    }
    const delta=Math.max(maxR-minR,maxG-minG,maxB-minB);
    const motion=clamp((delta-low)/Math.max(1,high-low),0,1);
    const alpha=Math.round(255*motion);
    for(const frame of frameImages){
      const d=frame.data;
      d[i+3]=Math.min(d[i+3],alpha,maxA);
    }
  }
  return frameImages;
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
  const canvases=[],images=[];
  for(let frame=0;frame<frameCount;frame++){
    const column=frame%columns,row=Math.floor(frame/columns),sx=cropX+(column*cropWidth),sy=cropY+(row*cropHeight);
    const canvas=document.createElement('canvas');canvas.width=cropWidth;canvas.height=cropHeight;
    const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.clearRect(0,0,cropWidth,cropHeight);ctx.drawImage(img,sx,sy,cropWidth,cropHeight,0,0,cropWidth,cropHeight);
    let image=ctx.getImageData(0,0,cropWidth,cropHeight);
    if(options.whiteTransparent!==false)image=whitenToAlpha(image);
    canvases.push({canvas,ctx});images.push(image);
  }
  if(options.motionOnly===true)isolateSpriteMotion(images);
  const frames=canvases.map((entry,index)=>{
    entry.ctx.putImageData(images[index],0,0);
    return entry.canvas.toDataURL('image/png');
  });
  // Decode the fixed-size frames before playback so animation does not
  // alternate between layout/redecode states on mobile Safari.
  await Promise.all(frames.map(src=>loadDataImage(src).catch(()=>null)));
  return frames;
}
function stopSpriteMotion(item){
  const timer=spriteTimers.get(item?.id);
  if(timer){cancelAnimationFrame(timer);clearTimeout(timer)}
  if(item?.id)spriteTimers.delete(item.id);
  if(item)item.playing=false;
}
function startSpriteMotion(item){
  if(!item||item.kind!=='sprite'||!Array.isArray(item.frameSources)||item.frameSources.length<2)return;
  stopSpriteMotion(item);item.playing=true;
  let last=performance.now();
  const step=now=>{
    if(!item.playing||!item.committed||!item.node?.isConnected){stopSpriteMotion(item);return}
    const fps=clamp(Number(item.spriteFps)||6,1,60),interval=1000/fps,elapsed=now-last;
    if(elapsed>=interval){
      const advance=Math.max(1,Math.floor(elapsed/interval));
      last+=advance*interval;
      item.currentFrame=((Number(item.currentFrame)||0)+advance)%item.frameSources.length;
      refreshUserImage(item);
    }
    spriteTimers.set(item.id,requestAnimationFrame(step));
  };
  spriteTimers.set(item.id,requestAnimationFrame(step));
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
function normalizeAlphaCrop(raw){
  if(!raw||typeof raw!=='object')return null;
  const x=clamp(Number(raw.x)||0,0,1),y=clamp(Number(raw.y)||0,0,1),width=clamp(Number(raw.width)||0,0,1),height=clamp(Number(raw.height)||0,0,1);
  if(!(width>0&&height>0))return null;
  return{x,y,width,height};
}
function normalizeAlphaSeed(raw){
  if(!raw||typeof raw!=='object')return null;
  const x=clamp(Number(raw.x)||0,0,1),y=clamp(Number(raw.y)||0,0,1);
  return{x,y};
}
async function cropImageSource(src,crop){
  crop=normalizeAlphaCrop(crop);if(!crop)return String(src||'');
  const img=await loadDataImage(src),w=Math.max(1,img.naturalWidth||img.width||1),h=Math.max(1,img.naturalHeight||img.height||1);
  const sx=clamp(Math.floor(crop.x*w),0,w-1),sy=clamp(Math.floor(crop.y*h),0,h-1);
  const sw=clamp(Math.ceil(crop.width*w),1,w-sx),sh=clamp(Math.ceil(crop.height*h),1,h-sy);
  const canvas=document.createElement('canvas');canvas.width=sw;canvas.height=sh;
  const ctx=canvas.getContext('2d');ctx.clearRect(0,0,sw,sh);ctx.drawImage(img,sx,sy,sw,sh,0,0,sw,sh);
  return canvas.toDataURL('image/png');
}
async function alphaComponentAnalysis(source){
  source=String(source||'');if(!source)return{source:'',transparentSrc:'',pieces:[]};
  if(alphaComponentCache.has(source))return alphaComponentCache.get(source);
  const task=(async()=>{
    const transparentSrc=await transparencyCandidate(source),img=await loadDataImage(transparentSrc);
    const sourceWidth=Math.max(1,img.naturalWidth||img.width||1),sourceHeight=Math.max(1,img.naturalHeight||img.height||1);
    const max=1536,ratio=Math.min(1,max/Math.max(sourceWidth,sourceHeight)),width=Math.max(1,Math.round(sourceWidth*ratio)),height=Math.max(1,Math.round(sourceHeight*ratio));
    const canvas=document.createElement('canvas');canvas.width=width;canvas.height=height;
    const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.clearRect(0,0,width,height);ctx.drawImage(img,0,0,width,height);
    const image=ctx.getImageData(0,0,width,height),px=image.data,count=width*height,labels=new Int32Array(count),queue=new Int32Array(count);
    const minimumArea=Math.max(16,Math.floor(count*.00004)),components=[];let label=0;
    for(let start=0;start<count;start++){
      if(labels[start]||px[start*4+3]<=8)continue;
      label++;let head=0,tail=0,minX=width,minY=height,maxX=-1,maxY=-1;
      labels[start]=label;queue[tail++]=start;
      while(head<tail){
        const p=queue[head++],x=p%width,y=(p/width)|0;
        if(x<minX)minX=x;if(x>maxX)maxX=x;if(y<minY)minY=y;if(y>maxY)maxY=y;
        for(let oy=-1;oy<=1;oy++)for(let ox=-1;ox<=1;ox++){
          if(!ox&&!oy)continue;const nx=x+ox,ny=y+oy;
          if(nx<0||nx>=width||ny<0||ny>=height)continue;
          const n=ny*width+nx;if(labels[n]||px[n*4+3]<=8)continue;
          labels[n]=label;queue[tail++]=n;
        }
      }
      if(tail>=minimumArea)components.push({label,area:tail,minX,minY,maxX,maxY,seed:queue[Math.floor(tail/2)]});
    }
    components.sort((a,b)=>b.area-a.area);
    const kept=components.slice(0,64),pieces=[];
    for(const component of kept){
      const pad=1,minX=Math.max(0,component.minX-pad),minY=Math.max(0,component.minY-pad),maxX=Math.min(width-1,component.maxX+pad),maxY=Math.min(height-1,component.maxY+pad);
      const cw=maxX-minX+1,ch=maxY-minY+1,out=document.createElement('canvas');out.width=cw;out.height=ch;
      const outCtx=out.getContext('2d',{willReadFrequently:true}),crop=ctx.getImageData(minX,minY,cw,ch),cp=crop.data;
      for(let yy=0;yy<ch;yy++)for(let xx=0;xx<cw;xx++){
        const global=(minY+yy)*width+(minX+xx);
        if(labels[global]!==component.label)cp[(yy*cw+xx)*4+3]=0;
      }
      outCtx.putImageData(crop,0,0);
      const seedIndex=component.seed,seedX=(seedIndex%width+.5)/width,seedY=(((seedIndex/width)|0)+.5)/height;
      pieces.push({
        src:out.toDataURL('image/png'),
        crop:{x:minX/width,y:minY/height,width:cw/width,height:ch/height},
        seed:{x:seedX,y:seedY},
        area:component.area
      });
    }
    return{source,transparentSrc,sourceWidth,sourceHeight,width,height,pieces};
  })().catch(error=>{alphaComponentCache.delete(source);throw error});
  alphaComponentCache.set(source,task);return task;
}
async function preparedImageSource(source,{transparent=false,alphaCrop=null,alphaComponentSeed=null}={}){
  source=String(source||'');if(!source)return'';
  const seed=normalizeAlphaSeed(alphaComponentSeed);
  if(seed){
    const analysis=await alphaComponentAnalysis(source);
    if(analysis.pieces.length){
      let best=analysis.pieces[0],bestDistance=Infinity;
      for(const piece of analysis.pieces){
        const dx=piece.seed.x-seed.x,dy=piece.seed.y-seed.y,d=(dx*dx)+(dy*dy);
        if(d<bestDistance){bestDistance=d;best=piece}
      }
      return best.src;
    }
  }
  let visible=transparent?await transparencyCandidate(source):source;
  if(alphaCrop)visible=await cropImageSource(visible,alphaCrop);
  return visible;
}
function linkedSelectionMembers(item=selectedImage){
  const group=String(item?.linkGroupId||'').trim();
  if(!group)return item?[item]:[];
  return userLayers.filter(entry=>String(entry?.linkGroupId||'')===group&&entry?.node?.isConnected);
}
function refreshLinkedSelectionClasses(){
  for(const item of userLayers)item?.node?.classList.remove('linked-selected');
  if(!selectedImage)return;
  const members=linkedSelectionMembers(selectedImage);
  if(members.length>1)for(const item of members)item.node?.classList.add('linked-selected');
}
function linkedSelectionCenter(members){
  if(!members?.length)return{x:0,y:0};
  let x=0,y=0;for(const item of members){x+=(Number(item.x)||0)*naturalWidth;y+=(Number(item.y)||0)*naturalHeight}
  return{x:x/members.length,y:y/members.length};
}
function rotateLinkedSelection(item,delta){
  const members=linkedSelectionMembers(item);if(!members.length)return;
  if(members.length===1){item.rotation=(Number(item.rotation)||0)+delta;refreshUserImage(item);return}
  const center=linkedSelectionCenter(members),rad=delta*Math.PI/180,c=Math.cos(rad),s=Math.sin(rad);
  for(const member of members){
    const px=(Number(member.x)||0)*naturalWidth-center.x,py=(Number(member.y)||0)*naturalHeight-center.y;
    member.x=clamp((center.x+(px*c)-(py*s))/Math.max(naturalWidth,1),0,1);
    member.y=clamp((center.y+(px*s)+(py*c))/Math.max(naturalHeight,1),0,1);
    member.rotation=(Number(member.rotation)||0)+delta;refreshUserImage(member);
  }
  refreshAssetResizeOverlay(item);scheduleRegionEnhancement(20);
}
function adjustLinkedOpacity(item,delta){
  for(const member of linkedSelectionMembers(item)){member.opacity=clamp((Number(member.opacity)||1)+delta,.1,1);refreshUserImage(member)}
}
async function toggleLinkedTransparency(item){
  const next=!item.transparent,members=linkedSelectionMembers(item);
  for(const member of members){
    member.transparent=next;
    if(next&&member.originalSrc){
      member.transparentSrc=await preparedImageSource(member.originalSrc,{transparent:true,alphaCrop:member.alphaCrop,alphaComponentSeed:member.alphaComponentSeed}).catch(()=>member.transparentSrc||member.originalSrc);
    }
    member.renderedSrc='';refreshUserImage(member);
  }
  renderKeyboardKeys();scheduleRegionEnhancement(20);
}
function unlinkSelectedGroup(){
  const members=linkedSelectionMembers(selectedImage);
  if(members.length<2){announce('This image is already independent.');return false}
  for(const item of members){item.linkGroupId='';item.linkGroupIndex=null;item.linkGroupCount=null;item.node?.classList.remove('linked-selected')}
  refreshLinkedSelectionClasses();renderKeyboardKeys();announce(`Unlinked ${members.length} pieces. Each piece can now move independently.`);return true;
}
async function splitImageByAlpha(item=selectedImage){
  if(READ_ONLY||!item||item.kind!=='image'||item.sourceLocked||isWorldMapItem(item))return false;
  try{
    if(item.personalUploadPromise)await item.personalUploadPromise.catch(()=>null);
    let source=String(item.originalSrc||'');
    if(item.personalAssetKey)source=await resolvePersonalAssetSource(item.personalAssetKey,source);
    if(!source){announce('The image source is unavailable.');return false}
    announce('Cutting transparent sections into linked pieces…');
    const analysis=await alphaComponentAnalysis(source);
    if(!analysis.pieces.length){announce('No visible image sections were found.');return false}
    const oldSize=Math.max(Number(item.size)||1,.00001),oldX=Number(item.x)||0,oldY=Number(item.y)||0,baseW=naturalWidth*.12,baseH=baseW*(analysis.sourceHeight/Math.max(analysis.sourceWidth,1));
    const makeGeometry=piece=>{
      const crop=piece.crop,localDx=((crop.x+(crop.width/2))-.5)*baseW*oldSize,localDy=((crop.y+(crop.height/2))-.5)*baseH*oldSize;
      const rad=(Number(item.rotation)||0)*Math.PI/180,c=Math.cos(rad),s=Math.sin(rad),worldDx=(localDx*c)-(localDy*s),worldDy=(localDx*s)+(localDy*c);
      return{
        x:clamp(oldX+(worldDx/Math.max(naturalWidth,1)),0,1),
        y:clamp(oldY+(worldDy/Math.max(naturalHeight,1)),0,1),
        size:clamp(oldSize*crop.width,.05,20)
      };
    };
    if(analysis.pieces.length===1){
      const piece=analysis.pieces[0],geometry=makeGeometry(piece);
      item.originalSrc=source;item.transparentSrc=piece.src;item.transparent=true;item.alphaCrop=piece.crop;item.alphaComponentSeed=piece.seed;
      item.x=geometry.x;item.y=geometry.y;item.size=geometry.size;item.renderedSrc='';item.committed=false;
      refreshUserImage(item);refreshAssetResizeOverlay(item);renderKeyboardKeys();scheduleRegionEnhancement(20);
      announce('Transparent outer pixels were cut away. The visible image remains one object.');return true;
    }
    const groupId=`alpha-group:${crypto.randomUUID?.()||Date.now()}`,originalIndex=Math.max(0,userLayers.indexOf(item)),members=[];
    for(let index=0;index<analysis.pieces.length;index++){
      const piece=analysis.pieces[index],geometry=makeGeometry(piece),member={
        ...item,
        // Preserve the original object identity on the lead piece so existing
        // Local anchors and other stable references do not break when an image
        // is separated into linked visible sections.
        id:index===0?String(item.id||`alpha-piece:${Date.now()}:0`):`alpha-piece:${crypto.randomUUID?.()||Date.now()}:${index}`,
        authorityResourceId:index===0?String(item.authorityResourceId||''):'',
        name:index===0?String(item.name||'Image'):`${item.name||'Image'} · piece ${index+1}/${analysis.pieces.length}`,
        originalSrc:source,transparentSrc:piece.src,transparent:true,alphaCrop:piece.crop,alphaComponentSeed:piece.seed,
        linkGroupId:groupId,linkGroupIndex:index,linkGroupCount:analysis.pieces.length,
        x:geometry.x,y:geometry.y,size:geometry.size,committed:false,renderOpacity:1,renderedSrc:'',zoomPassed:false,zoomPassScale:null,
        progressiveSlices:null,node:null
      };
      const node=document.createElement('img');node.className='user-image-placement';node.alt=member.name;node.draggable=false;member.node=node;
      node.addEventListener('pointerdown',event=>beginImageDrag(event,member));node.addEventListener('pointermove',moveImageDrag);node.addEventListener('pointerup',endImageDrag);node.addEventListener('pointercancel',endImageDrag);
      members.push(member);
    }
    stopSpriteMotion(item);item.node?.remove();const oldIndex=userLayers.indexOf(item);if(oldIndex>=0)userLayers.splice(oldIndex,1);
    userLayers.splice(originalIndex,0,...members);
    for(const member of members){mountUserPlacement(member);refreshUserImage(member)}
    updateLayerOrder();selectUserImage(members[0]);applyParallax();renderKeyboardKeys();scheduleRegionEnhancement(20);
    announce(`Cut image into ${members.length} linked pieces. They move together until you choose UNLINK.`);return true;
  }catch(error){
    announce(`Image split failed: ${String(error?.message||error||'unknown error')}`);return false;
  }
}
const LABEL_COLORS=Object.freeze(['#fff2c7','#ffffff','#f0cc69','#a9d8ff','#b7f0c2','#ffb7b7','#d6c2ff','#121820']);
function refreshUserLabel(item){
  if(!item?.node)return;
  item.node.textContent=String(item.text||'Label');
  item.node.style.left=`${item.x*naturalWidth}px`;
  item.node.style.top=`${item.y*naturalHeight}px`;
  item.node.style.opacity=String(item.renderOpacity??item.opacity??1);
  item.node.style.pointerEvents=item.sourceLocked&&!isLocalAnchorCandidate(item)?'none':(REGION_DEFINER&&item.regionOverlay?'auto':(item.committed&&selectedImage!==item?'none':'auto'));
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
  if(item===selectedImage)requestAnimationFrame(()=>refreshAssetResizeOverlay(item));
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
  userLayers.push(item);mountUserPlacement(item);updateLayerOrder();refreshUserLabel(item);selectUserImage(item);keyboardMode='Labels';openKeyboard();renderKeyboardTabs();renderKeyboardKeys();applyParallax();
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
    ...(REGION_DEFINER
      ?[
        readoutKey(`WORLD TIER ${pos.tier}`,pos.tierLabel),
        readoutKey(`WORLD Z ${pos.worldZ}`,`WorldBuilder Layer ${pos.layer}`),
        readoutKey(`REGION L ${pos.regionLayer}`,`Exact Z ${pos.z}`)
      ]
      :[readoutKey(`TIER ${pos.tier}`,pos.tierLabel),readoutKey(`LAYER ${pos.layer}`,'label layer')]),
    toolKey('A−',`${Math.round(selected.fontSize||48)} px`,()=>adjustSelectedLabelFont(-1),selected.fontSize<=12),
    toolKey('A+',`${Math.round(selected.fontSize||48)} px`,()=>adjustSelectedLabelFont(1),selected.fontSize>=180),
    sizeNumberInput(selected),sizeRangeInput(selected),
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
    ...(LOCAL_DEFINER
      ?[
        toolKey('LOCAL T −',`T ${pos.localTier}`,()=>moveSelectedTier(-1),pos.localTier<=0),
        toolKey('LOCAL T +',`T ${pos.localTier}`,()=>moveSelectedTier(1)),
        toolKey('LOCAL L −',`L ${pos.localLayer}`,()=>moveSelectedLayer(-1),pos.localLayer<=1),
        toolKey('LOCAL L +',`L ${pos.localLayer}`,()=>moveSelectedLayer(1),pos.localLayer>=9)
      ]
      :REGION_DEFINER
      ?[
        toolKey('WORLD Z −',`Z ${pos.worldZ}`,()=>moveSelectedTier(-1),pos.worldZ<=0),
        toolKey('WORLD Z +',`Z ${pos.worldZ}`,()=>moveSelectedTier(1),pos.worldZ>=9),
        toolKey('REGION L −',`L ${pos.regionLayer}`,()=>moveSelectedLayer(-1),pos.regionLayer<=1),
        toolKey('REGION L +',`L ${pos.regionLayer}`,()=>moveSelectedLayer(1),pos.regionLayer>=9)
      ]
      :[
        toolKey('TIER −',`T${pos.tier}`,()=>moveSelectedTier(-1),selected.tier<=0),
        toolKey('TIER +',`T${pos.tier}`,()=>moveSelectedTier(1),selected.tier>=TIERS.length-1),
        toolKey('LAYER −',`L${pos.layer}`,()=>moveSelectedLayer(-1),selected.tier<=0&&selected.layer<=0),
        toolKey('LAYER +',`L${pos.layer}`,()=>moveSelectedLayer(1),selected.tier>=TIERS.length-1&&selected.layer>=9)
      ]),
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
  // Map-attached images are ordinary editable layers, not floating depth
  // slices. Region-owned imagery also stays directly hit-testable on mobile.
  if(REGION_DEFINER&&item.regionOverlay){
    item.progressiveParallaxHost?.remove();
    item.progressiveParallaxHost=null;
    item.progressiveParallaxSlices=[];
    item.node.style.visibility='visible';
    return false;
  }
  if(itemParallaxMode(item)==='anchored'){
    item.progressiveParallaxHost?.remove();
    item.progressiveParallaxHost=null;
    item.progressiveParallaxSlices=[];
    item.node.style.visibility='visible';
    return false;
  }
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
function selectedSizeValue(item){
  return item?.kind==='label'
    ?clamp(Number(item.fontSize)||48,12,180)
    :clamp(Number(item?.size)||1,.05,20);
}
function applySelectedSize(item,value,{announceChange=false}={}){
  if(READ_ONLY||!item||item.sourceLocked||isWorldMapItem(item))return false;
  if(item.kind==='label'){
    item.fontSize=clamp(Number(value)||48,12,180);
    refreshUserLabel(item);
  }else{
    const next=clamp(Number(value)||1,.05,20),members=linkedSelectionMembers(item);
    if(members.length>1){
      const current=Math.max(Number(item.size)||1,.00001),factor=next/current,center=linkedSelectionCenter(members);
      for(const member of members){
        const px=(Number(member.x)||0)*naturalWidth-center.x,py=(Number(member.y)||0)*naturalHeight-center.y;
        member.x=clamp((center.x+(px*factor))/Math.max(naturalWidth,1),0,1);
        member.y=clamp((center.y+(py*factor))/Math.max(naturalHeight,1),0,1);
        member.size=clamp((Number(member.size)||1)*factor,.05,20);refreshUserImage(member);
      }
    }else{
      item.size=next;refreshUserImage(item);
    }
  }
  refreshAssetResizeOverlay(item);
  scheduleRegionEnhancement(20);
  if(announceChange){
    const valueNow=selectedSizeValue(item),count=linkedSelectionMembers(item).length;
    announce(item.kind==='label'
      ?`Label size ${Math.round(valueNow)} pixels.`
      :count>1?`Linked selection size changed (${count} pieces).`:`${item.kind==='sprite'?'Sprite':'Asset'} size ${valueNow.toFixed(2)} times.`);
  }
  return true;
}
function sizeNumberInput(item){
  const field=document.createElement('label');field.className='asset-size-field';
  const caption=document.createElement('span');caption.textContent=item.kind==='label'?'FONT PX':'SIZE ×';
  const input=document.createElement('input');
  input.type='number';input.className='asset-size-number';
  input.min=item.kind==='label'?'12':'0.05';
  input.max=item.kind==='label'?'180':'20';
  input.step=item.kind==='label'?'1':'0.01';
  input.value=item.kind==='label'?String(Math.round(selectedSizeValue(item))):selectedSizeValue(item).toFixed(2);
  input.setAttribute('aria-label',item.kind==='label'?'Label size in pixels':'Asset size multiplier');
  const commit=()=>{if(applySelectedSize(item,input.value,{announceChange:true})){input.value=item.kind==='label'?String(Math.round(selectedSizeValue(item))):selectedSizeValue(item).toFixed(2)}};
  input.addEventListener('change',commit);
  input.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();commit();input.blur()}});
  field.append(caption,input);return field;
}
function sizeRangeInput(item){
  const field=document.createElement('label');field.className='asset-size-range-field';
  const caption=document.createElement('span');caption.textContent='FINE SIZE';
  const input=document.createElement('input');
  input.type='range';input.className='asset-size-range';
  input.min=item.kind==='label'?'12':'0.05';
  input.max=item.kind==='label'?'180':'20';
  input.step=item.kind==='label'?'1':'0.01';
  input.value=String(selectedSizeValue(item));
  input.setAttribute('aria-label',item.kind==='label'?'Fine label size':'Fine asset size');
  input.addEventListener('input',()=>applySelectedSize(item,input.value));
  input.addEventListener('change',()=>applySelectedSize(item,input.value,{announceChange:true}));
  field.append(caption,input);return field;
}
function removeAssetResizeOverlay(){
  assetResizeDrag=null;
  assetResizeOverlay?.remove();
  assetResizeOverlay=null;
}
function ensureAssetResizeOverlay(){
  if(assetResizeOverlay?.isConnected)return assetResizeOverlay;
  const overlay=document.createElement('div');
  overlay.className='asset-resize-overlay';
  overlay.setAttribute('aria-hidden','false');
  for(const corner of ['nw','ne','sw','se']){
    const handle=document.createElement('button');
    handle.type='button';handle.className=`asset-resize-handle ${corner}`;
    handle.dataset.corner=corner;
    handle.setAttribute('aria-label',`Resize selected asset from ${corner.toUpperCase()} corner`);
    handle.addEventListener('pointerdown',beginAssetResize);
    handle.addEventListener('pointermove',moveAssetResize);
    handle.addEventListener('pointerup',endAssetResize);
    handle.addEventListener('pointercancel',endAssetResize);
    overlay.appendChild(handle);
  }
  assetResizeOverlay=overlay;
  return overlay;
}
function refreshAssetResizeOverlay(item=selectedImage){
  if(!item||item.sourceLocked||isWorldMapItem(item)||!item.node?.isConnected){
    removeAssetResizeOverlay();return;
  }
  const overlay=ensureAssetResizeOverlay();
  const parent=item.node.parentElement;
  if(overlay.parentElement!==parent)parent?.appendChild(overlay);
  overlay.dataset.kind=String(item.kind||'image');
  overlay.style.left=item.node.style.left;
  overlay.style.top=item.node.style.top;
  overlay.style.zIndex='4095';
  if(item.kind==='label'){
    overlay.style.width=`${Math.max(20,item.node.offsetWidth)}px`;
    overlay.style.height=`${Math.max(20,item.node.offsetHeight)}px`;
    overlay.style.aspectRatio='';
    const px=(Number(item.parallaxX)||0)+(Number(item.offsetX)||0),py=(Number(item.parallaxY)||0)+(Number(item.offsetY)||0);
    overlay.style.transform=`translate(-50%,-50%) translate3d(${px.toFixed(2)}px,${py.toFixed(2)}px,0) rotate(${Number(item.rotation)||0}deg)`;
  }else{
    overlay.style.width=`${12*selectedSizeValue(item)}%`;
    overlay.style.height='auto';
    overlay.style.aspectRatio=String(stableAssetAspect(item));
    const px=Number(item.parallaxX)||0,py=Number(item.parallaxY)||0;
    overlay.style.transform=`translate(-50%,-50%) translate3d(${px.toFixed(2)}px,${py.toFixed(2)}px,0) rotate(${Number(item.rotation)||0}deg)`;
  }
}
function beginAssetResize(event){
  const item=selectedImage;
  if(READ_ONLY||!item||item.sourceLocked||isWorldMapItem(item))return;
  event.preventDefault();event.stopPropagation();
  const overlay=assetResizeOverlay;if(!overlay)return;
  const rect=overlay.getBoundingClientRect(),centerX=rect.left+rect.width/2,centerY=rect.top+rect.height/2;
  const distance=Math.max(8,Math.hypot(event.clientX-centerX,event.clientY-centerY));
  const resumeSprite=item.kind==='sprite'&&item.playing;
  if(resumeSprite)stopSpriteMotion(item);
  event.currentTarget.setPointerCapture?.(event.pointerId);
  assetResizeDrag={id:event.pointerId,item,handle:event.currentTarget,centerX,centerY,startDistance:distance,startValue:selectedSizeValue(item),resumeSprite};
  stage.classList.add('asset-resizing');
  suspendRegionEnhancement();
}
function moveAssetResize(event){
  if(!assetResizeDrag||assetResizeDrag.id!==event.pointerId)return;
  event.preventDefault();event.stopPropagation();
  const drag=assetResizeDrag;
  const distance=Math.max(4,Math.hypot(event.clientX-drag.centerX,event.clientY-drag.centerY));
  applySelectedSize(drag.item,drag.startValue*(distance/drag.startDistance));
  const number=keyboardKeys.querySelector('.asset-size-number'),range=keyboardKeys.querySelector('.asset-size-range');
  if(number)number.value=drag.item.kind==='label'?String(Math.round(selectedSizeValue(drag.item))):selectedSizeValue(drag.item).toFixed(2);
  if(range)range.value=String(selectedSizeValue(drag.item));
}
function endAssetResize(event){
  if(!assetResizeDrag||assetResizeDrag.id!==event.pointerId)return;
  const drag=assetResizeDrag;assetResizeDrag=null;
  stage.classList.remove('asset-resizing');
  if(drag.handle?.hasPointerCapture?.(event.pointerId))drag.handle.releasePointerCapture(event.pointerId);
  refreshAssetResizeOverlay(drag.item);
  scheduleRegionEnhancement(40);
  if(drag.resumeSprite&&drag.item.committed)startSpriteMotion(drag.item);
  applySelectedSize(drag.item,selectedSizeValue(drag.item),{announceChange:true});
}
function refreshUserImage(item){
  if(!item?.node)return;
  if(item.kind==='label'){refreshUserLabel(item);return}
  const spriteFrame=item.kind==='sprite'&&Array.isArray(item.frameSources)&&item.frameSources.length?item.frameSources[clamp(Math.trunc(Number(item.currentFrame)||0),0,item.frameSources.length-1)]:null;
  const desired=spriteFrame||(item.transparent&&item.transparentSrc?item.transparentSrc:item.originalSrc);
  if(!desired){
    item.node.dataset.assetPending=item.personalAssetKey?'true':'false';
    item.node.style.visibility='hidden';
  }else{
    item.node.dataset.assetPending='false';
    if(item.renderedSrc!==desired){
      item.node.src=desired;item.renderedSrc=desired;
      if(item.kind!=='sprite')void primeCollisionMask(desired);
    }
    if(!item.progressiveSlices?.length)item.node.style.visibility='';
  }
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
  item.node.style.aspectRatio=item.kind==='sprite'?String(stableAssetAspect(item)):'';
  item.node.style.left=`${item.x*naturalWidth}px`;item.node.style.top=`${item.y*naturalHeight}px`;
  item.node.style.pointerEvents=item.sourceLocked&&!isLocalAnchorCandidate(item)?'none':(REGION_DEFINER&&item.regionOverlay?'auto':(item.committed&&selectedImage!==item?'none':'auto'));
  item.node.style.transformOrigin='50% 50%';
  const px=Number(item.parallaxX)||0,py=Number(item.parallaxY)||0;
  item.node.style.transform=`translate(-50%,-50%) translate3d(${px.toFixed(2)}px,${py.toFixed(2)}px,0) rotate(${item.rotation}deg) scale(${item.size})`;
  if(!desired){item.node.style.visibility='hidden';return}
  refreshProgressiveParallax(item);
  if(item===selectedImage)refreshAssetResizeOverlay(item);
}function selectUserImage(item){
  const localAnchorCandidate=isLocalAnchorCandidate(item);
  if((item?.sourceLocked&&!localAnchorCandidate)||(REGION_DEFINER&&item&&(!item.regionOverlay
    ||String(item.regionId||'')!==activeRegionMapId()))){
    announce('The parent world tier is locked. Select a regional object above it.');return;
  }
  const previous=selectedImage;
  previous?.node?.classList.remove('selected');selectedImage=item||null;selectedImage?.node?.classList.add('selected');refreshLinkedSelectionClasses();
  if(previous&&previous!==selectedImage)refreshUserImage(previous);
  if(selectedImage)refreshUserImage(selectedImage);
  if(selectedImage)refreshAssetResizeOverlay(selectedImage);else removeAssetResizeOverlay();
  if(REGION_DEFINER&&regionDeedIsComplete()&&selectedImage&&keyboardMode==='Select'&&!LOCAL_DEFINER){
    keyboardMode=selectedImage.kind==='label'?'Labels':'Image';
    renderKeyboardTabs();
    announce(`${selectedImage.name||'Region object'} selected. Editing controls are open.`);
  }else if(LOCAL_DEFINER&&selectedImage){
    announce(localIsOpen()
      ?`${selectedImage.name||'Local object'} selected for Local editing.`
      :`${selectedImage.name||'Regional object'} selected as a Local anchor candidate.`);
  }
  renderKeyboardKeys();scheduleRegionEnhancement(20);
}
function deselectUserImage(announceChange=false){
  if(!selectedImage)return false;
  const previous=selectedImage;
  previous.node?.classList.remove('selected');selectedImage=null;refreshLinkedSelectionClasses();removeAssetResizeOverlay();refreshUserImage(previous);renderKeyboardKeys();scheduleRegionEnhancement(20);
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
  if(LOCAL_DEFINER){
    if(localIsOpen()){
      const localId=activeLocalMapId();
      return userLayers.filter(item=>item?.node&&!item.sourceLocked&&item.localOverlay&&String(item.localId||'')===localId);
    }
    return userLayers.filter(item=>isLocalAnchorCandidate(item));
  }
  return userLayers.filter(item=>item?.node&&(!REGION_DEFINER
    ||(regionDeedIsComplete()&&!item.sourceLocked&&item.regionOverlay&&!item.localOverlay
      &&String(item.regionId||'')===activeRegionMapId())));
}
function assetModeMatches(item,mode){
  if(!item)return false;
  if(mode==='Sprites')return item.kind==='sprite';
  if(mode==='Labels')return item.kind==='label';
  if(mode==='Tiles')return !!item.libraryTile&&item.kind!=='sprite'&&item.kind!=='label';
  if(mode==='Image')return item.kind!=='sprite'&&item.kind!=='label'&&!item.libraryTile;
  return true;
}
function selectablePlacedContentForMode(mode){
  return selectablePlacedContent().filter(item=>assetModeMatches(item,mode));
}
function typedPlacedContentSelect(mode){
  const select=document.createElement('select');
  select.className='placed-content-select';
  select.setAttribute('aria-label',`Select placed ${mode.toLowerCase()} asset`);
  const items=selectablePlacedContentForMode(mode);
  const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent=items.length?`Select ${mode.toLowerCase()}…`:`No ${mode.toLowerCase()} assets yet`;placeholder.selected=!selectedImage||!assetModeMatches(selectedImage,mode);select.appendChild(placeholder);
  items.forEach((item,index)=>{const option=document.createElement('option');option.value=String(item.id);option.textContent=placedContentLabel(item,index);option.selected=item===selectedImage;select.appendChild(option)});
  select.disabled=!items.length;
  select.addEventListener('change',()=>{const item=items.find(entry=>String(entry.id)===select.value);if(item){selectUserImage(item);renderKeyboardKeys();announce(`${placedContentLabel(item,userLayers.indexOf(item))} selected.`)}});
  return select;
}
function appendCommonAssetEditControls(mode,item){
  if(!item||!assetModeMatches(item,mode)||isWorldMapItem(item))return;
  keyboardKeys.append(
    toolKey('SIZE −',`${selectedSizeValue(item).toFixed(2)}×`,()=>adjustSelectedSize(-1),selectedSizeValue(item)<=.05),
    toolKey('SIZE +',`${selectedSizeValue(item).toFixed(2)}×`,()=>adjustSelectedSize(1),selectedSizeValue(item)>=20),
    sizeNumberInput(item),sizeRangeInput(item),
    toolKey('DELETE',mode.toLowerCase(),removeSelectedImage)
  );
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
  const available=selectablePlacedContent();
  const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent=available.length?'Select regional object…':'No regional objects yet';placeholder.disabled=!!available.length;placeholder.selected=!selectedImage;select.appendChild(placeholder);
  selectablePlacedContent().forEach((item,index)=>{
    const option=document.createElement('option');option.value=item.id;option.textContent=placedContentLabel(item,index);option.selected=item===selectedImage;select.appendChild(option);
  });
  select.disabled=!available.length;
  select.addEventListener('change',()=>{
    const item=userLayers.find(entry=>String(entry.id)===select.value);
    if(item){selectUserImage(item);announce(`${placedContentLabel(item,userLayers.indexOf(item))} selected.`)}
  });
  return select;
}
function removeSelectedImage(){
  if(READ_ONLY)return;if(!selectedImage)return;
  if(selectedImage.sourceLocked){announce('This map content is outside your Region Definer edit permission.');return}
  const doomed=linkedSelectionMembers(selectedImage);
  for(const item of doomed){stopSpriteMotion(item);item.node?.remove();const index=userLayers.indexOf(item);if(index>=0)userLayers.splice(index,1)}
  selectedImage=null;refreshLinkedSelectionClasses();removeAssetResizeOverlay();updateLayerOrder();applyParallax();renderKeyboardKeys();
  announce(doomed.length>1?`Linked selection removed (${doomed.length} pieces).`:'Placed content removed from the layer stack.');
}
function beginImageDrag(event,item){
  if(LOCAL_DEFINER&&!localIsOpen()){event.preventDefault();event.stopPropagation();selectUserImage(item);return;}
  if(READ_ONLY||item?.sourceLocked||isWorldMapItem(item))return;
  if(LOCAL_DEFINER&&localIsOpen()&&(!item?.localOverlay||String(item.localId||'')!==activeLocalMapId()))return;
  if(REGION_DEFINER&&!LOCAL_DEFINER&&(!regionDeedIsComplete()||!item?.regionOverlay
    ||String(item.regionId||'')!==activeRegionMapId()))return;
  if(event.pointerType==='mouse'&&event.button!==0)return;
  const alreadySelected=selectedImage===item;
  if(item?.committed&&!alreadySelected&&REGION_DEFINER){
    // Tap once to select a saved region object. A later gesture may drag it.
    event.preventDefault();event.stopPropagation();selectUserImage(item);return;
  }
  if(item?.committed&&!alreadySelected)return;
  event.preventDefault();event.stopPropagation();selectUserImage(item);item.node.setPointerCapture?.(event.pointerId);
  if(REGION_DEFINER)stage.classList.add('region-asset-moving');
  const resumeSprite=item.kind==='sprite'&&item.playing;
  if(resumeSprite)stopSpriteMotion(item);
  suspendRegionEnhancement();
  const linked=linkedSelectionMembers(item).filter(member=>!member.sourceLocked);
  imageDrag={id:event.pointerId,item,startX:event.clientX,startY:event.clientY,x:item.x,y:item.y,resumeSprite,members:linked.map(member=>({item:member,x:Number(member.x)||0,y:Number(member.y)||0}))};
}
function moveImageDrag(event){
  if(READ_ONLY)return;
  if(!imageDrag||imageDrag.id!==event.pointerId)return;event.preventDefault();event.stopPropagation();
  const rawX=clamp(imageDrag.x+(event.clientX-imageDrag.startX)/(Math.max(scale,.00001)*Math.max(naturalWidth,1)),0,1);
  const rawY=clamp(imageDrag.y+(event.clientY-imageDrag.startY)/(Math.max(scale,.00001)*Math.max(naturalHeight,1)),0,1);
  const bounded=LOCAL_DEFINER&&localIsOpen()?constrainLocalPoint(rawX,rawY):(REGION_DEFINER?constrainRegionPoint(rawX,rawY):{x:rawX,y:rawY});
  const dx=bounded.x-imageDrag.x,dy=bounded.y-imageDrag.y,members=imageDrag.members?.length?imageDrag.members:[{item:imageDrag.item,x:imageDrag.x,y:imageDrag.y}];
  let blocked=false,next=[];
  for(const entry of members){
    const px=clamp(entry.x+dx,0,1),py=clamp(entry.y+dy,0,1);
    const constrained=LOCAL_DEFINER&&localIsOpen()?constrainLocalPoint(px,py):(REGION_DEFINER?constrainRegionPoint(px,py):{x:px,y:py});
    if(Math.abs(constrained.x-px)>.000001||Math.abs(constrained.y-py)>.000001){blocked=true;break}
    next.push({item:entry.item,x:px,y:py});
  }
  if(!blocked){
    for(const entry of next){entry.item.x=entry.x;entry.item.y=entry.y;refreshUserImage(entry.item)}
    refreshAssetResizeOverlay(imageDrag.item);
  }
  if((keyboardMode==='Image'||keyboardMode==='Labels')&&selectedImage===imageDrag.item)renderKeyboardKeys();
}
function endImageDrag(event){
  if(!imageDrag||imageDrag.id!==event.pointerId)return;
  const drag=imageDrag;imageDrag=null;
  stage.classList.remove('region-asset-moving');
  if(drag.item.node.hasPointerCapture?.(event.pointerId))drag.item.node.releasePointerCapture(event.pointerId);
  refreshAssetResizeOverlay(drag.item);
  scheduleRegionEnhancement(40);
  if(drag.resumeSprite&&drag.item.committed)startSpriteMotion(drag.item);
}
async function placeUploadedImage(file){
  if(READ_ONLY){announce('World reference mode is view only.');return;}
  if(!file?.type?.startsWith('image/')){announce('Choose an image file.');return}
  const originalSrc=await fileDataUrl(file),transparentSrc=await transparencyCandidate(originalSrc);
  const placementRole=requestedPlacementRole(imagePlacementRole?.value||currentAssetPlacementRole());
  const address=placementAddress(currentTierIndex(),1);
  const tier=placementRole==='world-map'?0:(REGION_DEFINER?currentTierIndex():clamp(Math.trunc(Number(imageTier.value)||address.tier),0,TIERS.length-1));
  const layer=placementRole==='world-map'?0:clamp(Math.trunc(Number(imageLayer.value)||address.layer),0,9);
  const requestedPoint={x:clamp(Number(imageX.value)||0,0,1),y:clamp(Number(imageY.value)||0,0,1)};
  const placementPoint=placementRole==='world-map'?{x:.5,y:.5}:(LOCAL_DEFINER&&localIsOpen()?constrainLocalPoint(requestedPoint.x,requestedPoint.y):(REGION_DEFINER?constrainRegionPoint(requestedPoint.x,requestedPoint.y):requestedPoint));
  const item={
    id:crypto.randomUUID?.()||String(Date.now()),assetId:null,personalAssetKey:null,name:String(file.name||'Uploaded image').replace(/\.[^.]+$/,''),kind:'image',libraryTile:false,sourceLocked:false,regionOverlay:REGION_DEFINER,regionId:REGION_DEFINER?activeRegionMapId():'',
    placementRole,fullWorld:placementRole==='world-map',
    originalSrc,transparentSrc,transparent:!!imageTransparency.checked,
    x:placementPoint.x,y:placementPoint.y,tier,layer,size:1,rotation:0,opacity:1,committed:false,renderOpacity:1,zoomPassed:false,zoomPassScale:null,node:null
  };
  if(isWorldMapItem(item))removeCustomWorldMap(item);
  const node=document.createElement('img');node.className=`user-image-placement${isWorldMapItem(item)?' full-world-placement':''}`;node.alt=item.name;node.draggable=false;item.node=node;
  node.addEventListener('pointerdown',event=>beginImageDrag(event,item));node.addEventListener('pointermove',moveImageDrag);node.addEventListener('pointerup',endImageDrag);node.addEventListener('pointercancel',endImageDrag);
  userLayers.push(item);mountUserPlacement(item);world.dataset.emptyWorld='false';void primeCollisionMask(originalSrc);if(transparentSrc!==originalSrc)void primeCollisionMask(transparentSrc);updateLayerOrder();refreshUserImage(item);selectUserImage(item);closeImageUpload();keyboardMode='Image';openKeyboard();renderKeyboardTabs();renderKeyboardKeys();applyParallax();scheduleRegionEnhancement(30);
  item.personalUploadPromise=trackPersonalUpload(
    saveFileToPersonalLibrary(file,{category:'Images',folder:'My Images',assetKind:'image',name:item.name})
      .then(asset=>{item.assetId=`private:${asset.key}`;item.personalAssetKey=asset.key;announce(`${item.name} added to My Images.`);return asset})
      .catch(error=>{announce(`${item.name} is placed, but My Images could not save it: ${String(error?.message||error)}`);return null})
  );
  if(isWorldMapItem(item)){
    assetPlacementRole='layer';
    announce(`${item.name} is now the Sea Level World Map at 100% by 100%. Future images and tiles default to adjustable layers.`);
  }else announce(LOCAL_DEFINER&&localIsOpen()
    ?`Image placed at Local Tier ${item.localTier||0}, Local Layer ${item.localLayer||1}; canonical X/Y ${item.x.toFixed(3)}, ${item.y.toFixed(3)} retained.`
    :REGION_DEFINER
    ?`Image placed at World Z ${regionWorldLayer(item)}, Region layer ${regionOverlayLayer(item)}, exact Z ${regionZLabel(item)}.`
    :`Image placed above ${tierLabel(tierByIndex(tier))} as adjustable layer ${layer}.`);
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
function parentTierOffset(tier){
  // The tier reference and all same-tier images must use the exact same
  // camera displacement, never independent per-object parallax.
  if(REGION_DEFINER&&!LOCAL_DEFINER&&regionDeedIsComplete())return{x:0,y:0};
  const key=CANONICAL_PLANE_KEYS[clamp(Math.trunc(Number(tier)||0),0,TIERS.length-1)];
  const plane=planeByKey[key];
  return{x:Number(plane?.dataset.parallaxX)||0,y:Number(plane?.dataset.parallaxY)||0};
}
function applyParallax(){
  const selectionFrozen=REGION_DEFINER&&regionClaimPhase==='select'&&regionSelectionEnabled;
  // RegionDefiner is an orthographic editing view over the chosen parent
  // map, not a second parallax stack. Keep every source plane, lake tile and
  // same-tier object aligned while editing the deed.
  const regionReferenceFrozen=REGION_DEFINER&&!LOCAL_DEFINER&&regionDeedIsComplete();
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
    const px=selectionFrozen||regionReferenceFrozen?0:((-dx*panStrength)+(tiltX*tiltStrength))/Math.max(scale,.00001),py=selectionFrozen||regionReferenceFrozen?0:((-dy*panStrength)+(tiltY*tiltStrength))/Math.max(scale,.00001);
    entry.node.dataset.parallaxX=px.toFixed(4);entry.node.dataset.parallaxY=py.toFixed(4);
    entry.node.style.transform=`translate3d(${px.toFixed(2)}px,${py.toFixed(2)}px,0)`;
  }
  for(const item of userLayers){
    // A new/unsaved placement must stay visible even when its target tier is hidden,
    // otherwise it looks as if upload failed. Canonical lower tiers remain visible
    // as read-only context while Region Definer edits the selected tier.
    const regionTier=currentRegionTierIndex();
    const regionalLayerVisible=!item.canonicalSource||regionSourceLayerVisible(item.tier,item.layer);
    const visible=LOCAL_DEFINER&&localIsOpen()
      ? !!item.localAnchor||(!!item.localOverlay&&String(item.localId||'')===activeLocalMapId())
      : REGION_DEFINER
        ? regionProjectionLoaded
          ?(item.regionOverlay?String(item.regionId||'')===activeRegionMapId():!!item.sourceLocked)
          :(item.canonicalSource?item.tier<=regionTier:item.tier===regionTier)&&regionalLayerVisible
        : (!item.committed||viewerTier==='all'||item.tier===tierByKey(viewerTier).index);
    if(isWorldMapItem(item)){
      item.parallaxX=0;item.parallaxY=0;item.renderOpacity=visible&&!item.zoomPassed?item.opacity:0;refreshUserImage(item);continue;
    }
    if(LOCAL_DEFINER&&localIsOpen()&&item.localAnchor){
      item.parallaxX=0;item.parallaxY=0;item.renderOpacity=item.opacity;refreshUserImage(item);continue;
    }
    const attached=itemParallaxMode(item)==='anchored'&&!LOCAL_DEFINER;
    const reference=attached?parentTierOffset(item.tier):null;
    const depth=LOCAL_DEFINER&&item.localOverlay
      ? Math.max(0,Number(item.localTier)||0)+(clamp(Number(item.localLayer)||1,1,9)/10)
      : item.tier;
    const representationDepth=LOCAL_DEFINER?2:1;
    const panStrength=depth*.022*representationDepth,tiltStrength=depth*.48*representationDepth;
    item.parallaxX=selectionFrozen?0:attached?reference.x:((-dx*panStrength)+(tiltX*tiltStrength))/Math.max(scale,.00001);
    item.parallaxY=selectionFrozen?0:attached?reference.y:((-dy*panStrength)+(tiltY*tiltStrength))/Math.max(scale,.00001);
    item.renderOpacity=visible&&!item.zoomPassed?item.opacity:0;refreshUserImage(item);
  }
}
function updateReadouts(){
  stage.dataset.worldId=WORLD_ID;
  stage.dataset.worldSeed=WORLD_SEED;
  stage.dataset.viewerTier=viewerTier;
  stage.dataset.viewerLayer=String(viewerLayer);
  stage.dataset.representationAngle=String(REPRESENTATION_ANGLE_DEGREES);
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
  world.style.transform=REPRESENTATION_ANGLE_DEGREES>0
    ? `translate3d(${x}px,${y}px,0) scale(${scale}) rotateX(${REPRESENTATION_ANGLE_DEGREES}deg)`
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
  if(LOCAL_DEFINER&&localIsOpen()){fitLocalAnchor(activeLocal);return}
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
function focusNormalizedBounds(bounds={}){
  if(!naturalWidth||!naturalHeight)return false;
  const cx=clamp(Number(bounds.x)||.5,0,1),cy=clamp(Number(bounds.y)||.5,0,1);
  const width=clamp(Number(bounds.width)||1,.0001,1),height=clamp(Number(bounds.height)||1,.0001,1);
  const r=stage.getBoundingClientRect();
  if(r.width<=0||r.height<=0)return false;
  suspendRegionEnhancement();
  const targetScale=Math.min(r.width/(naturalWidth*width),r.height/(naturalHeight*height))*.84;
  scale=clamp(targetScale,Math.max(minScale,MIN_VIEW_SCALE),maxScale);
  x=(r.width/2)-(cx*naturalWidth*scale);
  y=(r.height/2)-(cy*naturalHeight*scale);
  applyTransform();scheduleRegionEnhancement(50);
  return true;
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
  if(LOCAL_DEFINER)return localIsOpen()?((localRegionEditable&&!READ_ONLY)?BASE_KEYBOARD_MODES:['Viewer','Tiers','Select']):(activeRegionMapId()?['Viewer','Tiers','Select']:['Select']);
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
function regionGridExtents(shape=regionGridShape){
  return normalizeRegionGridShape(shape)==='hex'
    ?{width:REGION_GRID_COLUMNS*.75+.25,height:REGION_GRID_ROWS+.5}
    :{width:REGION_GRID_COLUMNS,height:REGION_GRID_ROWS};
}
function regionCellCenter(cell,shape=regionGridShape){
  const row=regionCellRow(cell),column=regionCellColumn(cell),extent=regionGridExtents(shape);
  if(normalizeRegionGridShape(shape)==='hex')
    return{x:(column*.75+.5)/extent.width,y:(row+(column%2)*.5+.5)/extent.height};
  return{x:(column+.5)/extent.width,y:(row+.5)/extent.height};
}
function regionCellFromPoint(x,y,shape=regionGridShape){
  const px=clamp(Number(x)||0,0,1),py=clamp(Number(y)||0,0,1);
  if(normalizeRegionGridShape(shape)!=='hex'){
    const col=clamp(Math.floor(Math.min(px,.999999)*REGION_GRID_COLUMNS),0,REGION_GRID_COLUMNS-1);
    const row=clamp(Math.floor(Math.min(py,.999999)*REGION_GRID_ROWS),0,REGION_GRID_ROWS-1);
    return row*REGION_GRID_COLUMNS+col;
  }
  // Claim hitboxes, displayed cells, deed mask and placement use the same
  // column-staggered flat-top hexes (not the old row-offset approximation).
  let best=0,bestDistance=Infinity;
  for(let cell=0;cell<REGION_GRID_COLUMNS*REGION_GRID_ROWS;cell++){
    const center=regionCellCenter(cell,'hex'),dx=center.x-px,dy=center.y-py,d=dx*dx+dy*dy;
    if(d<bestDistance){bestDistance=d;best=cell}
  }
  return best;
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
function constrainRegionPoint(x,y){
  const point={x:clamp(Number(x)||0,0,1),y:clamp(Number(y)||0,0,1)};
  if(!REGION_DEFINER)return point;
  const allowed=regionActiveCellSet();
  if(!allowed||!allowed.size)return point;
  const cell=regionCellFromPoint(point.x,point.y);
  // Placement inside the deed is continuous. The grid defines ownership only;
  // it must not snap authored cities, labels, sprites, or images to cell centers.
  if(allowed.has(cell))return point;
  return regionCellCenter(nearestAllowedRegionCell(cell,allowed));
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
    const editable=!LOCAL_DEFINER&&ACCESS_MODE==='edit'&&belongsToActiveRegion;
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
function syncRegionReferenceImage(tier,src){
  if(!REGION_DEFINER||!src)return;
  // A late successful database probe must replace BOTH the working plane
  // and its reference copy. Otherwise a stale fallback could cover geography
  // such as lakes even after the canonical world image has loaded.
  for(const entry of regionWorldTierImages){
    if(entry.tier!==tier||entry.src===src)continue;
    entry.src=src;
    entry.node.src=src;
  }
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
      syncRegionReferenceImage(tier,resolved);
      refreshRegionTierPreview();
      return;
    }

    const probe=new Image();
    probe.onload=()=>{
      regionCanonicalTierImages[tier]=resolved;
      syncRegionReferenceImage(tier,resolved);
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
// Claimed children use the exact source-cell projection returned by the
// authority. Unlike the pre-claim preview, this path never mounts parent
// world-tier PNGs or off-deed assets.
async function renderRegionProjection(payload){
  const envelope=payload&&typeof payload==='object'?payload:{};
  const state=envelope.state&&typeof envelope.state==='object'?envelope.state:{};
  if(state.projection!=='region-world-z-v2')throw new Error('Unexpected regional source format');
  const revision=++canonicalHydrationRevision;
  clearRegionWorldSource();
  const projectedId=String(state.regionId||envelope.regionId||REQUESTED_REGION_ID||'');
  const savedDeed=regionCatalog.find(region=>String(region.id||'')===projectedId);
  if(!regionClaimedRegion||regionClaimedRegion.id!==projectedId){
    const deed=savedDeed||{
      id:projectedId,name:'Region',tierIndex:Number(state.parentTierIndex)||0,
      gridShape:state.gridShape||'hex',selectedCells:state.selectedCells||[]
    };
    applyClaimedRegionCrop(deed);
  }
  regionProjectionLoaded=true;
  regionLayerIndex=1;
  viewerLayer=0;
  viewerTier=tierByIndex(clamp(Math.trunc(Number(state.parentTierIndex)||0),0,TIERS.length-1)).key;
  const sourceCells=Array.isArray(state.sourceCells)?state.sourceCells:[];
  const expected=new Set((state.selectedCells||[]).map(Number));
  const parentTier=Number(state.parentTierIndex)||0;
  naturalWidth=Math.max(1,Number(state.sourcePixelWidth)||2508);
  naturalHeight=Math.max(1,Number(state.sourcePixelHeight)||2508);
  regionWorldSourceMeta={
    worldId:String(state.worldId||WORLD_ID),worldName:String(envelope.worldName||WORLD_NAME),
    gridColumns:REGION_GRID_COLUMNS,gridRows:REGION_GRID_ROWS,gridStyle:String(state.gridShape||'hex'),
    planeIndex:parentTier,updatedAtUtc:String(envelope.updatedAtUtc||'')
  };
  // Do not leave the parent PNG in the DOM as a hidden, fetched full-world
  // source. The browser gets selected cells only, and these replace the preview.
  for(const key of CANONICAL_PLANE_KEYS){
    const plane=planeByKey[key];
    layerReady[key]=false;
    plane.removeAttribute('src');
    plane.style.display='none';plane.style.opacity='0';
  }
  regionCanonicalTierImages=[];
  for(let i=userLayers.length-1;i>=0;i--){
    const item=userLayers[i];
    if(!(item.regionOverlay||item.sourceLocked||item.canonicalSource))continue;
    stopSpriteMotion(item);
    item.node?.remove();
    userLayers.splice(i,1);
  }
  selectedImage=null;
  const shape=normalizeRegionGridShape(state.gridShape||'hex');
  const extents=regionGridExtents(shape);
  let indexedCount=0;
  const indexed=Array.isArray(state.sourceTileIndex)?state.sourceTileIndex:[];
  const knownCells=new Set(indexed.filter(raw=>Number(raw.layerOffset||0)===0).map(raw=>Number(raw.cellIndex)));
  const slices=sourceCells.flatMap(cell=>{
    const index=Number(cell.cellIndex);
    if(!expected.has(index))return[];
    const indexedCell=indexed.filter(raw=>Number(raw.cellIndex)===index);
    const staticPattern=String(state.publicTilePattern||'');
    const official=staticPattern&&!knownCells.has(index)?[{
      cellIndex:index,layerOffset:0,id:String(cell.id||''),name:'Locked parent terrain',
      image:staticPattern.replace('{shape}',shape).replace('{cell}',String(index).padStart(3,'0'))
    }]:[];
    return[...official,...indexedCell];
  });
  for(const raw of slices){
    const cell=Number(raw.cellIndex);
    if(!expected.has(cell)||!raw.image)continue;
    const col=cell%REGION_GRID_COLUMNS,row=Math.floor(cell/REGION_GRID_COLUMNS);
    const gx=shape==='hex'?col*.75:col,gy=shape==='hex'?row+(col%2)*.5:row;
    const node=document.createElement('img');
    node.className='region-world-source-tile region-world-source-cell';
    node.src=String(raw.image);
    node.alt='';
    node.draggable=false;
    node.dataset.sourceCellId=String(raw.id||sourceCells.find(c=>Number(c.cellIndex)===cell)?.id||'');
    node.dataset.sourceLocked='true';
    node.dataset.cell=String(cell);
    node.dataset.parentTier=String(parentTier);
    node.dataset.tier=String(parentTier);node.dataset.layer=String(Number(raw.layerOffset)||0);
    node.style.left=`${(gx/extents.width*100).toFixed(5)}%`;
    node.style.top=`${(gy/extents.height*100).toFixed(5)}%`;
    node.style.width=`${(100/extents.width).toFixed(5)}%`;
    node.style.height=`${(100/extents.height).toFixed(5)}%`;
    node.style.zIndex=String((Number(raw.layerOffset)||0)*100);
    node.style.objectFit='fill';
    world.appendChild(node);
    regionWorldSourceTiles.push({node,image:node,tier:parentTier,layer:Number(raw.layerOffset)||0,id:node.dataset.sourceCellId,name:String(raw.name||''),assetKind:'source-cell'});
    indexedCount++;
  }
  // Additional authored world terrain tiles were already filtered by exact
  // source-cell IDs in the database, not by a client-side visibility mask.
  for(const raw of Array.isArray(state.tiles)?state.tiles:[]){
    const node=document.createElement('div'),layer=Number(raw.layerOffset)||0;
    node.className='region-world-source-tile';
    node.dataset.sourceLocked='true';node.dataset.parentTier=String(parentTier);
    node.dataset.tier=String(parentTier);node.dataset.layer=String(layer);
    node.setAttribute('aria-label',String(raw.name||'Locked parent terrain'));
    const zoom=Math.max(Number(raw.placementZoom)||1,1/REGION_GRID_COLUMNS);
    node.style.left=`${(Number(raw.x||0)*100).toFixed(5)}%`;
    node.style.top=`${(Number(raw.y||0)*100).toFixed(5)}%`;
    node.style.width=`${(100/REGION_GRID_COLUMNS/zoom).toFixed(5)}%`;
    node.style.height=`${(100/REGION_GRID_ROWS/zoom).toFixed(5)}%`;
    node.style.zIndex=String(layer*100);
    const frame=document.createElement('span');frame.className='region-world-source-crop';
    const img=document.createElement('img');img.alt='';img.src=String(raw.image||'');
    regionSourceCropStyle(img,raw);frame.appendChild(img);node.appendChild(frame);world.appendChild(node);
    regionWorldSourceTiles.push({node,image:img,tier:parentTier,layer,id:String(raw.id||''),name:String(raw.name||''),assetKind:'parent-tile'});
  }
  regionRasterIndexMissing=!!state.requiresRasterIndex&&indexedCount<expected.size;
  stage.dataset.sourceScope='selected-parent-cells';
  stage.dataset.parentTier=String(parentTier);
  stage.dataset.sourceCellCount=String(expected.size);
  stage.dataset.loadedCellCount=String(indexedCount);
  stage.dataset.rasterIndex=regionRasterIndexMissing?'incomplete':'selected-only';
  if(regionRasterIndexMissing){
    announce('This parent world bitmap needs a source-cell index. Its other territory has not been fetched.');
  }
  const inherited=Array.isArray(state.sourceUserLayers)?state.sourceUserLayers:[];
  const inheritedPending=inherited.map(async raw=>{
    const item=await attachRestoredLayer(raw,{sourceLocked:true,regionOverlay:false,canonicalSource:true});
    if(revision!==canonicalHydrationRevision){discardCanonicalHydrationItem(item);return null}
    updateLayerOrder();applyParallax();return item;
  });
  const owned=(Array.isArray(state.userLayers)?state.userLayers:[])
    .filter(raw=>String(raw?.regionId||'')===projectedId);
  regionPersistenceDbCount=owned.length;
  refreshRegionPersistenceStatus();
  const pending=owned.map(async raw=>{
    const item=await attachRestoredLayer(raw,{sourceLocked:LOCAL_DEFINER||READ_ONLY,regionOverlay:true,canonicalSource:false});
    if(revision!==canonicalHydrationRevision){discardCanonicalHydrationItem(item);return null}
    updateLayerOrder();applyParallax();return item;
  });
  stage.dataset.renderer='region-world-z-v2';
  world.dataset.emptyWorld=regionWorldSourceTiles.length?'false':'true';
  updateTierButton();renderTierMenu();updateLayerOrder();updateRegionWorldSourceVisibility();
  loading.hidden=true;fitClaimedRegion(regionClaimedRegion);
  if(LOCAL_DEFINER)keyboardMode='Select';
  renderKeyboardTabs();renderKeyboardKeys();applyParallax();
  await Promise.all([...inheritedPending,...pending]);
  if(revision!==canonicalHydrationRevision)return;
  updateLayerOrder();applyParallax();ensureActiveRegionOverlaysShown(projectedId);refreshRegionPersistenceStatus();
  if(LOCAL_DEFINER)localRegionSourceReady=true;
  maybeOpenRequestedLocal();
  announce(`${regionClaimedRegion.name} ready. ${expected.size} claimed coordinates from World Tier ${parentTier+1}. ${owned.length} saved regional overlay${owned.length===1?'':'s'} loaded. World Z 0–9 is locked; regional overlays use .01–.09 above each World Z.`);
}
async function renderRegionWorldSource(payload){
  if(!REGION_DEFINER)return;
  const envelope=payload&&typeof payload==='object'?payload:{};
  let snapshot=envelope.state&&typeof envelope.state==='object'?envelope.state:envelope;
  if(snapshot.projection==='region-world-z-v2'){
    await renderRegionProjection(envelope);return;
  }
  // An older pre-claim load must never replace a loaded child projection.
  if(regionProjectionLoaded)return;
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
    if(LOCAL_DEFINER){localRegionSourceReady=true;maybeOpenRequestedLocal()}
  }).catch(error=>{
    if(hydrationRevision!==canonicalHydrationRevision)return;
    stage.dataset.canonicalHydrationError=String(error?.message||error||'unknown error').slice(0,160);
  });
}
function revealCompleteRegionWorldReference(){
  // A newly opened deed should never inherit hidden world layers from an
  // unrelated session. The underlying canonical tier is reference-only.
  for(const layers of regionWorldLayerVisibility){
    layers.clear();
    for(let layer=0;layer<10;layer++)layers.add(layer);
  }
}
function updateRegionWorldSourceVisibility(){
  if(!REGION_DEFINER)return;
  if(LOCAL_DEFINER&&localIsOpen()){
    if(regionWorldSourceOcean)regionWorldSourceOcean.style.opacity='0';
    for(const item of regionWorldTierImages)item.node.style.opacity='0';
    for(const entry of regionWorldSourceTiles)entry.node.style.display='none';
    return;
  }
  if(regionProjectionLoaded){
    const parentTier=Number(regionClaimedRegion?.tierIndex)||0;
    for(const entry of regionWorldSourceTiles){
      entry.node.style.display=regionSourceLayerVisible(parentTier,entry.layer)?'block':'none';
    }
    return;
  }
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
  announce(`${regionGridShape==='hex'?'Hex':'Square'} claim grid selected. Region assets remain free-placement inside the deed.`);
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
  const {x:px,y:py}=regionCellCenter(cell);
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
function retireRegionSelectionOverlay(){
  // A deed's selected cells remain in canonical region metadata / its clip mask,
  // not in a second hit-testable grid above WorldBuilder's assets.
  if(regionSelectionOverlay){
    regionSelectionOverlay.remove();
    regionSelectionOverlay=null;
  }
}
function regionDeedIsComplete(){
  return !!regionClaimedRegion&&(regionClaimPhase==='saved'||regionClaimPhase==='build');
}
function ensureRegionSelectionOverlay(){
  if(!REGION_DEFINER)return null;
  if(LOCAL_DEFINER){
    retireRegionSelectionOverlay();
    return null;
  }
  // Saved regions never instantiate the selection overlay, including after
  // a keyboard change or viewer rerender. Existing deeds wait for catalog load.
  if(regionDeedIsComplete()||(REGION_FLOW==='existing'&&!!pendingClaimedRegionId)){
    retireRegionSelectionOverlay();
    return null;
  }
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
  if(regionDeedIsComplete()){
    retireRegionSelectionOverlay();
    stage.classList.remove('region-crop-preview');
    return;
  }
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
  const extents=regionGridExtents('hex'),cellWidth=100/extents.width,cellHeight=100/extents.height;
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
  const extents=regionGridExtents(region.gridShape);
  regionClaimOutline.style.left=`${(bounds.minX/extents.width)*100}%`;
  regionClaimOutline.style.top=`${(bounds.minY/extents.height)*100}%`;
  regionClaimOutline.style.width=`${(bounds.width/extents.width)*100}%`;
  regionClaimOutline.style.height=`${(bounds.height/extents.height)*100}%`;
  regionClaimOutline.dataset.label=String(region?.name||'YOUR CLAIM').toUpperCase();
}
function clearClaimedRegionCrop(refit=true){
  if(!REGION_DEFINER)return;
  regionClaimedRegion=null;pendingClaimedRegionId='';regionProjectionLoaded=false;
  regionLayerIndex=1;
  syncClaimedRegionOutline(null);
  syncRegionEditLayer();
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
  const extents=regionGridExtents(shape);
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${extents.width} ${extents.height}" preserveAspectRatio="none">${figures.join('')}</svg>`;
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
  const extent=regionGridExtents(shape);
  minX=clamp(minX,0,extent.width);maxX=clamp(maxX,0,extent.width);
  minY=clamp(minY,0,extent.height);maxY=clamp(maxY,0,extent.height);
  return{minX,minY,maxX,maxY,width:Math.max(1,maxX-minX),height:Math.max(1,maxY-minY)};
}

function fitLocalAnchor(local=activeLocal){
  const bounds=localAnchorBounds(local);if(!bounds||!naturalWidth||!naturalHeight)return;
  suspendRegionEnhancement();
  const r=stage.getBoundingClientRect();if(r.width<=0||r.height<=0)return;
  const cropX=bounds.minX*naturalWidth,cropY=bounds.minY*naturalHeight;
  const cropW=Math.max(1,bounds.width*naturalWidth),cropH=Math.max(1,bounds.height*naturalHeight);
  const tiltHeight=cropH*Math.cos(REPRESENTATION_ANGLE_DEGREES*Math.PI/180);
  scale=Math.min(r.width/cropW,r.height/Math.max(tiltHeight,1))*.90;
  scale=clamp(scale,MIN_VIEW_SCALE,Math.max(maxScale,scale));
  const centerX=cropX+cropW/2,centerY=cropY+cropH/2;
  x=fitX=(r.width/2)-(centerX*scale);
  y=fitY=(r.height/2)-(centerY*scale);
  applyTransform();
}
function isolateLocalContext(){
  if(!LOCAL_DEFINER||!localIsOpen())return;
  const anchorId=String(activeLocal?.anchorObjectId||'');
  localAnchorItem=userLayers.find(item=>String(item?.id||'')===anchorId)||localAnchorItem;
  for(const item of userLayers){
    if(!item?.node)continue;
    if(item.localOverlay){
      item.node.hidden=String(item.localId||'')!==activeLocalMapId();
      continue;
    }
    const isAnchor=String(item.id||'')===anchorId;
    item.localAnchor=isAnchor;
    item.node.hidden=!isAnchor;
    if(isAnchor){
      item.sourceLocked=true;
      item.regionAnchorX=Number(item.x)||0;
      item.regionAnchorY=Number(item.y)||0;
      item.regionAnchorSize=Number(item.size)||1;
      item.node.classList.add('local-parent-anchor');
      item.node.dataset.authority='region-parent';
      item.node.dataset.regionTier=String(item.regionTier??0);
      item.node.dataset.regionLayer=String(item.regionLayer??1);
      refreshUserImage(item);
    }
  }
  for(const entry of regionWorldSourceTiles)if(entry?.node)entry.node.hidden=true;
  for(const plane of [surface,highlands,mountains])if(plane)plane.style.visibility='hidden';
  world.style.maskImage='none';world.style.webkitMaskImage='none';
  world.style.maskSize='';world.style.webkitMaskSize='';
  stage.dataset.localContext='asset';
  stage.dataset.localId=activeLocalMapId();
  stage.dataset.localAnchorObjectId=anchorId;
  syncLocalEditLayer();
}
async function enterLocalBuild(local,sourceEnvelope=null){
  if(!LOCAL_DEFINER||!local?.id)return;
  activeLocal=local;
  localTierIndex=0;localLayerIndex=1;
  localCreatePending=false;
  removeAssetResizeOverlay();selectedImage=null;

  // Remove any previously hydrated Local child layers before loading this Local.
  for(let index=userLayers.length-1;index>=0;index--){
    const item=userLayers[index];
    if(!item?.localOverlay)continue;
    stopSpriteMotion(item);item.node?.remove();userLayers.splice(index,1);
  }

  isolateLocalContext();
  const state=sourceEnvelope?.state&&typeof sourceEnvelope.state==='object'?sourceEnvelope.state:null;
  const saved=Array.isArray(state?.userLayers)?state.userLayers:[];
  const sourceWasLocalNormalized=String(state?.coordinateSpace||'')==='local-anchor-normalized-v2';
  localPersistenceDbCount=saved.length;
  for(const raw of saved){
    const canonicalRaw=sourceWasLocalNormalized||String(raw?.localCoordinateSpace||'')==='local-anchor-normalized-v2'
      ?(()=>{
        const point=localPointToWorld(raw?.x,raw?.y,local);
        const bounds=localAnchorBounds(local);
        return{
          ...raw,
          x:point.x,y:point.y,
          size:bounds?Math.max(.05,(Number(raw?.size)||1)*Math.max(bounds.width,.0001)):raw?.size,
          localCoordinateSpace:undefined,localX:undefined,localY:undefined,projectedWorldX:undefined,projectedWorldY:undefined
        };
      })()
      :raw;
    const item=await attachRestoredLayer(canonicalRaw,{
      sourceLocked:READ_ONLY||!localRegionEditable,
      regionOverlay:true,
      localOverlay:true,
      localId:String(local.id)
    });
    if(item)applyLocalAddress(item,item.localTier??0,item.localLayer??1);
  }
  syncLocalEditLayer();
  persistentSave.hidden=READ_ONLY||!localRegionEditable;
  imageUploadToggle.hidden=READ_ONLY||!localRegionEditable;
  keyboardMode='Viewer';
  renderKeyboardTabs();renderKeyboardKeys();updateLayerOrder();applyParallax();
  fitLocalAnchor(local);
  if(keyboard.hidden)openKeyboard();
  announce(`${local.name||'Local'} opened from ${local.anchorName||'the selected Region asset'}. The camera is framed to that Region asset; canonical X/Y are retained and new content adds Local tier/layer depth.`);
}
function fitClaimedRegion(region){
  const bounds=regionClaimBounds(region);if(!bounds||!naturalWidth||!naturalHeight)return;
  suspendRegionEnhancement();
  const extent=regionGridExtents(region.gridShape);
  const r=stage.getBoundingClientRect(),cropX=(bounds.minX/extent.width)*naturalWidth,cropY=(bounds.minY/extent.height)*naturalHeight;
  const cropW=(bounds.width/extent.width)*naturalWidth,cropH=(bounds.height/extent.height)*naturalHeight;
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
  const extent=regionGridExtents(region.gridShape);
  const cropW=(bounds.width/extent.width)*naturalWidth,cropH=(bounds.height/extent.height)*naturalHeight;
  const tiltHeight=cropH*Math.cos(15*Math.PI/180);
  return Math.min(r.width/Math.max(cropW,1),r.height/Math.max(tiltHeight,1))*.92;
}
function syncClaimedRegionContextMask(){
  if(!REGION_DEFINER||!regionClaimedRegion||!regionClaimMaskUrl)return;
  if(LOCAL_DEFINER&&localIsOpen()){
    world.style.maskImage='none';world.style.webkitMaskImage='none';
    world.style.maskSize='';world.style.webkitMaskSize='';
    return;
  }
  const focusScale=claimedRegionFitScale(regionClaimedRegion);
  if(!(focusScale>0))return;
  // A claimed RegionDefiner view is permanently scoped to the deed footprint.
  // Zoom and pan may change representation, but they must never reveal or edit
  // canonical world space outside the claimed region.
  world.style.maskImage=regionClaimMaskUrl;world.style.webkitMaskImage=regionClaimMaskUrl;
  stage.dataset.regionContext='region';stage.dataset.cropMode='visibility-mask';
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
  stage.classList.remove('region-tier-previewing','region-selection-only','region-claim-confirming');
  regionGridShape=normalizeRegionGridShape(region.gridShape||regionGridShape);
  regionLayerIndex=1;
  const savedTier=clamp(Math.trunc(Number(region.tierIndex)||0),0,TIERS.length-1);
  viewerTier=tierByIndex(savedTier).key;viewerLayer=0;
  revealCompleteRegionWorldReference();
  updateTierButton();renderTierMenu();updateRegionWorldSourceVisibility();
  regionCropPreview=false;regionSelectionEnabled=false;
  const editableRegion=ACCESS_MODE==='edit';
  regionClaimPhase=editableRegion?'build':'saved';
  stage.classList.toggle('region-build-mode',editableRegion&&!LOCAL_DEFINER);
  stage.classList.toggle('region-free-placement',editableRegion&&!LOCAL_DEFINER);
  updateTierButton();renderTierMenu();
  retireRegionSelectionOverlay();
  syncClaimedRegionOutline(region);
  updateRegionSelectionOverlay();
  if(editableRegion)keyboardMode=LOCAL_DEFINER?'Select':'Viewer';
  updateLayerOrder();
  clearRegionMask(false);
  stage.classList.add('region-cropped');
  stage.dataset.cropMode='selected-source-cells';
  stage.dataset.regionContext='region';
  requestAnimationFrame(()=>fitClaimedRegion(region));
  if(editableRegion)queueMicrotask(()=>{renderKeyboardTabs();renderKeyboardKeys();if(keyboard.hidden)openKeyboard()});
}
function selectedLocalRegion(){
  if(!regionCatalog.length)return null;
  localRegionPreviewIndex=clamp(Math.trunc(Number(localRegionPreviewIndex)||0),0,regionCatalog.length-1);
  return regionCatalog[localRegionPreviewIndex]||null;
}
function ensureLocalRegionPreview(){
  if(!LOCAL_DEFINER)return null;
  if(localRegionPreview?.isConnected)return localRegionPreview;
  const panel=document.createElement('section');
  panel.className='region-tier-preview local-region-preview';
  panel.hidden=true;
  panel.setAttribute('role','dialog');
  panel.setAttribute('aria-modal','true');
  panel.setAttribute('aria-label','Choose a Region for the Local zone');
  panel.innerHTML=`
    <div class="region-tier-preview-copy">
      <small>LOCAL DEFINER · REGION</small>
      <strong data-local-region-title>SELECT REGION</strong>
      <span data-local-region-help>Choose the Region, then select the asset that becomes the Local zone.</span>
    </div>
    <div class="region-tier-preview-map" aria-hidden="true">
      <div class="local-region-preview-card">
        <small>REGION</small>
        <strong data-local-region-name>LOADING REGIONS…</strong>
        <span data-local-region-meta></span>
        <span data-local-region-authority></span>
      </div>
    </div>
    <div class="region-tier-preview-actions">
      <button type="button" data-local-region-prev aria-label="Previous Region">‹</button>
      <div class="region-tier-preview-dots" data-local-region-dots aria-hidden="true"></div>
      <button type="button" data-local-region-next aria-label="Next Region">›</button>
    </div>
    <button type="button" class="region-tier-preview-select" data-local-region-select>SELECT REGION</button>`;
  stage.appendChild(panel);
  panel.querySelector('[data-local-region-prev]')?.addEventListener('click',()=>stepLocalRegionPreview(-1));
  panel.querySelector('[data-local-region-next]')?.addEventListener('click',()=>stepLocalRegionPreview(1));
  panel.querySelector('[data-local-region-select]')?.addEventListener('click',confirmLocalRegionPreview);
  panel.addEventListener('pointerdown',event=>{
    if(event.target instanceof Element&&event.target.closest('button'))return;
    localRegionPreviewPointer={id:event.pointerId,x:event.clientX,y:event.clientY};
    try{panel.setPointerCapture(event.pointerId)}catch{}
  });
  panel.addEventListener('pointerup',event=>{
    if(!localRegionPreviewPointer||localRegionPreviewPointer.id!==event.pointerId)return;
    const dx=event.clientX-localRegionPreviewPointer.x,dy=event.clientY-localRegionPreviewPointer.y;
    localRegionPreviewPointer=null;
    if(Math.abs(dx)>48&&Math.abs(dx)>Math.abs(dy)*1.15)stepLocalRegionPreview(dx<0?1:-1);
  });
  panel.addEventListener('pointercancel',()=>{localRegionPreviewPointer=null});
  localRegionPreview=panel;
  refreshLocalRegionPreview();
  return panel;
}
function refreshLocalRegionPreview(){
  const panel=ensureLocalRegionPreview();if(!panel)return;
  const region=selectedLocalRegion();
  const title=panel.querySelector('[data-local-region-title]');
  const name=panel.querySelector('[data-local-region-name]');
  const meta=panel.querySelector('[data-local-region-meta]');
  const authority=panel.querySelector('[data-local-region-authority]');
  const dots=panel.querySelector('[data-local-region-dots]');
  const select=panel.querySelector('[data-local-region-select]');
  const prev=panel.querySelector('[data-local-region-prev]');
  const next=panel.querySelector('[data-local-region-next]');
  if(!region){
    if(title)title.textContent='NO REGIONS AVAILABLE';
    if(name)name.textContent='DEFINE A REGION FIRST';
    if(meta)meta.textContent='Local zones are created from assets placed inside Regions.';
    if(authority)authority.textContent='';
    if(dots)dots.innerHTML='';
    if(select){select.disabled=true;select.textContent='NO REGION TO SELECT'}
    if(prev)prev.disabled=true;if(next)next.disabled=true;
    return;
  }
  if(title)title.textContent=String(region.name||'Region').toUpperCase();
  if(name)name.textContent=String(region.name||'Region');
  const cells=Array.isArray(region.selectedCells)?region.selectedCells.length:0;
  if(meta)meta.textContent=`WORLD TIER ${Math.trunc(Number(region.tierIndex)||0)+1} · ${String(region.gridShape||'grid').toUpperCase()} · ${cells} CELLS · ${Number(region.localCount)||0} LOCALS`;
  if(authority)authority.textContent=region.canEdit===false?'VIEW ONLY':'EDITABLE · SELECT AN ASSET NEXT';
  if(dots)dots.innerHTML=regionCatalog.map((item,index)=>`<i class="${index===localRegionPreviewIndex?'active':''}"></i>`).join('');
  if(select){select.disabled=localRegionSelectPending;select.textContent=localRegionSelectPending?'OPENING REGION…':'SELECT REGION'}
  if(prev)prev.disabled=localRegionSelectPending||regionCatalog.length<2;
  if(next)next.disabled=localRegionSelectPending||regionCatalog.length<2;
}
function stepLocalRegionPreview(delta){
  if(!LOCAL_DEFINER||!regionCatalog.length||localRegionSelectPending)return;
  localRegionPreviewIndex=(localRegionPreviewIndex+Number(delta)+regionCatalog.length)%regionCatalog.length;
  refreshLocalRegionPreview();
}
function clearLocalRegionSelection(){
  if(!LOCAL_DEFINER)return;
  activeLocal=null;localAnchorItem=null;localRegionEditable=false;localCreatePending=false;localRegionSourceReady=false;
  deselectUserImage(false);
  for(let index=userLayers.length-1;index>=0;index--){
    const item=userLayers[index];
    if(!item?.regionOverlay||item.localOverlay)continue;
    stopSpriteMotion(item);item.node?.remove();userLayers.splice(index,1);
  }
  clearRegionWorldSource();
  clearClaimedRegionCrop(false);
  regionClaimPhase='idle';
  stage.dataset.localContext='region-selection';
  renderKeyboardTabs();renderKeyboardKeys();
}
function showLocalRegionPreview(resetRegion=false){
  if(!LOCAL_DEFINER||localIsOpen())return;
  if(resetRegion)clearLocalRegionSelection();
  stage.classList.add('region-tier-previewing');
  stage.dataset.localEntry='region-selection';
  const panel=ensureLocalRegionPreview();
  if(panel){panel.hidden=false;refreshLocalRegionPreview()}
  if(!keyboard.hidden)closeKeyboard();
  announce(regionCatalog.length?'Choose a Region. Then Local Definer will show that Region so you can select its asset.':'No Regions are available for this world yet.');
}
function hideLocalRegionPreview(){
  if(localRegionPreview)localRegionPreview.hidden=true;
  stage.classList.remove('region-tier-previewing');
  stage.dataset.localEntry='asset-selection';
}
function confirmLocalRegionPreview(){
  if(!LOCAL_DEFINER||localRegionSelectPending)return;
  const region=selectedLocalRegion();
  if(!region){announce('No Region is available to select.');return}
  localRegionSelectPending=true;refreshLocalRegionPreview();
  if(!postRegionMessage('open-local-region',{regionId:String(region.id||'')})){
    localRegionSelectPending=false;refreshLocalRegionPreview();announce('Local Region selector bridge is unavailable.');return;
  }
  announce(`Opening ${region.name||'Region'} for Local asset selection.`);
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
  stage.classList.add('region-tier-previewing');stage.classList.remove('region-selection-only','region-build-mode','region-claim-confirming');
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
  stage.classList.add('region-selection-only');stage.classList.remove('region-build-mode','region-claim-confirming');
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
  stage.classList.add('region-selection-only','region-claim-confirming');
  updateRegionSelectionOverlay();
  applyRegionMask(preview,'selection-preview',false);
  renderKeyboardKeys();
  announce(`Crop preview ready for ${regionSelectedCells.size} selected ${regionGridShape} tile${regionSelectedCells.size===1?'':'s'}. Name this regional map, then save it.`);
}
function returnToRegionSelection(){
  if(!REGION_DEFINER)return;
  clearRegionMask(false);
  regionClaimPhase='select';regionCropPreview=false;regionSelectionEnabled=true;stage.classList.add('region-selection-only');stage.classList.remove('region-claim-confirming');
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
  if(!name){announce('Name the region before claiming the deed.');return}
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
      toolKey('BACK','edit selected tiles',returnToRegionSelection),
      toolKey(regionCreatePending?'CLAIMING…':'CLAIM DEED',CLAIM_ONLY?'submit deed to GM for approval':'claim selected region',createRegionDefinition,READ_ONLY||regionCreatePending||!regionSelectedCells.size)
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
    readoutKey(String(region?.name||'REGION').toUpperCase(),'claimed regional map'),
    readoutKey(`TIER ${Math.trunc(Number(region?.tierIndex)||currentRegionTierIndex())+1}`,tierLabel(tierByIndex(Math.trunc(Number(region?.tierIndex)||currentRegionTierIndex())))),
    readoutKey(normalizeRegionGridShape(region?.gridShape||regionGridShape).toUpperCase(),'claim grid · placement free'),
    readoutKey(`${Array.isArray(region?.selectedCells)?region.selectedCells.length:0} TILES`,'full regional map')
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
    if(regionProjectionLoaded){
      loading.hidden=true;
      announce('The loaded regional source remains available. A background database refresh failed and can be retried.');
      return;
    }
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
  if(data.type==='local-catalog'){
    localCatalog=Array.isArray(data.locals)?data.locals:[];
    renderKeyboardKeys();
    maybeOpenRequestedLocal();
    return;
  }
  if(data.type==='local-catalog-error'){
    announce(String(data.message||'Local catalog is unavailable.'));
    return;
  }
  if(data.type==='local-region-opened'){
    localRegionSelectPending=false;
    const region=data.region||null;
    if(!region?.id){
      refreshLocalRegionPreview();announce('The selected Region could not be opened.');return;
    }
    localRegionEditable=data.canEdit===true;
    localCatalog=Array.isArray(data.locals)?data.locals:[];
    pendingClaimedRegionId=String(region.id);
    regionClaimedRegion=null;
    regionProjectionLoaded=false;
    localRegionSourceReady=false;
    hideLocalRegionPreview();
    if(data.worldSource)await renderRegionWorldSource(data.worldSource);
    else{refreshLocalRegionPreview();announce('The selected Region map is unavailable.');return}
    keyboardMode='Select';renderKeyboardTabs();renderKeyboardKeys();
    if(keyboard.hidden)openKeyboard();
    announce(`${region.name||'Region'} selected. Now select the Region asset that becomes the Local zone.`);
    return;
  }
  if(data.type==='local-created'){
    localCreatePending=false;
    const local=data.local||{};
    if(local?.id)localCatalog=[...localCatalog.filter(item=>String(item?.id||'')!==String(local.id)),local];
    await enterLocalBuild(local,data.localSource||null);
    return;
  }
  if(data.type==='local-opened'){
    localCreatePending=false;
    requestedLocalOpenPending=false;
    const localId=String(data.localId||'');
    const local=localCatalog.find(item=>String(item?.id||'')===localId);
    if(local)await enterLocalBuild(local,data.localSource||null);
    else{renderKeyboardKeys();announce('The selected Local could not be matched to the Region catalog.');}
    return;
  }
  if(data.type==='catalog'){
    regionCatalog=Array.isArray(data.regions)?data.regions:[];
    if(LOCAL_DEFINER&&!pendingClaimedRegionId&&!regionClaimedRegion){
      localRegionPreviewIndex=clamp(localRegionPreviewIndex,0,Math.max(0,regionCatalog.length-1));
      showLocalRegionPreview(false);
      renderKeyboardKeys();
      return;
    }
    if(pendingClaimedRegionId&&!regionClaimedRegion){
      const claimed=regionCatalog.find(region=>String(region?.id||'')===pendingClaimedRegionId);
      if(claimed){
        if(LOCAL_DEFINER)localRegionEditable=claimed.canEdit===true;
        applyClaimedRegionCrop(claimed);
      }
    }else if(regionClaimedRegion){
      const canonical=regionCatalog.find(region=>String(region?.id||'')===String(regionClaimedRegion.id||''));
      if(canonical){
        if(LOCAL_DEFINER)localRegionEditable=canonical.canEdit===true;
        regionClaimedRegion=canonical;syncClaimedRegionOutline(canonical);
      }
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
    regionSelectedCells.clear();updateRegionSelectionOverlay();
    stage.classList.remove('region-claim-confirming');
    stage.dataset.regionEntry='editor';
    await persistRegionClaimWorkspace();
    if(data.worldSource)await renderRegionWorldSource(data.worldSource);
    keyboardMode='Viewer';renderKeyboardTabs();renderKeyboardKeys();
    if(keyboard.hidden)openKeyboard();
    announce(`${savedName} claimed. Region editing is open with only the deed footprint visible; the underlying canonical world map remains unchanged.`);return;
  }
  if(data.type==='map-local-saved'||data.type==='map-local-save-error'){
    const requestId=String(data.requestId||''),waiter=localMapSaveWaiters.get(requestId);
    if(!waiter)return;
    clearTimeout(waiter.timeout);localMapSaveWaiters.delete(requestId);
    if(data.type==='map-local-saved'&&data.result?.success!==false){
      const persisted=new Set((Array.isArray(data.persistedIds)?data.persistedIds:[]).map(String));
      const missing=(waiter.expectedIds||[]).filter(id=>!persisted.has(String(id)));
      const readbackLocalId=String(data.localId||data.result?.localId||'');
      const sameLocal=!readbackLocalId||readbackLocalId===String(waiter.localId||'');
      const countMatches=persisted.size===Number(waiter.expectedCount||0);
      if(data.verified===true&&sameLocal&&countMatches&&!missing.length){
        waiter.resolve({verified:true,result:data.result,persistedIds:[...persisted]});
      }else{
        waiter.reject(new Error(missing.length
          ?`Local database verification is missing ${missing.length} saved object${missing.length===1?'':'s'}.`
          :!sameLocal
            ?'Local database readback returned a different Local.'
            :!countMatches
              ?'Local database verification count did not match the saved payload.'
              :'Local database readback could not verify the saved objects.'));
      }
    }else waiter.reject(new Error(String(data.message||'Local map database save failed.')));
    return;
  }
  if(data.type==='map-region-saved'||data.type==='map-region-save-error'){
    const requestId=String(data.requestId||''),waiter=regionMapSaveWaiters.get(requestId);
    if(!waiter)return;
    clearTimeout(waiter.timeout);regionMapSaveWaiters.delete(requestId);
    if(data.type==='map-region-saved'&&data.result?.success!==false){
      const persisted=new Set((Array.isArray(data.persistedIds)?data.persistedIds:[]).map(String));
      const missing=(waiter.expectedIds||[]).filter(id=>!persisted.has(String(id)));
      const readbackRegionId=String(data.regionId||data.result?.regionId||'');
      const sameRegion=!readbackRegionId||readbackRegionId===String(waiter.regionId||'');
      const countMatches=persisted.size===Number(waiter.expectedCount||0);
      if(data.verified===true&&sameRegion&&countMatches&&!missing.length){
        waiter.resolve({verified:true,result:data.result,persistedIds:[...persisted]});
      }else{
        waiter.reject(new Error(missing.length
          ? `Region database verification is missing ${missing.length} saved object${missing.length===1?'':'s'}.`
          :!sameRegion
            ?'Region database readback returned a different deed.'
            :!countMatches
              ?`Region database readback count ${persisted.size} did not match save count ${waiter.expectedCount||0}.`
              :'Region database verification did not confirm the save.'));
      }
    }else waiter.reject(new Error(String(data.message||'Canonical world map save failed.')));
    return;
  }
  if(data.type==='claim-requested'){
    regionCreatePending=false;
    const result=data.result||{};
    if(result.success){
      regionClaimPhase='requested';regionCropPreview=false;regionSelectionEnabled=false;stage.classList.remove('region-claim-confirming');updateRegionSelectionOverlay();renderKeyboardKeys();
      announce(String(result.message||'Claim request sent to the GM. No build authority has been granted yet.'));
    }else{
      renderKeyboardKeys();announce(String(result.message||'The claim request was not accepted. Nothing was granted.'));
    }
    return;
  }
  if(data.type==='error'){
    regionCreatePending=false;
    requestedLocalOpenPending=false;
    if(localRegionSelectPending){localRegionSelectPending=false;refreshLocalRegionPreview()}
    renderKeyboardKeys();announce(String(data.message||'Region operation failed.'));
  }
}
if(REGION_DEFINER){
  window.addEventListener('message',handleRegionHostMessage);
  // Build the tier chooser immediately from the canonical/base tier sources. The
  // database message may refine those images/layers later, but it must not gate
  // the first visible step of the new-region workflow.
  if(!LOCAL_DEFINER&&REGION_FLOW==='new'&&!READ_ONLY)showRegionTierPreview();
  queueMicrotask(()=>{ensureRegionSelectionOverlay();postRegionMessage('ready')});
}else if(LIVE_WORLDBUILDER&&window.parent!==window){
  window.addEventListener('message',handleWorldBuilderHostMessage);
  queueMicrotask(()=>postWorldBuilderHostMessage('ready'));
}
function tierDisplay(index){const tier=tierByIndex(clamp(Math.trunc(Number(index)||0),0,TIERS.length-1));return{number:tier.index+1,label:tierLabel(tier)}}
function layerDisplay(index){return clamp(Math.trunc(Number(index)||0),0,9)+1}
function selectedPositionSummary(item){
  if(!item)return{tier:1,tierLabel:tierLabel(TIERS[0]),layer:1,worldZ:0,regionTier:0,regionLayer:1,localTier:0,localLayer:0,instanceTier:0,instanceLayer:0,z:'0.01',x:'0.000',y:'0.000'};
  const tier=tierDisplay(item.tier);
  if(REGION_DEFINER&&regionDeedIsComplete()){
    const address=nestedVerticalAddress(item),worldZ=address.worldLayer,regionLayer=address.regionLayer;
    return{tier:tier.number,tierLabel:tier.label,layer:worldZ+1,worldZ,regionTier:address.regionTier,regionLayer,localTier:address.localTier,localLayer:address.localLayer,instanceTier:address.instanceTier,instanceLayer:address.instanceLayer,z:regionZLabel(worldZ,regionLayer),x:(Number(item.x)||0).toFixed(3),y:(Number(item.y)||0).toFixed(3)};
  }
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
function personalHydrationDelay(attempt){
  return [0,120,350,800,1600,3000,5000][clamp(Math.trunc(Number(attempt)||0),0,6)];
}
async function resolvePersonalAssetSource(key,fallback='',attempts=3){
  const stable=String(key||'').trim();
  if(!stable)return String(fallback||'');
  for(let attempt=0;attempt<Math.max(1,attempts);attempt++){
    const wait=personalHydrationDelay(attempt);
    if(wait)await new Promise(resolve=>setTimeout(resolve,wait));
    try{
      const url=await personalDownloadUrl(stable);
      if(url)return url;
    }catch{}
  }
  return String(fallback||'');
}
function schedulePersonalAssetHydration(item,attempt=0){
  if(!item?.personalAssetKey||!item?.node?.isConnected||attempt>6)return;
  if(item.personalHydrationTimer)return;
  item.node.dataset.assetPending='true';
  const wait=Math.max(120,personalHydrationDelay(attempt+1));
  item.personalHydrationTimer=setTimeout(async()=>{
    item.personalHydrationTimer=0;
    if(!item?.node?.isConnected)return;
    try{
      const fresh=await personalDownloadUrl(item.personalAssetKey);
      if(fresh){
        item.originalSrc=fresh;
        if(item.kind==='sprite'){
          item.transparentSrc=fresh;
          if(item.spritePages?.length){
            const refreshed=[];
            for(let index=0;index<item.spritePages.length;index++){
              const page=item.spritePages[index],key=String(page.personalAssetKey||'').trim();
              const sheetSrc=key?await resolvePersonalAssetSource(key,page.sheetSrc||'',1):String(page.sheetSrc||'');
              if(sheetSrc)refreshed.push(normalizedSpritePage({...page,sheetSrc},index));
            }
            if(refreshed.length){
              item.spritePages=refreshed;
              item.spriteSheetSrc=refreshed[0].sheetSrc;
              const frames=await extractSpriteChainFrames(refreshed,{motionOnly:item.spriteMotionOnly===true}).catch(()=>[]);
              if(frames.length){item.frameSources=frames;item.spriteFrameCount=frames.length;item.currentFrame=0}
            }
          }else{
            item.spriteSheetSrc=fresh;
            const frames=await extractSpriteFrames(fresh,{
              columns:item.spriteColumns||1,rows:item.spriteRows||1,frameCount:item.spriteFrameCount||1,
              sourceWidth:item.spriteSourceWidth||0,sourceHeight:item.spriteSourceHeight||0,
              cropX:item.spriteCropX||0,cropY:item.spriteCropY||0,cropWidth:item.spriteCropWidth||0,cropHeight:item.spriteCropHeight||0,
              whiteTransparent:item.spriteWhiteTransparent!==false,motionOnly:item.spriteMotionOnly===true
            }).catch(()=>[]);
            if(frames.length){item.frameSources=frames;item.currentFrame=0}
          }
        }else{
          item.transparentSrc=await preparedImageSource(fresh,{transparent:!!item.transparent,alphaCrop:item.alphaCrop,alphaComponentSeed:item.alphaComponentSeed});
        }
        item.renderedSrc='';
        item.node.dataset.assetPending='false';
        item.node.style.visibility='';
        refreshUserImage(item);applyParallax();scheduleRegionEnhancement(30);refreshRegionPersistenceStatus();
        return;
      }
    }catch{}
    refreshRegionPersistenceStatus();
    schedulePersonalAssetHydration(item,attempt+1);
  },wait);
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
    whiteTransparent:!!personalEntryValue(entry,'WhiteTransparent',false),motionOnly:!!personalEntryValue(entry,'MotionOnly',false),
    chainId:String(personalEntryValue(entry,'ChainId','')),
    chainIndex:Math.max(0,Math.trunc(Number(personalEntryValue(entry,'ChainIndex',0))||0)),
    chainLength:Math.max(1,Math.trunc(Number(personalEntryValue(entry,'ChainLength',1))||1))
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
    WhiteTransparent:!!metadata.whiteTransparent,MotionOnly:!!metadata.motionOnly,
    ChainId:String(metadata.chainId||''),ChainIndex:Math.max(0,Math.trunc(Number(metadata.chainIndex)||0)),ChainLength:Math.max(1,Math.trunc(Number(metadata.chainLength)||1))
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
    cropWidth:item.spriteCropWidth||0,cropHeight:item.spriteCropHeight||0,whiteTransparent:item.spriteWhiteTransparent!==false,motionOnly:!!item.spriteMotionOnly
  });
  item.assetId=`private:${asset.key}`;item.personalAssetKey=asset.key;
  announce(`${item.name||'Saved upload'} migrated into ${folder}.`);
  return asset;
}
function personalAssetsFor(type){
  if(type==='Sprites')return personalAssets.filter(asset=>(asset.assetKind==='sprite'||asset.category==='Sprites')&&(!asset.chainId||asset.chainIndex===0));
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
  const placementRole=currentAssetPlacementRole(),rawPoint=viewerCenterPosition(),point=REGION_DEFINER?constrainRegionPoint(rawPoint.x,rawPoint.y):rawPoint,address=placementAddress(currentTierIndex(),1);
  const item={
    id:`private-image:${crypto.randomUUID?.()||Date.now()}`,assetId:`private:${asset.key}`,personalAssetKey:asset.key,name:asset.name,kind:'image',libraryTile:false,sourceLocked:false,regionOverlay:REGION_DEFINER,regionId:REGION_DEFINER?activeRegionMapId():'',
    placementRole,fullWorld:placementRole==='world-map',
    originalSrc:asset.url,transparentSrc:asset.url,transparent:false,x:placementRole==='world-map'?.5:point.x,y:placementRole==='world-map'?.5:point.y,tier:placementRole==='world-map'?0:address.tier,layer:placementRole==='world-map'?0:address.layer,
    size:1,rotation:0,opacity:1,committed:false,renderOpacity:1,zoomPassed:false,zoomPassScale:null,node:null
  };
  if(isWorldMapItem(item))removeCustomWorldMap(item);
  const node=document.createElement('img');node.className=`user-image-placement${isWorldMapItem(item)?' full-world-placement':''}`;node.alt=item.name;node.draggable=false;item.node=node;
  node.addEventListener('pointerdown',event=>beginImageDrag(event,item));node.addEventListener('pointermove',moveImageDrag);node.addEventListener('pointerup',endImageDrag);node.addEventListener('pointercancel',endImageDrag);
  userLayers.push(item);mountUserPlacement(item);world.dataset.emptyWorld='false';void primeCollisionMask(asset.url);updateLayerOrder();refreshUserImage(item);selectUserImage(item);
  if(REGION_DEFINER)refreshRegionPersistenceStatus();
  personalFolderType=null;keyboardMode='Image';openKeyboard();renderKeyboardTabs();renderKeyboardKeys();applyParallax();scheduleRegionEnhancement(30);
  if(isWorldMapItem(item)){assetPlacementRole='layer';announce(`${item.name} is now the Sea Level World Map at 100% by 100%.`)}
  else announce(`${item.name} placed from My Images as an adjustable layer. Save commits this instance.`);
}
async function placePersonalSprite(asset){
  if(READ_ONLY){announce('World reference mode is view only.');return;}
  if(!asset?.url)return;
  const chain=asset.chainId
    ?personalAssets.filter(entry=>(entry.assetKind==='sprite'||entry.category==='Sprites')&&entry.chainId===asset.chainId)
      .sort((a,b)=>a.chainIndex-b.chainIndex)
    :[asset];
  const pages=chain.map((entry,index)=>({
    index,name:entry.name,sheetSrc:entry.url,personalAssetKey:entry.key,assetId:`private:${entry.key}`,
    columns:entry.columns,rows:entry.rows,frameCount:entry.frameCount,sourceWidth:entry.sourceWidth,sourceHeight:entry.sourceHeight,
    cropX:entry.cropX,cropY:entry.cropY,cropWidth:entry.cropWidth,cropHeight:entry.cropHeight,whiteTransparent:entry.whiteTransparent
  }));
  const first=chain[0]||asset;
  const item=await placeSpriteDefinition({
    id:`private-sprite:${crypto.randomUUID?.()||Date.now()}`,assetId:`private:${first.key}`,
    name:asset.chainId?`${first.name} chain`:first.name,pages,chainId:asset.chainId||'',
    columns:first.columns,rows:first.rows,frameCount:first.frameCount,fps:first.fps||6,
    whiteTransparent:first.whiteTransparent,motionOnly:first.motionOnly
  });
  item.personalAssetKey=first.key;
  item.spriteChainId=asset.chainId||'';
  item.spritePages.forEach((page,index)=>{
    const entry=chain[index];
    if(entry){page.personalAssetKey=entry.key;page.assetId=`private:${entry.key}`}
  });
  personalFolderType=null;
  announce(asset.chainId
    ?`${item.name} placed from My Sprites with ${pages.length} chained pages / ${item.frameSources.length} frames.`
    :`${item.name} placed from My Sprites.`);
  return item;
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
  const label=document.createElement('small');label.textContent=asset.chainId&&asset.chainLength>1?`${asset.name} · ${asset.chainLength} pages`:asset.name;button.append(image,label);
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
  const placementRole=currentAssetPlacementRole(),rawPoint=viewerCenterPosition(),point=REGION_DEFINER?constrainRegionPoint(rawPoint.x,rawPoint.y):rawPoint,address=placementAddress(currentTierIndex(),1),item={
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
  userLayers.push(item);mountUserPlacement(item);world.dataset.emptyWorld='false';void primeCollisionMask(asset.image);updateLayerOrder();refreshUserImage(item);selectUserImage(item);
  keyboardMode='Tiles';openKeyboard();renderKeyboardTabs();renderKeyboardKeys();applyParallax();scheduleRegionEnhancement(30);
  if(isWorldMapItem(item)){assetPlacementRole='layer';announce(`${asset.name} is now the Sea Level World Map at 100% by 100%. Future images and tiles default to adjustable layers.`)}
  else announce(REGION_DEFINER?`${asset.name} placed inside ${regionClaimedRegion?.name||'the claimed region'} with free placement inside the deed.`:`${asset.name} placed at the viewer center as an adjustable layer above Sea Level.`);
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
function fitSelectedAssetToDeed(item=selectedImage){
  if(!REGION_DEFINER||!regionClaimedRegion||!item||item.sourceLocked||isWorldMapItem(item))return false;
  const bounds=regionClaimBounds(regionClaimedRegion);if(!bounds)return false;
  const extent=regionGridExtents(regionClaimedRegion.gridShape);
  const claimW=bounds.width/Math.max(extent.width,.00001),claimH=bounds.height/Math.max(extent.height,.00001);
  const aspect=Math.max(stableAssetAspect(item),.00001);
  const sizeByWidth=claimW/.12,sizeByHeight=(claimH*aspect)/.12;
  item.x=(bounds.minX+(bounds.width/2))/extent.width;
  item.y=(bounds.minY+(bounds.height/2))/extent.height;
  item.rotation=0;
  applySelectedSize(item,Math.min(sizeByWidth,sizeByHeight));
  if(item.kind==='label')refreshUserLabel(item);else refreshUserImage(item);
  refreshAssetResizeOverlay(item);applyParallax();
  announce(`${item.name||'Asset'} fitted to the claimed deed bounds.`);
  return true;
}
async function rebuildSelectedSpriteMotionOnly(enabled){
  const item=selectedImage;
  if(!item||item.kind!=='sprite'||(!item.spritePages?.length&&!item.spriteSheetSrc)){announce('Select a sprite with its source page(s) available.');return false}
  const wasPlaying=item.playing;stopSpriteMotion(item);
  item.spriteMotionOnly=!!enabled;
  announce(item.spriteMotionOnly?'Building motion-only sprite chain…':'Restoring full sprite chain…');
  try{
    const pages=item.spritePages?.length?item.spritePages:[normalizedSpritePage({
      name:item.name||'Sprite page 1',sheetSrc:item.spriteSheetSrc,personalAssetKey:item.personalAssetKey||null,assetId:item.assetId||null,
      columns:item.spriteColumns||1,rows:item.spriteRows||1,frameCount:item.spriteFrameCount||1,
      sourceWidth:item.spriteSourceWidth||0,sourceHeight:item.spriteSourceHeight||0,
      cropX:item.spriteCropX||0,cropY:item.spriteCropY||0,cropWidth:item.spriteCropWidth||0,cropHeight:item.spriteCropHeight||0,
      whiteTransparent:item.spriteWhiteTransparent!==false
    },0)];
    const frames=await extractSpriteChainFrames(pages,{motionOnly:item.spriteMotionOnly});
    if(!frames.length)throw new Error('No sprite frames were produced.');
    item.frameSources=frames;item.spriteFrameCount=frames.length;item.currentFrame=0;item.spriteReady=true;
    item.originalSrc=frames[0];item.transparentSrc=frames[0];item.renderedSrc='';
    refreshUserImage(item);refreshAssetResizeOverlay(item);
    if(wasPlaying&&item.committed)startSpriteMotion(item);
    renderKeyboardKeys();
    announce(item.spriteMotionOnly?'Motion-only overlay ready. Static frame content is transparent.':'Full sprite frames restored.');
    return true;
  }catch(error){
    item.spriteMotionOnly=!enabled;
    if(wasPlaying&&item.committed)startSpriteMotion(item);
    announce(`Sprite rebuild failed: ${String(error?.message||error||'unknown error')}`);
    return false;
  }
}
function spriteLibraryFolders(){return[...new Set(spriteCatalog.map(asset=>asset.folder).filter(Boolean))].sort((a,b)=>a.localeCompare(b))}
function currentSpriteLibraryAssets(){return spriteLibraryFolder?spriteCatalog.filter(asset=>asset.folder===spriteLibraryFolder):[]}
function spriteLibraryPageCount(){return Math.max(1,Math.ceil(currentSpriteLibraryAssets().length/SPRITE_LIBRARY_PAGE_SIZE))}
function spriteLibraryPageAssets(){spriteLibraryPage=clamp(spriteLibraryPage,0,spriteLibraryPageCount()-1);const start=spriteLibraryPage*SPRITE_LIBRARY_PAGE_SIZE;return currentSpriteLibraryAssets().slice(start,start+SPRITE_LIBRARY_PAGE_SIZE)}
function normalizedSpritePage(definition,index=0){
  const columns=clamp(Math.trunc(Number(definition.columns)||1),1,32);
  const rows=clamp(Math.trunc(Number(definition.rows)||1),1,32);
  return{
    index,
    sheetSrc:String(definition.sheetSrc||''),
    personalAssetKey:String(definition.personalAssetKey||'')||null,
    assetId:definition.assetId||null,
    name:String(definition.name||`Sprite page ${index+1}`),
    columns,rows,
    frameCount:clamp(Math.trunc(Number(definition.frameCount)||columns*rows),1,columns*rows),
    sourceWidth:Number(definition.sourceWidth)||0,sourceHeight:Number(definition.sourceHeight)||0,
    cropX:Number(definition.cropX)||0,cropY:Number(definition.cropY)||0,
    cropWidth:Number(definition.cropWidth)||0,cropHeight:Number(definition.cropHeight)||0,
    whiteTransparent:definition.whiteTransparent!==false
  };
}
function normalizedSpritePages(definition){
  const supplied=Array.isArray(definition?.pages)&&definition.pages.length?definition.pages:[definition];
  return supplied.map((page,index)=>normalizedSpritePage({...definition,...page},index)).filter(page=>page.sheetSrc||page.personalAssetKey);
}
async function spritePageSource(page){
  if(page.personalAssetKey)return resolvePersonalAssetSource(page.personalAssetKey,page.sheetSrc||'');
  return String(page.sheetSrc||'');
}
async function extractSpriteChainFrames(pages,{motionOnly=false}={}){
  const all=[];
  for(const page of pages){
    const src=await spritePageSource(page);
    if(!src)continue;
    const frames=await extractSpriteFrames(src,{
      columns:page.columns,rows:page.rows,frameCount:page.frameCount,
      sourceWidth:page.sourceWidth,sourceHeight:page.sourceHeight,
      cropX:page.cropX,cropY:page.cropY,cropWidth:page.cropWidth,cropHeight:page.cropHeight,
      whiteTransparent:page.whiteTransparent!==false,motionOnly
    });
    all.push(...frames);
  }
  return all;
}
async function appendSpriteChainPages(item,pages){
  if(!item||item.kind!=='sprite')throw new Error('Select a sprite before adding pages.');
  const normalized=pages.map((page,index)=>normalizedSpritePage(page,(item.spritePages?.length||0)+index));
  const frames=await extractSpriteChainFrames(normalized,{motionOnly:!!item.spriteMotionOnly});
  if(!frames.length)throw new Error('No frames were found in the added sprite pages.');
  item.spritePages=[...(item.spritePages||[]),...normalized].map((page,index)=>({...page,index}));
  item.frameSources=[...(item.frameSources||[]),...frames];
  item.spriteFrameCount=item.frameSources.length;
  item.currentFrame=clamp(Number(item.currentFrame)||0,0,Math.max(0,item.frameSources.length-1));
  item.committed=false;
  refreshUserImage(item);renderKeyboardKeys();
  announce(`${normalized.length} sprite page${normalized.length===1?'':'s'} added. Chain now has ${item.spritePages.length} pages / ${item.frameSources.length} frames. Save to commit it.`);
  return normalized;
}
async function placeSpriteDefinition(definition){
  if(READ_ONLY)throw new Error('World reference mode is view only.');
  const point=viewerCenterPosition(),address=placementAddress(currentTierIndex(),1);
  const pages=normalizedSpritePages(definition);
  if(!pages.length)throw new Error('Sprite chain has no pages.');
  announce(`Preparing ${definition.motionOnly===true?'motion-only ':''}${pages.length}-page sprite chain for ${definition.name||'sprite'}.`);
  const preparedFrames=definition.motionOnly===true?await extractSpriteChainFrames(pages,{motionOnly:true}):null;
  const firstPage=pages[0],firstPageSrc=await spritePageSource(firstPage);
  const firstFrame=preparedFrames?.[0]||await extractSpriteFrame(firstPageSrc,{
    columns:firstPage.columns,rows:firstPage.rows,frameCount:firstPage.frameCount,
    sourceWidth:firstPage.sourceWidth,sourceHeight:firstPage.sourceHeight,cropX:firstPage.cropX,cropY:firstPage.cropY,
    cropWidth:firstPage.cropWidth,cropHeight:firstPage.cropHeight,whiteTransparent:firstPage.whiteTransparent
  },0);
  const item={
    id:definition.id||crypto.randomUUID?.()||String(Date.now()),assetId:definition.assetId||null,name:definition.name||'Sprite',kind:'sprite',libraryTile:false,sourceLocked:false,regionOverlay:REGION_DEFINER,regionId:REGION_DEFINER?activeRegionMapId():'',spriteChainId:String(definition.chainId||''),
    spritePages:pages,spriteSheetSrc:firstPageSrc,spriteColumns:firstPage.columns,spriteRows:firstPage.rows,spriteFrameCount:preparedFrames?.length||pages.reduce((sum,page)=>sum+page.frameCount,0),spriteFps:clamp(Number(definition.fps)||6,1,60),
    spriteSourceWidth:firstPage.sourceWidth||null,spriteSourceHeight:firstPage.sourceHeight||null,spriteCropX:firstPage.cropX||0,spriteCropY:firstPage.cropY||0,
    spriteCropWidth:firstPage.cropWidth||null,spriteCropHeight:firstPage.cropHeight||null,spriteWhiteTransparent:firstPage.whiteTransparent!==false,spriteMotionOnly:definition.motionOnly===true,
    frameSources:preparedFrames||[firstFrame],currentFrame:0,playing:false,spriteReady:!!preparedFrames,originalSrc:firstFrame,transparentSrc:firstFrame,transparent:true,
    x:point.x,y:point.y,tier:address.tier,layer:address.layer,size:1,rotation:0,opacity:1,committed:false,renderOpacity:1,zoomPassed:false,zoomPassScale:null,node:null
  };
  const node=document.createElement('img');node.className='user-image-placement sprite-placement';node.alt=item.name;node.draggable=false;item.node=node;
  node.addEventListener('pointerdown',event=>beginImageDrag(event,item));node.addEventListener('pointermove',moveImageDrag);node.addEventListener('pointerup',endImageDrag);node.addEventListener('pointercancel',endImageDrag);
  userLayers.push(item);mountUserPlacement(item);void primeCollisionMask(firstFrame);updateLayerOrder();refreshUserImage(item);selectUserImage(item);
  keyboardMode='Sprites';openKeyboard();renderKeyboardTabs();renderKeyboardKeys();applyParallax();scheduleRegionEnhancement(30);
  announce(`${item.name} placed using frame 1. It stays above the map while positioning; Save commits it to Tier ${selectedPositionSummary(item).tier}, Layer ${selectedPositionSummary(item).layer} and begins motion.`);

  item.spriteReadyPromise=(preparedFrames?Promise.resolve(preparedFrames):extractSpriteChainFrames(pages,{motionOnly:false})).then(frames=>{
    if(!item.node?.isConnected||!frames.length)return item;
    item.frameSources=frames;item.spriteFrameCount=frames.length;item.spriteReady=true;item.currentFrame=0;
    item.originalSrc=frames[0];item.transparentSrc=frames[0];refreshUserImage(item);
    frames.forEach(frame=>void primeCollisionMask(frame));
    if(item.committed&&frames.length>1)startSpriteMotion(item);
    announce(`${item.name} sprite chain ready with ${item.spritePages.length} page${item.spritePages.length===1?'':'s'} / ${frames.length} frames.`);
    return item;
  }).catch(error=>{
    item.spriteReady=false;item.spriteLoadError=String(error?.message||error||'frame preparation failed');
    announce(`${item.name} was placed with frame 1, but animation preparation failed: ${item.spriteLoadError}`);
    return item;
  });
  return item;
}
async function placeUploadedSprites(files){
  if(READ_ONLY){announce('World reference mode is view only.');return;}
  const list=[...(files||[])].filter(file=>file?.type?.startsWith('image/'));
  if(!list.length){announce('Choose one or more sprite sheet images.');return}
  try{
    const columns=clamp(Math.trunc(Number(spriteColumns.value)||2),1,16),rows=clamp(Math.trunc(Number(spriteRows.value)||2),1,16);
    const frameCount=clamp(Math.trunc(Number(spriteFrameCount.value)||columns*rows),1,columns*rows),fps=clamp(Number(spriteFps.value)||60,1,60),motionOnly=!!spriteMotionOnly?.checked;
    const pages=[];
    for(let index=0;index<list.length;index++){
      pages.push({name:list[index].name||`Sprite page ${index+1}`,sheetSrc:await fileDataUrl(list[index]),columns,rows,frameCount,whiteTransparent:true});
    }

    const target=spriteChainTarget?.kind==='sprite'?spriteChainTarget:null;
    const chainId=String(target?.spriteChainId||crypto.randomUUID?.()||Date.now());
    if(target)target.spriteChainId=chainId;
    let item=target;
    let appendedPages;
    if(target){
      appendedPages=await appendSpriteChainPages(target,pages);
    }else{
      item=await placeSpriteDefinition({
        name:list.length===1?(list[0].name||'Uploaded sprite'):`${String(list[0].name||'Sprite').replace(/\.[^.]+$/,'')} chain`,
        pages,columns,rows,frameCount,fps,whiteTransparent:true,motionOnly,chainId
      });
      appendedPages=item.spritePages;
    }

    const startIndex=Math.max(0,(item.spritePages?.length||appendedPages.length)-appendedPages.length);
    const uploads=list.map((file,index)=>saveFileToPersonalLibrary(file,{
      category:'Sprites',folder:'My Sprites',assetKind:'sprite',name:String(file.name||`Sprite page ${index+1}`).replace(/\.[^.]+$/,''),
      columns,rows,frameCount,fps,whiteTransparent:true,motionOnly,
      chainId,chainIndex:startIndex+index,chainLength:(item.spritePages?.length||appendedPages.length)
    }).then(asset=>{
      const page=item.spritePages?.[startIndex+index];
      if(page){page.personalAssetKey=asset.key;page.assetId=`private:${asset.key}`}
      if(startIndex+index===0){item.assetId=`private:${asset.key}`;item.personalAssetKey=asset.key}
      return asset;
    }));
    item.personalUploadPromise=trackPersonalUpload(
      Promise.allSettled(uploads).then(results=>{
        const saved=results.filter(result=>result.status==='fulfilled').length;
        announce(`${saved}/${list.length} sprite chain page${list.length===1?'':'s'} saved to My Sprites.`);
        return results;
      })
    );
    spriteUploadPanel.hidden=true;stage.classList.remove('image-upload-open');spriteChainTarget=null;
    keyboardMode='Sprites';openKeyboard();renderKeyboardTabs();renderKeyboardKeys();selectUserImage(item);
  }catch(error){announce(`Sprite chain upload failed: ${String(error?.message||error||'unknown error')}`)}
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
function isLocalAnchorCandidate(item){
  return !!(LOCAL_DEFINER&&!localIsOpen()&&item?.node&&item.kind!=='label'&&!isWorldMapItem(item)&&item.regionOverlay&&!item.localOverlay&&String(item.regionId||'')===activeRegionMapId());
}
function localAnchorItems(){
  return selectablePlacedContent().filter(isLocalAnchorCandidate);
}
function localAnchorSelect(items=localAnchorItems()){
  const select=document.createElement('select');
  select.className='placed-content-select';
  select.setAttribute('aria-label','Select Region asset for Local zone');
  const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent=items.length?'Select Region asset…':'No Region assets available';select.append(placeholder);
  items.forEach((item,index)=>{
    const option=document.createElement('option');option.value=String(item.id||index);option.textContent=item.name||item.assetId||`Object ${index+1}`;select.append(option);
  });
  if(selectedImage&&items.includes(selectedImage))select.value=String(selectedImage.id||items.indexOf(selectedImage));
  select.addEventListener('change',()=>{
    const chosen=items.find((item,index)=>String(item.id||index)===select.value);
    if(chosen)selectUserImage(chosen);else deselectUserImage(false);
  });
  return select;
}
function cycleLocalAnchorSelection(items=localAnchorItems(),delta=1){
  if(!items.length)return;
  const current=Math.max(-1,items.indexOf(selectedImage));
  const next=(current+delta+items.length)%items.length;
  selectUserImage(items[next]);renderKeyboardKeys();
}
function localAnchorPayload(item){
  const aspect=Math.max(stableAssetAspect(item),.00001);
  const width=clamp(.12*Math.max(Number(item?.size)||1,.00001),.0001,1);
  const height=clamp(width/aspect,.0001,1);
  return{
    id:String(item?.id||''),assetId:String(item?.assetId||''),name:String(item?.name||item?.assetId||'Local object'),kind:String(item?.kind||'image'),
    x:clamp(Number(item?.x)||0,0,1),y:clamp(Number(item?.y)||0,0,1),width,height,
    tier:clamp(Math.trunc(Number(item?.tier)||0),0,2),layer:clamp(Math.trunc(Number(item?.layer)||0),0,9),
    worldTier:nestedVerticalAddress(item).worldTier,worldLayer:nestedVerticalAddress(item).worldLayer,
    regionTier:nestedVerticalAddress(item).regionTier,regionLayer:nestedVerticalAddress(item).regionLayer,
    localTier:nestedVerticalAddress(item).localTier,localLayer:nestedVerticalAddress(item).localLayer,
    instanceTier:nestedVerticalAddress(item).instanceTier,instanceLayer:nestedVerticalAddress(item).instanceLayer,
    z100:regionZ100(regionWorldLayer(item),regionOverlayLayer(item)),rotation:Number(item?.rotation)||0
  };
}
function createSelectedLocal(){
  if(!LOCAL_DEFINER||!selectedImage||localCreatePending)return;
  const existing=localCatalog.find(local=>String(local?.anchorObjectId||'')===String(selectedImage.id||''));
  if(!existing&&!localRegionEditable){announce('This Region is view only. Edit permission is required to create a Local zone here.');return}
  localCreatePending=true;renderKeyboardKeys();
  if(existing){
    if(!postRegionMessage('open-local',{localId:String(existing.id||'')})){
      localCreatePending=false;renderKeyboardKeys();announce('Local database bridge is unavailable.');
    }
    return;
  }
  const proposed=String(selectedImage.name||'Local').trim();
  const name=String(prompt('Name this Local',proposed)||'').trim();
  if(!name){localCreatePending=false;renderKeyboardKeys();return}
  if(!postRegionMessage('create-local',{name,anchor:localAnchorPayload(selectedImage)})){
    localCreatePending=false;renderKeyboardKeys();announce('Local database bridge is unavailable.');
  }
}
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
    if(REGION_DEFINER&&regionClaimPhase!=='build')keyboardKeys.append(
      readoutKey(regionClaimedRegion?'REGION':'WORLD MAP',regionClaimedRegion?'claimed full map':'claim source'),
      regionClaimedRegion
        ? readoutKey(regionGridShape.toUpperCase(),'saved placement grid')
        : toolKey(regionGridShape==='square'?'SQUARE ✓':'HEX ✓','selection + placement grid',cycleRegionGridShape),
      toolKey(regionClaimedRegion?'REGION':(regionWorldSourceMeta?'CLAIM':'LOADING…'),regionClaimedRegion?'open claimed region':(regionWorldSourceMeta?'open Select tools':'waiting for selected world'),()=>{if(!regionClaimedRegion&&!regionWorldSourceMeta)return;keyboardMode='Select';renderKeyboardTabs();renderKeyboardKeys();announce(regionClaimedRegion?'Claimed Region controls opened.':'Claim Region controls opened.')},!regionClaimedRegion&&!regionWorldSourceMeta)
    );
    return;
  }
  if(keyboardMode==='Tiers'){
    if(REGION_DEFINER&&regionDeedIsComplete()){
      keyboardKeys.append(
        readoutKey(`WORLD TIER ${Number(regionClaimedRegion.tierIndex)+1}`,'fixed by the deed'),
        readoutKey(`WORLD L ${viewerLayer}`,'World layer inherited from Worldbuilder'),
        readoutKey(`REGION T ${regionTierIndex}`,LOCAL_DEFINER?'inherited from selected regional object':'regional tier'),
        readoutKey(`REGION L ${regionLayerIndex}`,LOCAL_DEFINER?'inherited from selected regional object':'regional layer'),
        ...(LOCAL_DEFINER?[
          readoutKey(`LOCAL T ${localTierIndex}`,localIsOpen()?'editable Local tier':'new Local starts at Local Tier 0'),
          readoutKey(`LOCAL L ${localLayerIndex}`,localIsOpen()?'editable Local layer':'new Local starts at Local Layer 1'),
          ...(localIsOpen()?[
            toolKey('LOCAL T −',`T ${localTierIndex}`,()=>{localTierIndex=Math.max(0,localTierIndex-1);syncLocalEditLayer();renderKeyboardKeys()},localTierIndex<=0),
            toolKey('LOCAL T +',`T ${localTierIndex}`,()=>{localTierIndex+=1;syncLocalEditLayer();renderKeyboardKeys()}),
            toolKey('LOCAL L −',`L ${localLayerIndex}`,()=>{localLayerIndex=clamp(localLayerIndex-1,1,9);syncLocalEditLayer();renderKeyboardKeys()},localLayerIndex<=1),
            toolKey('LOCAL L +',`L ${localLayerIndex}`,()=>{localLayerIndex=clamp(localLayerIndex+1,1,9);syncLocalEditLayer();renderKeyboardKeys()},localLayerIndex>=9)
          ]:[])
        ]:[
          toolKey('WORLD L −',`L ${viewerLayer}`,()=>{viewerLayer=clamp(viewerLayer-1,0,9);updateTierButton();syncRegionEditLayer();renderKeyboardKeys();announce(`Placement World Layer ${viewerLayer}.`)} ,viewerLayer<=0),
          toolKey('WORLD L +',`L ${viewerLayer}`,()=>{viewerLayer=clamp(viewerLayer+1,0,9);updateTierButton();syncRegionEditLayer();renderKeyboardKeys();announce(`Placement World Layer ${viewerLayer}.`)} ,viewerLayer>=9),
          toolKey('REGION T −',`T ${regionTierIndex}`,()=>{regionTierIndex=Math.max(0,regionTierIndex-1);updateTierButton();syncRegionEditLayer();renderKeyboardKeys()} ,regionTierIndex<=0),
          toolKey('REGION T +',`T ${regionTierIndex}`,()=>{regionTierIndex+=1;updateTierButton();syncRegionEditLayer();renderKeyboardKeys()}),
          toolKey('REGION L −',`L ${regionLayerIndex}`,()=>{regionLayerIndex=clamp(regionLayerIndex-1,1,9);updateTierButton();syncRegionEditLayer();renderKeyboardKeys()} ,regionLayerIndex<=1),
          toolKey('REGION L +',`L ${regionLayerIndex}`,()=>{regionLayerIndex=clamp(regionLayerIndex+1,1,9);updateTierButton();syncRegionEditLayer();renderKeyboardKeys()} ,regionLayerIndex>=9)
        ])
      );return;
    }
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
    const selectedTile=assetModeMatches(selectedImage,'Tiles')?selectedImage:null;
    keyboardKeys.append(typedPlacedContentSelect('Tiles'));
    if(selectedTile)appendCommonAssetEditControls('Tiles',selectedTile);
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
    const selectedSprite=assetModeMatches(selectedImage,'Sprites')?selectedImage:null;
    keyboardKeys.append(
      typedPlacedContentSelect('Sprites'),
      toolKey('UPLOAD','sprite set',openSpriteUpload),
      toolKey('MY SPRITES','Personal folder',()=>openPersonalFolder('Sprites')),
      toolKey(ASSET_SCALE,'Sprite library filter',()=>{},true)
    );
    if(selectedSprite){
      appendCommonAssetEditControls('Sprites',selectedSprite);
      keyboardKeys.append(
        toolKey('FPS −',`${Math.max(1,Number(selectedSprite.spriteFps)||6)} fps`,()=>{selectedSprite.spriteFps=clamp((Number(selectedSprite.spriteFps)||6)-1,1,60);if(selectedSprite.playing)startSpriteMotion(selectedSprite);renderKeyboardKeys()}),
        toolKey('FPS +',`${Math.max(1,Number(selectedSprite.spriteFps)||6)} fps`,()=>{selectedSprite.spriteFps=clamp((Number(selectedSprite.spriteFps)||6)+1,1,60);if(selectedSprite.playing)startSpriteMotion(selectedSprite);renderKeyboardKeys()}),
        toolKey('FPS 60','real-time',()=>{selectedSprite.spriteFps=60;if(selectedSprite.playing)startSpriteMotion(selectedSprite);renderKeyboardKeys()}),
        toolKey(`PAGES ${Math.max(1,selectedSprite.spritePages?.length||1)}`,`${selectedSprite.frameSources?.length||selectedSprite.spriteFrameCount||1} frames chained`,()=>{},true),
        toolKey('ADD PAGE','append sprite set(s)',()=>openSpriteUpload(selectedSprite)),
        toolKey(selectedSprite.playing?'PAUSE':'PLAY','motion',()=>{if(selectedSprite.playing)stopSpriteMotion(selectedSprite);else if(selectedSprite.committed)startSpriteMotion(selectedSprite);else announce('Save the sprite first to begin world motion.');renderKeyboardKeys()}),
        toolKey(selectedSprite.spriteMotionOnly?'FX ONLY ✓':'FX ONLY','changing pixels only',()=>void rebuildSelectedSpriteMotionOnly(!selectedSprite.spriteMotionOnly)),
        toolKey('FIT DEED','align to claim',()=>fitSelectedAssetToDeed(selectedSprite),!REGION_DEFINER||!regionClaimedRegion)
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
    const selectedImageAsset=assetModeMatches(selectedImage,'Image')?selectedImage:null;
    keyboardKeys.append(typedPlacedContentSelect('Image'));
    if(!selectedImageAsset){
      appendPlacementRoleControls();
      keyboardKeys.append(
        toolKey('UPLOAD','image',openImageUpload),
        toolKey('MY IMAGES','Personal folder',()=>openPersonalFolder('Images'))
      );return;
    }
    selectedImage=selectedImageAsset;
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
      ...(REGION_DEFINER
        ?[
          readoutKey(`WORLD TIER ${pos.tier}`,pos.tierLabel),
          readoutKey(`WORLD L ${pos.worldZ}`,`World Tier ${pos.tier}`),
          readoutKey(`REGION T ${pos.regionTier}`,'regional tier'),
          readoutKey(`REGION L ${pos.regionLayer}`,'regional layer'),
          ...(LOCAL_DEFINER?[readoutKey(`LOCAL T ${pos.localTier}`,'local tier'),readoutKey(`LOCAL L ${pos.localLayer}`,'local layer')]:[]),
          readoutKey('MAP ATTACHED','nested coordinates retained independently')
        ]
        :[
          readoutKey(`TIER ${pos.tier}`,pos.tierLabel),
          readoutKey(`LAYER ${pos.layer}`,'current layer'),
          readoutKey(itemParallaxMode(selectedImage)==='anchored'?'MAP ATTACHED':'PARALLAX',
            itemParallaxMode(selectedImage)==='anchored'?'moves with parent world tier':'explicit separate tier')
        ]),
      readoutKey(`X ${pos.x}`,LOCAL_DEFINER?'canonical X within Local anchor':'world position'),
      readoutKey(`Y ${pos.y}`,LOCAL_DEFINER?'canonical Y within Local anchor':'world position'),
      toolKey('SIZE −',`${selectedImage.size.toFixed(selectedImage.size<2?1:2)}×`,()=>adjustSelectedSize(-1),selectedImage.size<=.2),
      toolKey('SIZE +',`${selectedImage.size.toFixed(selectedImage.size<2?1:2)}×`,()=>adjustSelectedSize(1),selectedImage.size>=20),
      sizeNumberInput(selectedImage),sizeRangeInput(selectedImage),
      toolKey('↺','rotate',()=>rotateLinkedSelection(selectedImage,-15)),
      toolKey('↻','rotate',()=>rotateLinkedSelection(selectedImage,15)),
      toolKey('OP −','opacity',()=>adjustLinkedOpacity(selectedImage,-.1)),
      toolKey('OP +','opacity',()=>adjustLinkedOpacity(selectedImage,.1)),
      toolKey(selectedImage.transparent?'TRANS ✓':'TRANS','background',()=>void toggleLinkedTransparency(selectedImage)),
      ...(linkedSelectionMembers(selectedImage).length>1
        ?[readoutKey(`LINKED ${linkedSelectionMembers(selectedImage).length}`,'moves as one selection'),toolKey('UNLINK','move pieces separately',unlinkSelectedGroup)]
        :[toolKey('SPLIT ALPHA','cut transparent sections',()=>void splitImageByAlpha(selectedImage))]),
      ...(LOCAL_DEFINER
        ?[
          toolKey('LOCAL T −',`T ${pos.localTier}`,()=>moveSelectedTier(-1),pos.localTier<=0),
          toolKey('LOCAL T +',`T ${pos.localTier}`,()=>moveSelectedTier(1)),
          toolKey('LOCAL L −',`L ${pos.localLayer}`,()=>moveSelectedLayer(-1),pos.localLayer<=1),
          toolKey('LOCAL L +',`L ${pos.localLayer}`,()=>moveSelectedLayer(1),pos.localLayer>=9)
        ]
        :REGION_DEFINER
        ?[
          toolKey('WORLD L −',`L ${pos.worldZ}`,()=>moveSelectedTier(-1),pos.worldZ<=0),
          toolKey('WORLD L +',`L ${pos.worldZ}`,()=>moveSelectedTier(1),pos.worldZ>=9),
          toolKey('REGION T −',`T ${pos.regionTier}`,()=>moveSelectedRegionTier(-1),pos.regionTier<=0),
          toolKey('REGION T +',`T ${pos.regionTier}`,()=>moveSelectedRegionTier(1)),
          toolKey('REGION L −',`L ${pos.regionLayer}`,()=>moveSelectedLayer(-1),pos.regionLayer<=1),
          toolKey('REGION L +',`L ${pos.regionLayer}`,()=>moveSelectedLayer(1),pos.regionLayer>=9)
        ]
        :[
          toolKey('TIER −',`T${pos.tier} · ${pos.tierLabel}`,()=>moveSelectedTier(-1),selectedImage.tier<=0),
          toolKey('TIER +',`T${pos.tier} · ${pos.tierLabel}`,()=>moveSelectedTier(1),selectedImage.tier>=TIERS.length-1),
          toolKey('LAYER −',`L${pos.layer}`,()=>moveSelectedLayer(-1),selectedImage.tier<=0&&selectedImage.layer<=0),
          toolKey('LAYER +',`L${pos.layer}`,()=>moveSelectedLayer(1),selectedImage.tier>=TIERS.length-1&&selectedImage.layer>=9)
        ]),
      toolKey('MY IMAGES','Personal folder',()=>{deselectUserImage(false);openPersonalFolder('Images')}),
      toolKey('DELETE','image',removeSelectedImage)
    );return;
  }
  if(keyboardMode==='Select'){
    if(LOCAL_DEFINER&&!activeRegionMapId()){
      keyboardKeys.append(
        readoutKey('REGION','select the Region containing the Local zone'),
        readoutKey(`${regionCatalog.length} SAVED`,'available Regions'),
        toolKey(regionCatalog.length?'CHOOSE REGION':'NO REGIONS','Region selector',()=>showLocalRegionPreview(false),!regionCatalog.length)
      );
      return;
    }
    if(LOCAL_DEFINER&&!localIsOpen()){
      const items=localAnchorItems();
      const existing=selectedImage?localCatalog.find(local=>String(local?.anchorObjectId||'')===String(selectedImage.id||'')):null;
      keyboardKeys.append(
        readoutKey(String(regionClaimedRegion?.name||'REGION').toUpperCase(),'select one asset to become the Local zone'),
        toolKey('REGIONS','change Region',()=>showLocalRegionPreview(true)),
        toolKey('‹','previous asset',()=>cycleLocalAnchorSelection(items,-1),!items.length),
        toolKey('›','next asset',()=>cycleLocalAnchorSelection(items,1),!items.length),
        localAnchorSelect(items),
        toolKey(existing?'OPEN LOCAL':'CREATE LOCAL',existing?.name||'selected Region asset',createSelectedLocal,!selectedImage||localCreatePending||(!existing&&!localRegionEditable)),
        toolKey('CLEAR','selection',()=>deselectUserImage(true),!selectedImage)
      );
      return;
    }
    if(REGION_DEFINER&&regionClaimPhase!=='build'){renderRegionSelectKeyboard();return}
    const items=selectablePlacedContent();
    if(REGION_DEFINER&&regionDeedIsComplete()&&!items.length){
      keyboardKeys.append(
        readoutKey('WORLD LOCKED','Add an object to edit on the selected regional tier'),
        toolKey('ADD IMAGE','editable regional image',()=>{keyboardMode='Image';renderKeyboardTabs();renderKeyboardKeys()}),
        toolKey('ADD TILE','editable regional tile',()=>{keyboardMode='Tiles';renderKeyboardTabs();renderKeyboardKeys()})
      );
      return;
    }
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
spriteFile.addEventListener('change',()=>{const files=[...(spriteFile.files||[])].filter(file=>file.type.startsWith('image/'));if(files.length)void placeUploadedSprites(files);spriteFile.value=''});
spriteColumns.addEventListener('input',syncSpriteFrameCount);spriteRows.addEventListener('input',syncSpriteFrameCount);
spriteDropzone.addEventListener('click',event=>{if(event.target===spriteDropzone)spriteFile.click()});
spriteDropzone.addEventListener('keydown',event=>{if(event.target===spriteDropzone&&(event.key==='Enter'||event.key===' ')){event.preventDefault();spriteFile.click()}});
for(const type of ['dragenter','dragover'])spriteDropzone.addEventListener(type,event=>{event.preventDefault();event.stopPropagation();spriteDropzone.classList.add('dragover')});
for(const type of ['dragleave','drop'])spriteDropzone.addEventListener(type,event=>{event.preventDefault();event.stopPropagation();spriteDropzone.classList.remove('dragover')});
spriteDropzone.addEventListener('drop',event=>{const files=[...(event.dataTransfer?.files||[])].filter(file=>file.type.startsWith('image/'));if(files.length)void placeUploadedSprites(files)});
$('keyboardClose').addEventListener('click',closeKeyboard);

stage.addEventListener('wheel',e=>{
  if(REGION_DEFINER&&regionClaimPhase==='select'&&regionSelectionEnabled)return;
  if(e.target instanceof Element&&e.target.closest('[data-ui]'))return;
  if(!e.deltaY)return;
  e.preventDefault();
  const unit=e.deltaMode===1?16:e.deltaMode===2?stage.clientHeight:1;
  zoomAt(e.clientX,e.clientY,Math.exp(-clamp(e.deltaY*unit,-240,240)*.0015));
},{passive:false});
stage.addEventListener('contextmenu',event=>{
  if(event.target instanceof Element&&event.target.closest('.user-image-placement,.asset-resize-overlay')){
    event.preventDefault();event.stopPropagation();
  }
},{capture:true});
stage.addEventListener('dragstart',event=>{
  if(event.target instanceof Element&&event.target.closest('.user-image-placement')){
    event.preventDefault();event.stopPropagation();
  }
},{capture:true});
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
stage.addEventListener('lostpointercapture',event=>{release(event);endImageDrag(event);endAssetResize(event)});
window.addEventListener('blur',()=>{
  for(const pointerId of [...pointers.keys()])release({pointerId});
  if(imageDrag)endImageDrag({pointerId:imageDrag.id});
  if(assetResizeDrag)endAssetResize({pointerId:assetResizeDrag.id});
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
  fitWorld:()=>{fitMap();return true},
  focusNormalizedBounds,
  save:saveWorldBuilder,
  tiers:TIERS,
  baseLayers:BASE_WORLD_ASSETS,
  regionGeometry:REGION_DEFINER?Object.freeze({extents:regionGridExtents,center:regionCellCenter,cellAt:regionCellFromPoint,constrain:constrainRegionPoint}):null,
  getViewerState:()=>({
    workspaceMode:WORKSPACE_MODE,assetScale:ASSET_SCALE,mapAuthorityScoped:MAP_AUTHORITY_SCOPED,
    viewerTier,viewerLayer,
    layerCount:BASE_LAYER_COUNT+regionWorldSourceTiles.length+userLayers.length,
    regionChild:REGION_DEFINER&&regionDeedIsComplete()?{
      sourceScope:stage.dataset.sourceScope||'pending',
      parentTierIndex:Number(regionClaimedRegion.tierIndex)||0,
      worldZ:viewerLayer,
      regionLayer:regionLayerIndex,
      exactZ:regionZLabel(viewerLayer,regionLayerIndex),
      zModel:'world-integer-region-hundredth-v1',
      sourceCellCount:Number(stage.dataset.sourceCellCount)||0,
      loadedCellCount:Number(stage.dataset.loadedCellCount)||0,
      rasterIndexMissing:regionRasterIndexMissing
    }:null,
    userLayers:userLayers.map(item=>({
      id:item.id,authorityResourceId:assetAuthorityResourceId(item),kind:item.kind||'image',text:item.kind==='label'?item.text:undefined,
      tier:item.tier,layer:item.layer,
      worldLayer:REGION_DEFINER?regionWorldLayer(item):undefined,
      regionLayer:REGION_DEFINER&&item.regionOverlay?regionOverlayLayer(item):0,
      z100:REGION_DEFINER?(item.regionOverlay?regionZ100(regionWorldLayer(item),regionOverlayLayer(item)):regionWorldLayer(item)*100):undefined,
      sourceLocked:!!item.sourceLocked,regionOverlay:!!item.regionOverlay,
      x:item.x,y:item.y,size:item.size,rotation:item.rotation,opacity:item.opacity,transparent:item.transparent,linkGroupId:item.linkGroupId||'',linkGroupIndex:item.linkGroupIndex??null,linkGroupCount:item.linkGroupCount??null,
      parallaxMode:itemParallaxMode(item),parallaxX:Number(item.parallaxX)||0,parallaxY:Number(item.parallaxY)||0,
      committed:!!item.committed,zoomPassed:!!item.zoomPassed
    })),
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
