import { recordTabletopEvent } from "./scene.js";

export function activeInitiativeProfile(tabletop) {
  return tabletop.initiativeProfiles[tabletop.initiative.profileId] || { entries: [] };
}

export function advanceInitiative(tabletop) {
  const profile = activeInitiativeProfile(tabletop);
  const entries = profile.entries || [];
  if (!entries.length) return { ok: false, message: "No initiative entries." };
  const index = Math.max(0, entries.findIndex((entry) => entry.entryId === tabletop.initiative.activeEntryId));
  const nextIndex = (index + 1) % entries.length;
  if (nextIndex === 0) tabletop.initiative.round += 1;
  tabletop.initiative.activeEntryId = entries[nextIndex].entryId;
  tabletop.initiative.remainingSeconds = tabletop.initiative.turnSeconds;
  recordTabletopEvent(tabletop, "initiative_advance", {
    activeEntryId: tabletop.initiative.activeEntryId,
    round: tabletop.initiative.round
  });
  return { ok: true, activeEntry: entries[nextIndex] };
}
