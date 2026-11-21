# Endemar authority pilot (NONCANONICAL / NOT DEPLOYED)

This is a **gated one-player server-state experiment** built on top of the existing
`wwwroot/first-player/core.mjs` and PR #60's `authority-contract.mjs`. It does not
replace RIST WORLD, Shaelvien's canonical database, RecursiveAuthority.cs, the
legacy weather system, production account identity, or any authoritative MMORPG.
It contains no AWS dependency, paid API, telemetry, or NPC LLM.

## Trust boundary

- **Worker (edge):** grants a temporary experimental capability only when the
  operator supplies a 32+-character `ENDEMAR_BOOTSTRAP_KEY` deployment secret.
  A configured secret is NOT proof of Shaelvien owner, GM or account identity.
  The pilot **does not** integrate production authentication or delegation.
- **Durable Object:** stores the pilot world and its monotonic revision in its
  own SQLite-backed storage (using the KV API and transaction). The only
  mutate-capable endpoints are internal and not exposed from the Worker.
- **Session:** generated with 256 bits of randomness. Only its SHA-256 hash is
  stored. One active capability for the world, rotated on each new issuance;
  expiration is 2 hours, under the public AI session cap. Up to 512 unique
  action requests are permitted per session. **Exact** request-id retries return
  the cached result without a second mutation. Reusing an ID with a different
  verb/argument returns HTTP 409 `REQUEST_ID_CONFLICT`; unreadable/legacy replay
  records return HTTP 409 `REQUEST_ID_UNVERIFIABLE`. Neither conflict grants a
  new action, reports an old success as a new action, or increments revision.
  Replay IDs are scoped to one server-issued session and reset only on capability
  rotation; the old capability then fails authentication. Capabilities are
  secrets, do not publish or commit them.
- **Intent:** reuses PR #60's allowlisted parser and the existing Endemar
  experimental Rion world engine; rejects client role/identity/world claims.
  No owner, GM, claims, transfers, protected content, or outside actions.
- **Observation:** snapshot is a limited *synthetic* projection only; no server
  session capability, hash, hidden database records or secrets are returned.
  ReLiC/RIOT have no write, authentication or canon-promotion path.
- **Continuity:** Cloudflare alarm attempts one deterministic world tick every
  2 minutes while within the bounded experiment; game weather and NPC behavior
  use the existing engine. An alarm is not a proof of uninterrupted uptime.

## Verification

Run from repository root:

```sh
node --test tests/test_first_player.mjs tests/test_first_player_authority.mjs tests/test_endemar_room.mjs
```

The new suite uses a fake transactional Durable Object storage instance. These
are **local unit tests**, not proof of an actual Cloudflare deployment, secure
account authentication, live multiplayer, or a 24/7 continuously running process.

## Candidate free hosting (owner action required)

Cloudflare Workers Free currently supports **SQLite-backed** Durable Objects;
usage beyond free limits fails rather than auto-billing on the free plan.
`wrangler.jsonc` is a deployment proposal, not an installed service.
Deployment requires the owner to review connected Cloudflare permissions, choose
an account, verify billing/free plan, configure a high-entropy
`ENDEMAR_BOOTSTRAP_KEY` secret, and explicitly approve the pilot release.
Never store the secret in GitHub, browser code, site builds, logs or chat.
Do not run automated deploy CI with privileged credentials.

Example *after* an owner-reviewed install and a connected Cloudflare account:

```sh
cd apps/rist-world/experimental-authority
npx wrangler secret put ENDEMAR_BOOTSTRAP_KEY
npx wrangler deploy
```

To request a gated pilot capability from the deployed Worker, the operator uses
an HTTPS `POST /api/endemar/session` with the deployment bootstrap secret as a
Bearer token (minimum 32 characters). Store the returned capability securely;
use it for `GET /api/endemar/snapshot` and `POST /api/endemar/intent` with
`{ "version":"endemar-intent/1", "requestId":"unique-1", "verb":"move", "arg":"north" }`.
There is no browser client integration or production login in this milestone.

## Weather-cycle builder trace

- Cloud: governing contracts, repo/PR state and permissions inspected.
- Rain: reuse existing Rion/weather engine and PR #60 intent parser.
- Snow/Hail: actual Durable Object runtime, account access, OAuth, multi-player
  permissions, economic limits and end-to-end usability remain UNKNOWN.
- Peak/Melt: frozen noncanonical one-player pilot contract, fail-closed secret.
- Stream/River: implementation in `worker.mjs` and `room.mjs`.
- Dam: bootstrap key, rotated capability, parser, transactional mutation.
- Pond: local negative and deterministic restart/alarm/replay tests.
- Lake: GitHub CI evidence after PR workflows complete.
- Ocean: **NOT VERIFIED** — no deployed endpoint, multiplayer room or live player.
- Evaporation: handoff after review to account-auth integration and verified
  Cloudflare pilot, then multi-player identity and recursive permission tests.

## Security and completion blockers

This is **not** safe to advertise as the production MMORPG. It deliberately lacks
real account authentication, robust rate limiting, content moderation, multiple
players, authenticated Discord handoff, world-scoped RecursiveAuthority checks,
perception filtering of private content, general collision arbitration, security
review and real deployment tests. The live site and Geonaph build blockers are
unaffected. Do not merge/release based on local unit tests alone.

ChatGPT assisted source creation. Human owner approval and review remain required
for account integration, Cloudflare activation and production publication.
