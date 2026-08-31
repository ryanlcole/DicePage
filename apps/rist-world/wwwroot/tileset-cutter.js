/* RIST tileset cutter.
   Tilesets are physical asset sheets, not assumed grids. We detect only dark
   separator corridors that cross the entire current region, recursively split
   along those corridors, and never inspect artwork inside a finished cut. */
(()=>{
 const DARK_LEVEL=50;
 const SEPARATOR_SCORE=.965;
 const MIN_DIM=32;
 const MAX_DEPTH=64;

 const splitTileset=dataUrl=>new Promise((resolve,reject)=>{
  const img=new Image();
  img.onerror=()=>reject(new Error('Unable to read tileset image'));
  img.onload=()=>{
   const w=img.naturalWidth,h=img.naturalHeight;
   if(!w||!h){resolve([]);return;}
   const source=document.createElement('canvas');
   source.width=w;source.height=h;
   const ctx=source.getContext('2d',{willReadFrequently:true});
   ctx.drawImage(img,0,0);
   const pixels=ctx.getImageData(0,0,w,h).data;

   // Integral image of separator-colored pixels. A separator must remain dark
   // across almost the complete width/height of the region being considered.
   const stride=w+1;
   const integral=new Uint32Array((w+1)*(h+1));
   for(let y=0;y<h;y++){
    let row=0;
    const py=y*w*4;
    for(let x=0;x<w;x++){
     const p=py+x*4;
     row+=((pixels[p]+pixels[p+1]+pixels[p+2])/3<DARK_LEVEL)?1:0;
     integral[(y+1)*stride+x+1]=integral[y*stride+x+1]+row;
    }
   }
   const area=(x0,y0,x1,y1)=>integral[y1*stride+x1]-integral[y0*stride+x1]-integral[y1*stride+x0]+integral[y0*stride+x0];
   const lineBands=(box,vertical)=>{
    const [x0,y0,x1,y1]=box, length=vertical?x1-x0:y1-y0, span=vertical?y1-y0:x1-x0;
    const hits=[];
    for(let i=0;i<length;i++){
     const dark=vertical?area(x0+i,y0,x0+i+1,y1):area(x0,y0+i,x1,y0+i+1);
     const score=dark/span;
     if(score>=SEPARATOR_SCORE)hits.push([i,score]);
    }
    if(!hits.length)return [];
    const bands=[];
    let start=hits[0][0],last=start,best=hits[0][1];
    for(let n=1;n<hits.length;n++){
     const [pos,score]=hits[n];
     if(pos<=last+2){last=pos;best=Math.max(best,score);}
     else{bands.push([start,last+1,best]);start=last=pos;best=score;}
    }
    bands.push([start,last+1,best]);
    return bands;
   };
   const recurse=(box,depth=0)=>{
    let [x0,y0,x1,y1]=box,w0=x1-x0,h0=y1-y0;
    if(w0<MIN_DIM||h0<MIN_DIM||depth>=MAX_DEPTH)return [box];
    const cols=lineBands(box,true),rows=lineBands(box,false);

    // Remove only separator bands touching the outside edge of this region.
    // This strips sheet gutters while preserving the complete bordered asset.
    let left=0,right=w0,top=0,bottom=h0;
    for(const [a,b] of cols){if(a<=3)left=Math.max(left,b);if(b>=w0-3)right=Math.min(right,a);}
    for(const [a,b] of rows){if(a<=3)top=Math.max(top,b);if(b>=h0-3)bottom=Math.min(bottom,a);}
    if((left||right<w0||top||bottom<h0)&&right-left>=MIN_DIM&&bottom-top>=MIN_DIM)
     return recurse([x0+left,y0+top,x0+right,y0+bottom],depth+1);

    const choices=[];
    for(const [a,b,score] of cols)if(a>=MIN_DIM&&w0-b>=MIN_DIM)choices.push(['v',a,b,score]);
    for(const [a,b,score] of rows)if(a>=MIN_DIM&&h0-b>=MIN_DIM)choices.push(['h',a,b,score]);
    if(!choices.length)return [box];
    choices.sort((A,B)=>{
     if(B[3]!==A[3])return B[3]-A[3];
     const aw=A[2]-A[1],bw=B[2]-B[1];if(bw!==aw)return bw-aw;
     const an=A[0]==='v'?w0:h0,bn=B[0]==='v'?w0:h0;
     const ab=Math.min(A[1],an-A[2])/an,bb=Math.min(B[1],bn-B[2])/bn;
     return bb-ab;
    });
    const [axis,a,b]=choices[0];
    return axis==='v'
     ? [...recurse([x0,y0,x0+a,y1],depth+1),...recurse([x0+b,y0,x1,y1],depth+1)]
     : [...recurse([x0,y0,x1,y0+a],depth+1),...recurse([x0,y0+b,x1,y1],depth+1)];
   };

   const boxes=recurse([0,0,w,h]).filter(([x0,y0,x1,y1])=>x1-x0>=MIN_DIM&&y1-y0>=MIN_DIM)
    .sort((a,b)=>a[1]-b[1]||a[0]-b[0]);
   const output=[];
   for(const [sx,sy,ex,ey] of boxes){
    const sw=ex-sx,sh=ey-sy;
    const out=document.createElement('canvas');out.width=sw;out.height=sh;
    out.getContext('2d').drawImage(source,sx,sy,sw,sh,0,0,sw,sh);
    output.push(out.toDataURL('image/png'));
   }
   resolve(output.length?output:[source.toDataURL('image/png')]);
  };
  img.src=dataUrl;
 });
 const install=()=>{if(!window.ristWorld){requestAnimationFrame(install);return;}window.ristWorld.splitTileset=splitTileset;};
 install();
})();
