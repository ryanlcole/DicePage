# 𓋹 Shaelvien — Endemar First Player

**Public experimental alpha / noncanonical mechanics.** This is an additional playable module of the existing RIST WORLD published asset tree. It does **not** replace Shaelvien, its authoritative project records, RuneCore, WaveCore, or the server-side Shaelvien Lite.

## Play
Navigate to `app/first-player/` under the existing RIST WORLD GitHub Pages site. Desktop: arrow keys or WASD. Phone: touchscreen direction buttons, actions, and tapping adjacent map cells. World → Region → Local → Tactical are representations of the same persistent identities, not separate worlds.

## Tested functions
Deterministic world seed and rion-state organisms; two parents and offspring; bounded Q-table experience learning; needs-based resource consumption and movement; local weather cycle using temperature, humidity, pressure, wind, debris and polarity; plant fruit regrowth, drinking, gathering, planting and rest; NPC dialogue; immutable hypothesis projection; ranked RIOT project proposals; player inventory and browser-local save/restore and JSON export/import.

## Critical boundaries
This is **not** online multiplayer. No server exists for this module. First Player is a local identity, not a secure globally reserved account. The world advances while the page is open and bounded catch-up occurs when reopened; it does not keep running in the background while the browser is closed. The weather is a fresh simplified experimental mechanic, not a representation of the unpublished canonical WaveCore implementation.

RIOT is a simulated project planner; it cannot impersonate the real owner, change canon, approve purchases, or execute code outside explicit authorization. ReLiC is read-only. Future real-time multiplayer needs authoritative server-side world mutation, sessions, reconnect, abuse controls and tests; Cloudflare Workers Durable Objects with SQLite and hibernating WebSockets are a possible free-tier host but not yet deployed.

## Verify
`node --test tests/test_first_player.mjs`

The frontend uses no paid service, no AI API, no third-party JavaScript dependency and no external telemetry. Source authored with ChatGPT assistance under owner direction.
