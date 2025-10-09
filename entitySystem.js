// ============================================================
// Entity System – Phase 1
// - Player movement, collision, placeholders for NPCs and dice
// - No rendering (debug outlines handled by engine)
// ============================================================
let ENT = {
  player: { x: 520, y: 820, w: 34, h: 42, intentDx:0, intentDy:0 },
  npcs: [],
  dice: [],
  debug: false
};

export function initEntities(){
  ENT.player.x = 520; ENT.player.y = 820;
  ENT.npcs = []; ENT.dice = [];
}

export function getPlayer(){ return ENT.player; }
export function setDebug(v){ ENT.debug = !!v; }

export function stepEntities(dt, queryColliders){
  // player collide-move
  const p = ENT.player;
  moveAndCollide(p, p.intentDx, p.intentDy, dt, queryColliders);
}

function moveAndCollide(e, dx, dy, dt, query){
  const speedX = dx, speedY = dy;
  // X axis
  let nx = e.x + speedX;
  const ax = { x:nx - e.w/2, y:e.y - e.h/2, w:e.w, h:e.h };
  const hitX = query(ax);
  if(hitX.length){ // resolve X
    for(const c of hitX){
      if(speedX > 0) nx = Math.min(nx, c.x - e.w/2); // right
      else           nx = Math.max(nx, c.x + c.w + e.w/2); // left
    }
  }
  e.x = nx;

  // Y axis
  let ny = e.y + speedY;
  const ay = { x:e.x - e.w/2, y:ny - e.h/2, w:e.w, h:e.h };
  const hitY = query(ay);
  if(hitY.length){
    for(const c of hitY){
      if(speedY > 0) ny = Math.min(ny, c.y - e.h/2); // down
      else           ny = Math.max(ny, c.y + c.h + e.h/2); // up (height)
    }
  }
  e.y = ny;
}

// Debug info
export function debugEntitiesString(){
  const p = ENT.player;
  return `PLAYER pos=(${p.x.toFixed(1)}, ${p.y.toFixed(1)})  size=${p.w}x${p.h}`;
}
