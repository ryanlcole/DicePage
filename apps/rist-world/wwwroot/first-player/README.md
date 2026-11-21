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


## Optional public ReLiC ecology checkpoint observer (review branch only)

The "External ReLiC Ecology" sidebar observes an **independent, synthetic** world
from `ryanlcole/ReLiC-Continuity`'s publicly readable
`experiment-autonomous-ecology-state` branch. The experiment runs Python
through GitHub Actions and persists results on a separate branch. The browser
fetches a checkpoint from `raw.githubusercontent.com` **only after the user clicks**
"Read GitHub ecology checkpoint". No credentials, tokens, plugins, account
identity, or privileged API scopes are required.

**This is not synchronization or a bridge to game authority.** External
organisms A/B/C are different identities from Endemar's existing NPCs. The
remote simulation can neither create Endemar beings nor mutate the browser
world, canonical project database, player save, privileges, or ReLiC lineage.
Hash-like event fields are *not* declared verified cryptographic proof. The
UI labels remote information "observed public synthetic state", not a claim
that an NPC is conscious or a game server is always awake.

Source:
https://github.com/ryanlcole/ReLiC-Continuity/actions/workflows/autonomous-ecology.yml
and
https://github.com/ryanlcole/ReLiC-Continuity/tree/experiment-autonomous-ecology-state/experiments/continuity_ecology

As inspected 2026-11-21, the public state branch contained **48 synthetic ticks,
3 alive agents, and 146 reported events**, supported by 4 successful scheduled
Actions executions. These numbers are a dated observation and are **not**
hardcoded into the application; each manual refresh reads current public state.
Runs can be skipped or delayed, and the public checkpoint may be stale or
unavailable. A failed request displays a notice and does not break offline play.

The reader refuses unknown schemas, non-read-only policies, invalid agent IDs,
oversize responses, and malformed event metadata. Unit tests inject a fake
fetcher without network access. External hosting and CORS behavior must still
be tested from a deployed webpage; no HTTP endpoint for online gameplay is
provided by the module.

Run tests from the repository root:
`node --test tests/test_relic_online_observer.mjs`

**Governance:** This module and UI are on a human-reviewed draft PR stacked on
#63/#62/#61/#60/#57. It has no license to publish unpublished Shaelvien
source, and it does not change ReLiC or Shaelvien canonical records.
AI assistance: ChatGPT, owner-directed, tests subject to CI verification.
