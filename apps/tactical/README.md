# Shaelvien Recursive Tactical Tabletop

Build: `SHAELVIEN-TACTICAL-EDITOR-1`

This folder is the local static frontend entrypoint for the first working vertical slice of the recursive GM-versus-player tactical tabletop.

## Run

The existing static server is serving this folder:

```powershell
python -m http.server 8780 --bind 0.0.0.0
```

Open:

```text
http://127.0.0.1:8780/
```

## Model

Everything is represented through the reusable map model. A map contains tiles, and a tile may reference a child map, actions, triggers, and an encounter.

Implemented proof chain:

```text
World -> City -> Block -> Tavern Main Floor -> Tavern Encounter
```

`Tavern Exterior` is included as a building-category map using the same schema, but the acceptance path opens the Tavern Main Floor directly from the Block tavern tile.

## Runtime

- HTML/CSS/vanilla JavaScript
- Canvas 2D renderer
- JSON data
- ES modules
- One central state object
- One requestAnimationFrame loop
- localStorage persistence
- Deterministic combat and replay hashing
- Map-first GM editor with square and optional per-map axial hex geometry
- Registered tile image assets under `data/assets/tile_asset_registry.json`

## Verification

Reports are written to:

```text
C:\Shaelvien\verify_reports\shaelvien_tactical_editor_1
```

Primary commands:

```powershell
python tools\cdp_verify.py --port 9223 --app-url http://127.0.0.1:8780/
python tools\cdp_verify_editor.py --port 9224 --app-url http://127.0.0.1:8780/
python tools\route_compatibility_check.py
```

The supported deterministic replay command uses the Shaelvien Node wrapper, not global PATH:

```powershell
C:\Shaelvien\tools\node.cmd tests\deterministic_replay_test.mjs
C:\Shaelvien\tools\node.cmd tests\editor_geometry_test.mjs
```

Browser verification is performed through `tools\cdp_verify.py`.

## Archive

Prior frontend archive:

```text
C:\Shaelvien\backups\dev_studio_alpha_pre_shaelvien_tactical_20260802_190917
```

Rollback instructions:

```text
C:\Shaelvien\verify_reports\shaelvien_tactical_web_0\rollback_procedure.md
```
