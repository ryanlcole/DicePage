# RIST WORLD authoritative grid

The public-alpha WORLD map is a square 30 × 30 logical terrain surface: 900 addressable tiles at exactly 1 km × 1 km per tile.

Each logical kilometre tile is presented with a 10 × 10 viewer subdivision. One minor square is therefore 100 m × 100 m, and each block of 10 × 10 minor squares is one authoritative 1 km × 1 km terrain tile.

Ocean 071 is the implicit base terrain. It is rendered as a repeating visual layer and is not materialized as 900 placed objects. Authored terrain, pieces, regions, and recursive content remain sparse semantic state above that base.

The viewer grid is a separate presentation layer with `square`, `hex`, and `none` modes. Changing or hiding the viewer grid never changes terrain or world identity.

The square map element is also the pointer coordinate surface. Tile drops, moves, fill/edit tools, and persisted normalized positions therefore resolve against the same 30 × 30 kilometre-tile authority in portrait and landscape layouts. Space outside the square map is null workspace rather than extra world cells.

At WORLD scale the canonical terrain distance is 1 km per tile. The ten subdivisions inside that tile are viewer references, not separate terrain tiles. Encounter mode may temporarily switch grid representation and units; leaving the encounter restores the world grid state.

Grid style, recursive address, terrain overrides, and pieces remain part of saved world state. Existing normalized placements are preserved when loaded into the 30 × 30 alpha surface; pre-metric WORLD saves are migrated to the canonical 1 km tile scale without moving their normalized content.
