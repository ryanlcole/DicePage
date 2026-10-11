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

`observatory.py` creates bounded event envelopes for an authorized collector to submit to ReLiC's existing append-only `/v1/events` endpoint.

The durable AWS path intentionally separates submission identity from ReLiC write authority:

```text
GitHub Actions
    |
    | GitHub OIDC, short-lived AWS role
    v
relic-observatory-ingest Lambda
    |
    | validates OBSERVATION doctrine again
    | discovers highest RUNNING relic-host task revision
    | retrieves RELIC_WRITE_TOKEN inside AWS
    v
private relic-host:8080/v1/events
    |
    v
encrypted durable ReLiC storage

ChatGPT
    |
    v
OpenAI Secure MCP Tunnel -> relic-mcp
                           no RELIC_WRITE_TOKEN
```

No public ReLiC ingestion endpoint is required. GitHub does not receive `RELIC_WRITE_TOKEN`; its OIDC role may invoke only the dedicated ingestion Lambda. The Lambda runs inside the ReLiC VPC, and the ReLiC host security group permits TCP 8080 only from the dedicated ingestion security group.

`infra/aws/relic-observatory-ingest.yml` defines this boundary. It also creates private ECS and Secrets Manager interface endpoints so the VPC Lambda can discover the running ReLiC task and retrieve the existing write secret without public Internet routing.

`observatory_ingest_lambda.py` rejects non-`OBSERVATION` envelopes before reading the write secret. Historical standalone ECS tasks may coexist, so it selects the highest RUNNING `relic-host` task-definition revision instead of hard-coding a disposable task IP.

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

## GitHub CI behavior

`.github/workflows/relic-observatory-ci.yml` always compiles and tests the Observatory boundary, generates a code-change observation on branch pushes, validates it locally, and uploads the evidence artifact.

Durable append is enabled only after AWS deployment and configuration of the repository variable:

`RELIC_OBSERVATORY_ROLE_ARN`

When that variable is absent, the workflow retains the validated evidence artifact and explicitly reports that private ingestion is not configured. No long-lived AWS key or ReLiC write token is stored in the workflow.

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
