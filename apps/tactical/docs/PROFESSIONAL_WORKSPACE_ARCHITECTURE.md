# Professional Workspace Architecture

Milestone: `SHAELVIEN-TACTICAL-WORKSPACE-1`

The Tactical Tabletop now uses a fixed full-viewport application shell:

- Top app bar: product mark, current location, runtime state, GM/player controls, save/reset.
- Main toolbar: grouped file/map, edit, authoring, view, and mode controls.
- Left tool rail: compact desktop-only GM tools.
- Center map workspace: bounded Canvas 2D viewport with hidden overflow.
- Right inspector: contextual docked panel on desktop, bottom sheet on mobile.
- Bottom status bar: map, grid, scale, selection, zoom, rotation, and time state.

Normal editing does not use page-level scrolling. Overflow is constrained to the inspector, menus, dialogs, palette list, and intentionally scrollable mobile toolbar strips.

The redesign preserves the existing gameplay loop, recursive map model, deterministic replay, GM/player authority boundaries, and first-preset square-grid authority.

## State Boundary

Workspace presentation state is stored under `state.editor`:

- `viewportByMap`
- `inspectorOpen`
- `inspectorWidth`
- `inspectorSheetState`
- `moreMenuOpen`

Gameplay replay events do not include viewport panning, zoom, rotation, compass state, or inspector state.

