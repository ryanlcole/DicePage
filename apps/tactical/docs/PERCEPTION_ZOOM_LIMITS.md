# Perception Zoom Limits

Milestone: `SHAELVIEN-PERCEPTION-1`

GM zoom remains governed by editor viewport bounds.

Player zoom-out is clamped by the active controlled PC's maximum sensory radius:

```text
maximum sensory radius = max(vision range, hearing range)
map scale converts physical range to cells
minimum player zoom = workspace size / sensory diameter in canvas pixels
```

Example:

```text
5 ft per cell
140 ft hearing range
140 / 5 = 28 cells
diameter = 56 cells
```

The clamp is a presentation rule and not a security boundary. Player map data is still filtered before rendering.
