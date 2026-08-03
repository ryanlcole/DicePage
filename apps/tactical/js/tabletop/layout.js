export function tabletopLayoutForRole(tabletop, role = "gm") {
  const scene = tabletop.scenes[tabletop.activeSceneId];
  return scene?.tabletopLayout?.[role] || scene?.tabletopLayout?.gm || {};
}

export function setReducedMotion(tabletop, enabled) {
  tabletop.layout.reducedMotion = Boolean(enabled);
}
