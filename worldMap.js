// ============================================================
// Endemar world layout – Phase 1
// - Town blocks, building footprints, shop zones
// - Pure data + collision queries (no rendering)
// ============================================================
let WORLD = {
  bounds: { x:0, y:0, w: 4000, h: 3000 },
  colliders: [],   // solid AABBs: buildings, fences, props
  shops: []        // interactive zones: tavern, apothecary, forge, curio
};

export function initWorld(){
  WORLD = {
    bounds: { x:0, y:0, w: 4000, h: 3000 },
    colliders: [],
    shops: []
  };

  // --- Place some buildings (footprints only) ---
  // Tavern/Inn with stables
  addBuilding( 600,  600, 420, 260, "tavern_inn");
  addBuilding(1050,  650, 220, 180, "stables");

  // Apothecary
  addBuilding(1500,  550, 320, 220, "apothecary");

  // Armory/Forge
  addBuilding( 900, 1100, 380, 260, "armory");

  // Curio Shop
  addBuilding(1400, 1150, 280, 220, "curio");

  // Market road props (simple blockers to make paths)
  for(let i=0;i<6;i++){
    addProp(600 + i*120, 900, 60, 40);   // crates along road
  }

  // --- Shop interactive zones (front counters) ---
  addShopZone( 600,  540, 420, 40,  "tavern_inn", "The Emberlight Tavern");
  addShopZone(1500,  530, 320, 30,  "apothecary", "Moonpetal Apothecary");
  addShopZone( 900, 1080, 380, 30,  "armory",     "Anvil & Star Forge");
  addShopZone(1400, 1130, 280, 30,  "curio",      "Oddments & Oracles");

  // Paths are currently free space (no colliders). Rendering comes later.
}

function addBuilding(x,y,w,h,type){
  WORLD.colliders.push({ x, y, w, h, type:"building", tag:type });
}
function addProp(x,y,w,h){
  WORLD.colliders.push({ x, y, w, h, type:"prop" });
}
function addShopZone(x,y,w,h, shopId, name){
  WORLD.shops.push({ x, y, w, h, shopId, name });
}

export function getWorld(){ return WORLD; }

// Simple AABB query used by entity system for collisions
export function queryColliders(aabb){
  const out = [];
  for(const c of WORLD.colliders){
    if(intersects(aabb, c)) out.push(c);
  }
  return out;
}
function intersects(a,b){
  return !(a.x+a.w < b.x || a.x > b.x+b.w || a.y+a.h < b.y || a.y > b.y+b.h);
}

// Debug info string
export function debugWorldString(){
  return `WORLD  size=${WORLD.bounds.w}x${WORLD.bounds.h}  colliders=${WORLD.colliders.length}  shops=${WORLD.shops.length}`;
}
