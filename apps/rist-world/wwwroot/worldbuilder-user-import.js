// Opens the existing rated private-upload flow from the WorldBuilder quick rail.
// The asset library may be rendered one or two frames after Blazor toggles it,
// so retry briefly instead of depending on browser timing.
export function open() {
  let attempts = 0;
  const tryOpen = () => {
    const button = document.querySelector('.map-asset-inventory .map-asset-upload');
    if (button && !button.disabled) {
      button.click();
      return;
    }
    attempts += 1;
    if (attempts < 20) requestAnimationFrame(tryOpen);
  };
  requestAnimationFrame(tryOpen);
}
