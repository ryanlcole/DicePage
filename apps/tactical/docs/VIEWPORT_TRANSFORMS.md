# Viewport Transforms

Milestone: `SHAELVIEN-TACTICAL-WORKSPACE-1`

The map canvas uses one render path:

1. Clear the screen-space canvas.
2. Translate by viewport pan.
3. Scale by viewport zoom.
4. Rotate around the logical map center.
5. Draw the map, entities, overlays, and grid.

Input uses the inverse transform before hit testing. Logical tile coordinates remain unchanged by viewport rotation.

## Supported View Modes

- Fit Map
- Fit Width
- Fit Height
- Actual Size
- Fit Selection
- Custom Zoom

Supported zoom range: `25%` to `400%`.

Supported rotation angles: `0`, `90`, `180`, and `270` degrees.

## Persistence

Viewport state is saved per map:

```json
{
  "zoom": 1,
  "offsetX": 0,
  "offsetY": 0,
  "rotationDeg": 0,
  "fitMode": "fit-map",
  "gridVisible": true,
  "compassVisible": true,
  "initialized": true
}
```

Invalid or missing viewport values normalize to Fit Map and North-up.

