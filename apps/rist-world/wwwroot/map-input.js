(()=>{
 'use strict';
 const pointers=new Map();
 let boundMap=null,lastDistance=0;
 const touchLike=e=>e.pointerType==='touch'||e.pointerType==='pen';
 const distance=()=>{const pts=[...pointers.values()];if(pts.length<2)return 0;return Math.hypot(pts[0].x-pts[1].x,pts[0].y-pts[1].y)};
 const midpoint=()=>{const pts=[...pointers.values()];if(pts.length<2)return null;return{x:(pts[0].x+pts[1].x)/2,y:(pts[0].y+pts[1].y)/2}};
 function down(e){if(!touchLike(e))return;pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});if(pointers.size===2)lastDistance=distance()}
 function move(e){if(!pointers.has(e.pointerId))return;pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});if(pointers.size!==2)return;const next=distance(),mid=midpoint();if(!lastDistance||!next||!mid){lastDistance=next;return}const ratio=next/lastDistance;if(Math.abs(ratio-1)<.008)return;e.preventDefault();e.stopPropagation();const deltaY=-Math.log(ratio)*360;boundMap?.dispatchEvent(new WheelEvent('wheel',{bubbles:true,cancelable:true,clientX:mid.x,clientY:mid.y,deltaY,deltaMode:0}));lastDistance=next}
 function end(e){pointers.delete(e.pointerId);if(pointers.size<2)lastDistance=0}
 function bind(map){if(!map||map===boundMap)return;if(boundMap){boundMap.removeEventListener('pointerdown',down,true);boundMap.removeEventListener('pointermove',move,true);boundMap.removeEventListener('pointerup',end,true);boundMap.removeEventListener('pointercancel',end,true)}boundMap=map;pointers.clear();lastDistance=0;map.addEventListener('pointerdown',down,true);map.addEventListener('pointermove',move,{capture:true,passive:false});map.addEventListener('pointerup',end,true);map.addEventListener('pointercancel',end,true)}
 function ensure(){bind(document.querySelector('.release-map-region .map'))}
 const observer=new MutationObserver(ensure);
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>{ensure();observer.observe(document.body,{childList:true,subtree:true})},{once:true});else{ensure();observer.observe(document.body,{childList:true,subtree:true})}
 window.ristMapInput={
  read:()=>{const el=document.querySelector('.release-map-region .map');return el?[Number(el.dataset.panX)||0,Number(el.dataset.panY)||0,Number(el.dataset.zoom)||1]:[0,0,1]},
  refresh:ensure
 };
})();
