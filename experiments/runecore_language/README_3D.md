# RuneCore 3D/1 — Coil Coordinates and Traversable Shaep Scene

**Experiment, not a trained LLM, a physics simulator, or atomic chemistry.**

The current RuneCore language hierarchy is `Rion = bit; Ring = atomic rotating ring; Rune = element instance; Glyph = periodic-table identity; Shaep = what elements form; Repeat = recurrence`. `RuneCore.Scene3D/1` adds a spatial **scene representation** containing Shaep references. The lake, shoreline and building are semantic/visual cells, **not proven atomic compositions or actual physical atoms**.

## User-defined spatial coordinate convention

- `X` = horizontal/lateral, `Y` = vertical, `Z` = depth.
- The screen projects `(x,y,z)` through a camera. A camera can be at `(1,0,-100)` looking toward positive `Z`; projection depends on depth and camera angle.
- First coil points, exactly following the user's example:

  ```text
  (0,0,0), (1,0,0), (1,1,0), (0,1,0), (-1,1,0),
  (-1,0,0), (-1,-1,0), (0,-1,0), (1,-1,0), (1,0,1) ...
  ```

- A **coil is traversal/indexing order**, not inherently a sphere. `coil_xyz(n, sphere_radius=r)` optionally applies a 3D Euclidean radius mask. `coil_xyz(n)` enumerates every integer coordinate in an axis-aligned cube exactly once.
- Spatial coordinate **placement** is separate from atomic `Ring` rotation. A scene voxel is a viewable material/shape cell; physics is not inferred from its label.

## Files

- `scene3d.py` — deterministic bounded command handler; 3D coil, scene authoring, SQLite persistence, compact JSON export and perspective reference projection.
- `scene3d.sqlite3` — **generated persistent 3D scene**, one record per unique `(x,y,z)`, indexed by `x,z`, with integrity digest.
- `scene_data.json` — 248 contiguous Z spans, encoding exactly the 3,604 stored scene cells; same SHA as SQLite readback.
- `viewer3d.html` — standalone offline perspective viewer with WebGL depth-buffer path and Canvas 2D depth-sorted fallback. A local HTML file works without a server. Renders no text/debug information inside the scene.
- `viewer3d_template.html` — source template; replace `__SCENE_JSON__` with exported JSON to create the standalone viewer.
- `test_scene3d.py` — 23 tested assertions for original coil sequence, full 3D coverage and uniqueness, sphere mask, SQLite readback/restart, tamper checks, scene composition, perspective and culling.
- `scene_preview.png`, `scene_mobile_preview.png`, `scene_alternate_angle.png` — captured automated Chromium snapshots, not physical-device Safari tests.

## Run

Requires Python 3.10+ standard library only for the scene builder; a browser with Canvas 2D or WebGL for viewing.

```sh
python -m unittest -v test_scene3d
python scene3d.py --database new_scene.sqlite3 --export new_scene.json --command "create a scene with a lake, shore and building"
```

Open `viewer3d.html` in a browser. Desktop: **WASD** to move horizontally, **drag** to look, **Q/E** or Shift/Space for height, **R** to reset. Touch: left joystick to move, drag the scene to look. Camera begins at `(1,9,-29)` looking toward positive Z and slightly downward. It supports alternate views including `(1,0,-100)`; the example viewing position is not hard-coded as the only camera.

## Verified results

- The first 10 coil coordinates exactly match the user's example; radius 3 cube traversed without duplicates.
- 3,604 spatial cells stored, 248 compact spans, unmodified scene digest `f8ce495e755273408f4a4e94e1ede5d3f4771d6c64b26e845ce57ab7d52e580f`.
- Python `test_scene3d.py` 23/23 local tests passed.
- JS syntax checked under Node 22.
- Chromium browser rendering tested on 1100×720 and 375×667 with software fallback (environment's WebGL unavailable); camera changed on keyboard/drag input without altering stored coordinates.
- Browser security blocked local navigation via `file://` and HTTP; test used `set_content` of the identical generated HTML, so live URL availability and physical iPhone Safari remain **UNKNOWN**.
- WebGL GPU execution path compiled at JavaScript syntax level but **not exercised in this environment**.

## Next steps

1. Establish a 3D world object schema linking stored Shaep placements to verified Rune/Glyph references without fabricating element composition.
2. Add LOD/chunk streaming and persist camera, interactions and **authoritative** world changes separately from immutable history.
3. Extend the RuneCore instruction grammar beyond the single supported scene phrase and gather a licensed training dataset. A deterministic command interpreter is not a trained LLM.
4. Integrate with the separately tested v0.9 contact matching engine after authority/provenance tests; nothing here establishes physically accurate bonding.
5. Verify physically on an iPhone and a free hosted site before claiming deployment or complete user usability.

**Continuity principle:** ReLiC observations and generated geometry do not become project canon merely by being stored. Preserve source, verification, errors and corrections separately.
