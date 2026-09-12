# RIST Truth Conservation Contract

Status: P0 runtime contract

## Principle

Canonical truth is never discarded to save resources.

RIST conserves resources by refusing to repeat work whose semantic result is already known to be identical. Representation, transport, rendering, timestamps, cache state, and input motion are not automatically canonical truth.

`resource use ~= unique truth + unique semantic change`

## Existing sparse authority

The canonical 30 x 30 origin uses implicit Ocean 071 terrain. The default ocean is one rule, not 900 authored tile records. Authored terrain is stored as sparse exceptions above that default.

Truth Conservation extends that existing model; it does not introduce a second world-state authority.

## P0 guarantees

1. `WorldSession` remains the world-state authority.
2. Serialized world truth receives a SHA-256 content fingerprint before persistence deduplication.
3. An unknown target is always written. Optimization fails closed.
4. A persistence write may be skipped only when that exact target is already confirmed to contain the same semantic fingerprint.
5. Local world, private world, local map-card, private map-card, and published map-card targets are tracked independently.
6. Map-card semantic identity uses the existing `ManifestHash`. `UpdatedAtUtc` alone is not a semantic world mutation.
7. Pure-state editor intents may be collapsed when record equality proves the proposed state is exactly the current state.
8. No-op intents do not create undo history, rerender notification, or persistence work.
9. Restoring already-persisted state seeds the known-truth cache but is not counted as a new write.
10. Metrics are observational. They never authorize a mutation or a skipped write.

## Non-collapsible classes

End-state equality alone MUST NOT be used to erase or suppress an operation with independent meaning or side effects, including:

- economic transactions, purchases, ownership transfers, balances, fees, or entitlements;
- security, authentication, authorization, moderation, or access-control events;
- combat actions, resource expenditures, damage, healing, triggers, rolls, commitments, or encounter history;
- provenance, audit, publication, signing, legal, or compliance events;
- observations or discoveries that change what an actor is allowed to know;
- external messages, webhooks, notifications, or other irreversible side effects;
- any operation whose path matters even when its final scalar state equals its starting state.

These operations require their own authoritative event semantics. Truth Conservation may optimize their representation or delivery only after the event itself is preserved.

## Pure-state example

Moving a tile onto the same snapped cell with the same Tier, Layer, treatment, footprint, rotation, and identity produces the same `TileItem`. That intent is a proven no-op and may end before undo, render notification, or persistence.

Moving onto a trap and moving back is not equivalent to never moving when the path can trigger game state. The movement event must be preserved by the future event authority even if the final coordinates match.

## Persistence scopes

Current P0 scope keys:

- `local-world`
- `private-world`
- `local-map-card`
- `private-map-card`
- `published-map-card`

A match in one scope never proves another scope is current.

## Future extensions

The same contract may later govern chunk/Merkle world roots, perception cohorts, asset content identities, dependency-based recomputation, and reliable-vs-ephemeral transport. Those extensions must preserve the same rule:

> Optimize everything surrounding truth; never optimize truth away.
