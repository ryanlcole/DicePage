// ============================================================
// UI Frame – Phase 1
// - No visible UI; only supports debug overlay toggle
// - Future: RPG frame (bag, wallet, dialogs)
// ============================================================
let debugVisible = false;
export function initUIFrame(){ /* reserved for future UI mount */ }
export function setDebugVisible(v){
  debugVisible = !!v;
  const el = document.getElementById('dbg');
  el.style.display = debugVisible ? 'block' : 'none';
}
