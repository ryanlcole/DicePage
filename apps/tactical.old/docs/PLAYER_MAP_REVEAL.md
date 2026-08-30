# Player Map Reveal

Milestone: `SHAELVIEN-PERCEPTION-1`

Player-facing fog states:

- `VISIBLE_NOW`: terrain, objects, and permitted entities render normally.
- `DISCOVERED_NOT_VISIBLE`: previously seen terrain renders dimmed; dynamic hidden details are not exposed.
- `AUDIBLE_ONLY`: terrain is not revealed; only a sound marker may appear.
- `UNKNOWN`: hidden.

The renderer and public snapshot both use these states. This prevents a canvas-only cover from becoming the only protection.

Grid display is also perception-scoped in player view so full-map grid geometry does not reveal unseen map extent.

