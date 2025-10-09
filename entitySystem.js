let ENT={ player:{x:520,y:820,w:34,h:42,intentDx:0,intentDy:0}, npcs:[], dice:[], debug:false };

export function initEntities(){ ENT.player.x=520; ENT.player.y=820; ENT.npcs=[]; ENT.dice=[]; }
export function getPlayer(){ return ENT.player; }
export function setDebug(v){ ENT.debug=!!v; }

export function stepEntities(dt, query){
  const p=ENT.player; moveAndCollide(p,p.intentDx,p.intentDy,dt,query);
}
function moveAndCollide(e,dx,dy,dt,query){
  // X
  let nx=e.x+dx; const ax={x:nx-e.w/2,y:e.y-e.h/2,w:e.w,h:e.h}; const hx=query(ax);
  if(hx.length){ for(const c of hx){ if(dx>0) nx=Math.min(nx,c.x-e.w/2); else nx=Math.max(nx,c.x+c.w+e.w/2);} }
  e.x=nx;
  // Y
  let ny=e.y+dy; const ay={x:e.x-e.w/2,y:ny-e.h/2,w:e.w,h:e.h}; const hy=query(ay);
  if(hy.length){ for(const c of hy){ if(dy>0) ny=Math.min(ny,c.y-e.h/2); else ny=Math.max(ny,c.y+c.h+e.h/2);} }
  e.y=ny;
}
export function debugEntitiesString(){ const p=ENT.player; return `PLAYER pos=(${p.x.toFixed(1)},${p.y.toFixed(1)}) size=${p.w}x${p.h}`; }

