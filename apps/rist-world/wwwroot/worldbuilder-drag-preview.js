(()=>{
 'use strict';
 let drag=null;
 let target=null;
 let loupe=null;
 let prompt=null;
 let redispatching=false;

 const studio=()=>document.querySelector('.worldbuilder-studio');
 const stage=()=>studio()?.querySelector('.world-stage');
 const footprint=()=>{
  const value=Number(studio()?.querySelector('.tile-size-button')?.dataset.footprint);
  return Math.max(1,Math.min(Number.isFinite(value)?value:1,30));
 };
 const placementPoint=(x,y)=>({x,y:y-92});
 const loupePoint=(x,y)=>{
  const side=x<window.innerWidth/2?1:-1;
  return {x:Math.max(72,Math.min(window.innerWidth-72,x+(side*94))),y:Math.max(78,Math.min(window.innerHeight-78,y-178))};
 };
 const clearPreview=()=>{target?.remove();target=null;loupe?.remove();loupe=null;};
 const clearPrompt=()=>{prompt?.remove();prompt=null;};

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
  return {inside:true,rect,cells,cellWidth,cellHeight,x:rect.left+column*cellWidth,y:rect.top+row*cellHeight,width:cellWidth*cells,height:cellHeight*cells};
 };

 const overlapsPlacedTile=geometry=>{
  if(!geometry?.inside)return false;
  const x=geometry.x+(geometry.width/2);
  const y=geometry.y+(geometry.height/2);
  return document.elementsFromPoint(x,y).some(el=>el.classList?.contains('tile-cell'));
 };

 const updateLoupeWorld=geometry=>{
  if(!loupe||!geometry?.inside)return;
  const world=loupe._world;
  const tile=loupe._tile;
  if(!world||!tile)return;
  const mag=2.35;
  const centerX=(geometry.x-geometry.rect.left)+(geometry.width/2);
  const centerY=(geometry.y-geometry.rect.top)+(geometry.height/2);
  world.style.setProperty('width',`${geometry.rect.width}px`,'important');
  world.style.setProperty('height',`${geometry.rect.height}px`,'important');
  world.style.setProperty('left','0','important');
  world.style.setProperty('top','0','important');
  world.style.setProperty('inset','auto','important');
  world.style.setProperty('transform-origin','0 0','important');
  world.style.setProperty('transform',`translate(${66-centerX*mag}px,${66-centerY*mag}px) scale(${mag})`,'important');
  tile.style.left=`${geometry.x-geometry.rect.left}px`;
  tile.style.top=`${geometry.y-geometry.rect.top}px`;
  tile.style.width=`${geometry.width}px`;
  tile.style.height=`${geometry.height}px`;
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
  updateLoupeWorld(geometry);
 };

 const createPreview=(button,x,y)=>{
  clearPreview();
  const sourceStage=stage();
  if(!sourceStage)return;
  target=document.createElement('div');
  target.className='wb-placement-target';
  target.setAttribute('aria-hidden','true');
  document.body.appendChild(target);

  loupe=document.createElement('div');
  loupe.className='wb-placement-loupe';
  loupe.setAttribute('aria-hidden','true');
  const glass=document.createElement('div');
  glass.className='wb-placement-loupe-glass';

  const world=sourceStage.cloneNode(true);
  world.classList.add('wb-placement-loupe-world');
  world.querySelectorAll('[id]').forEach(el=>el.removeAttribute('id'));
  const tile=document.createElement('div');
  tile.className='wb-placement-loupe-tile';
  const img=button.querySelector('img');
  if(img){const copy=document.createElement('img');copy.src=img.src;copy.alt='';copy.draggable=false;tile.appendChild(copy);}
  world.appendChild(tile);
  glass.appendChild(world);
  loupe._world=world;
  loupe._tile=tile;

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

 const dispatchPlacement=(e,options)=>{
  const point=placementPoint(e.clientX,e.clientY);
  window.ristPlacement?.set(options||{upperLayer:false,treatment:'normal'});
  redispatching=true;
  try{
   const synthetic=new PointerEvent('pointerup',{bubbles:true,cancelable:true,composed:true,pointerId:e.pointerId,pointerType:e.pointerType,isPrimary:e.isPrimary,clientX:point.x,clientY:point.y,screenX:e.screenX,screenY:e.screenY,button:e.button,buttons:0,pressure:0});
   document.dispatchEvent(synthetic);
  }finally{redispatching=false;}
 };

 const showPlacementPrompt=e=>{
  clearPrompt();
  clearPreview();
  let upper=false;
  let treatment='normal';
  prompt=document.createElement('div');
  prompt.className='wb-placement-prompt';
  prompt.innerHTML=`<section role="dialog" aria-modal="true" aria-label="Tile placement options"><h3>Place over existing terrain?</h3><p>This position already contains terrain.</p><div class="wb-layer-choice"><button type="button" data-layer="same" class="active">Same layer</button><button type="button" data-layer="upper">Upper layer</button></div><p class="wb-layer-warning">Upper Layer places this tile one Z layer above. You must navigate to that layer to see or edit it.</p><strong>Edge treatment</strong><div class="wb-treatment-choice"><button type="button" data-treatment="normal" class="active">Normal</button><button type="button" data-treatment="blend">Blend</button><button type="button" data-treatment="crop">Crop</button></div><div class="wb-placement-actions"><button type="button" data-action="cancel">Cancel</button><button type="button" data-action="apply" class="apply">Apply</button></div></section>`;
  prompt.addEventListener('click',event=>{
   const b=event.target.closest('button');if(!b)return;
   if(b.dataset.layer){upper=b.dataset.layer==='upper';prompt.querySelectorAll('[data-layer]').forEach(x=>x.classList.toggle('active',x===b));return;}
   if(b.dataset.treatment){treatment=b.dataset.treatment;prompt.querySelectorAll('[data-treatment]').forEach(x=>x.classList.toggle('active',x===b));return;}
   if(b.dataset.action==='cancel'){clearPrompt();return;}
   if(b.dataset.action==='apply'){clearPrompt();dispatchPlacement(e,{upperLayer:upper,treatment});}
  });
  document.body.appendChild(prompt);
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
  drag=null;
  if(current.moved&&e.type==='pointerup'&&e.isTrusted){
   const point=placementPoint(e.clientX,e.clientY);
   const geometry=snappedGeometry(point.x,point.y);
   e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();
   if(overlapsPlacedTile(geometry))showPlacementPrompt(e);
   else{clearPreview();dispatchPlacement(e,{upperLayer:false,treatment:'normal'});}
   return;
  }
  clearPreview();
 };

 const style=document.createElement('style');
 style.textContent=`
  .wb-quick-drag-ghost{opacity:0!important}
  .wb-placement-target{position:fixed;z-index:2147482998;pointer-events:none;box-sizing:border-box;border:2px solid rgba(255,230,156,.96);background:rgba(255,255,255,.025);box-shadow:0 0 0 1px rgba(5,9,12,.75),inset 0 0 18px rgba(255,230,156,.08);transform:translate(-50%,-50%);transition:width 45ms linear,height 45ms linear}.wb-placement-target.snapped{transform:none}.wb-placement-target::before,.wb-placement-target::after{content:"";position:absolute;pointer-events:none;background:rgba(255,230,156,.92)}.wb-placement-target::before{left:50%;top:-7px;bottom:-7px;width:1px;transform:translateX(-50%)}.wb-placement-target::after{top:50%;left:-7px;right:-7px;height:1px;transform:translateY(-50%)}
  .wb-placement-loupe{position:fixed;z-index:2147483002;pointer-events:none;width:132px;height:148px;transform:translate(-50%,-50%);display:grid;grid-template-rows:132px 16px;place-items:center;filter:drop-shadow(0 10px 18px #000c)}.wb-placement-loupe-glass{position:relative;box-sizing:border-box;width:132px;height:132px;border:3px solid #f0d37f;border-radius:50%;overflow:hidden;background:#071015;box-shadow:inset 0 0 0 2px #17252e,0 0 0 1px #000}.wb-placement-loupe-world{position:absolute!important;pointer-events:none!important;margin:0!important}.wb-placement-loupe-world .tile-cell{pointer-events:none!important}.wb-placement-loupe-tile{position:absolute;z-index:50;overflow:hidden;box-shadow:0 0 0 1px #fff0aa}.wb-placement-loupe-tile img{width:100%;height:100%;object-fit:fill;display:block;user-select:none;-webkit-user-drag:none}.wb-placement-loupe-cross::before,.wb-placement-loupe-cross::after{content:"";position:absolute;z-index:100;background:#fff0aa;box-shadow:0 0 2px #000}.wb-placement-loupe-cross::before{left:50%;top:6px;bottom:6px;width:1px}.wb-placement-loupe-cross::after{top:50%;left:6px;right:6px;height:1px}.wb-placement-loupe-size{display:grid;place-items:center;min-width:42px;height:16px;margin-top:-2px;padding:0 6px;border-radius:8px;background:#071015;border:1px solid #d7be80;color:#f3dfa7;font:900 9px/16px system-ui}.wb-placement-loupe.outside{opacity:.55}
  .wb-placement-prompt{position:fixed;inset:0;z-index:2147483600;display:grid;place-items:center;padding:18px;background:rgba(2,7,11,.72);backdrop-filter:blur(4px);font-family:system-ui,-apple-system,sans-serif}.wb-placement-prompt section{box-sizing:border-box;width:min(92vw,420px);padding:18px;border:1px solid #d7be80;border-radius:14px;background:#081117;color:#d9e1e5;box-shadow:0 18px 50px #000c}.wb-placement-prompt h3{margin:0 0 8px;color:#f0d37f}.wb-placement-prompt p{margin:7px 0;color:#aebdc5;font-size:13px;line-height:1.35}.wb-placement-prompt .wb-layer-warning{color:#e7c36d}.wb-placement-prompt strong{display:block;margin-top:12px;color:#e9d69c;font-size:12px}.wb-layer-choice,.wb-treatment-choice,.wb-placement-actions{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap}.wb-placement-prompt button{min-height:42px;flex:1 1 90px;border:1px solid #536975;border-radius:8px;background:#0e1920;color:#d7e0e4;font-weight:800}.wb-placement-prompt button.active{border-color:#e1bd62;background:#28210f;color:#ffe7a1}.wb-placement-actions{margin-top:16px}.wb-placement-actions .apply{border-color:#d7be80;color:#ffe4a0}
 `;
 document.head.appendChild(style);
 document.addEventListener('pointerdown',onDown,{capture:true,passive:true});
 document.addEventListener('pointermove',onMove,{capture:true,passive:true});
 document.addEventListener('pointerup',onFinish,{capture:true,passive:false});
 document.addEventListener('pointercancel',onFinish,{capture:true,passive:true});
 if(!document.querySelector('script[data-rist-wb-navigation]')){const nav=document.createElement('script');nav.src='worldbuilder-navigation-authority.js?v=20260909-z-pan-scale-1';nav.dataset.ristWbNavigation='1';document.head.appendChild(nav);}
})();
