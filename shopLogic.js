// ============================================================
// Shop Logic – Phase 1 placeholder
// - Will handle NPC dialog, checkout, item claim/release in Phase 2
// ============================================================
export async function claimDie(productId){
  try{
    const r = await fetch('/api/item/claim', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ productId })
    });
    return await r.json();
  }catch(e){
    return { ok:false, error: String(e) };
  }
}
export async function releaseDie(productId){
  try{
    const r = await fetch('/api/item/release', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ productId })
    });
    return await r.json();
  }catch(e){
    return { ok:false, error: String(e) };
  }
}
