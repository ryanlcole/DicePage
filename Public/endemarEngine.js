// ============================================================
// Endemar Engine – Phase 1 foundation
// - No legacy graphics/UI. Pure engine, input, loop.
// - ES modules: worldMap, entitySystem, uiFrame, shopLogic.
// - 120 Hz target; zero libraries; Azure-ready.
// ============================================================
import { initWorld, getWorld, queryColliders, debugWorldString } from "./worldMap.js";
import { initEntities, getPlayer, setDebug, stepEntities, debugEntitiesString } from "./entitySystem.js";
import { initUIFrame, setDebugVisible } from "./uiFrame.js";

// ---------- Canvas / buffer ----------
const canvas = document.getElementById("screen");
const ctx = canvas.getContext("2d", { willReadFrequently:false });
let W=0, H=0, image, pix32;

function allocScreen(){
  W = innerWidth; H = innerHeight;
  canvas.width = W; canvas.height = H;
  image = ctx.createImageData(W, H);
  pix32 = new Uint32Array(image.data.buffer);
}
addEventListener("resize", ()=>{ allocScreen(); });
allocScreen();

// ---------- Minimal renderer (no art) ----------
function clear(r=0,g=0,b=0){
  const v = (255<<24) | (b<<16) | (g<<8) | r;
  pix32.fill(v);
}
function putPixel(x,y,r,g,b){
  if(x<0||y<0||x>=W||y>=H) return;
  pix32[y*W + x] = (255<<24)|(b<<16)|(g<<8)|r;
}
// Simple debug draw for AABBs
function strokeRect(x,y,w,h,r=0,g=255,b=0){
  x|=0; y|=0; const x2=(x+w)|=0, y2=(y+h)|=0;
  for(let i=x;i<=x2;i++){ putPixel(i,y,r,g,b); putPixel(i,y2,r,g,b); }
  for(let j=y;j<=y2;j++){ putPixel(x,j,r,g,b); putPixel(x2,j,r,g,b); }
}

// ---------- Input ----------
const keys = new Set();
addEventListener("keydown", e=>{
  keys.add(e.key.toLowerCase());
  // toggle debug overlay on backtick `
  if(e.key === '`'){ debugOverlay = !debugOverlay; setDebug(debugOverlay); setDebugVisible(debugOverlay); }
});
addEventListener("keyup", e=> keys.delete(e.key.toLowerCase()));

// ---------- Camera ----------
const camera = { x:0, y:0, w:()=>W, h:()=>H, speed: 300 };
function follow(target, dt){
  const pad = 120;
  const left = camera.x + pad, right = camera.x + camera.w() - pad;
  const top = camera.y + pad, bottom = camera.y + camera.h() - pad;
  if(target.x < left) camera.x = target.x - pad;
  if(target.x > right) camera.x = target.x - camera.w() + pad;
  if(target.y < top) camera.y = target.y - pad;
  if(target.y > bottom) camera.y = target.y - camera.h() + pad;
}

// ---------- Engine init ----------
initWorld();       // shops, buildings, colliders (no graphics)
initEntities();    // player + systems (no graphics)
initUIFrame();     // hidden; debug-only overlay support

let debugOverlay = false;

// ---------- Main loop ----------
let last = performance.now(), acc = 0, target = 1000/120;
function loop(now){
  const dtMs = now - last; last = now; acc += dtMs;

  // physics/logic step(s)
  while(acc >= target){
    step(dtMs/1000);
    acc -= target;
  }

  // render
  render();
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);

function step(dt){
  // basic movement (WASD/arrow). Collision in entity system.
  const p = getPlayer();
  const v = 220; // walk speed
  let dx=0, dy=0;
  if(keys.has('w') || keys.has('arrowup'))    dy -= v*dt;
  if(keys.has('s') || keys.has('arrowdown'))  dy += v*dt;
  if(keys.has('a') || keys.has('arrowleft'))  dx -= v*dt;
  if(keys.has('d') || keys.has('arrowright')) dx += v*dt;

  p.intentDx = dx; p.intentDy = dy;

  // step entities & interactions
  stepEntities(dt, queryColliders);

  // camera follow
  follow(p, dt);
}

function render(){
  clear(0,0,0);

  // Debug outlines only when overlay is enabled.
  if(debugOverlay){
    // draw world colliders
    const { colliders } = getWorld();
    for(const c of colliders){
      // transform to screen
      strokeRect(
        (c.x - camera.x)|0,
        (c.y - camera.y)|0,
        c.w|0, c.h|0,
        0, 255, 128
      );
    }
    // draw player debug box
    const p = getPlayer();
    strokeRect(
      (p.x - camera.x - p.w/2)|0,
      (p.y - camera.y - p.h/2)|0,
      p.w|0, p.h|0,
      255, 255, 0
    );
  }

  ctx.putImageData(image, 0, 0);

  if(debugOverlay){
    const dbg = document.getElementById('dbg');
    dbg.style.display = 'block';
    dbg.textContent =
      debugWorldString() + "\n" +
      debugEntitiesString() + "\n" +
      `cam=(${camera.x.toFixed(1)}, ${camera.y.toFixed(1)})  scr=${W}x${H}`;
  }else{
    document.getElementById('dbg').style.display = 'none';
  }
}
