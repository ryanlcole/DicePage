# Grid Geometry

Square remains the default and authoritative geometry for the first preset campaign.

## Map Field

```json
{
  "gridType": "square"
}
```

or:

```json
{
  "gridType": "hex"
}
```

Missing `gridType` loads as `square`.

## Square Coordinates

Square cells use integer `{ "x": 0, "y": 0 }` coordinates.

## Hex Coordinates

Hex cells use axial `{ "q": 0, "r": 0 }` coordinates. Tile records also preserve `x/y` as compatibility aliases so existing map and encounter functions can operate without a second engine.

## Hex Radius

`radius` means center to corner. Side length equals radius. Center-to-edge distance equals `radius * cos(30deg)`.

Supported orientations:

- `pointy`
- `flat`

Hit testing uses axial conversion plus polygon containment. It does not use rectangular approximation.

## Physical Sizing

Square physical mode requires whole-cell dimensions. Non-whole results are rejected.

Hex physical mode derives approximate layout bounds and reports:

- requested width and height
- derived columns and rows
- actual covered width and height
- difference from requested bounds

Hex packing is not forced into an exact rectangle.
