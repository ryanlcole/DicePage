const KEY = 'rist.world.simple.v1';
const BASE = {
  role: 'gm',
  grid: { style: 'square', diameter: 48, distance: 5, unit: 'mi' },
  piece: 'coin', tile: '', objects: [], rolls: [], mods: []
};
export function loadWorldState() {
  try {
    const saved = JSON.parse(localStorage.getItem(KEY) || 'null');
    return saved ? { ...structuredClone(BASE), ...saved, grid: { ...BASE.grid, ...(saved.grid || {}) } } : structuredClone(BASE);
  } catch { return structuredClone(BASE); }
}
export function saveWorldState(state) { localStorage.setItem(KEY, JSON.stringify(state)); }
export function clamp01(value) { return Math.max(0, Math.min(1, Number(value) || 0)); }
export function rollTotal(state) {
  return state.rolls.reduce((n, r) => n + Number(r.value || 0), 0) + state.mods.reduce((n, m) => n + Number(m.value || 0), 0);
}
