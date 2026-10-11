# ReLiC Observatory

## Purpose

ReLiC Observatory is an engineering experience recorder. It observes what enters and happens to a software system after tools, including AI, are used. It does **not** monitor AI thoughts or treat AI output as authority.

Primary evidence chain:

`CODE_CHANGE -> BUILD/TEST -> DEPLOYMENT -> USER_ERROR_REPORT -> INVESTIGATION -> CORRECTIVE_CHANGE -> VERIFICATION`

Each step remains its own observation. A later step does not erase an earlier one.

## Doctrine

- Identity is not representation.
- Representation is not truth.
- Unknown is not fact.
- Memory is not canon.
- Temporal association is not causation.
- User reports are evidence of reported experience, not automatic proof of cause.
- Observatory emits `OBSERVATION` only. It cannot promote records to canon or grant mutation authority.
- The existing ReLiC MCP remains read-only for AI clients.

## Initial observation kinds

- `CODE_CHANGE`
- `BUILD_RESULT`
- `TEST_RESULT`
- `DEPLOYMENT`
- `RUNTIME_ERROR`
- `USER_ERROR_REPORT`
- `INVESTIGATION`
- `CORRECTIVE_CHANGE`
- `VERIFICATION`

## Observation Gateway

`observatory.py` creates bounded event envelopes for an authorized collector to submit to ReLiC's existing append-only `/v1/events` endpoint. The collector owns write credentials. AI clients do not receive those credentials.

Each observation contains:

- kind and immutable subject scope
- `OBSERVATION` status
- observed facts
- source and optional actor
- source-evidence pointers
- optional prior ReLiC event pointer
- observation time
- a deterministic collector fingerprint for deduplication
- explicit doctrine flags preventing representation/truth, temporal/causal, and observation/canon collapse

## User error reports

A user report begins with `cause: UNKNOWN`. Observatory must not infer that the most recent commit caused the reported behavior. Investigation and verification may later add evidence through new events while preserving the original report.

## errors.md projection

A future renderer may generate a human-readable `errors.md` from durable ReLiC events. `errors.md` is a representation of the event history, not the authoritative store. It should show the report, affected observed version, evidence, investigation, attempted corrections, verification, and unresolved uncertainty without deleting failed attempts.

## Next adapters

1. Git repository adapter: observe commit/ref/path changes.
2. CI adapter: observe build and test results.
3. Deployment adapter: bind deployed version to runtime environment.
4. User-report adapter: accept bounded error reports with product/version evidence.
5. Runtime adapter: observe application errors without collecting unnecessary personal data.
6. Projection layer: produce `errors.md` and ReLiC Share evidence views from stored events.

Adapters should be independent of the read-only MCP surface. ReLiC Share may display bounded evidence, while the ReLiC service and ingestion credentials remain private.
