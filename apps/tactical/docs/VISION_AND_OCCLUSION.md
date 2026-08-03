# Vision And Occlusion

Milestone: `SHAELVIEN-PERCEPTION-1`

Vision uses bounded 2D line-of-sight from the player character's perception origin.

Current implementation:

- Square grids use Bresenham-style logical cell lines.
- Hex grids use axial interpolation and rounding.
- Vision range is converted from physical scale to logical cells.
- Walls and closed-door collision can block vision.
- Open doors and openings permit line of sight.
- Target cell identity remains logical square or axial coordinates.

This is not a full 3D visibility simulation. Height, ceilings, and partial opacity are represented in data and used by the collision model, but the first implementation uses cell-level occlusion.

