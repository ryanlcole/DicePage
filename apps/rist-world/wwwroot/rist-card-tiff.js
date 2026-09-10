(()=>{
 'use strict';
 const W=768,H=896,ART=768,COLS=32,ROWS=8,CELL=24,FOOTER_Y=768;
 const enc=new TextEncoder(),dec=new TextDecoder();
 const clamp=v=>Math.max(0,Math.min(255,v|0));

 function tokenFor(card){
  const id=String(card?.CardId||card?.cardId||'');
  const hash=String(card?.ManifestHash||card?.manifestHash||'');
  return `RIST1|${id}|${hash}`;
 }

 function glyphBits(n){return [(n>>3)&1,(n>>2)&1,(n>>1)&1,n&1];}
 function drawGlyph(ctx,n,x,y){
  ctx.fillStyle='#efe4bb';ctx.fillRect(x,y,CELL,CELL);
  ctx.fillStyle='#071015';
  ctx.fillRect(x+2,y+2,3,3);ctx.fillRect(x+CELL-5,y+2,3,3);
  const bits=glyphBits(n),p=[[7,7],[14,7],[7,14],[14,14]];
  for(let i=0;i<4;i++)if(bits[i])ctx.fillRect(x+p[i][0]-2,y+p[i][1]-2,5,5);
 }
 function readGlyph(data,width,x,y){
  const pts=[[7,7],[14,7],[7,14],[14,14]];let n=0;
  for(let i=0;i<4;i++){
   const px=Math.min(width-1,x+pts[i][0]),py=y+pts[i][1],o=(py*width+px)*4;
   const lum=(data[o]+data[o+1]+data[o+2])/3;
   n=(n<<1)|(lum<120?1:0);
  }
  return n;
 }
 function encodeGlyphFooter(ctx,token){
  const bytes=enc.encode(token);if(bytes.length>127)throw new Error('Card reference is too large for glyph footer.');
  const framed=new Uint8Array(bytes.length+1);framed[0]=bytes.length;framed.set(bytes,1);
  const nib=[];for(const b of framed){nib.push((b>>4)&15,b&15);}
  if(nib.length>COLS*ROWS)throw new Error('Card reference exceeds glyph capacity.');
  ctx.fillStyle='#071015';ctx.fillRect(0,FOOTER_Y,W,H-FOOTER_Y);
  for(let i=0;i<COLS*ROWS;i++)drawGlyph(ctx,i<nib.length?nib[i]:0,(i%COLS)*CELL,FOOTER_Y+Math.floor(i/COLS)*CELL);
 }
 function decodeGlyphFooter(image){
  const {data,width,height}=image;if(width!==W||height!==H)throw new Error('Unsupported Shaelvien TIFF dimensions.');
  const nib=[];for(let i=0;i<COLS*ROWS;i++)nib.push(readGlyph(data,width,(i%COLS)*CELL,FOOTER_Y+Math.floor(i/COLS)*CELL));
  const bytes=[];for(let i=0;i+1<nib.length;i+=2)bytes.push((nib[i]<<4)|nib[i+1]);
  const len=bytes[0]||0;if(len<1||len>127)throw new Error('Shaelvien glyph payload not found.');
  const token=dec.decode(new Uint8Array(bytes.slice(1,1+len)));
  if(!token.startsWith('RIST1|'))throw new Error('Invalid Shaelvien glyph signature.');
  return token;
 }

 function writeTiff(imageData){
  const width=imageData.width,height=imageData.height,rgba=imageData.data,rgbLen=width*height*3;
  const ifdOffset=8+rgbLen,entries=10,bitsOffset=ifdOffset+2+entries*12+4,total=bitsOffset+6;
  const buf=new ArrayBuffer(total),v=new DataView(buf),u=new Uint8Array(buf);
  v.setUint8(0,0x49);v.setUint8(1,0x49);v.setUint16(2,42,true);v.setUint32(4,ifdOffset,true);
  let p=8;for(let i=0;i<rgba.length;i+=4){u[p++]=rgba[i];u[p++]=rgba[i+1];u[p++]=rgba[i+2];}
  v.setUint16(ifdOffset,entries,true);let e=ifdOffset+2;
  const tag=(id,type,count,val)=>{v.setUint16(e,id,true);v.setUint16(e+2,type,true);v.setUint32(e+4,count,true);if(type===3&&count===1){v.setUint16(e+8,val,true);v.setUint16(e+10,0,true);}else v.setUint32(e+8,val,true);e+=12;};
  tag(256,4,1,width);tag(257,4,1,height);tag(258,3,3,bitsOffset);tag(259,3,1,1);tag(262,3,1,2);tag(273,4,1,8);tag(277,3,1,3);tag(278,4,1,height);tag(279,4,1,rgbLen);tag(284,3,1,1);
  v.setUint32(e,0,true);v.setUint16(bitsOffset,8,true);v.setUint16(bitsOffset+2,8,true);v.setUint16(bitsOffset+4,8,true);
  return new Blob([buf],{type:'image/tiff'});
 }
 function readTiff(buffer){
  const v=new DataView(buffer);if(v.getUint8(0)!==0x49||v.getUint8(1)!==0x49||v.getUint16(2,true)!==42)throw new Error('Unsupported TIFF.');
  const ifd=v.getUint32(4,true),count=v.getUint16(ifd,true);let width=0,height=0,offset=0,bytes=0,samples=3,compression=1;
  for(let i=0;i<count;i++){const e=ifd+2+i*12,id=v.getUint16(e,true),type=v.getUint16(e+2,true),c=v.getUint32(e+4,true),val=(type===3&&c===1)?v.getUint16(e+8,true):v.getUint32(e+8,true);if(id===256)width=val;else if(id===257)height=val;else if(id===259)compression=val;else if(id===273)offset=val;else if(id===277)samples=val;else if(id===279)bytes=val;}
  if(compression!==1||samples!==3||!width||!height||!offset)throw new Error('TIFF is not a Shaelvien uncompressed RGB card image.');
  const src=new Uint8Array(buffer,offset,bytes),rgba=new Uint8ClampedArray(width*height*4);let s=0,d=0;while(d<rgba.length&&s+2<src.length){rgba[d++]=src[s++];rgba[d++]=src[s++];rgba[d++]=src[s++];rgba[d++]=255;}
  return new ImageData(rgba,width,height);
 }
 async function renderPreview(ctx,svg){
  ctx.fillStyle='#071015';ctx.fillRect(0,0,W,ART);
  if(!svg)return;
  const blob=new Blob([svg],{type:'image/svg+xml'}),url=URL.createObjectURL(blob),img=new Image();
  try{await new Promise((ok,bad)=>{img.onload=ok;img.onerror=bad;img.src=url;});ctx.drawImage(img,0,0,W,ART);}finally{URL.revokeObjectURL(url);}
 }
 function download(blob,name){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
 async function exportJson(raw,name='shaelvien-card.tiff'){
  const card=typeof raw==='string'?JSON.parse(raw):raw,canvas=document.createElement('canvas');canvas.width=W;canvas.height=H;const ctx=canvas.getContext('2d',{willReadFrequently:true});
  await renderPreview(ctx,card.PreviewSvg||card.previewSvg||'');encodeGlyphFooter(ctx,tokenFor(card));download(writeTiff(ctx.getImageData(0,0,W,H)),name);
 }
 async function pickAndRead(){
  return await new Promise(resolve=>{const input=document.createElement('input');input.type='file';input.accept='.tif,.tiff,image/tiff,.json,application/json';input.onchange=async()=>{const f=input.files?.[0];if(!f)return resolve(null);try{if(/\.json$/i.test(f.name)||f.type==='application/json'){const raw=await f.text();const card=JSON.parse(raw);resolve({kind:'json',raw,cardId:card.CardId||card.cardId||''});return;}const image=readTiff(await f.arrayBuffer());resolve({kind:'tiff',token:decodeGlyphFooter(image)});}catch(err){alert(err?.message||'Card import failed.');resolve(null);}};input.click();});
 }
 window.ristCardTiff={exportJson,pickAndRead,decodeBuffer:async b=>decodeGlyphFooter(readTiff(b))};
})();
