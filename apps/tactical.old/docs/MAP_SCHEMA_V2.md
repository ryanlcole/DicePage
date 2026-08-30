# Map Schema V2

Schema v2 adds map-specific geometry and optional image-backed tile references while preserving existing v1 square maps.

## Migration

Maps without `gridType` normalize in memory as:

```json
{
  "gridType": "square",
  "gridSettings": {
    "square": {
      "columns": 16,
      "rows": 10,
      "cellWidth": 5,
      "cellHeight": 5,
      "unitSystem": "imperial",
      "distanceUnit": "ft"
    }
  }
}
```

Source JSON files are not rewritten blindly. New fields are written only through intentional save or map settings changes.

## Square Settings

```json
{
  "columns": 16,
  "rows": 10,
  "cellWidth": 5,
  "cellHeight": 5,
  "unitSystem": "imperial",
  "distanceUnit": "ft"
}
```

## Hex Settings

```json
{
  "orientation": "pointy",
  "radius": 5,
  "radiusMeaning": "center_to_corner",
  "unitSystem": "imperial",
  "distanceUnit": "ft",
  "layoutBounds": {
    "columns": 16,
    "rows": 10
  }
}
```

## Tile Image Field

Tiles may add:

```json
{
  "image": {
    "imageAssetId": "tile-asset-stone-floor-001",
    "fitMode": "cover",
    "rotationDeg": 0,
    "flipX": false,
    "flipY": false,
    "opacity": 1,
    "tint": null
  }
}
```

Missing or failed image references render a visible fallback.

## Resize Protection

Shrinking a map previews removed terrain overrides, placed tiles, entities, child maps, triggers, and encounters. Shrink does not proceed without explicit confirmation when content would be removed.

Retained cells keep stable logical IDs.
