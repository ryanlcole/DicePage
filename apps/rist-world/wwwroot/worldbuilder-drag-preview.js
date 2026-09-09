(()=>{
 'use strict';
 let drag=null;
 let target=null;
 let loupe=null;
 let redispatching=false;

 const studio=()=>document.querySelector('.worldbuilder-studio');
 const stage=()=>studio()?.querySelector('.world-stage');
 const footprint=()=>{
  const value=Number(studio()?.querySelector('.tile-size-button')?.dataset.footprint);
  return Math.max(1,Math.min(Number.isFinite(value)?value:1,30));
 };

 // The touch is the handle, not the placement point. Keep the destination above
 // the thumb so the user can see exactly where the tile will land.
 const placementPoint=(x,y)=>({x,y:y-92});
 const loupePoint=(x,y)=>{
  const side=x<window.innerWidth/2?1:-1;
  return {
   x:Math.max(72,Math.min(window.innerWidth-72,x+(side*94))),
   y:Math.max(78,Math.min(window.innerHeight-78,y-178))
  };
 };
 const clearPreview=()=>{target?.remove();target=null;loupe?.remove();loupe=null;};

 const snappedGeometry=(x,y)=>{
  const grid=stage();
  const rect=grid?.getBoundingClientRect();
  if(!rect||rect.width<1||rect.height<1)return null;
  const cells=footprint();
  const cellWidth=rect.width/30;
  const cellHeight=rect.height/30;
  const inside=x>=rect.left&&x<=rect.right&&y>=rect.top&&y<=rect.bottom;
  if(!inside)return {inside:false,rect,cells,cellWidth,cellHeight,x,y};
  const column=Math.max(0,Math.min(30-cells,Math.floor((x-rect.left)/cellWidth)));
  const row=Math.max(0,Math.min(30-cells,Math.floor((y-rect.top)/cellHeight)));
  return {
   inside:true,rect,cells,cellWidth,cellHeight,
   x:rect.left+column*cellWidth,
   y:rect.top+row*cellHeight,
   width:cellWidth*cells,
   height:cellHeight*cells
  };
 };

 const updatePreview=(fingerX,fingerY)=>{
  if(!target||!loupe)return;
  const point=placementPoint(fingerX,fingerY);
  const geometry=snappedGeometry(point.x,point.y);
  if(!geometry)return;

  target.classList.toggle('snapped',geometry.inside);
  target.style.width=`${geometry.inside?geometry.width:Math.max(24,geometry.cellWidth*geometry.cells)}px`;
  target.style.height=`${geometry.inside?geometry.height:Math.max(24,geometry.cellHeight*geometry.cells)}px`;
  target.style.left=`${geometry.x}px`;
  target.style.top=`${geometry.y}px`;

  const lp=loupePoint(fingerX,fingerY);
  loupe.style.left=`${lp.x}px`;
  loupe.style.top=`${lp.y}px`;
  loupe.classList.toggle('outside',!geometry.inside);

  const size=loupe.querySelector('.wb-placement-loupe-size');
  if(size)size.textContent=`${geometry.cells}×${geometry.cells}`;
 };

 const createPreview=(button,x,y)=>{
  clearPreview();
  if(!stage())return;

  target=document.createElement('div');
  target.className='wb-placement-target';
  target.setAttribute('aria-hidden','true');
  document.body.appendChild(target);

  loupe=document.createElement('div');
  loupe.className='wb-placement-loupe';
  loupe.setAttribute('aria-hidden','true');

  const glass=document.createElement('div');
  glass.className='wb-placement-loupe-glass';
  const img=button.querySelector('img');
  if(img){
   const copy=document.createElement('img');
   copy.src=img.src;
   copy.alt='';
   copy.draggable=false;
   glass.appendChild(copy);
  }
  const cross=document.createElement('span');
  cross.className='wb-placement-loupe-cross';
  glass.appendChild(cross);
  loupe.appendChild(glass);

  const size=document.createElement('small');
  size.className='wb-placement-loupe-size';
  loupe.appendChild(size);
  document.body.appendChild(loupe);
  updatePreview(x,y);
 };

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
  if(drag.moved)updatePreview(e.clientX,e.clientY);
 };
 const onFinish=e=>{
  if(redispatching||!drag||e.pointerId!==drag.id)return;
  const current=drag;

  // The existing world-builder placement handler owns the actual commit. Replace
  // the release coordinate with the visible target coordinate so what the loupe
  // shows is exactly where the tile is created.
  if(current.moved&&e.type==='pointerup'&&e.isTrusted){
   const point=placementPoint(e.clientX,e.clientY);
   e.preventDefault();
   e.stopPropagation();
   e.stopImmediatePropagation();
   redispatching=true;
   try{
    const synthetic=new PointerEvent('pointerup',{
     bubbles:true,cancelable:true,composed:true,
     pointerId:e.pointerId,pointerType:e.pointerType,isPrimary:e.isPrimary,
     clientX:point.x,clientY:point.y,
     screenX:e.screenX,screenY:e.screenY,
     button:e.button,buttons:0,pressure:0
    });
    document.dispatchEvent(synthetic);
   }finally{redispatching=false;}
  }

  drag=null;
  clearPreview();
 };

 const style=document.createElement('style');
 style.textContent=`
  .wb-quick-drag-ghost{opacity:0!important}
  .wb-placement-target{position:fixed;z-index:2147482998;pointer-events:none;box-sizing:border-box;border:2px solid rgba(255,230,156,.96);background:rgba(255,255,255,.025);box-shadow:0 0 0 1px rgba(5,9,12,.75),inset 0 0 18px rgba(255,230,156,.08);transform:translate(-50%,-50%);transition:width 45ms linear,height 45ms linear}
  .wb-placement-target.snapped{transform:none}
  .wb-placement-target::before,.wb-placement-target::after{content:"";position:absolute;pointer-events:none;background:rgba(255,230,156,.92)}
  .wb-placement-target::before{left:50%;top:-7px;bottom:-7px;width:1px;transform:translateX(-50%)}
  .wb-placement-target::after{top:50%;left:-7px;right:-7px;height:1px;transform:translateY(-50%)}
  .wb-placement-loupe{position:fixed;z-index:2147483002;pointer-events:none;width:132px;height:148px;transform:translate(-50%,-50%);display:grid;grid-template-rows:132px 16px;place-items:center;filter:drop-shadow(0 10px 18px #000c)}
  .wb-placement-loupe-glass{position:relative;box-sizing:border-box;width:132px;height:132px;border:3px solid #f0d37f;border-radius:50%;overflow:hidden;background:#071015;box-shadow:inset 0 0 0 2px #17252e,0 0 0 1px #000}
  .wb-placement-loupe-glass::after{content:"";position:absolute;inset:0;pointer-events:none;background-image:linear-gradient(to right,rgba(235,219,167,.22) 1px,transparent 1px),linear-gradient(to bottom,rgba(235,219,167,.22) 1px,transparent 1px);background-size:22px 22px}
  .wb-placement-loupe img{position:absolute;inset:10px;width:calc(100% - 20px);height:calc(100% - 20px);object-fit:fill;display:block;user-select:none;-webkit-user-drag:none}
  .wb-placement-loupe-cross::before,.wb-placement-loupe-cross::after{content:"";position:absolute;z-index:3;background:#fff0aa;box-shadow:0 0 2px #000}
  .wb-placement-loupe-cross::before{left:50%;top:6px;bottom:6px;width:1px}.wb-placement-loupe-cross::after{top:50%;left:6px;right:6px;height:1px}
  .wb-placement-loupe-size{display:grid;place-items:center;min-width:42px;height:16px;margin-top:-2px;padding:0 6px;border-radius:8px;background:#071015;border:1px solid #d7be80;color:#f3dfa7;font:900 9px/16px system-ui}
  .wb-placement-loupe.outside{opacity:.55}
 `;
 document.head.appendChild(style);
 document.addEventListener('pointerdown',onDown,{capture:true,passive:true});
 document.addEventListener('pointermove',onMove,{capture:true,passive:true});
 document.addEventListener('pointerup',onFinish,{capture:true,passive:false});
 document.addEventListener('pointercancel',onFinish,{capture:true,passive:true});

 if(!document.querySelector('script[data-rist-wb-navigation]')){
  const nav=document.createElement('script');
  nav.src='worldbuilder-navigation-authority.js?v=20260909-z-pan-scale-1';
  nav.dataset.ristWbNavigation='1';
  document.head.appendChild(nav);
 }
})();
