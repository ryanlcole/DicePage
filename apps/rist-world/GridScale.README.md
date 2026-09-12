# RIST WORLD authoritative grid

The public-alpha WORLD map is a square 30 × 30 logical surface: 900 addressable canonical cells.

Cells and coordinates are spatial truth. Miles, kilometres, metres, feet, and Measureficts are measurement representations applied to that truth. A world may therefore define one cell as one kilometre, five feet, one Giant's Leap, or any other authored unit without changing coordinates, terrain identity, or persistence addresses.

Ocean 071 is the implicit base terrain. It is rendered as a repeating visual layer and is not materialized as 900 placed objects. Authored terrain, pieces, regions, and recursive content remain sparse semantic state above that base.

The viewer grid is a separate presentation layer with `square`, `hex`, and `none` modes. Changing or hiding the viewer grid never changes terrain or world identity.

The square map element is also the pointer coordinate surface. Tile drops, moves, fill/edit tools, and persisted normalized positions therefore resolve against the same 30 × 30 cell authority in portrait and landscape layouts. Space outside the square map is null workspace rather than extra world cells.

A world's measurement profile controls how distance is spoken and displayed. Physical profiles may use conventional units. A Measurefict stores its singular name, plural name, optional abbreviation, and the number of authored units represented by one canonical cell. Measurement profiles may not rewrite canonical coordinates.

Grid style, calibration, measurement profile, recursive address, terrain overrides, and pieces remain part of saved world state. Existing normalized placements are preserved when loaded into the 30 × 30 alpha surface.
