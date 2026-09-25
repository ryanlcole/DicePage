# ReLiC Website Control & Accessibility Audit — 2026-09-25

Status: RECOVERED AUDIT CHECKPOINT  
Repository: ryanlcole/DicePage  
Branch: live-alpha-rist-blazor-world  
Inspected head before this report: `9fc8a3359f0918ba09aed339793c3f6f70f827d6`  
Audit rule: repository/current inspected source is implementation truth; deployment success and runtime/device behavior are tracked separately.

## Why this checkpoint exists

A ChatGPT Work audit exhausted its Work allowance before producing a clean final handoff. This document reconstructs the surviving findings and rechecks them against the current branch rather than assuming the interrupted workspace saved its patches or report.

No evidence was found that the interrupted Work session committed its claimed patches or saved its final audit report into this repository. Current source was therefore re-inspected from scratch.

## Evidence classes

- **VERIFIED SOURCE** — reproduced in current branch source.
- **VERIFIED AUTOMATION** — current exact-head CI/deployment/test evidence.
- **NEEDS DEVICE/LIVE TEST** — cannot be established by source alone.
- **NOT CURRENT / RECONCILED** — interrupted audit finding no longer matches current source/deployment intent.

---

## A. Verified current source defects

### A1. Region selection camera lock is incomplete

**Severity:** High  
**Area:** Region Definer / input parity  
**Evidence:** VERIFIED SOURCE

When Region Definer selection is locked, the UI announces that zoom, pan, and parallax are frozen. Pointer drag and mouse-wheel zoom respect that lock, and the contextual Select keyboard disables its own zoom/fit controls.

However, other camera paths still bypass the same lock:

- bottom-slider Fit / Zoom In / Zoom Out callbacks call `fitMap` / `zoomCenter` directly;
- Settings → Fit calls `fitMap` directly;
- `RistViewerInput.install` receives unconditional pan, zoom, and fit callbacks;
- `viewer-input.js` maps Arrow keys to pan, +/- to zoom, and F to fit without checking Region Definer selection lock.

**Effect:** a keyboard user or a user activating the persistent bottom controls can move the map while selecting deed cells, despite the interface stating the map is frozen.

**Required repair:** one authoritative camera-lock predicate must gate every user-originating pan/zoom/fit path.

---

### A2. Region grid creates 900 ordinary tab stops

**Severity:** High  
**Area:** Keyboard / screen reader  
**Evidence:** VERIFIED SOURCE

The Region Definer grid is 30 × 30. `ensureRegionSelectionOverlay()` creates a native `button` for each cell, giving 900 focusable controls. Each cell has useful semantic text (coordinate plus top tile beneath), but there is no roving-tabindex or equivalent active-descendant strategy.

`aria-hidden` is toggled on the grid, but cell tab order is not reduced to one active cell.

**Effect:** keyboard and screen-reader users can be forced through hundreds of tab stops.

**Required repair:** use a single tab stop for the grid, or roving `tabindex`, with arrow-key cell navigation and Enter/Space selection. Inactive/hidden grid cells must not remain in the page tab order.

---

### A3. Reduced-motion handling is incomplete in the World Builder / Region Definer prototype

**Severity:** High  
**Area:** Motion accessibility  
**Evidence:** VERIFIED SOURCE

`prototype.js` reads:

`matchMedia('(prefers-reduced-motion: reduce)').matches`

but the resulting `reducedMotion` value is not used elsewhere in the file.

Current consequences include:

- device-orientation tilt continues to update tilt targets;
- the tilt animation loop continues to use `requestAnimationFrame`;
- committed sprite animations can start automatically through `startSpriteMotion()`;
- automatic/resumed sprite playback does not consult reduced-motion preference.

The CSS media query disables plane opacity transitions only. That does not stop the motion systems above.

**Required repair:** reduced motion must suppress automatic tilt/parallax animation and automatic sprite playback, respond to preference changes during the session, and preserve a non-motion equivalent. Any explicit user override should be deliberate and clearly separate from autoplay behavior.

---

## B. Current source improvements that require physical-device verification

### B1. Narrow-phone bottom controls

**Interrupted Work finding:** toolbar required roughly 410 CSS px and controls began off-screen.

**Current source status:** NEEDS DEVICE/LIVE TEST; source has materially improved.

Current World Builder CSS now uses:

- full-width bottom slider;
- horizontal overflow scrolling;
- `width:max-content; min-width:100%`;
- iOS safe-area padding;
- 44 × 44 persistent controls;
- 48px contextual keyboard controls;
- Region Definer control lift above browser chrome.

This means the earlier “hard 410px minimum width” should not be treated as a confirmed current defect. The remaining question is discoverability: controls may still begin outside the initial horizontal viewport and require a swipe.

