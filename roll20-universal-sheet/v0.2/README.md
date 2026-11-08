# v0.2 — artwork and contextual Dice Bag changes

This is **a local iteration of the Universal Roll20 Sheet**, not a change to the live `ryanlcole.github.io` page.

- The same five illustrated navigation buttons (Character, Base, Abilities, Gear, Linked) are declared *once* outside all sections. Changing sections only changes the selected state.
- Artwork was extracted directly from the user-provided fantasy tileset examples, not reimagined with substitute CSS icons.
- Every currently rollable item in Skills, Flavor, Gear, Actions, Spellbook, Profession and Custom has a contextual Dice Bag expander with a numeric bonus, difficulty target and an Edit recipe disclosure. It uses native Roll20 roll buttons; the roll belongs to that character.
- The full saved Dice Bag recipe library is retained under secondary navigation for advanced users; the **Gear** bottom button never opens the Dice Bag.
- Adds can be created through native repeating sections, and external rules references may be entered manually. Automatic AoN lookup is NOT built; sheet workers cannot fetch live websites. Roll20 Mod/script integration would be a separate design with explicit GM permission.

## Important Roll20 artwork restriction

Local CSS backgrounds such as `url('assets/nav-gear.png')` work in the package's browser `preview.html` only. Roll20 custom sheets use hosted exact image URLs. **Before GM installation with artwork**, upload the included `assets/` images to an accessible public web host (GitHub is a good option), then replace `url('assets/...')` values in `universal.css` with their verified public HTTPS raw URLs. Relative file paths will not work in the Roll20 editor. No public image URLs have been invented and no GitHub site was changed.

Native HTML, CSS and worker logic remain prototypes pending an actual Roll20 GM-hosted sandbox test. The Dice Bag popover uses `<details>` and may require layout adjustments under Roll20's renderer; character rolls and macro expansion are not browser-tested.

# Universal Character Sheet for Roll20 — v0.2 (CSE)

**Original system-neutral character sheet, built for Roll20.** The Dice Bag is a *saved roll-command builder*: each recipe is a native Roll20 sheet roll button backed by a repeating section. No external Dice Bag service, API, or Pro Mod script is required for basic rolls.

## Install in a GM's game

1. The **game creator needs Roll20 Pro** to install a *private custom sheet*. Other players do not need Pro to play in that game. This is not yet a Roll20 community-listed sheet.
2. In the game's settings, select **Custom** character sheet (exact navigation varies with Roll20 UI). Open the Custom Sheet editor or Sheet Sandbox.
3. Ensure **CSE** mode is used (turn off “Legacy Sheet Sanitation” in the editor; Sheet Sandbox can use the provided `sheet.json`, which has `"legacy": false`).
4. Paste `universal.html` into the **HTML** panel and `universal.css` into the **CSS** panel. Do **not** paste `worker.js` separately—the worker is already embedded in the HTML.
5. Save, open a test character, and add one Dice Bag entry using Roll20's `+ Add` control. Confirm the recipe and roll button work **in Roll20** before using it with live characters.
6. Use a new **test game** first; changing a game's sheet does **not** automatically migrate a different sheet's existing attributes. Do not switch a live Pathfinder campaign to this sheet without a rollback plan.

## Dice Bag

Click the **Dice Bag** tab and choose `+Add`:

- **Structured / Dice builder**: choose number of dice (1–20 in the control), d4/d6/d8/d10/d12/d20/d100/dF or custom numeric die, keep/drop highest/lowest, bonus/penalty, reroll 1, exploding dice, optional success threshold, and public/GM whisper.
- **Manual**: open **Advanced / manual macro options** and put a one-line Roll20 chat macro into **Manual Roll20 command**, e.g. `/roll 1d20 + @{strength_mod}` or `/roll 4d6kh3`, or an advanced Roll20 roll template. Use the **Roll recipe** button. Manual mode is also the route for custom Roll20 commands and attributes.
- **Generated / active command** displays the exact command the roll button uses (write-protected to avoid command drift). `Ready: ...` means worker syntax validation passed, **not** that Roll20 executed the roll successfully.
- **Saved macro access**: Roll20 repeating roll buttons can be dragged to its macro quickbar. Their row IDs are owned by Roll20; order might change.
- **No auto-spend**: Dice rolls do not automatically reduce HP, spell slots, ammunition, or other resources. A compatible GM-authorized Mod script would be a separate integration.
- **No external dice implementation**: Actual randomness, chat messages, permissions, and macro parsing are all handled by Roll20.

Example recipes:

| Selection | Expected command structure |
| --- | --- |
| 1×d20 | `&{template:default} {{name=Perception check}} {{Roll=[[1d20]]}}` |
| 2×d20, keep highest, +3 | `&{template:default} {{name=Attack}} {{Roll=[[2d20kh1+3]]}}` |
| 6×d6 success ≥5 | `&{template:default} {{name=Pool}} {{Roll=[[6d6>5]]}}` |
| GM-only 3×d6 | `/w gm &{template:default} {{name=Hidden}} {{Roll=[[3d6]]}}` |

## Tabs

The sheet has the approved core: **Artwork, Bio, Classes, Base, Flavor, Gear, Loot, Actions, Buffs/Debuffs, Spellbook, Knowledge, Profession, Journal, Player**, plus **Dice Bag** and **Custom**. All collections use native repeating sections. No ruleset or attribute names are forced; the sheet does not impersonate Pathfinder or D&D rules automation.

**Known limitations:**

- **Roll20 character image and tokens** are managed by Roll20's Journal / token controls, not by the sheet HTML. Artwork tab stores image references only.
- **GM secrets**: any field inside this sheet may be visible to character viewers. Use Roll20's GM Notes for unrevealed campaign knowledge. Do not put private contact data in character fields.
- **Universal mechanics**: the sheet does not infer game-specific bonus stacking, class prerequisites, spell-slot limits, encumbrance rules, or action-economy legality. These require ruleset packs or manual GM adjudication.
- **Dice Bag command macros**: basic `/roll` commands and roll templates work natively; token movement, automatic resource reductions, deck manipulation, or APIs typically require Pro Mod integrations.
- **Character migration** from a previous sheet is **not automatic**. The new attribute names differ. Export/back up character data first.
- **Browser preview** is an approximation. Roll20 controls and worker APIs only truly work in Roll20 or its Sandbox.

## Files

- `universal.html` — Roll20 sheet HTML, repeating sections, native roll buttons, embedded sheet worker.
- `universal.css` — responsive blue/gold style scoped to sheet classes.
- `worker.js` — source copy of the sheet worker in the HTML for review/testing.
- `sheet.json` — Roll20 metadata, `legacy: false` (CSE).
- `preview.html` / `preview.png` — browser-only layout inspection (does not simulate Roll20).
- `tests/worker.test.js` — Roll20 API-mocked dice-recipe + totals regression tests.
- `tests/validate.py` — structural audit for Roll20-specific markup.

## Validation

```sh
node tests/worker.test.js
python tests/validate.py
```

These tests verify command construction, event callbacks, the section layout, and basic safety constraints. They do **not** prove behavior in Roll20, and no GM installation was performed.

## Documentation references

- [Roll20: Building Character Sheets](https://wiki.roll20.net/BCS)
- [Roll20: CSE framework](https://wiki.roll20.net/CSE)
- [Roll20: Repeating Sections](https://wiki.roll20.net/BCS/Repeating_Sections)
- [Roll20: Buttons & Rolls](https://wiki.roll20.net/Buttons)
- [Roll20: Dice Syntax](https://wiki.roll20.net/Dice_Syntax)
