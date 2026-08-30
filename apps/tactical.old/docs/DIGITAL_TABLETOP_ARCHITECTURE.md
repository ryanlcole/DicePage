# Digital Tabletop Architecture

Milestone: `SHAELVIEN-DIGITAL-TABLETOP-1`

The Tactical workspace is now organized as a fixed single-screen tabletop. The Canvas map stays central while tabletop objects sit in bounded edge trays and major tools open as centered overlays.

## Shell

- The application root is fixed to the visible viewport.
- Normal tabletop play does not require page-level scrolling.
- The map viewport owns pan, zoom, rotation, selection, and contextual map gestures.
- Decks, cards, dice, chips, initiative, clock, lore, and menus are rendered as tabletop objects rather than stacked form panels.

## State Boundary

Tabletop state is separate from map terrain and editor viewport state:

- `scene`: current table context around a map.
- `sceneState`: card sharing, revealed cards, active chips, dice results, card use counts, and drag state.
- `initiative`: active turn, round, pause state, and turn clock.
- `replayBoundary`: authoritative tabletop events that belong in deterministic replay.
- `layout`: per-user tabletop preferences such as active deck, selected die, scroll open state, and reduced motion.

Personal UI layout, menu state, and viewport transforms are not gameplay replay data.

