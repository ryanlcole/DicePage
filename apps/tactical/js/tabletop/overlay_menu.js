import { closeOverlay, openOverlay, TABLETOP_CATEGORIES } from "./scene.js";

export function setOverlayCategory(tabletop, category) {
  openOverlay(tabletop, TABLETOP_CATEGORIES.includes(category) ? category : "scene");
}

export function closeTabletopOverlay(tabletop) {
  closeOverlay(tabletop);
}
