(()=>{
 'use strict';

 const GRID_CELLS=30;
 const MIN_VISIBLE_CELLS=10;
 const MAX_VISIBLE_CELLS=16;
 const TARGET_CELL_PX=30;
 const MIN_ZOOM=GRID_CELLS/MAX_VISIBLE_CELLS;
 const MAX_ZOOM=GRID_CELLS/MIN_VISIBLE_CELLS;
 const LOCK_KEY='rist.world.viewerLocked';
 const X_KEY='rist.world.viewX';
 const Y_KEY='rist.world.viewY';
 const ZOOM_KEY='rist.world.viewerZoom';
 const MODE_KEY='rist.world.viewerZoom.cameraWindowV3';
 const GRID_KEY='rist.world.viewerGrid';
 const DOTNET_ASSEMBLY='RistWorld';

 let observer=null;
 let frame=0;
 let restoring=false;
 const prefs={locked:true,grid:true,mode:'auto',parallax:null,playback:null,fps:null};
 const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
 const studio=()=>document.querySelector('.worldbuilder-studio');
 const map=()=>studio()?.querySelector('.studio-viewer-canvas .map')||studio()?.querySelector('.map');
 const stage=()=>map()?.querySelector('.world-stage');
 const grid=()=>studio()?.querySelector('.studio-viewer-grid');
 const canvas=()=>studio()?.querySelector('.studio-viewer-canvas');

 function readNumber(key,fallback){try{const n=Number(localStorage.getItem(key));return Number.isFinite(n)?n:fallback}catch{return fallback}}
 function readBool(key,fallback){try{const raw=localStorage.getItem(key);return raw===null?fallback:raw!=='false'&&raw!=='off'}catch{return fallback}}
 function readText(key,fallback){try{return localStorage.getItem(key)||fallback}catch{return fallback}}
 function write(key,value){try{localStorage.setItem(key,String(value))}catch{}}

 function desiredVisibleCells(){
  const rect=(canvas()||map())?.getBoundingClientRect();
  if(!rect||rect.width<1||rect.height<1)return 12;
  return clamp(Math.round(Math.min(rect.width,rect.height)/TARGET_CELL_PX),MIN_VISIBLE_CELLS,MAX_VISIBLE_CELLS);
 }
 function zoomForCells(cells){return clamp(GRID_CELLS/clamp(Number(cells)||12,MIN_VISIBLE_CELLS,MAX_VISIBLE_CELLS),MIN_ZOOM,MAX_ZOOM)}
 function readCamera(){
  const node=map();
  const panX=Number(node?.dataset?.panX);
  const panY=Number(node?.dataset?.panY);
  const zoom=Number(node?.dataset?.zoom);
  return{
   panX:Number.isFinite(panX)?panX:0,
   panY:Number.isFinite(panY)?panY:0,
   zoom:Number.isFinite(zoom)&&zoom>0?zoom:zoomForCells(desiredVisibleCells())
  };
 }
 function cellSize(){
  const world=stage();
  const width=world?.offsetWidth||0,height=world?.offsetHeight||0;
  if(width>0&&height>0)return[width/GRID_CELLS,height/GRID_CELLS];
  const rect=(map()||canvas())?.getBoundingClientRect();
  const camera=readCamera();
  return rect&&rect.width>0&&rect.height>0?[rect.width/(GRID_CELLS*camera.zoom),rect.height/(GRID_CELLS*camera.zoom)]:[1,1];
 }
 function snapshot(source='read',cameraOverride=null){
  const camera=cameraOverride||readCamera();
  const [cw,ch]=cellSize();
  return{
   x:camera.panX/Math.max(cw,1),y:camera.panY/Math.max(ch,1),panX:camera.panX,panY:camera.panY,zoom:camera.zoom,
   visibleCells:GRID_CELLS/camera.zoom,locked:prefs.locked,unlocked:!prefs.locked,grid:prefs.grid,mode:prefs.mode,
   localGridCells:GRID_CELLS,minZoom:MIN_ZOOM,maxZoom:MAX_ZOOM,parallax:prefs.parallax,playback:prefs.playback,fps:prefs.fps,source
  };
 }

 function installStyle(){
  if(document.getElementById('rist-viewer-authority-style'))return;
  const style=document.createElement('style');
  style.id='rist-viewer-authority-style';
  style.textContent=`
 html body .worldbuilder-studio.viewer-grid-disabled .studio-viewer-canvas .world-stage>.grid,
 html body .worldbuilder-studio.viewer-grid-disabled .studio-viewer-grid{display:none!important;visibility:hidden!important;background:none!important;background-image:none!important}`;
  document.head.appendChild(style);
 }
 function emit(source='sync',cameraOverride=null){
  installStyle();
  const root=studio(),view=canvas(),marker=grid(),snap=snapshot(source,cameraOverride);
  if(view)view.dataset.viewerLocked=prefs.locked?'true':'false';
  if(root){
   root.classList.toggle('viewer-locked',prefs.locked);
   root.classList.toggle('viewer-unlocked',!prefs.locked);
   root.classList.toggle('viewer-grid-disabled',!prefs.grid);
   root.dataset.cameraMode=prefs.mode;
   root.dataset.cameraZoom=snap.zoom.toFixed(4);
   root.dataset.cameraVisibleCells=String(Math.round(snap.visibleCells));
  }
  marker?.classList.toggle('off',!prefs.grid);
  document.documentElement.style.setProperty('--wb-ruler-x-offset',`${snap.panX}px`);
  document.documentElement.style.setProperty('--wb-ruler-y-offset',`${snap.panY}px`);
  window.ristProjection?.apply?.();
  window.dispatchEvent(new CustomEvent('rist:viewer-state',{detail:snap}));
  window.dispatchEvent(new CustomEvent('rist:viewer-pan',{detail:snap}));
  window.dispatchEvent(new CustomEvent('rist:camera-window',{detail:snap}));
  return snap;
 }

 function invoke(method,...args){
  if(!window.DotNet?.invokeMethodAsync)return Promise.resolve(null);
  return window.DotNet.invokeMethodAsync(DOTNET_ASSEMBLY,method,...args).catch(error=>{console.warn(`[RIST viewer] ${method} failed`,error);return null});
 }
 function command(method,args,source){
  return invoke(method,...args).then(camera=>{
   if(camera){
    write(X_KEY,snapshot(source,camera).x);write(Y_KEY,snapshot(source,camera).y);write(ZOOM_KEY,camera.zoom);
    return emit(source,camera);
   }
   return emit(`${source}-unavailable`);
  });
 }
 function setPosition(x,y,force=false,source='navigation'){
  if(!force&&prefs.locked)return Promise.resolve(snapshot(`${source}-locked`));
  const [cw,ch]=cellSize();
  return setPan((Number(x)||0)*cw,(Number(y)||0)*ch,false,force,source);
 }
 function setPan(x,y,snapToGrid=true,force=false,source='navigation'){
  if(!force&&prefs.locked)return Promise.resolve(snapshot(`${source}-locked`));
  const [cw,ch]=cellSize();
  let panX=Number(x)||0,panY=Number(y)||0;
  if(snapToGrid){panX=Math.round(panX/Math.max(cw,1))*cw;panY=Math.round(panY/Math.max(ch,1))*ch;}
  return command('WorldMapViewerSetPan',[panX,panY],source);
 }
 function setZoom(value,{mode='manual',source='zoom'}={}){
  prefs.mode=mode==='auto'?'auto':'manual';write(MODE_KEY,prefs.mode);
  const zoom=clamp(Number(value)||MIN_ZOOM,MIN_ZOOM,MAX_ZOOM);write(ZOOM_KEY,zoom);
  return command('WorldMapViewerSetZoom',[zoom],source);
 }
 function zoomBy(factor,options){return setZoom(readCamera().zoom*(Number(factor)||1),options)}
 function resetAutoZoom({source='auto'}={}){prefs.mode='auto';write(MODE_KEY,prefs.mode);return setZoom(zoomForCells(desiredVisibleCells()),{mode:'auto',source})}
 function reset({source='reset'}={}){prefs.mode='manual';write(MODE_KEY,prefs.mode);return command('WorldMapViewerReset',[],source)}
 function syncViewport(source='viewport'){return prefs.mode==='auto'?resetAutoZoom({source}):Promise.resolve(emit(source))}
 function setLocked(value,{source='lock'}={}){prefs.locked=!!value;write(LOCK_KEY,prefs.locked);return emit(source)}
 function setGrid(value,{source='grid'}={}){prefs.grid=!!value;write(GRID_KEY,prefs.grid);return emit(source)}
 function nudge(axis,steps){
  if(prefs.locked)return Promise.resolve(snapshot('nudge-locked'));
  const snap=snapshot('nudge-read');
  const amount=Number(steps)||0;
  return axis==='x'?setPosition(snap.x+amount,snap.y,false,'nudge'):setPosition(snap.x,snap.y+amount,false,'nudge');
 }
 function readPrefs(){prefs.locked=readBool(LOCK_KEY,true);prefs.grid=readBool(GRID_KEY,true);prefs.mode=readText(MODE_KEY,'auto')==='manual'?'manual':'auto'}
 async function restoreCamera(){
  if(restoring)return;restoring=true;
  try{
   const current=readCamera();
   const persistedZoom=clamp(readNumber(ZOOM_KEY,zoomForCells(desiredVisibleCells())),MIN_ZOOM,MAX_ZOOM);
   const targetZoom=prefs.mode==='auto'?zoomForCells(desiredVisibleCells()):persistedZoom;
   const [cw,ch]=cellSize();
   const x=readNumber(X_KEY,current.panX/Math.max(cw,1));
   const y=readNumber(Y_KEY,current.panY/Math.max(ch,1));
   await invoke('WorldMapViewerSetZoom',targetZoom);
   await invoke('WorldMapViewerSetPan',x*cw,y*ch);
   emit('restore');
  }finally{restoring=false;}
 }
 function resync(source='resync'){readPrefs();return emit(source)}
 function schedule(){if(frame)return;frame=requestAnimationFrame(()=>{frame=0;syncViewport('layout')})}
 function start(){
  if(!studio()||!map()||!window.DotNet?.invokeMethodAsync){setTimeout(start,100);return;}
  readPrefs();installStyle();emit('start');restoreCamera();
  observer?.disconnect();observer=new MutationObserver(mutations=>{
   if(mutations.some(m=>m.type==='attributes'&&['data-pan-x','data-pan-y','data-zoom'].includes(m.attributeName)))emit('worldmap');
   if(mutations.some(m=>m.type==='childList'))schedule();
  });
  observer.observe(studio(),{attributes:true,attributeFilter:['data-pan-x','data-pan-y','data-zoom'],childList:true,subtree:true});
  window.addEventListener('resize',schedule,{passive:true});
  window.addEventListener('orientationchange',schedule,{passive:true});
  window.addEventListener('pageshow',()=>resync('pageshow'),{passive:true});
  window.addEventListener('storage',event=>{if([LOCK_KEY,MODE_KEY,GRID_KEY].includes(event.key))resync('storage')});
  window.addEventListener('rist-parallax-settings',event=>{prefs.parallax=event.detail||null;emit('parallax')});
  window.addEventListener('rist-sprite-playback',event=>{prefs.playback=event.detail?.state??null;prefs.fps=event.detail?.fps??null;emit('playback')});
 }

 window.ristViewerAuthority={
  constants:{gridCells:GRID_CELLS,minVisibleCells:MIN_VISIBLE_CELLS,maxVisibleCells:MAX_VISIBLE_CELLS,targetCellPx:TARGET_CELL_PX,minZoom:MIN_ZOOM,maxZoom:MAX_ZOOM},
  get:()=>snapshot('get'),getZoom:()=>readCamera().zoom,setPosition,setPan,setZoom,zoomBy,nudge,setLocked,toggleLocked:options=>setLocked(!prefs.locked,options),setGrid,toggleGrid:options=>setGrid(!prefs.grid,options),resetAutoZoom,reset,syncViewport,resync
 };
 window.ristViewerNavigation={get:()=>snapshot('navigation-get'),setPosition,setPan,nudge,resync};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
