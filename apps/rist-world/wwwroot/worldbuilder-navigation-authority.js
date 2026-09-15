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
 let observer=null,frame=0;
 const state={x:0,y:0,zoom:GRID_CELLS/12,locked:true,grid:true,mode:'auto',parallax:null,playback:null,fps:null};
 const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
 const studio=()=>document.querySelector('.worldbuilder-studio');
 const stage=()=>studio()?.querySelector('.studio-viewer-canvas .world-stage');
 const grid=()=>studio()?.querySelector('.studio-viewer-grid');
 const canvas=()=>studio()?.querySelector('.studio-viewer-canvas');
 function readNumber(key,fallback){try{const n=Number(localStorage.getItem(key));return Number.isFinite(n)?n:fallback}catch{return fallback}}
 function readBool(key,fallback){try{const raw=localStorage.getItem(key);return raw===null?fallback:raw!=='false'&&raw!=='off'}catch{return fallback}}
 function write(key,value){try{localStorage.setItem(key,String(value))}catch{}}
 function desiredVisibleCells(){const rect=(grid()||canvas())?.getBoundingClientRect();if(!rect||rect.width<1||rect.height<1)return 12;return clamp(Math.round(Math.min(rect.width,rect.height)/TARGET_CELL_PX),MIN_VISIBLE_CELLS,MAX_VISIBLE_CELLS)}
 function zoomForCells(cells){return clamp(GRID_CELLS/clamp(Number(cells)||12,MIN_VISIBLE_CELLS,MAX_VISIBLE_CELLS),MIN_ZOOM,MAX_ZOOM)}
 function visibleCells(){return GRID_CELLS/state.zoom}
 function maxPanOffset(){return Math.max(0,Math.floor((GRID_CELLS-visibleCells())/2))}
 function clampAxis(value){const max=maxPanOffset();return clamp(Math.round(Number(value)||0),-max,max)}
 function readPersisted(){
  state.locked=readBool(LOCK_KEY,true);
  state.grid=readBool(GRID_KEY,true);
  const mode=(()=>{try{return localStorage.getItem(MODE_KEY)}catch{return null}})();
  state.mode=mode==='manual'?'manual':'auto';
  state.zoom=clamp(readNumber(ZOOM_KEY,zoomForCells(desiredVisibleCells())),MIN_ZOOM,MAX_ZOOM);
  if(state.mode==='auto')state.zoom=zoomForCells(desiredVisibleCells());
  state.x=readNumber(X_KEY,0);state.y=readNumber(Y_KEY,0);
  state.x=clampAxis(state.x);state.y=clampAxis(state.y);
 }
 function persistCamera(){write(X_KEY,state.x);write(Y_KEY,state.y);write(ZOOM_KEY,state.zoom);write(MODE_KEY,state.mode);write(LOCK_KEY,state.locked);write(GRID_KEY,state.grid)}
 function cellSize(){const rect=(grid()||canvas())?.getBoundingClientRect();return rect&&rect.width>0&&rect.height>0?[rect.width/GRID_CELLS,rect.height/GRID_CELLS]:[1,1]}
 function installStyle(){if(document.getElementById('rist-viewer-authority-style'))return;const s=document.createElement('style');s.id='rist-viewer-authority-style';s.textContent=`
 html body .worldbuilder-studio.viewer-grid-disabled .studio-viewer-canvas .world-stage>.grid,
 html body .worldbuilder-studio.viewer-grid-disabled .studio-viewer-grid{display:none!important;visibility:hidden!important;background:none!important;background-image:none!important}
 html body .worldbuilder-studio .studio-viewer-canvas .map .world-stage{transform:translate(var(--wb-pan-x,0%),var(--wb-pan-y,0%)) scale(var(--wb-view-zoom,1))!important;transform-origin:center center!important}`;document.head.appendChild(s)}
 function snapshot(source='read'){const [cw,ch]=cellSize();return{x:state.x,y:state.y,panX:state.x*cw,panY:state.y*ch,zoom:state.zoom,visibleCells:visibleCells(),locked:state.locked,unlocked:!state.locked,grid:state.grid,mode:state.mode,localGridCells:GRID_CELLS,minZoom:MIN_ZOOM,maxZoom:MAX_ZOOM,parallax:state.parallax,playback:state.playback,fps:state.fps,source}}
 function apply(source='sync',emit=true){
  installStyle();state.x=clampAxis(state.x);state.y=clampAxis(state.y);
  const root=studio(),world=stage(),view=canvas(),marker=grid();
  if(world){world.style.setProperty('--wb-pan-x',`${(state.x/GRID_CELLS)*100}%`);world.style.setProperty('--wb-pan-y',`${(state.y/GRID_CELLS)*100}%`);world.style.setProperty('--wb-view-zoom',String(state.zoom))}
  if(view){view.style.setProperty('--wb-view-zoom',String(state.zoom));view.dataset.viewerLocked=state.locked?'true':'false'}
  if(root){root.classList.toggle('viewer-locked',state.locked);root.classList.toggle('viewer-unlocked',!state.locked);root.classList.toggle('viewer-grid-disabled',!state.grid);root.dataset.cameraMode=state.mode;root.dataset.cameraZoom=state.zoom.toFixed(4);root.dataset.cameraVisibleCells=String(Math.round(visibleCells()))}
  marker?.classList.toggle('off',!state.grid);
  const snap=snapshot(source);document.documentElement.style.setProperty('--wb-ruler-x-offset',`${snap.panX}px`);document.documentElement.style.setProperty('--wb-ruler-y-offset',`${snap.panY}px`);
  window.ristProjection?.apply?.();
  if(emit){window.dispatchEvent(new CustomEvent('rist:viewer-state',{detail:snap}));window.dispatchEvent(new CustomEvent('rist:viewer-pan',{detail:snap}));window.dispatchEvent(new CustomEvent('rist:camera-window',{detail:snap}))}
  return snap;
 }
 function setPosition(x,y,force=false,source='navigation'){if(!force&&state.locked)return snapshot(source);state.x=clampAxis(x);state.y=clampAxis(y);write(X_KEY,state.x);write(Y_KEY,state.y);return apply(source)}
 function setPan(x,y,snapToGrid=true,force=false,source='navigation'){if(!force&&state.locked)return snapshot(source);const [cw,ch]=cellSize();const px=(Number(x)||0)/Math.max(cw,1),py=(Number(y)||0)/Math.max(ch,1);return setPosition(snapToGrid?Math.round(px):px,snapToGrid?Math.round(py):py,force,source)}
 function setZoom(value,{mode='manual',source='zoom'}={}){state.mode=mode==='auto'?'auto':'manual';state.zoom=clamp(Number(value)||MIN_ZOOM,MIN_ZOOM,MAX_ZOOM);state.x=clampAxis(state.x);state.y=clampAxis(state.y);write(ZOOM_KEY,state.zoom);write(MODE_KEY,state.mode);write(X_KEY,state.x);write(Y_KEY,state.y);return apply(source)}
 function resetAutoZoom({source='auto'}={}){state.mode='auto';return setZoom(zoomForCells(desiredVisibleCells()),{mode:'auto',source})}
 function syncViewport(source='viewport'){if(state.mode==='auto')return resetAutoZoom({source});state.zoom=clamp(readNumber(ZOOM_KEY,state.zoom),MIN_ZOOM,MAX_ZOOM);state.x=clampAxis(state.x);state.y=clampAxis(state.y);return apply(source)}
 function setLocked(value,{source='lock'}={}){state.locked=!!value;write(LOCK_KEY,state.locked);return apply(source)}
 function setGrid(value,{source='grid'}={}){state.grid=!!value;write(GRID_KEY,state.grid);return apply(source)}
 function resync(source='resync'){readPersisted();persistCamera();return apply(source)}
 function schedule(){if(frame)return;frame=requestAnimationFrame(()=>{frame=0;syncViewport('layout')})}
 function start(){if(!studio())return setTimeout(start,100);readPersisted();persistCamera();apply('start');observer=new MutationObserver(()=>{if(!studio())return;schedule()});observer.observe(studio(),{childList:true,subtree:true});window.addEventListener('resize',schedule,{passive:true});window.addEventListener('orientationchange',schedule,{passive:true});window.addEventListener('pageshow',()=>resync('pageshow'),{passive:true});window.addEventListener('storage',event=>{if([LOCK_KEY,X_KEY,Y_KEY,ZOOM_KEY,MODE_KEY,GRID_KEY].includes(event.key))resync('storage')});window.addEventListener('rist-parallax-settings',event=>{state.parallax=event.detail||null;apply('parallax',false)});window.addEventListener('rist-sprite-playback',event=>{state.playback=event.detail?.state??null;state.fps=event.detail?.fps??null;apply('playback',false)})}
 window.ristViewerAuthority={
  constants:{gridCells:GRID_CELLS,minVisibleCells:MIN_VISIBLE_CELLS,maxVisibleCells:MAX_VISIBLE_CELLS,targetCellPx:TARGET_CELL_PX,minZoom:MIN_ZOOM,maxZoom:MAX_ZOOM},
  get:()=>snapshot('get'),getZoom:()=>state.zoom,setPosition,setPan,setZoom,zoomBy:(factor,options)=>setZoom(state.zoom*(Number(factor)||1),options),nudge(axis,steps){if(state.locked)return snapshot('nudge-blocked');const amount=Math.round(Number(steps)||0);return axis==='x'?setPosition(state.x+amount,state.y,false,'nudge'):setPosition(state.x,state.y+amount,false,'nudge')},setLocked,toggleLocked:options=>setLocked(!state.locked,options),setGrid,toggleGrid:options=>setGrid(!state.grid,options),resetAutoZoom,syncViewport,resync
 };
 window.ristViewerNavigation={get:()=>snapshot('navigation-get'),setPosition,setPan,nudge:(axis,steps)=>window.ristViewerAuthority.nudge(axis,steps),resync};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
