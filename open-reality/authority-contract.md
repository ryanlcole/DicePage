# Open Reality shared-authority contract

Status: experimental boundary. This does not replace the existing Shaelvien/RIST architecture.

## Invariants

1. There is exactly one authoritative current Open Reality state.
2. Browser state is never authoritative.
3. Humans, AI agents, scripts, and future NPCs use the same action protocol.
4. No account identity is required by the world model.
5. Authorization and attribution are separate. A valid capability may permit work without becoming a character/account identity.
6. Reality, Knowledge, and History are separate stores.
7. An observer may inspect Reality but observation alone grants no mutation authority.
8. Accepted actions are serialized by the authority service and assigned a monotonically increasing revision.
9. Every accepted mutation must include enough inverse/pre-image information for deterministic restoration, or be rejected as non-reversible during this test.
10. ReLiC observes accepted transitions and their causal chain. ReLiC is not the mutation authority.

## Minimal HTTP boundary

### GET /api/open-reality/state
Returns the current public representation of the single authoritative world.

Response shape:
```json
{
  "worldId": "OR-0001",
  "revision": 12,
  "tick": 12,
  "reality": { "runes": {}, "glyphs": {}, "shaeps": {} },
  "knowledge": {},
  "capabilities": ["observe", "research", "propose"]
}
```

### POST /api/open-reality/actions
Submits a proposal. The client does not submit a replacement world state.

Request shape:
```json
{
  "expectedRevision": 12,
  "action": "combine",
  "arguments": { "members": ["H1", "H2", "O1"] },
  "authorization": null
}
```

The authority validates the proposal against the current revision and physical rules. If accepted, it computes the mutation itself, stores its reversible delta, advances the revision, and returns the new public state. If `expectedRevision` is stale, it returns a conflict and the client must observe the new reality before proposing again.

### POST /api/open-reality/research
Creates/updates Knowledge from permitted observations. It must never directly mutate Reality.

### POST /api/open-reality/rewind
Owner/test authority only during the experiment. Rewinds accepted mutations by applying stored inverse/pre-image data in reverse causal order. Public paid capabilities must not imply rewind authority.

## Capability/payment boundary

Payment is not part of world identity. A later payment service may issue a signed/bearer capability representing a bounded amount of permitted computation. The world authority verifies that capability before accepting metered work. The payment service, Bitcoin/Lightning handling, private signing material, and anti-replay accounting must remain outside browser code.

Free allowance may be enforced by the authority independently of identity. Do not use a reusable public key as a hidden player account unless that behavior is explicitly chosen later.

## First shared-world deployment

The existing browser prototype remains a deterministic laboratory until an authority endpoint is deployed. At that point `open-reality/reality.js` should switch to remote mode:

1. GET current state.
2. Render that state.
3. Submit proposals with `expectedRevision`.
4. Replace the local representation only with authority responses.
5. Poll or subscribe for revisions produced by other visitors.
6. Never write authoritative Reality to localStorage.

This preserves the central test: every participant encounters and changes the same world.
