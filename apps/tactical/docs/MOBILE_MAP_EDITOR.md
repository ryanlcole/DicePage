# Mobile Map Editor

Mobile editing is map-first. The canvas remains the primary work surface and controls are reduced to a compact top bar, a fixed GM tool rail, and an inspector sheet.

## Gestures

- Tap selects the exact logical cell or tile.
- Long-press opens the GM context menu in map edit mode.
- Long-press does not paint or move.
- Touch release clears active input state.
- Pan mode drag changes the per-map viewport offset.
- Two-pointer pinch changes the per-map viewport zoom.

The canvas uses `touch-action: none` to prevent page zoom conflicts while map gestures are active.

## Context Menu

The context menu is shared with desktop right-click and is constrained to the viewport. It is available only in GM map edit mode.

Player view never receives GM editing actions.

## Inspector

The inspector becomes a bottom sheet on mobile. It can be dismissed without clearing selection.

## Persistence

The current map, logical selection, and per-map viewport are saved through the existing localStorage state. If an unsafe scene is restored, state creation returns to `MAP_VIEW` with the last valid map.
