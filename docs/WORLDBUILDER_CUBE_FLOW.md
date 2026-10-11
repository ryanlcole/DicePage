# World Builder Recursive Cube Flow

Status: implementation contract for the current Shaelvien/RIST World Builder rebuild.

## Governing rule

The builder is one recursive spatial chain. A child scope never replaces or silently bypasses its parent.

```text
SHAELVIEN / DEED
      |
      v
WORLD  (0 degrees)
300 x 300 x 300 cube
30 tiers x 10 layers
builder Z: -150 .. +149/150 around sea level 0
      |
      | explicitly select/define a bounded Region from the World
      v
REGION (15 degrees)
300 x 300 x 300 local cube
preserves parent World coordinates + selected X/Y/Z volume
local depth prefix R
      |
      | explicitly select a Local inside the Region
      v
LOCAL  (30 degrees)
300 x 300 x 300 local cube
preserves Region parent identity
local depth prefix L
      |
      | explicitly select an Instance inside the Local
      v
INSTANCE (45 degrees)
300 x 300 x 300 local cube / playable scene
preserves Local parent identity
local depth prefix I
```

Reverse navigation unwinds the same chain:

```text
INSTANCE -> LOCAL -> REGION -> WORLD -> DEED
```

## Cube progression

The WORLD cube is the parent spatial truth for the builder. Its X/Y surface is 300 x 300 and its vertical model is 30 tiers x 10 layers = 300 layers. Builder-facing sea level is Z=0; storage may translate the 300 vertical slots internally, but presentation must not rewrite spatial identity.

Each descent is recursive rather than a geographic copy. A Region is a bounded X/Y/Z selection of World space. Local is selected inside that Region. Instance is selected inside that Local. Each child receives its own 300 x 300 x 300 authoring cube while retaining the parent path and canonical coordinates needed to return to the same place.

Tier and Layer are depth/representation controls inside the active scope. They are not substitutes for WORLD, REGION, LOCAL, or INSTANCE.

## Required UI flow

```text
Choose deed
   -> World Builder
      -> WORLD HOME (full world visible; no automatic Region takeover)
         -> edit WORLD
            -> choose Tier
               -> choose Layer
                  -> author/save world content
                  -> return to WORLD HOME
         -> explicitly choose/define REGION
            -> select Region footprint/volume from WORLD
               -> REGION HOME
                  -> edit Region tiers/layers
                  -> explicitly choose LOCAL
                     -> LOCAL HOME
                        -> edit Local tiers/layers
                        -> explicitly choose INSTANCE
                           -> INSTANCE HOME / playable scene
```

WORLD HOME must therefore expose World editing before Region tools. Opening World Builder must never invoke Region Definer automatically. Region tools activate only after an explicit Region action/selection.

## Continuous zoom

Zoom may change presentation detail and view angle, but it does not silently mutate scope identity. Scope transitions occur only at the defined fitted boundary/selection transition. Reverse zoom/navigation must unwind the same parent chain with hysteresis so camera motion cannot accidentally redefine ownership or spatial identity.

## Regression requirements

1. Selecting World Builder lands at WORLD HOME with the complete world visible.
2. The primary World action enters WORLD Tier/Layer editing, not Region Definer.
3. Region tools require an explicit Region action or saved Region selection.
4. REGION -> LOCAL -> INSTANCE are selection-first and preserve their parent path.
5. Back navigation is INSTANCE -> LOCAL -> REGION -> WORLD.
6. Tier/Layer changes never change spatial scope by themselves.
7. Camera zoom/angle never changes authoritative ownership or scope identity by itself.
8. The World map may remain interactive while Region/Local/Instance definitions are created from it; child tools do not create a second canonical world map.
