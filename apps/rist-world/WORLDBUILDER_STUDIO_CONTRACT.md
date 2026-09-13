# World Builder Studio Contract

The World Builder is a dedicated studio workspace for constructing the physical-style game table. It is not the roleplay/play grid itself.

## Physical table authority

- The table surface is the map/world surface. The table itself owns **no grid**.
- The viewer is a camera/window looking at that table. A rectangular screen never stretches the table into rectangular cells.
- At the default World Builder scale, the square construction surface is 30 cells across. Cell width determines cell height, so every construction cell remains a true square. A short viewport simply reveals fewer rows.
- Viewer lock freezes camera/navigation input only. It must not lock placed tiles or prevent the GM from manipulating table contents.

## GM construction grid authority

- The GM square construction grid is a separate presentation/tool overlay above the table.
- The grid can be shown or hidden without changing terrain, placed assets, coordinates, persistence, or the completed image.
- The grid can be raised through layers and tiers. Its current X/Y/Z is the placement plane.
- Tiles may stack at the same X/Y on different layers/tiers.
- Unsupported/mid-air placement is valid. Raising the grid and placing a tile must not silently snap the tile down to terrain or an authored default depth.
- Authored/default depth metadata is descriptive metadata; it never overrides the GM's current raised construction grid during a new placement.

## Tile footprint authority

- `Tile Size` (`1²`, `2²`, `4²`, `8²`, and other supported values) defines the footprint of the **next placement** on the GM construction grid.
- A `1²` tile occupies exactly one construction square. A `2²` tile occupies 2 × 2 squares, an `8²` tile occupies 8 × 8 squares, and so on.
- The selected Tile Size overrides an asset's catalog/default footprint for that new placement. Asset metadata may suggest a size but may not silently replace the GM's explicit selection.
- Placed tiles are transformed to the selected footprint while preserving square-cell geometry.

## Static and animated assets

- A static tile is a placed image with position, footprint, depth, and other placement state.
- A sprite is a **placed animated visual asset**, not a synonym for a terrain image, world map, or Z layer.
- A sprite follows the same placement rules as a static tile. Its position/footprint can remain fixed while its visual state changes over time (for example: a tiny fountain whose water flows, a torch that flickers, or a windmill that turns).
- Static images with one frame or zero animation rate must not be exposed as Sprite Library assets.
- Sprite directories use the same normal asset taxonomy as regular images (for example `Terrain → Fountains`). Geographic prototype names must not become a separate runtime directory authority.

## Play surface boundary

- The GM construction grid is not the gameplay grid.
- When play begins, a GM may place a separate play mat/grid (for example a hex mat) over the completed map.
- Player figurines occupy the play grid. A flying figure may occupy the same horizontal area at a higher layer/tier.
- Adding, changing, or removing a play grid must never rewrite the underlying table, construction-grid geometry, or authored terrain.

## Studio UI authority

- Header authority: Home 5% | context ticker 90% | account/profile image 5% on desktop; mobile may widen edge controls for touch safety while preserving ticker priority.
- Workbench rail: active creation mode and pinned working assets.
- Creation modes: Tiles, Cartography, Lightboard, Image, Draw.
- Tile rail: one horizontal quick-navigation slider at the bottom of World Building. Chat, Dice, Actors and other roleplay controls do not belong here.
- Tile shortcuts can be dragged or tapped to pin them to the workbench; drag is never the only interaction path.
- The general Library and Sprite Library feed the same quick-slot/placement pipeline; asset type changes rendering behavior, not placement authority.
- Campaign Builder remains responsible for campaign population and narrative state such as furniture, NPCs, monsters, lore, scenes and encounters.

## Non-negotiable authority chain

`table surface → independent GM square construction grid → placed static/animated asset stack → optional gameplay mat/grid`

No renderer, catalog, camera control, asset library, or legacy compatibility layer may collapse those authorities into one another.
