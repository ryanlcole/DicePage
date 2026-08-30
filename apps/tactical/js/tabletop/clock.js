import { recordTabletopEvent } from "./scene.js";

export function pauseClock(tabletop) {
  tabletop.initiative.paused = true;
  recordTabletopEvent(tabletop, "timer_paused", { activeEntryId: tabletop.initiative.activeEntryId });
  return { ok: true };
}

export function resumeClock(tabletop) {
  tabletop.initiative.paused = false;
  recordTabletopEvent(tabletop, "timer_resumed", { activeEntryId: tabletop.initiative.activeEntryId });
  return { ok: true };
}

export function clockProgress(tabletop) {
  const total = Math.max(1, Number(tabletop.initiative.turnSeconds || 90));
  const remaining = Math.max(0, Number(tabletop.initiative.remainingSeconds || 0));
  return {
    total,
    remaining,
    usedRatio: 1 - remaining / total,
    paused: tabletop.initiative.paused
  };
}
