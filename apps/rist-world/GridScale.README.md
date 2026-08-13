# RIST WORLD adaptive grid

The WORLD map uses a viewport overlay grid with 10 columns and 20 rows.

Grid modes are `square`, `hex`, and `none`.

A GM calibrates the current zoom by entering the distance represented by one visible grid cell and selecting **Set scale here**. The calibration stores both that distance and the zoom at which it was set. The displayed distance per cell then scales inversely with map zoom, so zooming out increases the represented distance per cell and zooming in decreases it.

The overlay remains fixed to the tabletop viewport while the underlying world map pans and zooms. Calibration is persisted with the saved world state.
