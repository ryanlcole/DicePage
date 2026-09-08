(()=>{
 'use strict';

 const clamp01=value=>Math.max(0,Math.min(.999999,Number(value)||0));
 const safeZoom=value=>Math.max(Number(value)||1,.01);

 function worldPointFromClient(rect,clientX,clientY,panX,panY,zoom){
  const z=safeZoom(zoom);
  const sx=(clientX-rect.left)/rect.width;
  const sy=(clientY-rect.top)/rect.height;
  return [
   ((sx-.5)/z)+.5-(Number(panX)||0)/(rect.width*z),
   ((sy-.5)/z)+.5-(Number(panY)||0)/(rect.height*z)
  ];
 }

 function snapWorldPoint(worldX,worldY,columns,rows){
  const cols=Math.max(1,Number(columns)||30);
  const gridRows=Math.max(1,Number(rows)||30);
  const x=(Math.floor(clamp01(worldX)*cols)+.5)/cols;
  const y=(Math.floor(clamp01(worldY)*gridRows)+.5)/gridRows;
  return [x,y];
 }

 function tileDropPoint(el,clientX,clientY,panX,panY,zoom,columns,rows){
  const rect=el.getBoundingClientRect();
  const inside=clientX>=rect.left&&clientX<=rect.right&&clientY>=rect.top&&clientY<=rect.bottom;
  if(!inside)return [0,0,0];

  // Convert the pointer into authored world coordinates first, then snap there.
  // Screen-space snapping drifts whenever the stage is panned or zoomed.
  const [worldX,worldY]=worldPointFromClient(rect,clientX,clientY,panX,panY,zoom);
  const [snapX,snapY]=snapWorldPoint(worldX,worldY,columns,rows);
  return [1,snapX,snapY];
 }

 const authority={worldPointFromClient,snapWorldPoint,tileDropPoint};
 window.ristWorldCoordinates=authority;

 // Keep the public interop contract stable while moving coordinate ownership
 // out of the legacy utility bundle into one canonical Shaelvien authority.
 if(window.ristWorld)window.ristWorld.tileDropPoint=tileDropPoint;
})();
