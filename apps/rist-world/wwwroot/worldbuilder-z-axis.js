import * as core from './worldbuilder-z-axis-core.js';

export const viewerPoint=core.viewerPoint;
export const viewerGridPoint=core.viewerGridPoint;
export const beginQuickPointerDrop=core.beginQuickPointerDrop;

export function attach(element,dotnet){
 if(!element)return core.attach(element,dotnet);
 const studio=element.closest('.worldbuilder-studio');
 let active=null;
 let disposed=false;

 const style=document.createElement('style');
 style.id='rist-worldbuilder-mahjong-picking';
 style.textContent=`
  .worldbuilder-studio .world-stage .tile-cell,
  .worldbuilder-studio .world-stage .tile-cell *{
   -webkit-touch-callout:none!important;
   -webkit-user-select:none!important;
   user-select:none!important;
   -webkit-user-drag:none!important;
   touch-action:none!important;
  }
 `;
 document.head.appendChild(style);

 const stage=()=>studio?.querySelector('.world-stage');
 const tiles=()=>studio?[...studio.querySelectorAll('.world-stage .tile-cell')]:[];
 const isBlocked=target=>!!target?.closest?.('.studio-mini-panel,.studio-load-panel,.studio-library-shade,.recursion-cockpit,.desktop-map-zoom,.locked-tile-menu,.recursive-region-actions');
 const tileAtPoint=(x,y)=>{
  const list=tiles();
  for(let i=list.length-1;i>=0;i--){
   const r=list[i].getBoundingClientRect();
   if(x>=r.left&&x<=r.right&&y>=r.top&&y<=r.bottom)return list[i];
  }
  return null;
 };
 const worldPoint=(x,y)=>{
  const s=stage();if(!s)return null;
  const r=s.getBoundingClientRect();
  if(r.width<1||r.height<1)return null;
  const px=(x-r.left)/r.width,py=(y-r.top)/r.height;
  if(px<0||px>1||py<0||py>1)return null;
  return [px,py];
 };
 const syncButtons=selected=>{
  const set=new Set((selected||[]).map(Number));
  tiles().forEach((tile,index)=>tile.classList.toggle('wb-selected',set.has(index)));
  for(const name of ['rotate','resize','remove']){
   const button=studio?.querySelector(`[data-wb-command="${name}"]`);
   if(button)button.disabled=set.size<1;
  }
  const remove=studio?.querySelector('[data-wb-command="remove"] small');
  if(remove)remove.textContent=`${set.size} Selected`;
  return [...set];
 };
 const pick=async(x,y,additive)=>{
  const p=worldPoint(x,y);if(!p)return [];
  try{
   const selected=await dotnet.invokeMethodAsync('SelectPlacedTileAtWorldPoint',p[0],p[1],!!additive);
   return syncButtons(selected||[]);
  }catch{return [];}
 };

 const onPointerDown=e=>{
  if(disposed||!studio||isBlocked(e.target))return;
  const s=stage();if(!s||!s.contains(e.target)&&!element.contains(e.target))return;
  const tile=tileAtPoint(e.clientX,e.clientY);
  if(!tile)return;
  const rect=tile.getBoundingClientRect();
  const additive=!!(e.shiftKey||e.ctrlKey||e.metaKey);
  active={id:e.pointerId,tile,startX:e.clientX,startY:e.clientY,lastX:e.clientX,lastY:e.clientY,grabX:e.clientX-rect.left,grabY:e.clientY-rect.top,moved:false,index:-1,pickPromise:null};
  active.pickPromise=pick(e.clientX,e.clientY,additive).then(selected=>{if(active&&active.id===e.pointerId)active.index=selected.length?selected[selected.length-1]:-1;return selected;});
  e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();
 };
 const onPointerMove=e=>{
  if(!active||e.pointerId!==active.id)return;
  const distance=Math.abs(e.clientX-active.startX)+Math.abs(e.clientY-active.startY);
  active.lastX=e.clientX;active.lastY=e.clientY;
  if(distance>8){active.moved=true;active.tile.classList.add('wb-moving');}
  e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();
 };
 const finish=async(e,cancel)=>{
  if(!active||e.pointerId!==active.id)return;
  const current=active;active=null;
  current.tile.classList.remove('wb-moving');
  e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();
  if(cancel)return;
  const selected=await current.pickPromise;
  const index=current.index>=0?current.index:(selected?.length?selected[selected.length-1]:-1);
  if(current.moved&&index>=0){
   try{
    const next=await dotnet.invokeMethodAsync('MovePlacedTileFromJs',index,e.clientX-current.grabX+.5,e.clientY-current.grabY+.5);
    syncButtons(next||[]);
   }catch{}
  }
 };
 const onPointerUp=e=>{if(active&&e.pointerId===active.id)void finish(e,false);};
 const onPointerCancel=e=>{if(active&&e.pointerId===active.id)void finish(e,true);};
 const onContextMenu=e=>{
  const s=stage();if(!s)return;
  if(tileAtPoint(e.clientX,e.clientY)){
   e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();
  }
 };
 const onDragStart=e=>{
  if(e.target?.closest?.('.world-stage .tile-cell')){e.preventDefault();e.stopPropagation();}
 };

 // Register before the legacy binding so this becomes the sole placed-tile interaction authority.
 document.addEventListener('pointerdown',onPointerDown,{capture:true,passive:false});
 document.addEventListener('pointermove',onPointerMove,{capture:true,passive:false});
 document.addEventListener('pointerup',onPointerUp,{capture:true,passive:false});
 document.addEventListener('pointercancel',onPointerCancel,{capture:true,passive:false});
 document.addEventListener('contextmenu',onContextMenu,true);
 document.addEventListener('dragstart',onDragStart,true);

 const coreBinding=core.attach(element,dotnet);
 return {dispose(){
  disposed=true;active=null;
  document.removeEventListener('pointerdown',onPointerDown,true);
  document.removeEventListener('pointermove',onPointerMove,true);
  document.removeEventListener('pointerup',onPointerUp,true);
  document.removeEventListener('pointercancel',onPointerCancel,true);
  document.removeEventListener('contextmenu',onContextMenu,true);
  document.removeEventListener('dragstart',onDragStart,true);
  style.remove();
  try{coreBinding?.dispose?.();}catch{}
 }};
}
