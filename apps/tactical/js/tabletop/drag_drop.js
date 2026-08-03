export function startDrag(tabletop, type, id, origin = {}) {
  tabletop.sceneState.drag = { type, id, origin, active: true };
  return { ok: true, drag: tabletop.sceneState.drag };
}

export function endDrag(tabletop, target = null) {
  const drag = tabletop.sceneState.drag;
  tabletop.sceneState.drag = null;
  return { ok: Boolean(drag), drag, target };
}
