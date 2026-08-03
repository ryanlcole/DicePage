# Compass And Rotation

Milestone: `SHAELVIEN-TACTICAL-WORKSPACE-1`

The map viewport supports view rotation without changing map coordinates.

## Controls

- Rotate left 90 degrees.
- Rotate right 90 degrees.
- Reset rotation.
- Floating compass reset.
- Rotation angle display.

The compass displays editor-up as North unless a future map metadata record declares geographic north. Clicking or tapping the compass resets the viewport to North-up.

## Input

Pointer coordinates are converted through the inverse viewport transform before tile hit testing:

- Square maps use `{ x, y }`.
- Hex maps use axial `{ q, r }`.

Selection, context menu targeting, and paint operations resolve against the logical cell, not rotated screen pixels.

View rotation is presentation state only and is not recorded in encounter replay.
