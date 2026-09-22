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

## Private project memory

Authenticated private imports use the existing `DiscordAuthClient` private-storage path:

`relic-observer/corpus.v1.json`

Private imports are not written to the public repository or public seed.

The browser stores the source text because the owner explicitly chose to import it. Imported source text is treated as data only; code is never dynamically evaluated or executed. The first version supports bounded plain-text/code/JSON imports and pasted text.

A private Shaelvien Project Knowledge JSON export is recognized by `dataset_id == "shaelvien-project-knowledge"`. Its records are indexed directly so existing truth-domain and source relationships survive import. Generic text is chunked for retrieval and defaults to `UNKNOWN` truth domain.

Uploading a source does not establish authorship. Generic private imports therefore retain `UNKNOWN` source origin and are handled at the `OUTSIDER_AI/RED` boundary until provenance is explicitly established by a future provenance workflow.

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

This is deliberately closer to software written under scarce compute: pre-index reusable state, retrieve a bounded working set, follow only a few precomputed associations, and spend computation only on the requested terms.

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
