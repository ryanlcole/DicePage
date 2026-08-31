/* Canonical RIST tileset cutter.
   Standard square atlas sheets are authored as exact 6x6 grids. Their artwork is
   allowed to touch every edge, so content/color detection must never move the
   crop origin. Irregular/non-square uploads retain a single outer-content cut. */
(()=>{
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

   // Production Shaelvien sheets are square 6x6 atlases. Use the complete
   // image rectangle. Inferring a rectangle from corner colors shifted Plains
   // by roughly one third of a cell because valid terrain resembles the corner.
   const squareish=Math.abs(w-h)<=Math.max(w,h)*.08;
   if(squareish&&Math.min(w,h)>=192){
    const output=[];
    for(let row=0;row<6;row++)for(let col=0;col<6;col++){
     const sx=Math.round(col*w/6),sy=Math.round(row*h/6);
     const ex=Math.round((col+1)*w/6),ey=Math.round((row+1)*h/6);
     const sw=ex-sx,sh=ey-sy;
     const out=document.createElement('canvas');
     out.width=sw;out.height=sh;
     out.getContext('2d').drawImage(source,sx,sy,sw,sh,0,0,sw,sh);
     output.push(out.toDataURL('image/png'));
    }
    resolve(output);return;
   }

   // Non-atlas artwork remains one image. Do not inspect its interior or try
   // to infer rows/columns from transparency, coastlines, rivers, or texture.
   const out=document.createElement('canvas');
   out.width=w;out.height=h;
   out.getContext('2d').drawImage(source,0,0);
   resolve([out.toDataURL('image/png')]);
  };
  img.src=dataUrl;
 });

 const install=()=>{
  if(!window.ristWorld){requestAnimationFrame(install);return;}
  window.ristWorld.splitTileset=splitTileset;
 };
 install();
})();
