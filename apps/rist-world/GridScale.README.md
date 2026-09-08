# RIST WORLD authoritative grid

The public-alpha WORLD map is a square 30 × 30 logical surface: 900 addressable cells at one mile per cell.

Ocean 071 is the implicit base terrain. It is rendered as a repeating visual layer and is not materialized as 900 placed objects. Authored terrain, pieces, regions, and recursive content remain sparse semantic state above that base.

The viewer grid is a separate presentation layer with `square`, `hex`, and `none` modes. Changing or hiding the viewer grid never changes terrain or world identity.

The square map element is also the pointer coordinate surface. Tile drops, moves, fill/edit tools, and persisted normalized positions therefore resolve against the same 30 × 30 authority in portrait and landscape layouts. Space outside the square map is null workspace rather than extra world cells.

At WORLD scale the default distance is one mile per cell. Encounter mode may temporarily switch grid representation and units; leaving the encounter restores the pre-encounter grid state.

Grid style, calibration, recursive address, terrain overrides, and pieces remain part of saved world state. Existing normalized placements are preserved when loaded into the 30 × 30 alpha surface.
