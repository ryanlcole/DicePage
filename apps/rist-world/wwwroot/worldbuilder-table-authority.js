(()=>{
 'use strict';
 const FRAME_PX=24;
 let observer=null;
 let guardInstalled=false;
 const lockedPointers=new Set();

 const studio=()=>document.querySelector('.worldbuilder-studio');
 const canvas=()=>studio()?.querySelector('.studio-viewer-canvas');

 function installStyle(){
  if(document.getElementById('rist-worldbuilder-table-authority'))return;
  const style=document.createElement('style');
  style.id='rist-worldbuilder-table-authority';
  style.textContent=`
   html body .worldbuilder-studio{
    grid-template-rows:36px 62px minmax(0,1fr) 62px!important;
   }
   html body .worldbuilder-studio .studio-header{
    position:relative!important;z-index:160!important;box-sizing:border-box!important;
    width:100%!important;height:36px!important;min-height:36px!important;min-width:0!important;
    grid-template-columns:40px minmax(0,1fr) 40px!important;overflow:hidden!important;
   }
   html body .worldbuilder-studio .studio-home,
   html body .worldbuilder-studio .studio-profile{
    display:grid!important;visibility:visible!important;opacity:1!important;
    width:40px!important;min-width:40px!important;height:36px!important;min-height:36px!important;
    position:relative!important;z-index:2!important;
   }
   html body .worldbuilder-studio .studio-home{font-size:19px!important}
   html body .worldbuilder-studio .studio-profile span{font-size:12px!important}
   html body .worldbuilder-studio .studio-coordinate-nav{
    align-self:center!important;width:100%!important;max-width:100%!important;min-width:0!important;
   }

   /* The viewer is a window looking at a square table. The table does not stretch
      to the viewport's aspect ratio. Short viewports simply reveal fewer rows. */
   html body .worldbuilder-studio .studio-viewer-canvas{
    --wb-table-frame:${FRAME_PX}px!important;
    overflow:hidden!important;background:#03090d!important;
   }
   html body .worldbuilder-studio .studio-viewer-canvas .map{
    position:absolute!important;left:var(--wb-table-frame)!important;top:var(--wb-table-frame)!important;
    right:auto!important;bottom:auto!important;inset:auto!important;
    width:calc(100% - (2 * var(--wb-table-frame)))!important;
    height:auto!important;min-width:0!important;min-height:0!important;max-width:none!important;max-height:none!important;
    aspect-ratio:1 / 1!important;margin:0!important;background:transparent!important;
   }
   html body .worldbuilder-studio .studio-viewer-canvas .world-stage{
    position:absolute!important;inset:0!important;width:100%!important;height:100%!important;
    min-width:0!important;min-height:0!important;max-width:none!important;max-height:none!important;
    aspect-ratio:1 / 1!important;background:transparent!important;
   }
   html body .worldbuilder-studio .studio-viewer-canvas .world-stage>.base.ocean-world{
    position:absolute!important;inset:0!important;width:100%!important;height:100%!important;
    z-index:0!important;opacity:1!important;background-position:0 0!important;
    background-size:calc(100% / 30) calc(100% / 30)!important;
   }

   /* One construction grid only. The table/base terrain owns no grid. */
   html body .worldbuilder-studio .studio-viewer-canvas .world-stage>.grid{
    display:none!important;visibility:hidden!important;background:none!important;background-image:none!important;
   }
   html body .worldbuilder-studio .studio-viewer-canvas .world-stage::before,
   html body .worldbuilder-studio .studio-viewer-canvas .world-stage::after,
   html body .worldbuilder-studio .studio-viewer-canvas .map::before,
   html body .worldbuilder-studio .studio-viewer-canvas .map::after{
    content:none!important;display:none!important;background:none!important;background-image:none!important;
   }
   html body .worldbuilder-studio .studio-viewer-grid{
    position:absolute!important;left:var(--wb-table-frame)!important;top:var(--wb-table-frame)!important;
    right:auto!important;bottom:auto!important;inset:auto!important;
    width:calc(100% - (2 * var(--wb-table-frame)))!important;height:auto!important;
    aspect-ratio:1 / 1!important;box-sizing:border-box!important;display:block!important;visibility:visible!important;
    opacity:1!important;z-index:35!important;pointer-events:none!important;
    border:1px solid rgba(215,199,145,.72)!important;
    background-image:linear-gradient(to right,rgba(215,199,145,.52) 1px,transparent 1px),linear-gradient(to bottom,rgba(215,199,145,.52) 1px,transparent 1px)!important;
    background-size:calc(100% / 30) calc(100% / 30)!important;background-position:0 0!important;background-repeat:repeat!important;
   }
   html body .worldbuilder-studio .studio-viewer-grid.off{display:none!important;visibility:hidden!important}

   html body .worldbuilder-studio .wb-underlay-host{display:none!important}
   html body .worldbuilder-studio .world-stage>.tile-cell:not(.wb-moving){opacity:1!important;filter:none!important}
   html body .worldbuilder-studio .studio-viewer-canvas>.map-asset-inventory{
    display:grid!important;visibility:visible!important;opacity:1!important;z-index:140!important;pointer-events:auto!important;
   }
  `;
  document.head.appendChild(style);
 }

 function sync(){
  installStyle();
  const root=studio();if(!root)return;
  root.querySelectorAll('.wb-underlay-host').forEach(node=>node.remove());
 }

 function isLocked(){
  const root=studio();
  if(!root)return false;
  if(root.classList.contains('viewer-locked'))return true;
  try{return localStorage.getItem('rist.world.viewerLocked')!=='false';}catch{return true;}
 }
 function isCameraBackground(target){
  const view=canvas();
  if(!view||!target||!view.contains(target))return false;
  if(target.closest?.('.tile-cell,.quick-slot,.studio-mini-panel,.studio-load-panel,.map-asset-inventory,.studio-command-slider,.studio-header,.locked-tile-menu,.recursive-region-actions,.wb-modal,.desktop-map-zoom,.wb-z-ruler,.wb-x-ruler,.wb-y-ruler'))return false;
  return true;
 }
 function stop(event){event.preventDefault();event.stopPropagation();event.stopImmediatePropagation();}
 function pointerDown(event){
  if(!isLocked()||!isCameraBackground(event.target))return;
  lockedPointers.add(event.pointerId);stop(event);
 }
 function pointerMove(event){if(lockedPointers.has(event.pointerId)){stop(event);}}
 function pointerEnd(event){if(lockedPointers.delete(event.pointerId))stop(event);}
 function wheel(event){if(isLocked()&&canvas()?.contains(event.target))stop(event);}
 function keydown(event){
  if(!isLocked()||!canvas()?.contains(document.activeElement))return;
  const key=(event.key||'').toLowerCase();
  if(['arrowleft','arrowright','arrowup','arrowdown','a','d','w','s','+','=','-','_','0'].includes(key))stop(event);
 }

 function installGuard(){
  if(guardInstalled)return;
  guardInstalled=true;
  window.addEventListener('pointerdown',pointerDown,{capture:true,passive:false});
  window.addEventListener('pointermove',pointerMove,{capture:true,passive:false});
  window.addEventListener('pointerup',pointerEnd,{capture:true,passive:false});
  window.addEventListener('pointercancel',pointerEnd,{capture:true,passive:false});
  window.addEventListener('wheel',wheel,{capture:true,passive:false});
  window.addEventListener('keydown',keydown,true);
 }

 function start(){
  installStyle();sync();
  observer=new MutationObserver(()=>requestAnimationFrame(sync));
  observer.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['style','class']});
  window.addEventListener('resize',()=>requestAnimationFrame(sync));
 }

 // Register the lock boundary immediately so later viewer/optics scripts never
 // receive locked camera gestures first. DOM-dependent table work can wait.
 installGuard();
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
