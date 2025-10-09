import { initWorld, getWorld, queryColliders, debugWorldString } from "./worldMap.js";
import { initEntities, getPlayer, setDebug, stepEntities, debugEntitiesString } from "./entitySystem.js";
import { initUIFrame, setDebugVisible } from "./uiFrame.js";

const canvas = document.getElementById("screen");
const ctx = canvas.getContext("2d", { willReadFrequently:false });
let W, H, image, pix32;
function alloc(){ W=innerWidth; H=innerHeight; canvas.width=W; canvas.height=H;
  image=ctx.createImageData(W,H); pix32=new Uint32Array(image.data.buffer); }
addEventListener("resize",()=>alloc()); alloc();

function clear(r=0,g=0,b=0){ const v=(255<<24)|(b<<16)|(g<<8)|r; pix32.fill(v); }
function put(x,y,r,g,b){ if(x<0||y<0||x>=W||y>=H)return; pix32[y*W+x]=(255<<24)|(b<<16)|(g<<8)|r; }
function strokeRect(x,y,w,h,r=0,g=255,b=0){ x|=0;y|=0;const x2=(x+w)|0,y2=(y+h)|0;
  for(let i=x;i<=x2;i++){put(i,y,r,g,b);put(i,y2,r,g,b);} for(let j=y;j<=y2;j++){put(x,j,r,g,b);put(x2,j,r,g,b);} }

const keys=new Set(); addEventListener("keydown",e=>{keys.add(e.key.toLowerCase());
  if(e.key==='`'){ dbg=!dbg; setDebug(dbg); setDebugVisible(dbg);} });
addEventListener("keyup",e=>keys.delete(e.key.toLowerCase()));

const cam={x:0,y:0,w:()=>W,h:()=>H};
function follow(t){ const pad=120, L=cam.x+pad,R=cam.x+cam.w()-pad,T=cam.y+pad,B=cam.y+cam.h()-pad;
  if(t.x<L) cam.x=t.x-pad; if(t.x>R) cam.x=t.x-cam.w()+pad; if(t.y<T) cam.y=t.y-pad; if(t.y>B) cam.y=t.y-cam.h()+pad; }

initWorld(); initEntities(); initUIFrame();
let dbg=false,last=performance.now(),acc=0,stepMs=1000/120;

function gameStep(dt){
  const p=getPlayer(); const v=220; let dx=0,dy=0;
  if(keys.has('w')||keys.has('arrowup')) dy-=v*dt;
  if(keys.has('s')||keys.has('arrowdown')) dy+=v*dt;
  if(keys.has('a')||keys.has('arrowleft')) dx-=v*dt;
  if(keys.has('d')||keys.has('arrowright')) dx+=v*dt;
  p.intentDx=dx; p.intentDy=dy;
  stepEntities(dt, queryColliders);
  follow(p);
}

function draw(){
  clear(0,0,0);
  if(dbg){
    const {colliders}=getWorld();
    for(const c of colliders) strokeRect((c.x-cam.x),(c.y-cam.y),c.w,c.h,0,255,128);
    const p=getPlayer(); strokeRect((p.x-cam.x-p.w/2),(p.y-cam.y-p.h/2),p.w,p.h,255,255,0);
  }
  ctx.putImageData(image,0,0);
  const el=document.getElementById('dbg');
  if(dbg){ el.style.display='block';
    el.textContent = `${debugWorldString()}\n${debugEntitiesString()}\ncam=(${cam.x.toFixed(1)},${cam.y.toFixed(1)}) scr=${W}x${H}`;
  } else el.style.display='none';
}

function loop(now){ const dt=now-last; last=now; acc+=dt; while(acc>=stepMs){ gameStep(stepMs/1000); acc-=stepMs; } draw(); requestAnimationFrame(loop); }
requestAnimationFrame(loop);

