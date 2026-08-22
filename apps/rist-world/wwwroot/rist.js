window.ristWorld={
 capturePointer:(pointerId,x,y)=>{
  const el=document.elementFromPoint(x,y);if(el?.setPointerCapture)el.setPointerCapture(pointerId);
 },
 point:(el,x,y)=>{const r=el.getBoundingClientRect();return[(x-r.left)/r.width,(y-r.top)/r.height]},
 worldPoint:(el,x,y,panX,panY,zoom)=>{
  const r=el.getBoundingClientRect();const sx=(x-r.left)/r.width;const sy=(y-r.top)/r.height;const z=Math.max(Number(zoom)||1,.01);
  return [((sx-.5)/z)+.5-(Number(panX)||0)/(r.width*z),((sy-.5)/z)+.5-(Number(panY)||0)/(r.height*z)];
 },
 dropPoint:(el,x,y,panX,panY,zoom)=>{
  const r=el.getBoundingClientRect();const inside=x>=r.left&&x<=r.right&&y>=r.top&&y<=r.bottom;if(!inside)return [0,0,0];const sx=(x-r.left)/r.width;const sy=(y-r.top)/r.height;const z=Math.max(Number(zoom)||1,.01);
  return [1,((sx-.5)/z)+.5-(Number(panX)||0)/(r.width*z),((sy-.5)/z)+.5-(Number(panY)||0)/(r.height*z)];
 },
 overPublicCardDrop:(x,y)=>{
  const el=document.querySelector('.public-card-drop');if(!el)return false;const r=el.getBoundingClientRect();return x>=r.left&&x<=r.right&&y>=r.top&&y<=r.bottom;
 },
 overPallet:(x,y)=>{
  const el=document.querySelector('.staging-tray');if(!el)return false;const r=el.getBoundingClientRect();return x>=r.left&&x<=r.right&&y>=r.top&&y<=r.bottom;
 },
 splitTileset:(dataUrl)=>new Promise((resolve,reject)=>{
  const img=new Image();
  img.onerror=()=>reject(new Error('Unable to read tileset image'));
  img.onload=()=>{
   const w=img.naturalWidth,h=img.naturalHeight,canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;
   const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.drawImage(img,0,0);const pixels=ctx.getImageData(0,0,w,h).data;
   const corners=[[0,0],[w-1,0],[0,h-1],[w-1,h-1]].map(([x,y])=>{const i=(y*w+x)*4;return[pixels[i],pixels[i+1],pixels[i+2],pixels[i+3]]});
   const bg=corners.reduce((a,c)=>a.map((v,i)=>v+c[i]/corners.length),[0,0,0,0]);
   const active=(x,y)=>{const i=(y*w+x)*4,a=pixels[i+3];if(a<18)return false;if(bg[3]<40)return true;const d=Math.abs(pixels[i]-bg[0])+Math.abs(pixels[i+1]-bg[1])+Math.abs(pixels[i+2]-bg[2])+Math.abs(a-bg[3]);return d>48};
   // Find only the sheet's outer usable rectangle. Never inspect inside a
   // resulting cell: transparency, coastlines and rivers belong to that tile.
   let minX=w,minY=h,maxX=-1,maxY=-1;const sampleStep=Math.max(1,Math.floor(Math.min(w,h)/700));
   for(let y=0;y<h;y+=sampleStep)for(let x=0;x<w;x+=sampleStep)if(active(x,y)){minX=Math.min(minX,x);minY=Math.min(minY,y);maxX=Math.max(maxX,x);maxY=Math.max(maxY,y)}
   if(maxX<minX||maxY<minY){resolve([]);return}
   // Snap near-square previews (including the Drive Ocean/Coast sheets) to
   // their full square cutout, then use the standard 6x6 tileset grid.
   let bw=maxX-minX+1,bh=maxY-minY+1;
   if(Math.abs(bw-bh)<=Math.max(bw,bh)*.08){const side=Math.max(bw,bh);minX=Math.max(0,Math.round((minX+maxX+1-side)/2));minY=Math.max(0,Math.round((minY+maxY+1-side)/2));bw=Math.min(side,w-minX);bh=Math.min(side,h-minY)}
   const squareish=Math.abs(bw-bh)<=Math.max(bw,bh)*.08;
   const cols=squareish&&Math.min(bw,bh)>=192?6:1,rows=cols;
   const output=[];
   for(let row=0;row<rows;row++)for(let col=0;col<cols;col++){
    const sx=Math.round(minX+col*bw/cols),sy=Math.round(minY+row*bh/rows),ex=Math.round(minX+(col+1)*bw/cols),ey=Math.round(minY+(row+1)*bh/rows);
    const sw=ex-sx,sh=ey-sy,out=document.createElement('canvas');out.width=sw;out.height=sh;out.getContext('2d').drawImage(canvas,sx,sy,sw,sh,0,0,sw,sh);output.push(out.toDataURL('image/png'));
   }
   resolve(output);
  };img.src=dataUrl;
 })
};

