# ReLiC Universal / Projects / Environment Boundary

Status: proposed implementation architecture. This document does not promote project history to canon and does not authorize historical migration.

## Doctrine

- Identity != Representation.
- Representation != Truth.
- UNKNOWN != FACT.
- MEMORY != CANON.
- Observation != Canon.
- Temporal association != causation.
- Current inspected repository/runtime state controls claims about current implementation behavior.
- ReLiC warns; it does not silently prevent project drift or take execution authority.

## Domains

### ReLiC Universal

Shared reusable engineering knowledge: generalized error signatures, failure modes, prevention rules, solutions, compatibility lessons, and provenance.

Universal MUST NOT expose PII, credentials, tokens, private project content, private paths, raw machine identity, private infrastructure identifiers, or security-sensitive material. Project evidence cannot automatically enter Universal. Generalization requires sanitization plus explicit review/approval.

### ReLiC Projects

Continuity isolated to an owner/project scope. It may retain project targets, plans, decisions, implementation observations, builds, tests, errors, conflicts, verification evidence, and historical changes. Repository/runtime evidence remains implementation truth for current behavior.

Project A has no direct read path to Project B. Universal may provide sanitized shared knowledge to either project.

### ReLiC Environment

Authorized telemetry associated with one Project. Connectors such as Codex, development agents, CI runners, OS services, containers, or cloud runtimes may provide telemetry when permission exists.

Environment data is project-private by default. Raw machine/user identity, command lines, environment variables, paths, addresses, and credentials must not be promoted to Universal.

ReLiC may advise about resource pressure, configured thermal thresholds, partitioning/throttling, under-utilization, profiling, and language/runtime alternatives. It does not independently claim hardware damage from a telemetry threshold and does not autonomously throttle, terminate, reprioritize, or rewrite workloads.

## Development loop

1. Human designs a plan.
2. AI records the plan as a Project Target and begins predevelopment.
3. Before and while writing, AI queries ReLiC Project history and applicable Universal knowledge.
4. ReLiC returns known errors, verified repairs, unresolved conflicts, and applicability confidence.
5. AI writes code. Observatory records implementation/build/test/runtime evidence separately from planning.
6. ReLiC compares new observations with project targets/history and Universal patterns and emits advisory warnings when errors or conflicts are observed.
7. Environment telemetry, when authorized, is evaluated for resource warnings and optimization opportunities.
8. Human/AI may continue, investigate, or amend the target. Drift is warned about, not silently prevented.

## Knowledge flow

- Universal -> Project: read-only reusable knowledge and warnings.
- Project -> Universal: denied by default; only reviewed, sanitized generalization may cross.
- Project A -> Project B: denied.
- Environment -> its Project: permitted when authorized.
- Environment -> Universal: denied by default; reviewed sanitized generalization only.

## Evidence classes

Warnings should preserve at least:

- FACT: directly observed measurement/result.
- INFERENCE: interpretation supported but not proven.
- UNKNOWN: missing/ambiguous cause or applicability.
- RECOMMENDATION: advisory next action, not authority.

A hardware/resource warning must identify whether the threshold came from hardware/vendor evidence or project/operator policy. Optimization recommendations require profiling/benchmark evidence before claiming a language rewrite is superior.

## Historical migration consequence

Historical migration candidates must be routed to UNIVERSAL, a specific PROJECT, or DO_NOT_MIGRATE/UNKNOWN before ingestion. Existing migration approval/idempotency gates remain required. Nothing in this architecture approves the current historical candidate batch.
