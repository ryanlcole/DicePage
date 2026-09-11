export function point(element, clientX, clientY) {
  const rect = element?.getBoundingClientRect?.();
  if (!rect || rect.width <= 0 || rect.height <= 0) return [0.5, 0.5];
  const x = Math.max(0, Math.min(1, (Number(clientX) - rect.left) / rect.width));
  const y = Math.max(0, Math.min(1, (Number(clientY) - rect.top) / rect.height));
  return [x, y];
}
