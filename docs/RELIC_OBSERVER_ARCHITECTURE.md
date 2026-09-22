# ReLiC Observer

Status: additive alpha architecture.

ReLiC Observer is the query surface for project knowledge. It is designed to work without requiring a paid language-model service and to keep evidence, truth domain, provenance, visibility, and authority boundaries visible.

## Purpose

The first implementation answers from a bounded indexed corpus rather than treating a model context window as memory.

Pipeline:

```text
authorized source
  -> immutable source metadata / source hash
  -> compact searchable evidence record
  -> deterministic retrieval + ranking
  -> bounded evidence window
  -> ReLiC observer response
  -> visible evidence trace
```

The response layer is intentionally extractive in the first version. When evidence is absent, the engine returns `UNKNOWN` instead of manufacturing an answer.

## Semantic boundary

This feature does **not** mint new Rune, Glyph, CHID, or SHAEP identities.

- Retrieval is compatible with the existing `rune.retrieve` concept, but the current C# query implementation is ordinary executable source, not a promotion of the semantic runtime.
- Query evidence bundles and in-memory indexes are implementation data structures, not canonical Glyphs.
- A query working set is **not a SHAEP**. SHAEP remains the Spatial Hot Preservation Object defined by `apps/rist-world/SHAEP_FORMAT.md`.
- ReLiC observes evidence. It does not grant permission, rewrite authority, or promote UNKNOWN/HYPOTHESIS/FICTION into FACT.

This corrects older experimental language that used “Shaep state” as a generic bounded memory concept. Current repository authority is SHAEP v2.

## Query location

The Observer lives inside the authenticated Game application rather than a public static page. After deployment it can be opened directly with:

`/Game/?workspace=observer`

The ordinary authenticated launcher also exposes a **RELIC OBSERVER** card. The query parameter requests a workspace; it does not bypass authentication or create authority.

## Public project seed

Source of truth:

`knowledge/project/public.json`

Build step:

`apps/rist-world/prepare_relic_observer.py`

Published generated representation:

`apps/rist-world/wwwroot/data/relic-observer-seed.json`

The generator includes only sources whose visibility starts with `public`. It deliberately does not copy the raw `sources[].content` bodies into the browser seed. It publishes the curated project records plus their source ledger metadata, dates, hashes, status, truth domain, scope, and source links.

The source-controlled public corpus remains evidence. It is not a permission grant, live deployment verification, or automatic canon promotion.

### Current repository overlay

The Project Knowledge snapshot is intentionally durable and may lag the current branch. To keep ReLiC aware of important current work without exposing the entire repository, the seed builder has a small explicit public-source allowlist.

If an allowlisted repository file has the same SHA-256 as the corresponding Project Knowledge source, ReLiC does not duplicate it. If it is new or has changed, the builder emits bounded overlay records with current source hashes.

The allowlist includes current semantic/authority contracts, the ReLiC Observer implementation and architecture, and selected historical ReLiC prototypes such as `relic_core.py`, `relic_analyzer.py`, `glyph_ai_core.py`, and `shaelvien_ai_adapter.py`. Historical prototype material is labeled UNKNOWN/historical rather than silently treated as current architecture.

Arbitrary repository discovery is forbidden for this browser seed. New public source files must be deliberately added to the allowlist.

### Evidence packet

A returned answer can be copied as a compact `relic.observer.evidence-packet`. The packet contains only the bounded returned evidence excerpts and their source/truth/provenance metadata, plus retrieval trace, intent, context state, and explicit conflict state. It does not export the complete private corpus.

This packet is the handoff boundary for a future optional reasoner: a model or external process can receive the small evidence packet instead of receiving the entire project database.

## Private project memory

Authenticated private imports use the existing `DiscordAuthClient` private-storage path:

`relic-observer/corpus.v1.json`

Private imports are not written to the public repository or public seed.

The browser stores the source text because the owner explicitly chose to import it. Imported source text is treated as data only; code is never dynamically evaluated or executed. The first version supports bounded plain-text/code/JSON imports and pasted text.

A private Shaelvien Project Knowledge JSON export is recognized by `dataset_id == "shaelvien-project-knowledge"`. Its records are indexed directly so existing truth-domain and source relationships survive import. Generic text is chunked for retrieval and defaults to `UNKNOWN` truth domain.

Uploading a source does not establish authorship. Generic private imports therefore retain `UNKNOWN` source origin and are handled at the `OUTSIDER_AI/RED` boundary until provenance is explicitly established by a future provenance workflow.

### Portable private source bundles

Observer also accepts a private multi-source JSON bundle with contract:

`relic.observer.private-source-bundle` version 1.

A bundle may carry multiple text sources plus optional provider/provider-reference hints so material exported from Google Drive, local archives, or another owner-authorized source can be moved into the private corpus in one import. Bundle-provided authorship, truth, visibility, or authority claims are **not trusted**. Every imported source remains private account storage with `UNKNOWN` source origin and `OUTSIDER_AI/RED` handling until a separate verified provenance workflow exists.

Bundles are capped, imported atomically after capacity checks, deduplicated by source title + content hash, and never become part of the public Observer seed.

## Retrieval

The engine builds an in-memory inverted index once when the corpus changes.

Characteristics:

