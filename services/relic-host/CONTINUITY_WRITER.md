# Dedicated continuity append capability — 2026-10-30

Status: implementation and local tests; production deployment must be verified separately.
User authorization: the owner agreed to a scoped append-only writer and requested build and deployment on 2026-10-30. This is a new engineering milestone; the October 11 freeze remains historical evidence.

## Boundary

The existing private, owner-scoped Secure MCP Tunnel may expose `relic_append_event`
when `RELIC_MCP_APPEND_ENABLED=1`. The adapter retains its read-only EFS mount and
read-only SQLite connection. It forwards a typed request only to the same task's
host at `127.0.0.1:8080/v1/continuity-events`; redirects and proxies are disabled.

The host alone writes the event and idempotency receipt in one rollback-journal
transaction. The new credential cannot use the general event, import, or proposal
gate routes. Existing ingestion and read tools remain available.

This is a **single-owner private connector capability**, not public or multi-user
authorization. The operator must verify tunnel access is restricted to the owner
before enabling it. Do not enable on a shared/public MCP endpoint. Multi-user
support requires per-request authenticated principal and project scope propagation.

Host configuration:

- `RELIC_APPEND_TOKEN`: separate Secrets Manager capability credential; never the general write token.
- `RELIC_APPEND_ACTOR`: fixed authenticated connector identity, not a caller-supplied human identity.
- `RELIC_APPEND_PROJECTS`: exact comma-separated project allowlist.

MCP receives only the append credential and enable flag; it never receives the
general writer credential. Revocation removes/rotates this capability and restarts
tasks. Scope is checked on each host request. Recording controls such as Pause and
Resume remain client-session controls; the server does not invent conversation state.

## Record and receipt

Requests require project, idempotency key, classification, subject, summary,
source references, and a timezone-aware occurrence time. An optional prior event
must exist in the same project. Corrections append; the prior row stays unchanged.
Source references are pointers; they are not fetched or executed.

The server records all submissions as `OBSERVATION`. Classification preserves
whether the submitted content describes a decision, hypothesis, test result, etc.
It does not claim independent verification, human identity, or canon authority.
AI ancestry remains explicit. The authoritative project database is not mutated.

Exact retries return the original event ID. Changed content with the same key
returns 409. A timeout means persistence is unknown: retry the identical request
with the same key. Receipts contain event ID, sequence, record time, payload hash,
request hash, project, duplicate status, and `canon_promoted=false`, only after commit.

Requests are bounded, extra fields rejected, and common credential patterns denied.
This filter cannot guarantee detection of all secrets/PII. Submit only authorized,
minimal continuity facts and references, never raw transcripts or credentials.
Validation responses omit submitted values.

## Deployment

### Standalone Fargate deployment (confirmed 2026-10-30)

The owner's CloudShell inspection found a HEALTHY standalone task in cluster
`relic-host`, group `family:relic-host`, running task definition `relic-host:9`.
There is no service named `relic-host`. Use `--task TASK_ID` to replace that task;
the service path is not appropriate for this deployment.

The standalone path reads the running ENI, preserves its subnet, security groups,
public-IP assignment, platform version, and execute-command setting. A public IP
does not itself establish port exposure. The script checks all attached security
groups and stops before deployment if MCP port 8000 permits network ingress or
host port 8080 permits CIDR/prefix-list ingress. It never changes ingress rules.
Private host ingestion from security-group references remains allowed.

Image build, isolated container import/schema smoke check, secret configuration,
and task registration finish before stopping the healthy task. A final preflight
rejects changed task/network state. A rollback request is saved in the operator's
home directory. The old task stops before the replacement starts, avoiding two
writers/tunnels. Three healthy observations are required. A failed replacement
is stopped before the previous task definition is restarted on the same network.
An unresolved AWS response/cleanup failure stops automatic recovery rather than
creating concurrent writers. The old public/private IP is not preserved; the
repository's Observatory Lambda discovers the current host task dynamically.

The operator's existing private owner-scoped tunnel must remain in place. Run:

```bash
python services/relic-host/deploy_continuity.py --task TASK_ID --private-tunnel-confirmed
```

Standalone rollback behavior is tested with simulated AWS responses; production
rollout and live append verification remain separate evidence.

Run the tests in `services/relic-host`: `python -m pytest -q`.

In an authorized AWS CloudShell with AWS CLI, Docker, and a clean checkout of this
commit, inspect the existing private tunnel scope, then run:

```bash
python services/relic-host/deploy_continuity.py --private-tunnel-confirmed
```

The script checks account 797661578124, existing service `relic-host` in cluster
`relic-host` (override names through arguments if inspection shows different names),
one desired task, no load balancer, expected containers and read-only MCP storage.
It builds/pushes an immutable ECR image, creates or reuses a separate append secret,
adds secret-read permission scoped to that ARN to the existing task execution role,
and registers an additive task revision. Only RELIC_CORE and SOURCERORS are enabled.
It does not change security groups, volumes, tunnel configuration, or the general token.

Rollout uses one task at a time (brief downtime) with ECS circuit-breaker rollback.
The previous task ARN is printed for recovery. If startup cannot retrieve the new
secret, inspect the existing Secrets Manager endpoint/resource policy and IAM; do
not broaden public network access. Deployment requires those AWS permissions; a
GitHub commit or Observatory ingestion run alone does not deploy this service.

After rollout, refresh the connector's tools. Append one clearly labeled deployment
verification observation in RELIC_CORE, retry it identically, and retrieve the event
by its returned ID. Confirm one row and matching hash. Inspect service health and
read-only retrieval. Only then report end-to-end persistence verified. If discovery
is cached, refresh/reconnect the ReLiC connector; do not claim a tool exists before
it is actually exposed.

Rollback: update the ECS service to the printed previous task definition and wait
for stability. Keep the append-only receipt table and committed events; the additive
schema is compatible with the old reader. No history rewrite is needed.
