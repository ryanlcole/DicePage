(()=>{
 'use strict';
 const LOCAL_GRID_CELLS=30;
 const MIN_VISIBLE_CELLS=10;
 const MAX_VISIBLE_CELLS=16;
 const TARGET_CELL_PX=30;
 const MIN_ZOOM=LOCAL_GRID_CELLS/MAX_VISIBLE_CELLS;
 const MAX_ZOOM=LOCAL_GRID_CELLS/MIN_VISIBLE_CELLS;
 const MODE_KEY='rist.world.viewerZoom.cameraWindowV3';
 let observer=null,raf=0;
 const authority=()=>window.ristViewerAuthority;
 const studio=()=>document.querySelector('.worldbuilder-studio');
 function sync(){raf=0;const api=authority();if(!api)return;if(api.get?.().mode==='auto')api.resetAutoZoom?.({source:'camera-window'});else api.syncViewport?.('camera-window')}
 function schedule(){if(!raf)raf=requestAnimationFrame(sync)}
 function initialize(){if(!studio())return setTimeout(initialize,100);sync();observer=new MutationObserver(schedule);observer.observe(studio(),{childList:true,subtree:true});window.addEventListener('resize',schedule,{passive:true});window.addEventListener('orientationchange',schedule,{passive:true});window.addEventListener('pageshow',schedule,{passive:true});window.addEventListener('rist-parallax-settings',schedule)}
 window.ristCameraWindow={
  minZoom:MIN_ZOOM,maxZoom:MAX_ZOOM,
  getZoom:()=>authority()?.getZoom?.()??MIN_ZOOM,
  setZoom:value=>authority()?.setZoom?.(value,{mode:'manual',source:'camera-window-control'})?.zoom??MIN_ZOOM,
  resetAuto:()=>authority()?.resetAutoZoom?.({source:'camera-window-reset'}),
  sync:schedule,
  modeKey:MODE_KEY,
  targetCellPx:TARGET_CELL_PX,
  localGridCells:LOCAL_GRID_CELLS,
  visibleBounds:[MIN_VISIBLE_CELLS,MAX_VISIBLE_CELLS]
 };
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialize,{once:true});else initialize();
})();