- Unicode-aware tokenization.
- Small stop-word set.
- BM25-style lexical relevance scoring.
- Exact phrase and title boosts.
- Hard cap on query terms and returned evidence.
- No embedding API.
- No remote inference dependency.
- No arbitrary source execution.
- Source-linked evidence cards for every response.
- FACT, HYPOTHESIS, FICTION, UNKNOWN remain explicit.

### Registered semantic candidate recall

The public seed compiles a tiny retrieval-alias table from the authoritative `.code-index/semantic_units.json` registry. A query that uses a registered surface form can therefore recall evidence filed under the corresponding semantic unit without requiring embeddings or a model.

For example, a registered surface such as `SELECT` or `get` can point retrieval toward `rune.retrieve`. This is deliberately labeled **ALIAS** / **REGISTERED SEMANTIC CANDIDATE** rather than exact identity. Form conditions and relation types still apply; alias recall is a search lead, never proof that two expressions are interchangeable in the active context.

Alias expansion is damped below direct lexical evidence, capped to a small number of terms and semantic units, and included in the evidence packet so a later reasoner can see exactly why the candidate was retrieved. ReLiC never invents aliases that are absent from the registered semantic-unit ledger.

### Bounded associative recall

ReLiC also builds a sparse, reusable association graph when the corpus changes. This is **not** a semantic-identity graph and it does not mint Rune/Glyph/CHID/SHAEP identities. It is only a retrieval aid.

Edges are formed from cheap evidence relationships:

- records that share the same declared source;
- records that share rare indexed terms;
- each evidence unit retains only its strongest bounded neighbor set.

At query time ReLiC:

1. retrieves direct lexical/phrase matches;
2. selects only the strongest direct seeds;
3. follows one bounded association hop with a damped score;
4. marks every returned record as DIRECT or ASSOCIATED and states why it was reached;
5. never treats association as proof of the query.

There is deliberately no unrestricted recursive walk. A one-hop, capped graph prevents broad topic drift and preserves the scarce-compute design.

### Visible chat + bounded conversational follow-up

The Observer now presents queries and responses as a visible chat transcript in the authenticated workspace. The visible transcript is page-memory only and keeps at most 12 turns; it is not silently written into account storage. **Clear Chat** clears the visible transcript and the retrieval follow-up context.

ReLiC separately keeps a tiny in-memory conversation window for follow-up questions. It is not written to account storage and is cleared whenever the evidence index is rebuilt or the user selects **Clear Context**.

The prior turn is consulted only when the new query contains explicit follow-up language such as “what about…”, “that”, “this”, “same”, “previous”, or similar references. Previous query terms and a few grounded evidence titles are scored at a heavily damped weight. Context-derived records are labeled **CONTEXT** in the UI and remain distinct from DIRECT matches and ASSOCIATED graph neighbors.

Only the last four turns are retained, and only the immediately prior turn supplies retrieval terms. This provides conversational continuity without turning the whole conversation into an unbounded prompt or silently contaminating unrelated questions.

### Deterministic intent shaping

The first version also detects a few narrow query intents from the user's own words:

- **SOURCE** — source, origin, provenance, or citation questions produce a source trace.
- **STATUS** — current/live/implemented questions summarize record status, truth domain, and scope.
- **HISTORY** — old/original/previous/prototype questions separate historical evidence from current or non-historical evidence.
- **GENERAL** — all other questions use the ordinary evidence synthesis path.

This is routing, not hidden model reasoning. The detected intent is displayed in the response and copied into the evidence packet.

### Explicit evidence scope

The user can constrain retrieval to **All**, **Current/non-historical**, **Historical**, **Public**, or **Private** evidence. The selected scope is applied before lexical scoring, follow-up context scoring, and graph expansion. Changing the scope clears conversational follow-up context so terms from a previous evidence class cannot silently bleed into the new one. The chosen scope is preserved in the evidence packet.

If grounded records explicitly carry a source-conflict status, ReLiC surfaces that conflict and does not select a winner. Mixed evidence is not silently flattened into a single confident answer.

This is deliberately closer to software written under scarce compute: pre-index reusable state, retrieve a bounded working set, follow only a few precomputed associations, retain only a tiny explicit conversation window, route a handful of deterministic intents, and spend computation only on the requested terms.

## Privacy and authority

The public seed and private corpus are separate storage classes.

ReLiC Observer must never:

- copy a private import into `knowledge/project/public.json` or another public web asset;
- treat retrieved text as authorization;
- expose private material to a public client or unauthenticated route;
- execute imported code;
- infer a protected permission path from source text;
- relabel unknown provenance as HUMAN merely because an authenticated human uploaded the file;
- turn a source's proposal, lore, hypothesis, or fiction into FACT.

Account deletion, export, legal acceptance, and other nondelegable operations remain governed by Recursive Authority and the existing account system.

## Accessibility

The workspace uses semantic form labels, visible focus, keyboard-operable controls, textual truth labels, and an ARIA live response/status path. Truth state is always written in text and never represented only by color.

## Model adapters later

A generative model may later be attached after retrieval as an optional renderer or reasoner. It should receive the bounded evidence window and source metadata, not become the storage authority.

Any such adapter must:

1. preserve source citations and truth domains;
2. distinguish its own inference from retrieved evidence;
3. keep private material within an authorized processing boundary;
4. return UNKNOWN when support is insufficient;
5. remain subordinate to Recursive Authority, policy, safety, privacy, and provenance controls.

The deterministic observer remains useful when no model adapter is configured.
