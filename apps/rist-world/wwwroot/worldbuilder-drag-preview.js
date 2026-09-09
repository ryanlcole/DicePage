(()=>{
 'use strict';
 let drag=null;
 let preview=null;

 const studio=()=>document.querySelector('.worldbuilder-studio');
 const stage=()=>studio()?.querySelector('.world-stage');
 const footprint=()=>{
  const text=studio()?.querySelector('.tile-size-button strong')?.textContent||'1';
  const value=parseInt(text,10);
  return Math.max(1,Math.min(Number.isFinite(value)?value:1,30));
 };
 const removePreview=()=>{preview?.remove();preview=null;};
 const createPreview=(button,x,y)=>{
  removePreview();
  const grid=stage();
  if(!grid)return;
  const rect=grid.getBoundingClientRect();
  if(rect.width<1||rect.height<1)return;
  const cells=footprint();
  preview=document.createElement('div');
  preview.className='wb-sized-drag-preview';
  preview.style.width=`${rect.width/30*cells}px`;
  preview.style.height=`${rect.height/30*cells}px`;
  const img=button.querySelector('img');
  if(img){const copy=document.createElement('img');copy.src=img.src;copy.alt='';preview.appendChild(copy);}
  document.body.appendChild(preview);
  movePreview(x,y);
 };
 const movePreview=(x,y)=>{if(preview){preview.style.left=`${x}px`;preview.style.top=`${y}px`;}};

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
  .wb-sized-drag-preview{position:fixed;z-index:2147483001;pointer-events:none;box-sizing:border-box;transform:translate(-50%,-50%);overflow:hidden;border:2px solid #f2cf72;border-radius:3px;background:#0d171e;box-shadow:0 8px 24px #000a;opacity:.88}
  .wb-sized-drag-preview img{display:block;width:100%;height:100%;object-fit:fill;pointer-events:none;user-select:none;-webkit-user-drag:none}
 `;
 document.head.appendChild(style);
 document.addEventListener('pointerdown',onDown,{capture:true,passive:true});
 document.addEventListener('pointermove',onMove,{capture:true,passive:true});
 document.addEventListener('pointerup',finish,{capture:true,passive:true});
 document.addEventListener('pointercancel',finish,{capture:true,passive:true});
})();