# Roll20 v0.3.2 — iPhone sandbox layout hotfix

Scope: fixes the **currently installed v0.3.1 Focus Viewer**; does not replace the separate Pathfinder v0.4 development build.

What changed:
* Replaces the unresponsive in-sheet CSS `zoom` declarations with tested CSS `transform:scale` and inverse widths for 80/100/120 percent inner-content zoom.
* Keeps Focus / Edit / Pocket controls visible on narrow iPhones with a two-line responsive toolbar.
* Reduces the in-sheet secondary navigation label to `☰ More sections`, while preserving the other section links.
* Retains the shared five-image artwork dock, repeaters, sheet workers, Dice Bag, and current attribute names.

Limitations:
* Roll20's outer modal, title bar and native tabs (`Character Sheet`, `Bio & Info`, `Attributes & Abilities`) are not part of custom sheet HTML and cannot be hidden/replaced using a custom sheet. Use Roll20's own zoom, minimize, and pop-out where the browser supports them.
* CSS scaling only changes size of *sheet content*, not Roll20's outer popup; long repeating lists still need scrolling. The touch-pan / 3-D canvas style cannot be implemented as arbitrary JavaScript inside a normal Roll20 CSE sheet.
* This patch was tested in a local browser, not verified inside the actual Roll20 Sandbox. If Roll20 sanitizes a CSS declaration, please send a new sandbox screenshot.

To install in the Sheet Sandbox: use the two standalone files at the root of this folder with the HTML and CSS upload controls. Keep Legacy Sanitization unchecked.