**Required physical test:** iPhone widths around 320/360/390/430 CSS px, portrait and landscape, with browser chrome visible.

---

### B2. Viewport resize / fitted-map cropping

**Interrupted Work finding:** a fitted map could crop incorrectly after the viewport shrank.

**Current automation status:** NEEDS DEVICE/LIVE TEST; regression coverage now passes.

The current exact-head deployment test suite reports:

- “viewport resize preserves zoom and world point at center across desktop and narrow dimensions” — PASS;
- “successful deed removes selection grid and transitions directly into the editor” — PASS.

The source also uses a `ResizeObserver` and `RistViewerInput.resizeCamera`.

Do not close the issue solely from unit/runtime-contract tests; recheck on real Safari/iOS and tablet browsers.

---

### B3. UI language duplicate choices

**Interrupted Work finding:** duplicate language menu entries.

**Current source status:** NOT REPRODUCED IN CURRENT SOURCE.

The current public home selector contains one entry for each supported language and the `LANGUAGE_META` source contains matching unique language identities. The sitewide language layer adds missing options by value instead of blindly duplicating them.

**Required live test:** open the public home and signed-in game after hydration/translation and verify that no duplicate options appear after scripts initialize.

---

## C. Perceiver reduced-motion status

**Evidence:** VERIFIED SOURCE, mixed result.

Perceiver is better than the World Builder prototype:

- initial scene/sprite playback is disabled when reduced motion is active;
- scene loading sets playback according to reduced-motion state;
- idle parallax offsets are suppressed under reduced motion.

Remaining review points:

- the device-motion/TILT path must also honor reduced motion consistently;
- video/spectral import must not silently reintroduce autoplay motion;
- explicit Play behavior should be distinguishable from automatic playback.

This is not the same defect as the prototype; treat the two surfaces separately.

---

## D. Physical game-controller support

**Status:** NEEDS DEVICE/LIVE TEST / implementation gap suspected.

Primary viewer input modules inspected in this pass expose pointer/touch, keyboard, device-orientation, and semantic button controls. No complete physical Gamepad API navigation/selection layer was established in the inspected World Builder / Region Definer path.

Do not claim controller parity until a real controller is tested.

Minimum parity target:

- directional navigation / camera motion;
- focus movement;
- activate/confirm;
- back/cancel;
- zoom;
- Select/DESELECT for Region Definer;
- menu open/close;
- no operation that exists only through pointer precision.

---

## E. Current exact-head deployment evidence

GitHub Actions run `36198239505` (“Deploy RIST Frontend to AWS”) completed successfully for exact head `9fc8a3359f0918ba09aed339793c3f6f70f827d6`.

Verified by that deployment:

- ReLiCGameMaster home;
- Creator Store canonical `/store/index.html`;
- membership page;
- RIST WORLD / framework MIME;
- Launcher;
- six ReLiC story scenes;
- authenticated launch contract;
- recursive World/Region/Local/Instance contract checks;
- canonical viewer input and claimed-deed-overlay tests;
- private canonical-source isolation tests.

Deployment success is **not** proof that touch, VoiceOver, physical gamepad, Safari cropping, or signed-in editor workflows are behaviorally correct.

---

## F. Kickstarter finding reconciled

**Interrupted Work finding:** Kickstarter link opened homepage content.

**Current deployment intent:** NOT A CURRENT PUBLIC-CAMPAIGN DEFECT.

The deployment explicitly removes `/kickstarter/` from the public origin and verifies:

> Kickstarter preparation surface is unpublished.

The current public home source does not contain a Kickstarter navigation link.

If an old client/cache still exposes a Kickstarter link, treat that as stale navigation/cache evidence rather than publishing the internal preparation page. Do not “fix” this by exposing the campaign draft.

---

## G. Current build/deployment warnings

These are warnings, not necessarily release blockers:

1. Several historical chat-import image files cannot be normalized because they are invalid/corrupt image payloads.
2. Optional MMO and Sandbox toggle artwork requests returned HTTP 403 during deployment.
3. C# warnings include unreachable code in external-AI runtime paths.
4. Possible nullability warnings exist in World Claim and Navigation code.
5. Two private fields are assigned but unused.
6. A browser platform-compatibility warning exists around `NormalizationForm.FormKC` in world-deletion code.
7. GitHub Actions reports Node.js 20 deprecation for some action dependencies.

Each warning should be triaged separately from the control/accessibility audit.

---

## H. Free automated accessibility stack already present

The repository already contains a free/local-first audit workflow:

`.github/workflows/accessibility-addons.yml` — **Accessibility Add-on Audit**

It is currently manual (`workflow_dispatch`) and uses pinned tooling to run:

