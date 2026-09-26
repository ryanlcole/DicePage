(() => {
'use strict';

/*
  ReLiC Image Engine
  ------------------
  Stable browser-facing image-processing boundary for Shaelvien/RIST.

  The editor owns world identity, coordinates, permissions, grouping and
  persistence. Pixel processing is delegated here. A GEGL/WebAssembly adapter
  can register itself as "gegl-wasm" without changing world/editor code.
  Until that module is bundled, the Canvas backend keeps every operation local
  to the device and provides the same contract.
*/

const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
const backends=new Map();
let preferred='auto';

function loadImage(src){
  src=String(src||'');
  return new Promise((resolve,reject)=>{
    const img=new Image();
    img.decoding='async';
    // Image processing reads pixels through Canvas. Remote CDN/presigned images
    // must opt into CORS before src is assigned or the canvas becomes tainted.
    if(src&&!src.startsWith('data:')&&!src.startsWith('blob:'))img.crossOrigin='anonymous';
    img.onload=()=>resolve(img);
    img.onerror=()=>reject(new Error('Image could not be decoded'));
    img.src=src;
  });
}

function canvas(){
  const node=document.createElement('canvas');
  return node;
}

async function makeTransparent(src){
  src=String(src||'');
  if(!src)return'';
  const img=await loadImage(src);
  const max=2048;
  const ratio=Math.min(1,max/Math.max(img.naturalWidth||1,img.naturalHeight||1));
  const w=Math.max(1,Math.round((img.naturalWidth||1)*ratio));
  const h=Math.max(1,Math.round((img.naturalHeight||1)*ratio));
  const out=canvas();out.width=w;out.height=h;
  const ctx=out.getContext('2d',{willReadFrequently:true});
  ctx.clearRect(0,0,w,h);ctx.drawImage(img,0,0,w,h);
  const data=ctx.getImageData(0,0,w,h),px=data.data,count=w*h;

  // Preserve genuinely authored alpha while ignoring a tiny anti-aliased fringe.
  // A single translucent pixel must not disable background removal for an
  // otherwise opaque PNG.
  let authoredAlpha=0;
  for(let i=3;i<px.length;i+=4)if(px[i]<224)authoredAlpha++;
  if(authoredAlpha/Math.max(count,1)>.01)return src;

  // Model GIMP-style "select background from the border": find the dominant
  // border colour, then remove only pixels connected to the image boundary.
  // This avoids deleting matching colours inside the artwork.
  const samples=[],step=Math.max(1,Math.floor(Math.min(w,h)/192));
  for(let x=0;x<w;x+=step){samples.push(x,(h-1)*w+x)}
  for(let y=0;y<h;y+=step){samples.push(y*w,y*w+w-1)}
  const buckets=new Map();
  for(const p of samples){
    const i=p*4,a=px[i+3];if(a<32)continue;
    const key=`${px[i]>>4}:${px[i+1]>>4}:${px[i+2]>>4}`;
    let bucket=buckets.get(key);if(!bucket){bucket={count:0,r:0,g:0,b:0};buckets.set(key,bucket)}
    bucket.count++;bucket.r+=px[i];bucket.g+=px[i+1];bucket.b+=px[i+2];
  }
  let dominant=null;
  for(const bucket of buckets.values())if(!dominant||bucket.count>dominant.count)dominant=bucket;
  if(!dominant||dominant.count/Math.max(samples.length,1)<.12)return src;
  const br=dominant.r/dominant.count,bg=dominant.g/dominant.count,bb=dominant.b/dominant.count;
  const distanceAt=p=>{const i=p*4;return Math.hypot(px[i]-br,px[i+1]-bg,px[i+2]-bb)};
  const threshold=64,seen=new Uint8Array(count),queue=new Int32Array(count);let head=0,tail=0;
  const enqueue=p=>{
    if(p<0||p>=count||seen[p]||px[p*4+3]<8||distanceAt(p)>threshold)return;
    seen[p]=1;queue[tail++]=p;
  };
  for(let x=0;x<w;x++){enqueue(x);enqueue((h-1)*w+x)}
  for(let y=0;y<h;y++){enqueue(y*w);enqueue(y*w+w-1)}
  while(head<tail){
    const p=queue[head++],x=p%w,y=(p/w)|0;
    if(x>0)enqueue(p-1);if(x+1<w)enqueue(p+1);if(y>0)enqueue(p-w);if(y+1<h)enqueue(p+w);
  }
  if(tail/Math.max(count,1)<.001)return src;

  for(let n=0;n<tail;n++){
    const p=queue[n],i=p*4,d=distanceAt(p);
    px[i+3]=d<threshold*.72?0:Math.min(px[i+3],Math.round(255*(d-threshold*.72)/(threshold*.28)));
  }
  ctx.putImageData(data,0,0);
  return out.toDataURL('image/png');
}
function normalizeCrop(raw){
  if(!raw||typeof raw!=='object')return null;
  const x=clamp(Number(raw.x)||0,0,1);
  const y=clamp(Number(raw.y)||0,0,1);
  const width=clamp(Number(raw.width)||0,0,1);
  const height=clamp(Number(raw.height)||0,0,1);
  return width>0&&height>0?{x,y,width,height}:null;
}

async function crop(src,rawCrop){
  const crop=normalizeCrop(rawCrop);
  if(!crop)return String(src||'');
  const img=await loadImage(src);
  const w=Math.max(1,img.naturalWidth||img.width||1),h=Math.max(1,img.naturalHeight||img.height||1);
  const sx=clamp(Math.floor(crop.x*w),0,w-1),sy=clamp(Math.floor(crop.y*h),0,h-1);
  const sw=clamp(Math.ceil(crop.width*w),1,w-sx),sh=clamp(Math.ceil(crop.height*h),1,h-sy);
  const out=canvas();out.width=sw;out.height=sh;
  const ctx=out.getContext('2d');
  ctx.clearRect(0,0,sw,sh);
  ctx.drawImage(img,sx,sy,sw,sh,0,0,sw,sh);
  return out.toDataURL('image/png');
}

async function components(source,{maxDimension=1536,maxPieces=64,alphaThreshold=8}={}){
  source=String(source||'');
  if(!source)return{source:'',transparentSrc:'',pieces:[]};
  const transparentSrc=await makeTransparent(source);
  const img=await loadImage(transparentSrc);
  const sourceWidth=Math.max(1,img.naturalWidth||img.width||1);
  const sourceHeight=Math.max(1,img.naturalHeight||img.height||1);
  const ratio=Math.min(1,maxDimension/Math.max(sourceWidth,sourceHeight));
  const width=Math.max(1,Math.round(sourceWidth*ratio));
  const height=Math.max(1,Math.round(sourceHeight*ratio));
  const work=canvas();work.width=width;work.height=height;
  const ctx=work.getContext('2d',{willReadFrequently:true});
  ctx.clearRect(0,0,width,height);ctx.drawImage(img,0,0,width,height);
  const image=ctx.getImageData(0,0,width,height),px=image.data,count=width*height;
  const labels=new Int32Array(count),queue=new Int32Array(count);
  const minimumArea=Math.max(16,Math.floor(count*.00004)),found=[];
  let label=0;

  for(let start=0;start<count;start++){
    if(labels[start]||px[start*4+3]<=alphaThreshold)continue;
    label++;
    let head=0,tail=0,minX=width,minY=height,maxX=-1,maxY=-1;
    labels[start]=label;queue[tail++]=start;
    while(head<tail){
      const p=queue[head++],x=p%width,y=(p/width)|0;
      minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);
      for(let oy=-1;oy<=1;oy++)for(let ox=-1;ox<=1;ox++){
        if(!ox&&!oy)continue;
        const nx=x+ox,ny=y+oy;
        if(nx<0||nx>=width||ny<0||ny>=height)continue;
        const n=ny*width+nx;
        if(labels[n]||px[n*4+3]<=alphaThreshold)continue;
        labels[n]=label;queue[tail++]=n;
      }
    }
    if(tail>=minimumArea)found.push({label,area:tail,minX,minY,maxX,maxY,seed:queue[Math.floor(tail/2)]});
  }

  found.sort((a,b)=>b.area-a.area);
  const pieces=[];
  for(const component of found.slice(0,maxPieces)){
    const pad=1,minX=Math.max(0,component.minX-pad),minY=Math.max(0,component.minY-pad);
    const maxX=Math.min(width-1,component.maxX+pad),maxY=Math.min(height-1,component.maxY+pad);
    const cw=maxX-minX+1,ch=maxY-minY+1;
    const out=canvas();out.width=cw;out.height=ch;
    const outCtx=out.getContext('2d',{willReadFrequently:true});
    const piece=ctx.getImageData(minX,minY,cw,ch),cp=piece.data;
    for(let yy=0;yy<ch;yy++)for(let xx=0;xx<cw;xx++){
      const global=(minY+yy)*width+(minX+xx);
      if(labels[global]!==component.label)cp[(yy*cw+xx)*4+3]=0;
    }
    outCtx.putImageData(piece,0,0);
    const seedIndex=component.seed;
    pieces.push({
      src:out.toDataURL('image/png'),
      crop:{x:minX/width,y:minY/height,width:cw/width,height:ch/height},
      seed:{x:(seedIndex%width+.5)/width,y:(((seedIndex/width)|0)+.5)/height},
      area:component.area
    });
  }
  return{source,transparentSrc,sourceWidth,sourceHeight,width,height,pieces};
}

const canvasBackend=Object.freeze({
  name:'canvas',
  kind:'browser-fallback',
  capabilities:Object.freeze(['transparency','crop','alpha-components']),
  makeTransparent,crop,components
});
backends.set('canvas',canvasBackend);

function registerBackend(name,backend,{prefer=false}={}){
  name=String(name||'').trim();
  if(!name||!backend||typeof backend!=='object')throw new TypeError('Image backend name and adapter are required');
  for(const fn of ['makeTransparent','crop','components']){
    if(typeof backend[fn]!=='function')throw new TypeError(`Image backend missing ${fn}()`);
  }
  backends.set(name,Object.freeze({...backend,name}));
  if(prefer)preferred=name;
  return true;
}

function choose(){
  if(preferred!=='auto'&&backends.has(preferred))return backends.get(preferred);
  if(backends.has('gegl-wasm'))return backends.get('gegl-wasm');
  return canvasBackend;
}

function setPreferredBackend(name='auto'){
  name=String(name||'auto');
  if(name!=='auto'&&!backends.has(name))throw new Error(`Unknown image backend: ${name}`);
  preferred=name;
}

async function invoke(method,...args){
  const active=choose();
  try{return await active[method](...args)}
  catch(error){
    if(active!==canvasBackend)return canvasBackend[method](...args);
    throw error;
  }
}

// A future separately licensed GEGL/WASM bundle can call this function.
// The RIST editor never needs to import or understand GEGL internals.
function registerGeglWasmAdapter(adapter){
  return registerBackend('gegl-wasm',adapter,{prefer:true});
}

window.ReLiCImageEngine=Object.freeze({
  version:'1.0.0',
  registerBackend,
  registerGeglWasmAdapter,
  setPreferredBackend,
  status:()=>Object.freeze({
    backend:choose().name,
    kind:choose().kind||'adapter',
    available:[...backends.keys()],
    localProcessing:true
  }),
  makeTransparent:(...args)=>invoke('makeTransparent',...args),
  crop:(...args)=>invoke('crop',...args),
  components:(...args)=>invoke('components',...args)
});
})();
