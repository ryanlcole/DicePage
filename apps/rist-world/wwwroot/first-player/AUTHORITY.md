# Endemar authority boundary — proposed, noncanonical

Status: **PROPOSED_CONTRACT_NOT_DEPLOYED**. RIOT recommendation, not an owner decision.
The browser-only first-player prototype is **not** a multiplayer server.

The pure `authority-contract.mjs` parser defines a minimal transport envelope:
`{version:"endemar-intent/1",requestId:"req-001",verb:"move",arg:"north"}`.
It explicitly rejects browser claims about role, owner, player identity, world, tick or
revision. Parsing is **not authentication or authorization**.

A future Cloudflare Durable Object should authenticate the session outside the
envelope; bind it to a persistent player and world; validate action against current
authoritative world state; atomically deduplicate request IDs; enforce revision
ordering, rate limits and permissions; commit the result to durable storage; and
broadcast only validated snapshots. Never accept client-submitted state as truth.
No tokens or personal information should be included in game logs.

ReLiC observes read-only; RIOT proposes read-only. Neither receives a write path.
Canonical project records and weather model are unchanged. Existing experimental
`core.mjs` remains browser-local and unmodified.

Verification: `node --test tests/test_first_player_authority.mjs`.
Do not merge as proof of multiplayer, hosting, or owner authority. A later server
implementation and authenticated integration tests are required.
