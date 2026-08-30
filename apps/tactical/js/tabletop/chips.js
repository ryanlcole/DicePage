export function activeChips(tabletop, affectedRoll = null) {
  const active = new Set(tabletop.sceneState.activeChipIds || []);
  return Object.values(tabletop.chips).filter((chip) => active.has(chip.chipId) && (!affectedRoll || chip.affectedRoll === affectedRoll));
}

export function modifierTotal(tabletop, affectedRoll) {
  return activeChips(tabletop, affectedRoll).reduce((sum, chip) => sum + Number(chip.value || 0), 0);
}

export function visibleModifierRows(tabletop, affectedRoll) {
  return activeChips(tabletop, affectedRoll).map((chip) => ({
    chipId: chip.chipId,
    label: chip.label,
    value: Number(chip.value || 0),
    category: chip.category,
    duration: chip.duration
  }));
}
