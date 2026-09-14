(()=>{
 'use strict';

 const catalogUrl='assets/sprites/catalog.json?v=20260914-raster-sprites-1';
 const sheets=new Map();
 let tracked=new Map();
 let raf=0;
 let observer=null;
 const reducedMotion=window.matchMedia?.('(prefers-reduced-motion: reduce)')??null;

 const number=(value,fallback=0)=>{
  const n=Number(value);
  return Number.isFinite(n)?n:fallback;
 };

 function canonicalUrl(value){
  try{
   const url=new URL(value,document.baseURI);
   url.hash='';
   url.search='';
   return url.href;
  }catch{return String(value??'');}
 }

 function read(asset,camel,pascal){return asset?.[camel]??asset?.[pascal];}

 function rasterSheetMetadata(asset){
  const kind=String(read(asset,'assetKind','AssetKind')??'').toLowerCase();
  const frameCount=Math.max(1,Math.floor(number(read(asset,'frameCount','FrameCount'),1)));
  const fps=Math.max(0,number(read(asset,'framesPerSecond','FramesPerSecond'),0));
  const sourceWidth=Math.floor(number(read(asset,'sourceWidth','SourceWidth'),0));
  const sourceHeight=Math.floor(number(read(asset,'sourceHeight','SourceHeight'),0));
  const cropX=Math.floor(number(read(asset,'cropX','CropX'),0));
  const cropY=Math.floor(number(read(asset,'cropY','CropY'),0));
  const cropWidth=Math.floor(number(read(asset,'cropWidth','CropWidth'),0));
  const cropHeight=Math.floor(number(read(asset,'cropHeight','CropHeight'),0));

  // Vector/internal animations (for example the fountain SVG) intentionally fall
  // through here. Only raster sheets with explicit frame geometry are advanced.
  if(kind!=='sprite'||frameCount<=1||fps<=0||sourceWidth<=0||sourceHeight<=0||cropWidth<=0||cropHeight<=0)return null;

  const columns=Math.max(1,Math.floor((sourceWidth-cropX)/cropWidth));
  const rows=Math.max(1,Math.floor((sourceHeight-cropY)/cropHeight));
  if(columns*rows<frameCount)return null;

  return {
   frameCount,
   fps,
   columns,
   rows,
   sourceWidth,
   sourceHeight,
   cropWidth,
   cropHeight,
   baseX:cropX/cropWidth,
   baseY:cropY/cropHeight
  };
 }

 function findMetadata(img){
  const src=img.currentSrc||img.getAttribute('src')||img.src;
  return sheets.get(canonicalUrl(src));
 }

 function scan(){
  const next=new Map();
  const images=document.querySelectorAll('.tile-image-crop img, .map-asset-preview img');
  for(const img of images){
   const meta=findMetadata(img);
   if(!meta)continue;
   const previous=tracked.get(img);
   next.set(img,{...meta,lastFrame:previous?.lastFrame??-1});
   img.dataset.ristSpriteSheet='true';
  }
  tracked=next;
  schedule();
 }

 function paint(img,state,frame){
  const column=frame%state.columns;
  const row=Math.floor(frame/state.columns);
  img.style.position='absolute';
  img.style.width=`${state.sourceWidth*100/state.cropWidth}%`;
  img.style.height=`${state.sourceHeight*100/state.cropHeight}%`;
  img.style.left=`${-(state.baseX+column)*100}%`;
  img.style.top=`${-(state.baseY+row)*100}%`;
  img.style.maxWidth='none';
  img.style.maxHeight='none';
  img.dataset.ristSpriteFrame=String(frame);
  state.lastFrame=frame;
 }

 function render(now){
  raf=0;
  if(document.hidden)return;
  const freeze=reducedMotion?.matches===true;
  let animate=false;

  for(const [img,state] of tracked){
   if(!img.isConnected)continue;
   // All sheets use the same monotonic clock. Matching FPS sheets therefore stay
   // phase-locked, which lets a transparent crest layer track its base ocean layer.
   const frame=freeze?0:Math.floor((now/1000)*state.fps)%state.frameCount;
   if(frame!==state.lastFrame)paint(img,state,frame);
   if(!freeze)animate=true;
  }

  if(animate)raf=requestAnimationFrame(render);
 }

 function schedule(){
  if(document.hidden||raf||tracked.size===0)return;
  raf=requestAnimationFrame(render);
 }

 async function loadCatalog(){
  try{
   const response=await fetch(catalogUrl,{cache:'no-store'});
   if(!response.ok)return;
   const assets=await response.json();
   sheets.clear();
   for(const asset of Array.isArray(assets)?assets:[]){
    const meta=rasterSheetMetadata(asset);
    const image=read(asset,'image','Image');
    if(meta&&image)sheets.set(canonicalUrl(image),meta);
   }
   scan();
  }catch{
   // Failure leaves ordinary static/vector assets untouched.
  }
 }

 function onVisibility(){
  if(document.hidden){if(raf){cancelAnimationFrame(raf);raf=0;}}
  else{scan();schedule();}
 }

 observer=new MutationObserver(scan);
 observer.observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['src']});
 document.addEventListener('visibilitychange',onVisibility,{passive:true});
 window.addEventListener('pageshow',scan,{passive:true});
 reducedMotion?.addEventListener?.('change',()=>{for(const state of tracked.values())state.lastFrame=-1;schedule();});

 window.ristSpriteSheets={
  refresh:scan,
  reload:loadCatalog,
  count:()=>tracked.size,
  registered:()=>sheets.size
 };

 loadCatalog();
})();
