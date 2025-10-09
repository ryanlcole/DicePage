let WORLD={bounds:{x:0,y:0,w:4000,h:3000},colliders:[],shops:[]};

export function initWorld(){
  WORLD={bounds:{x:0,y:0,w:4000,h:3000},colliders:[],shops:[]};
  addBuilding( 600,  600, 420,260,"tavern_inn");
  addBuilding(1050,  650, 220,180,"stables");
  addBuilding(1500,  550, 320,220,"apothecary");
  addBuilding( 900, 1100, 380,260,"armory");
  addBuilding(1400, 1150, 280,220,"curio");
  for(let i=0;i<6;i++) addProp(600+i*120, 900, 60, 40);
  addShop( 600,  540, 420, 40, "tavern_inn","The Emberlight Tavern");
  addShop(1500,  530, 320, 30, "apothecary","Moonpetal Apothecary");
  addShop( 900, 1080, 380, 30, "armory","Anvil & Star Forge");
  addShop(1400, 1130, 280, 30, "curio","Oddments & Oracles");
}
function addBuilding(x,y,w,h,tag){ WORLD.colliders.push({x,y,w,h,type:"building",tag}); }
function addProp(x,y,w,h){ WORLD.colliders.push({x,y,w,h,type:"prop"}); }
function addShop(x,y,w,h,shopId,name){ WORLD.shops.push({x,y,w,h,shopId,name}); }
export function getWorld(){ return WORLD; }
export function queryColliders(a){ const out=[]; for(const c of WORLD.colliders){ if(!(a.x+a.w<c.x||a.x>c.x+c.w||a.y+a.h<c.y||a.y>c.y+c.h)) out.push(c);} return out; }
export function debugWorldString(){ return `WORLD size=${WORLD.bounds.w}x${WORLD.bounds.h} colliders=${WORLD.colliders.length} shops=${WORLD.shops.length}`; }