- A11y Toolkit audit;
- keyboard audit;
- 320px reflow audit;
- accessibility snapshot;
- Playwright Chromium.

Artifacts are retained for 30 days.

No run of this workflow was found in the inspected recent Actions history. It must be manually dispatched before its evidence can be included in this audit.

Automated evidence is not WCAG conformance proof. Physical keyboard, screen reader, touch, gesture, and controller testing remains required.

---

## I. Device matrix still required

### Phone
- iPhone Safari portrait/landscape;
- bottom controls with browser chrome visible;
- safe-area behavior;
- one-finger pan, two-finger/pinch zoom where supported;
- Region Select lock;
- device tilt;
- reduced motion;
- VoiceOver.

### Tablet
- iPad Safari portrait/landscape;
- full-map fit;
- touch and hardware keyboard;
- VoiceOver;
- external pointer if available.

### Laptop / desktop
- Chrome/Edge/Firefox/Safari where available;
- full-map fit;
- mouse;
- keyboard-only;
- 200–400% browser zoom/reflow;
- Windows Narrator and/or NVDA;
- physical game controller.

### Signed-in paths
- Discord authentication;
- World Builder;
- Region Definer;
- Local Definer;
- asset library;
- personal/private assets;
- store/account surfaces.

---

## J. Repair order for next implementation pass

1. Fix Region Definer camera-lock bypass at a single authority boundary.
2. Replace 900-cell tab order with roving/active grid navigation.
3. Make reduced-motion behavior authoritative for prototype tilt and sprite autoplay.
4. Run the existing Accessibility Add-on Audit and preserve its artifacts.
5. Re-test mobile bottom-control visibility and fitted-map resizing on real iPhone/iPad.
6. Audit/implement physical gamepad parity.
7. Recheck hydrated language selector for runtime duplication.
8. Triage deployment warnings separately; do not mix cosmetic asset warnings with accessibility blockers.
9. Do not publish the Kickstarter preparation surface as a “fix.”

---

## Copy/paste repair prompt

Use the current `ryanlcole/DicePage` branch `live-alpha-rist-blazor-world`. Re-read the branch head immediately before editing and never push to main. Preserve all current private-storage, recursive-authority, viewer, Region/Local hierarchy, and deployment behavior.

Start from `docs/audits/2026-09-25-relic-control-accessibility-audit.md`. Treat its evidence labels literally; do not convert source evidence into live-device claims.

Fix only reproduced defects first:

1. Region Definer selection lock: create one authoritative predicate for “selection camera locked” and route every USER-ORIGINATING camera path through it — pointer pan/pinch, wheel, bottom Fit/Zoom buttons, Settings Fit, and `RistViewerInput` physical-keyboard pan/zoom/Fit callbacks. Programmatic refits required by workflow transitions may bypass the user lock deliberately. Add regression tests proving Arrow keys, +/−, F, bottom controls, wheel, drag and pinch cannot change the camera while SELECT is locked.

2. Region grid accessibility: the 30×30 grid must not create 900 normal Tab stops. Implement roving tabindex or `aria-activedescendant` so Tab enters/leaves the grid once; arrow keys move the active cell; Enter/Space toggles it; coordinate, top-tile description, existing-claim status and selected state remain announced. When the grid is inactive or hidden, none of its cells may stay tabbable. Add keyboard/focus regression tests.

3. Reduced motion: in the World Builder/Region Definer prototype, actually use the reduced-motion preference. Stop automatic device-tilt/parallax motion and automatic sprite playback when reduction is requested; handle preference changes during the session; retain a non-motion representation. Review Perceiver separately: its initial playback already respects reduced motion, but verify TILT and video/spectral-import paths. Do not remove an intentional explicit user-controlled Play option unless necessary; distinguish explicit play from autoplay.

Then run all existing viewer/Region/Local/recursive tests and the manual GitHub Action “Accessibility Add-on Audit.” Preserve the audit artifacts. Test 320, 360, 390, 430px phone widths plus tablet/laptop/desktop. On real hardware verify touch, mouse, keyboard, VoiceOver/Narrator/NVDA where available, and a physical game controller.

Current source already provides horizontal bottom-slider scrolling, safe-area padding, 44px persistent buttons, 48px contextual controls, viewport-resize preservation logic, and unique source-level language options. Do not regress them. Reproduce before modifying those areas.

Do not publish `/kickstarter/`: current deployment intentionally keeps Kickstarter preparation private/unpublished. Do not treat its fallback behavior as a reason to expose the draft.

Finally report each item as VERIFIED LIVE, VERIFIED SOURCE, AUTOMATED CHECK, or NOT YET TESTED, include exact test commands/results, exact commit SHA, exact deployment workflow result, and a remaining physical-device checklist.
