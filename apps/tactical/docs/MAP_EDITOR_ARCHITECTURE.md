# Map Editor Architecture

Build: `SHAELVIEN-TACTICAL-EDITOR-1`

The editor remains a presentation and interaction layer over the existing central state object. It does not introduce a second map engine, a second gameplay loop, or a competing persistence store.

## Runtime Shape

- Entry point: `index.html`
- Styling: `styles.css`
- Main loop: `js/app.js`
- Input: `js/input.js`
- Map model and navigation: `js/maps.js`
- Grid geometry: `js/grid.js`
- GM edit commands: `js/editor.js`
- Tile asset records: `js/assets.js` and `data/assets/tile_asset_registry.json`
- Persistence: existing localStorage key through `js/api.js`

## Map-First Layout

Desktop uses three working areas: compact left tool rail, dominant bounded canvas viewport, and collapsible right inspector.

Mobile uses the canvas as the primary surface, a compact top command bar, a bottom/fixed GM tool rail, and an inspector bottom sheet.

## Selection

Selection is stored as logical cell identity:

```json
{
  "mapId": "map-world",
  "cellId": "map-world:square:7:4",
  "gridType": "square",
  "coordinates": { "x": 7, "y": 4 }
}
```

Hex selections use axial coordinates:

```json
{
  "mapId": "map-editor-hex-pointy",
  "cellId": "map-editor-hex-pointy:hex:1:1",
  "gridType": "hex",
  "coordinates": { "q": 1, "r": 1 }
}
```

Screen pixels are never stored as canonical selection.

## Edit History

Undo/redo records full map snapshots in `state.editor.undoStack` and `state.editor.redoStack`. This history is separate from encounter replay records and is not used during deterministic replay reconstruction.

## First Preset Protection

Existing maps without `gridType` normalize in memory to `square`. Tavern Ambush remains square and its trigger/encounter/replay behavior is not changed by the editor upgrade.
