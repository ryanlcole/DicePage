(()=>{
 'use strict';
 let drag=null;
 let preview=null;

 const studio=()=>document.querySelector('.worldbuilder-studio');
 const stage=()=>studio()?.querySelector('.world-stage');
 const footprint=()=>{
  const value=Number(studio()?.querySelector('.tile-size-button')?.dataset.footprint);
  return Math.max(1,Math.min(Number.isFinite(value)?value:1,30));
 };
 const removePreview=()=>{preview?.remove();preview=null;};
 const placePreview=(x,y)=>{
  if(!preview)return;
  const grid=stage();
  const rect=grid?.getBoundingClientRect();
  if(!rect||rect.width<1||rect.height<1)return;
  const cells=footprint();
  const cellWidth=rect.width/30;
  const cellHeight=rect.height/30;
  preview.style.width=`${cellWidth*cells}px`;
  preview.style.height=`${cellHeight*cells}px`;
  const inside=x>=rect.left&&x<=rect.right&&y>=rect.top&&y<=rect.bottom;
  if(inside){
   const column=Math.max(0,Math.min(30-cells,Math.floor((x-rect.left)/cellWidth)));
   const row=Math.max(0,Math.min(30-cells,Math.floor((y-rect.top)/cellHeight)));
   preview.style.left=`${rect.left+column*cellWidth}px`;
   preview.style.top=`${rect.top+row*cellHeight}px`;
   preview.classList.add('snapped');
  }else{
   preview.style.left=`${x}px`;
   preview.style.top=`${y}px`;
   preview.classList.remove('snapped');
  }
 };
 const createPreview=(button,x,y)=>{
  removePreview();
  const grid=stage();
  if(!grid)return;
  const rect=grid.getBoundingClientRect();
  if(rect.width<1||rect.height<1)return;
  preview=document.createElement('div');
  preview.className='wb-sized-drag-preview';
  const img=button.querySelector('img');
  if(img){const copy=document.createElement('img');copy.src=img.src;copy.alt='';preview.appendChild(copy);}
  document.body.appendChild(preview);
  placePreview(x,y);
 };
 const movePreview=(x,y)=>placePreview(x,y);

 const onDown=e=>{
  if(e.pointerType==='mouse')return;
  const button=e.target?.closest?.('.worldbuilder-studio .quick-slot.filled');
  if(!button)return;
  drag={id:e.pointerId,x:e.clientX,y:e.clientY,button,moved:false};
 };
 const onMove=e=>{
  if(!drag||e.pointerId!==drag.id)return;
  const distance=Math.abs(e.clientX-drag.x)+Math.abs(e.clientY-drag.y);
  if(!drag.moved&&distance>6){drag.moved=true;createPreview(drag.button,e.clientX,e.clientY);}
  if(drag.moved)movePreview(e.clientX,e.clientY);
 };
 const finish=e=>{if(!drag||e.pointerId!==drag.id)return;drag=null;removePreview();};

 const style=document.createElement('style');
 style.textContent=`
  .wb-quick-drag-ghost{opacity:0!important}
  .wb-sized-drag-preview{position:fixed;z-index:2147483001;pointer-events:none;box-sizing:border-box;transform:translate(-50%,-50%);overflow:hidden;border:1px solid rgba(215,199,145,.92);border-radius:0;background:#0d171e;box-shadow:0 8px 24px #000a;opacity:.88}
  .wb-sized-drag-preview.snapped{transform:none;box-shadow:none;opacity:1}
  .wb-sized-drag-preview img{display:block;width:100%;height:100%;object-fit:fill;pointer-events:none;user-select:none;-webkit-user-drag:none}
 `;
 document.head.appendChild(style);
 document.addEventListener('pointerdown',onDown,{capture:true,passive:true});
 document.addEventListener('pointermove',onMove,{capture:true,passive:true});
 document.addEventListener('pointerup',finish,{capture:true,passive:true});
 document.addEventListener('pointercancel',finish,{capture:true,passive:true});
})();
