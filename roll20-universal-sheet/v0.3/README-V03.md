# Universal Roll20 Character Sheet — v0.3 Focus Viewer (TEST)

This is the native Roll20 CSE sheet update for the separate sandbox game. The existing v0.2 version is retained. 16 original sections, 27 dice worker tests.

## Files for your Roll20 Sheet Sandbox

- `universal.html` — choose this in the Sheet Sandbox **HTML** upload.
- `universal-roll20-ready.css` — choose this in the Sheet Sandbox **CSS** upload. Its URLs point at the public assets on the `roll20-universal-sheet-v0.3` GitHub branch.
- `universal.css` — local preview version only, not the recommended Roll20 CSS file.

Refresh the test character after the upload. Do not install in your GMs' live campaigns before verification.

## View controls

- **Focus**: view a single panel/card at a time, tap numbered panel tabs, and touch-scroll within a panel only when there is more content than fits. In the game, the five fixed artwork buttons still switch Character, Base, Abilities, Gear, Linked. To reach the other sections, expand *Navigate sections*.
- **Full Edit**: restores the full vertical character sheet and all standard Roll20 fields, Add/Modify controls and buttons.
- **Pocket**: hides the sheet's content inside the character frame; tap *Open Sheet* to restore. It cannot minimize the native Roll20 outer frame.
- **− 100% +**: scales the interior sheet to 80%, 100% or 120% using CSS `zoom`, where supported. Roll20's own magnifying-glass button controls the host character window independently.

## Native Roll20 window controls

- Double-click/double-tap on a blank region of the Roll20 character's title bar to minimize the **outer** character window. Roll20 supplies the actual minimizer; CSS in the sheet cannot minimize the host overlay.
- Roll20's Pop Out icon near the title can move a character sheet to another browser window on supported devices. Some controls (drag-and-drop, certain edit actions) do not work well when popped out.

## Technical limitations

Roll20's character sheet CSE blocks arbitrary DOM scripting and access to its host popup, so an integrated freehand mouse-drag/pinch-to-zoom canvas like an external web app cannot be implemented purely inside this sheet. Focus replaces much of the long-form scrolling with card selection and native touch panning of overflow. True freehand canvas behavior would require a separate application and a verified integration plan.

## Test status

Static Roll20 sheet validator passed; 27 dice worker tests passed. Chromium browser checks at 375, 390 and 1190 px pass: tabs, focus/editor, card switching, zoom, Pocket collapse/restore and no horizontal overflow. **These are not yet native Roll20 v0.3 installation tests.**

## Dice Bag clarification (v0.3.1)

Every rollable item now has separate **Bonus (+)** and **Penalty (−)** fields. They default to 0 and change the roll by **+bonus − penalty**. The former Difficulty/target DC field has been removed from the quick-roll popup, and the roll chat template no longer displays a Difficulty line. This also applies to the saved-recipe Dice Bag. Existing character roll bonuses are preserved; legacy target-DC attribute values are ignored. This is not a roll-versus-DC comparison.
