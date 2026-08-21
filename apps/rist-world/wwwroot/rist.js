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
   const bands=(length,cross,isColumn)=>{const filled=[];for(let p=0;p<length;p++){let hits=0;const step=Math.max(1,Math.floor(cross/180));for(let q=0;q<cross;q+=step)if(active(isColumn?p:q,isColumn?q:p))hits++;filled[p]=hits>1}const runs=[];let start=-1;for(let i=0;i<=length;i++){if(i<length&&filled[i]&&start<0)start=i;if((i===length||!filled[i])&&start>=0){if(i-start>=3)runs.push([start,i]);start=-1}}return runs};
   let xs=bands(w,h,true),ys=bands(h,w,false);
   if(xs.length*ys.length<2){const gcd=(a,b)=>b?gcd(b,a%b):a,g=gcd(w,h);if(g>=16&&w/g*h/g<=256&&(w/g>1||h/g>1)){xs=Array.from({length:w/g},(_,i)=>[i*g,(i+1)*g]);ys=Array.from({length:h/g},(_,i)=>[i*g,(i+1)*g]);}else{xs=[[0,w]];ys=[[0,h]]}}
   const output=[];for(const yr of ys)for(const xr of xs){if(output.length>=256)break;let minX=xr[1],minY=yr[1],maxX=-1,maxY=-1;for(let y=yr[0];y<yr[1];y++)for(let x=xr[0];x<xr[1];x++)if(active(x,y)){minX=Math.min(minX,x);minY=Math.min(minY,y);maxX=Math.max(maxX,x);maxY=Math.max(maxY,y)}if(maxX<minX||maxY<minY)continue;const pad=1,sx=Math.max(xr[0],minX-pad),sy=Math.max(yr[0],minY-pad),sw=Math.min(xr[1]-sx,maxX-minX+1+pad*2),sh=Math.min(yr[1]-sy,maxY-minY+1+pad*2);const out=document.createElement('canvas');out.width=sw;out.height=sh;out.getContext('2d').drawImage(canvas,sx,sy,sw,sh,0,0,sw,sh);output.push(out.toDataURL('image/png'))}
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
