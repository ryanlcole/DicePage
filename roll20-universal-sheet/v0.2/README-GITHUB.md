# Universal Roll20 Character Sheet — isolated testing branch (v0.2)

**Status:** Development test only. This is not an installed Roll20 game, and is not the canonical RIST site.

## Roll20 Custom Sheet editor
- Keep Legacy Sanitization unchecked (CSE).
- Paste the full contents of `universal.html` into **HTML Layout**.
- Paste the full contents of `universal-roll20-ready.css` into **CSS Styling**.
- Save and open a NEW test character; do not change an existing campaign.
- `universal-roll20-ready.css` points to RAW public artwork URLs in this GitHub review branch.
- Confirm image URLs load, then test a repeating row and its adjacent Dice Bag control.
- No automated AoN scraping is implemented: enter a reference URL manually.
- `preview.html` is visual-only; native Roll20 rolls and sheet-worker behavior require a Roll20 game.

The five bottom icons remain uniform on every section; only the selected icon changes. Each rollable item can expand the Dice Bag controls with bonus, difficulty and edit recipe fields.

**Privacy:** This branch is in a PUBLIC repo, so anyone with the GitHub URLs can view the code and art. No campaign or personal game data is included.

## Contents
`universal.html`, `universal-roll20-ready.css`, `universal.css`, `preview.html`, `worker.js`, `sheet.json`, 8 artwork files in `assets/`, and test source in `tests/`.

See `README.md` for full limitations.
