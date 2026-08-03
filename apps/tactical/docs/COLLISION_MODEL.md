# Collision Model

Milestone: `SHAELVIEN-PERCEPTION-1`

Collision is represented independently from sprite bounds. A placed tile or entity may block movement, vision, sound, projectiles, or reach separately.

Authoritative fields:

```json
{
  "collision": {
    "blocksMovement": true,
    "blocksVision": true,
    "blocksSound": false,
    "blocksProjectile": true,
    "blocksReach": false,
    "blocksOverhead": false,
    "isFloor": false,
    "isCeiling": false,
    "height": 2.5,
    "heightUnit": "m",
    "opacity": 1,
    "soundTransmission": 0.35,
    "soundAbsorption": 0.45,
    "openings": []
  },
  "collisionShape": {
    "type": "rectangle",
    "anchor": "center",
    "width": 1,
    "depth": 1,
    "height": 1,
    "unit": "cell"
  }
}
```

Supported initial shapes:

- `rectangle`
- `circle`
- `polygon`
- `tile_footprint`
- `hex_footprint`
- `line_segment`
- `doorway`
- `opening`

Collision presets live in `data/collision_presets.json`. Existing map JSON is normalized in memory, so legacy square maps keep loading without source rewrites.

