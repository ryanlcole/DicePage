# Tabletop Gestures

The map gesture layer uses a bounded priority order so mobile and desktop input do not compete.

## Priority

1. Multi-touch pinch and rotation.
2. Active drag or pan.
3. Long press.
4. Double tap or double click.
5. Single tap or click.

## Mobile

- One-finger swipe pans when the map gesture resolver classifies the movement as drag.
- Pinch distance changes zoom.
- Two-finger angle delta rotates the view and snaps to 0, 90, 180, or 270 degrees.
- A first tap selects a logical tile.
- A second tap on the same logical tile within threshold enters its child map when one exists.
- Long press opens a contextual map menu without triggering browser text selection.

## Desktop

- Left click selects.
- Double click enters a child layer when present.
- Right click opens the contextual menu inside the tabletop only.
- Wheel zoom and pan-tool drag continue to operate on viewport state.

Gesture state is cleared on pointer release, cancellation, and blur-safe cleanup paths.

