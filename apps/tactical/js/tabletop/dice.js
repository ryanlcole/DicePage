import { recordTabletopEvent } from "./scene.js";

export function rollDie(tabletop, dieId, options = {}) {
  const profile = tabletop.dice[dieId];
  if (!profile) return { ok: false, message: "Unknown die." };
  const resultIndex = tabletop.sceneState.diceResults.length;
  const sequence = Array.isArray(profile.sequence) && profile.sequence.length ? profile.sequence : null;
  const numeric = sequence
    ? sequence[resultIndex % sequence.length]
    : ((resultIndex * 17 + Number(profile.sides || 2)) % Number(profile.sides || 2)) + 1;
  const face = Array.isArray(profile.faces) ? profile.faces[Math.max(0, Math.min(profile.faces.length - 1, numeric - 1))] : String(numeric);
  const roll = {
    rollId: `roll-${tabletop.replayBoundary.nextSequence}`,
    dieId,
    label: profile.label,
    result: numeric,
    face,
    visibility: options.visibility || "scene_shared",
    source: options.source || "tabletop_die"
  };
  tabletop.sceneState.diceResults.push(roll);
  recordTabletopEvent(tabletop, "die_roll", roll);
  return { ok: true, roll };
}

export function rollCoin(tabletop, options = {}) {
  return rollDie(tabletop, "coin", options);
}
