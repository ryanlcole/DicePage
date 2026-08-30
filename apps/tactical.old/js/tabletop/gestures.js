export const GESTURE_DEFAULTS = Object.freeze({
  moveThreshold: 7,
  doubleTapMs: 360,
  doubleTapTolerancePx: 18,
  longPressMs: 550,
  rotationSnapDeg: 90
});

export function distance(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

export function angleDeg(a, b) {
  return (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI;
}

export function midpoint(points) {
  return {
    x: points.reduce((sum, point) => sum + point.x, 0) / points.length,
    y: points.reduce((sum, point) => sum + point.y, 0) / points.length
  };
}

export function snapRotationDeg(value, step = GESTURE_DEFAULTS.rotationSnapDeg) {
  const normalized = ((Number(value) % 360) + 360) % 360;
  return ((Math.round(normalized / step) * step) % 360 + 360) % 360;
}

export function sameTapTarget(previous, next, options = GESTURE_DEFAULTS) {
  if (!previous || !next) return false;
  if (previous.mapId !== next.mapId || previous.cellId !== next.cellId) return false;
  if (next.time - previous.time > options.doubleTapMs) return false;
  return distance(previous.point, next.point) <= options.doubleTapTolerancePx;
}
