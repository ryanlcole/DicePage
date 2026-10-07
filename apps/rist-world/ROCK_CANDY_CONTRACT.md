# ROCK CANDY CAPTURE CONTRACT

Status: IMPLEMENTATION CONTRACT — V1 D6

## Purpose
Rock Candy is Shaelvien/RIST's low-cost pseudo-3D miniature representation. It lets a player photograph a real physical miniature from several directions and place the result on the board without requiring a conventional polygon mesh, UV unwrap, rig, or 3D authoring package.

Representation is not object identity. The captured shell is a view of the miniature, not a replacement for the semantic identity of the game object.

## V1 capture
The first interoperable Rock Candy shell uses six canonical perspectives in this exact order:

1. Front
2. Right
3. Back
4. Left
5. Top
6. Bottom

Six images are sufficient to form the first d6 glass shell. More perspectives may be supported by later polyhedral shells; extra-view interpolation is not claimed by V1.

## Outside-in transparency
The player chooses the outside/background color and a tolerance.

Transparency MUST be created by a border-connected flood operation:

1. Begin only from pixels on the outside border of the photograph that match the selected color within tolerance.
2. Continue through adjacent pixels only while they remain within that selected-color tolerance.
3. Stop when a different color boundary is encountered.
4. Never remove every matching color globally.

This prevents an interior part of the miniature that happens to share the background color from being erased merely because its color matches.

## Private capture boundary
V1 processing occurs in the browser. The six original photographs are not persisted by Rock Candy Capture. Only the final transparent atlas is uploaded through the existing private user-asset storage path and existing content-rating boundary.

## Atlas representation
V1 packs six 512 x 512 cleaned faces into one transparent 1536 x 1024 PNG atlas:

- row 0: Front | Right | Back
- row 1: Left | Top | Bottom

The user asset catalog records:

- Category = `Miniatures`
- Folder = `Rock Candy`
- AssetKind = `rock-candy`
- SpriteColumns = 3
- SpriteRows = 2
- FrameCount = 6
- SourceWidth = 1536
- SourceHeight = 1024

The storage path includes `/rock-candy/` as a V1 rendering transport marker. Semantic representation identity remains `AssetKind = rock-candy`; a storage path is not object identity.

## Glass shell rendering
On the board, the atlas is projected onto six face planes of a transparent CSS 3D cube. The photographed view is the inner image layer; a translucent highlight/reflection layer is rendered over it as the glass shell.

The shell is additive representation. It does not create a second World, Region, Local, or Instance and does not replace underlying terrain.

## Scale integration
Rock Candy may represent Region-scale miniatures or Local/Instance miniatures according to the placement context. The same captured asset can therefore persist while its surrounding representation changes by scale.

## Future extension
Higher-order shells may add additional captured angles and choose/blend the best perspective for a viewer. Such behavior must preserve the original six-view V1 asset and must not claim generated or interpolated perspectives were photographed by the player.
