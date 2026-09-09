(()=>{
 'use strict';
 let pointer=null;
 let panX=0;
 let panY=0;
 let lastSceneZ=null;
 let observer=null;

 const studio=()=>document.querySelector('.worldbuilder-studio');
 const canvas=()=>studio()?.querySelector('.studio-viewer-canvas');
 const stage=()=>studio()?.querySelector('.world-stage');
 const zButton=()=>[...(studio()?.querySelectorAll('.studio-command-rail button')||[])].find(button=>(button.querySelector('strong')?.textContent||'').trim()==='Z-Lock');
 const zUnlocked=()=>{
  const button=zButton();
  if(!button)return false;
  const label=(button.querySelector('small')?.textContent||'').trim().toLowerCase();
  return label==='unlocked'||!button.classList.contains('active');
 };
 const sceneZ=()=>{
  const text=[...(studio()?.querySelectorAll('.studio-command-rail button small,.studio-mini-panel span')||[])].map(el=>el.textContent||'').join(' ');
  const match=text.match(/(?:^|\s)Z\s*(-?\d+)/i);
  return match?Number(match[1]):null;
 };
 const footprint=()=>Math.max(1,Number(studio()?.querySelector('.tile-size-button')?.dataset.footprint)||1);

 const parseDistance=label=>{
  const match=String(label||'').trim().match(/^([0-9]+(?:\.[0-9]+)?)\s*(Mm|km|m)$/i);
  if(!match)return null;
  const value=Number(match[1]);
  const unit=match[2].toLowerCase();
  return value*(unit==='mm'?1_000_000:unit==='km'?1000:1);
 };
 const formatDistance=meters=>{
  if(meters>=1_000_000)return `${(meters/1_000_000).toFixed(meters%1_000_000===0?0:2).replace(/\.00$/,'')} Mm`;
  if(meters>=1000)return `${(meters/1000).toFixed(meters%1000===0?0:2).replace(/\.00$/,'')} km`;
  return `${Number(meters.toFixed(2))} m`;
 };

 function applyPan(){
  const world=stage();
  if(!world)return;
  world.style.setProperty('--wb-pan-x',`${panX}px`);
  world.style.setProperty('--wb-pan-y',`${panY}px`);
 }

 function syncDistanceAndTileSize(){
  const controls=document.getElementById('viewer-frame-controls');
  const zLabel=controls?.dataset.zLabel||'';
  const meters=parseDistance(zLabel);
  const sizeButton=studio()?.querySelector('.tile-size-button');
  if(sizeButton&&meters){
   let small=sizeButton.querySelector('small');
   if(!small){small=document.createElement('small');sizeButton.appendChild(small);}
   small.textContent=`${formatDistance(meters*footprint())} / tile`;
   sizeButton.title=`Tile footprint: ${footprint()} × ${footprint()} viewer squares · ${formatDistance(meters*footprint())} per side`;
  }
 }

 function syncViewerDistanceFromLayer(){
  const next=sceneZ();
  if(next===null){syncDistanceAndTileSize();return;}
  if(lastSceneZ===null){lastSceneZ=next;syncDistanceAndTileSize();return;}
  if(next!==lastSceneZ){
   const input=document.querySelector('#viewer-frame-controls .viewer-edge-z input[type="range"]');
   if(input){
    const direction=Math.sign(next-lastSceneZ);
    const min=Number(input.min||0),max=Number(input.max||6);
    const value=Math.max(min,Math.min(max,(Number(input.value)||0)+direction));
    if(value!==Number(input.value)){
     input.value=String(value);
     input.dispatchEvent(new Event('input',{bubbles:true}));
    }
   }
   lastSceneZ=next;
  }
  syncDistanceAndTileSize();
 }

 function syncMode(){
  const unlocked=zUnlocked();
  document.documentElement.classList.toggle('rist-wb-z-unlocked',unlocked);
  const view=canvas();
  if(view)view.dataset.zUnlocked=unlocked?'true':'false';
  if(!unlocked){pointer=null;panX=0;panY=0;applyPan();}
  syncViewerDistanceFromLayer();
 }

 function onDown(e){
  if(!zUnlocked()||e.pointerType==='mouse'&&e.button!==0)return;
  if(e.target?.closest?.('.studio-command-slider,.studio-top-slider,.map-frame-controls,.desktop-map-zoom'))return;
  if(pointer)return;
  pointer={id:e.pointerId,x:e.clientX,y:e.clientY};
  canvas()?.setPointerCapture?.(e.pointerId);
 }
 function onMove(e){
  if(!pointer||pointer.id!==e.pointerId||!zUnlocked())return;
  if(e.pointerType==='touch'&&e.isPrimary===false)return;
  const dx=e.clientX-pointer.x,dy=e.clientY-pointer.y;
  pointer.x=e.clientX;pointer.y=e.clientY;
  if(Math.abs(dx)+Math.abs(dy)<.5)return;
  panX+=dx;panY+=dy;applyPan();e.preventDefault();
 }
 function release(e){if(pointer?.id===e.pointerId)pointer=null;}

 const style=document.createElement('style');
 style.id='rist-worldbuilder-z-unlock-navigation';
 style.textContent=`
  .worldbuilder-studio .studio-viewer-canvas .world-stage{
   transform:translate(var(--wb-pan-x,0px),var(--wb-pan-y,0px)) scale(var(--wb-z-scale,1))!important;
  }
  html.rist-wb-z-unlocked .worldbuilder-studio .studio-viewer-canvas{touch-action:none!important;cursor:grab!important}
  html.rist-wb-z-unlocked .worldbuilder-studio .studio-viewer-canvas:active{cursor:grabbing!important}
  html.rist-wb-z-unlocked .worldbuilder-studio .world-stage .tile-cell,
  html.rist-wb-z-unlocked .worldbuilder-studio .world-stage .piece{pointer-events:none!important;cursor:default!important}
  html.rist-wb-z-unlocked .worldbuilder-studio .world-stage .tile-cell::after{display:none!important}
 `;
 document.head.appendChild(style);

 function annotateDepth(){
  const cells=[...(studio()?.querySelectorAll('.world-stage .tile-cell')||[])];
  const source=window.__ristWorldBuilderTileVisuals||[];
  cells.forEach((tile,index)=>{
   const visual=source[index]||{};
   const tier=Number(visual.tierIndex??visual.TierIndex??0);
   const layer=Number(visual.layerOffset??visual.LayerOffset??0);
   tile.dataset.tier=String(tier);
   tile.dataset.layer=String(layer);
   tile.dataset.sceneZ=String((tier*9)+layer);
  });
 }

 const depthObserver=new MutationObserver(()=>requestAnimationFrame(annotateDepth));

 function start(){
  const root=studio();if(!root)return setTimeout(start,100);
  const view=canvas();
  view?.addEventListener('pointerdown',onDown,{passive:true});
  view?.addEventListener('pointermove',onMove,{passive:false});
  view?.addEventListener('pointerup',release,{passive:true});
  view?.addEventListener('pointercancel',release,{passive:true});
  observer=new MutationObserver(()=>requestAnimationFrame(syncMode));
  observer.observe(root,{childList:true,subtree:true,attributes:true,attributeFilter:['class','data-footprint']});
  depthObserver.observe(root,{childList:true,subtree:true});
  syncMode();
  annotateDepth();
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