window.ristCropPortrait=(dataUrl,zoom,xPct,yPct,size)=>new Promise((resolve,reject)=>{
 const img=new Image();
 img.onload=()=>{
  const s=Math.max(128,Number(size)||512),z=Math.max(1,Number(zoom)||1),xp=Math.max(0,Math.min(100,Number(xPct)||50)),yp=Math.max(0,Math.min(100,Number(yPct)||50));
  const canvas=document.createElement('canvas');canvas.width=s;canvas.height=s;const ctx=canvas.getContext('2d');
  const cover=Math.max(s/img.naturalWidth,s/img.naturalHeight);const baseW=img.naturalWidth*cover,baseH=img.naturalHeight*cover;
  const dw=baseW*z,dh=baseH*z;
  const centeredX=(s-dw)/2,centeredY=(s-dh)/2;
  const shiftX=((xp-50)/100)*s,shiftY=((yp-50)/100)*s;
  ctx.drawImage(img,centeredX+shiftX,centeredY+shiftY,dw,dh);
  resolve(canvas.toDataURL('image/jpeg',.9));
 };
 img.onerror=reject;img.src=dataUrl;
});

(()=>{
 let scheduled=false;
 const centerOf=el=>{const r=el.getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2};};
 function resolveDiceCollisions(){
  scheduled=false;const map=document.querySelector('.map');if(!map)return;const dice=[...map.querySelectorAll('.rolled-die')];if(dice.length<2)return;
  const mr=map.getBoundingClientRect();const minDistance=Math.max(48,Math.min(62,mr.width*.1));const placed=[];
  dice.forEach((die,index)=>{die.style.setProperty('--collision-x','0px');die.style.setProperty('--collision-y','0px');let ox=0,oy=0;for(let pass=0;pass<32;pass++){const c=centerOf(die);let hit=null;for(const p of placed){const dx=c.x-p.x,dy=c.y-p.y;const d=Math.hypot(dx,dy);if(d<minDistance){hit={p,dx,dy,d};break;}}if(!hit)break;let ax=hit.dx,ay=hit.dy;if(hit.d<1){const angle=((index+1)*2.399963229728653);ax=Math.cos(angle);ay=Math.sin(angle);}const len=Math.max(Math.hypot(ax,ay),.001);const push=(minDistance-hit.d)+5;ox+=(ax/len)*push;oy+=(ay/len)*push;const base=centerOf(die);const nx=Math.min(mr.right-26,Math.max(mr.left+26,base.x+ox));const ny=Math.min(mr.bottom-26,Math.max(mr.top+26,base.y+oy));ox+=nx-(base.x+ox);oy+=ny-(base.y+oy);die.style.setProperty('--collision-x',`${ox.toFixed(1)}px`);die.style.setProperty('--collision-y',`${oy.toFixed(1)}px`);}placed.push(centerOf(die));});
 }
 function schedule(){if(scheduled)return;scheduled=true;requestAnimationFrame(resolveDiceCollisions);}
 const observer=new MutationObserver(mutations=>{if(mutations.some(m=>m.type==='childList'&&(m.addedNodes.length||m.removedNodes.length))){schedule();initCircularRails();}});
 function start(){observer.observe(document.body,{childList:true,subtree:true});schedule();initCircularRails();}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.addEventListener('resize',()=>{schedule();initCircularRails(true);},{passive:true});window.addEventListener('orientationchange',()=>{schedule();initCircularRails(true);},{passive:true});
 let railInitScheduled=false;
 function initCircularRails(force=false){if(railInitScheduled)return;railInitScheduled=true;requestAnimationFrame(()=>{railInitScheduled=false;document.querySelectorAll('[data-circular-rail]').forEach(rail=>setupCircularRail(rail,force));});}
 function setupCircularRail(rail,force=false){const sets=[...rail.children].filter(x=>x.classList&&x.classList.contains('circular-set'));if(sets.length!==3)return;const width=sets[1].getBoundingClientRect().width;if(width<1)return;const oldWidth=Number(rail.dataset.loopWidth)||0;if(force||!rail.classList.contains('is-circular-ready')||Math.abs(oldWidth-width)>1){rail.dataset.loopWidth=String(width);rail.scrollLeft=width;rail.classList.add('is-circular-ready');}if(rail.dataset.loopBound==='1')return;rail.dataset.loopBound='1';let adjusting=false;rail.addEventListener('scroll',()=>{if(adjusting)return;const w=Number(rail.dataset.loopWidth)||sets[1].getBoundingClientRect().width;if(!w)return;if(rail.scrollLeft<w*.45){adjusting=true;rail.scrollLeft+=w;requestAnimationFrame(()=>adjusting=false);}else if(rail.scrollLeft>w*1.55){adjusting=true;rail.scrollLeft-=w;requestAnimationFrame(()=>adjusting=false);}},{passive:true});}
})();
