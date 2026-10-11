# ReLiC Observatory + Secure MCP Continuity — End-to-End Freeze

**Freeze date:** 2026-10-11  
**Status:** VERIFIED MILESTONE  
**Scope:** ReLiC Observatory ingestion, durable continuity storage, read-only MCP retrieval, and ChatGPT continuity access.

## Doctrine

This freeze preserves the following boundaries:

- Identity != representation.
- Representation != truth.
- UNKNOWN != FACT.
- MEMORY != CANON.
- Observation != Canon.
- Temporal association != causation.
- ReLiC is an observer and continuity layer. Retrieval, compression, translation, or temporal proximity do not promote information to canon.

## Verified end-to-end path

The following path has been independently demonstrated:

`GitHub Actions -> GitHub OIDC -> AWS Lambda -> private ReLiC Host -> EFS SQLite -> read-only ReLiC MCP -> OpenAI Secure MCP Tunnel -> ChatGPT`

### GitHub / OIDC / private ingestion proof

GitHub Actions workflow run #24 (`38107494482`) on branch `relic-independent-service`, commit `7a57011f95b1781dad3c8fa677f32842bfdf1636`, successfully assumed the branch-scoped AWS role through GitHub OIDC and invoked the private Observatory ingestion Lambda.

The resulting ReLiC event is immutable event ID:

`9527b2e0-1a01-4e7a-ae49-956cd5a42dd6`

with payload hash:

`59eb97baebb48f4049ae28367456ae9fcc7bf448bb3ec84fd4f26b7015185f1a`

The event is stored as `OBSERVATION`, source `GIT_REPOSITORY`, actor `ryanlcole`, with doctrine explicitly retaining `observation_is_canon: false`.

## SQLite/EFS incident and correction

The original writer forced SQLite `journal_mode=WAL` while the same EFS filesystem was mounted by multiple Fargate tasks/processes. The live MCP subsequently reported `database disk image is malformed`.

This error is retained as engineering history. It is not rewritten as if it never occurred.

Forensic preservation captured the live `relic.db`, `relic.db-wal`, and `relic.db-shm` before modification. A coherent disposable copy passed both `PRAGMA quick_check` and `PRAGMA integrity_check`. This demonstrated that the preserved database/WAL state was structurally valid when accessed coherently and did not justify `.recover` reconstruction.

The critical GitHub event above was independently present in the preserved database with its expected ID, `OBSERVATION` status, and payload hash.

All legacy ReLiC application tasks were stopped before recovery. The coherent database was checkpointed, preserved, converted from WAL to rollback-journal `DELETE` mode, and verified again.

## Hardened implementation

Source hardening commits:

- `c8e2bcfdd3c68a2a926f24eed9d659d63a4a4250` — harden ReLiC SQLite for EFS shared storage.
- `2457e9abdb1b13dd27b1d77d230d42aef5c9a0ac` — make ReLiC MCP database access physically read-only.

Hardened application image:

`797661578124.dkr.ecr.us-east-1.amazonaws.com/relic-host@sha256:1c8a56bbf7b7ded936c4c8736886b34b144ca1324bfff6d845a3066ec2532d3d`

ECS task definition `relic-host:8` uses that immutable image for both host and MCP. The writer mounts `/data` read/write. MCP mounts `/data` read-only and also opens SQLite with URI `mode=ro` plus `PRAGMA query_only=ON`. The tunnel has no EFS mount.

Writer connections use rollback-journal `DELETE`, `synchronous=FULL`, foreign keys, and a bounded busy timeout. WAL is intentionally not used for shared EFS storage.

## Startup network incident and correction

The first `relic-host:8` launch failed before container startup with `TaskFailedToStart`: Fargate could not retrieve `relic/write-token` from the private Secrets Manager endpoint.

The endpoint was healthy and present in both relevant subnets, but its security group allowed TCP/443 only from the Observatory Lambda security group. The minimal correction added TCP/443 from the ReLiC host security group to the private Secrets Manager endpoint security group. No public CIDR was added.

The same immutable `relic-host:8` definition was then retried without rebuilding the image or changing the task definition.

## Runtime verification

The hardened rev8 task `912811f358df4b76958a44f1c587d78f` reached `RUNNING`; task health was `HEALTHY`; `relic-mcp` was `RUNNING` and `HEALTHY`.

Before any new Observatory write, the recovered database was inspected read-only from the rev8 runtime:

- files: only `/data/relic.db` (32768 bytes); no persistent `-wal` or `-shm` files
- SHA-256: `4011371f636ef418de0355d41e5de0d33886bfaa85a00673e699724e2c29c21c`
- journal mode: `delete`
- `PRAGMA quick_check`: `ok`
- `PRAGMA integrity_check`: `ok`
- event count: `5`
- critical event remained `OBSERVATION`
- critical event payload hash remained `59eb97baebb48f4049ae28367456ae9fcc7bf448bb3ec84fd4f26b7015185f1a`

Finally, ChatGPT independently called the live read-only ReLiC MCP `relic_get_event` tool through the Secure MCP Tunnel and retrieved event `9527b2e0-1a01-4e7a-ae49-956cd5a42dd6` with the same status, provenance, doctrine, and payload hash.

## Preserved failure history

The milestone includes its failures rather than erasing them:

- Workflow run #22 (`38107112491`) failed test collection with `ModuleNotFoundError: No module named 'validation'`; OIDC was not exercised.
- Workflow run #23 (`38107125348`) failed from the same stale-tree import regression.
- The shared-EFS WAL architecture produced a live MCP `database disk image is malformed` error.
- The first rev8 startup failed because the private Secrets Manager endpoint security group did not yet trust the ReLiC host security group.

Each failure produced a bounded correction and subsequent verification.

## Freeze statement

As of this freeze, the verified engineering truth is:

1. GitHub can submit evidence through branch-scoped OIDC without holding the ReLiC write token.
2. AWS retains authoritative ReLiC write authority behind the private ingestion boundary.
3. Durable evidence survives in EFS-backed SQLite.
4. SQLite is no longer configured for shared-EFS WAL operation.
5. MCP has both application-level and filesystem-level read-only database access.
6. The Secure MCP Tunnel exposes the private MCP reader without exposing the MCP service publicly.
7. ChatGPT can retrieve the stored GitHub observation through that read-only path.
8. The stored observation remains an `OBSERVATION`; it is not promoted to canon by ingestion, storage, retrieval, or this freeze document.

This document freezes the verified milestone. Future changes are new engineering history and must not silently rewrite this record.