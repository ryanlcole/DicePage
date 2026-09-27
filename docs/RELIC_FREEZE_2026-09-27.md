# ReLiC Freeze Manifest — 2026-09-27

Status: **FROZEN TESTED SNAPSHOT**

This document records the exact ReLiC state frozen on 2026-09-27. The commit SHA is the authoritative freeze identity. Branch names are convenience references and are technically movable unless repository protection is applied.

## Tested freeze

- Repository: `ryanlcole/DicePage`
- Development branch at test time: `live-alpha-rist-blazor-world`
- Frozen reference: `relic-freeze-2026-09-27-tested`
- Immutable commit identity: `f36e188ce27cd2301e302cd959324cc3e6c0d577`
- ReLiC canon version: `RELIC-CANON-2026-09-27.5`

The tested freeze contains:
- Rune → Glyph → Shaep semantic core;
- canon-grounded system weakness analysis;
- human non-harm and ecological countermeasure rules;
- scoped five-minute proof/update/alert contract;
- auditability rule: ReLiC does not require trust in ReLiC;
- locked scientific-prediction and resource benchmark helpers;
- deterministic Infoton claim audit;
- compiler error-code regression fix.

## Preserved failed freeze

The first freeze was intentionally **not erased**.

- Frozen reference: `relic-freeze-2026-09-27`
- Commit: `6751f8dcccd5f11763e050b1b6ad8c7e0ffa56c1`
- ReLiC Scientific Validation: **FAILED**
- Failure: test collection could not import `ChangeProof` from `relic_core.py`.
- Cause: two compatible-but-incomplete core implementations had converged on Rune/Glyph/Shaep semantics while exposing different helper APIs.
- Resolution: preserved the newer semantic-digest core and restored the proof/analyzer compatibility API instead of discarding either design.

This failed snapshot remains evidence under **Errors become law** and **RELIC.AUDIT.FAILURES_VISIBLE**.

## Test evidence for tested freeze

### ReLiC Scientific Validation

- Workflow run: `36352662533`
- Commit tested: `f36e188ce27cd2301e302cd959324cc3e6c0d577`
- Result: **SUCCESS**
- Deterministic tests: **9 passed**
- Test runtime reported by CI: **0.16 s**
- Infoton audit step: **SUCCESS**

The deterministic audit classified the tested Infoton-related calculations as:
- temperature/mass line from self-derived temperature: `ALGEBRAIC_IDENTITY`;
- 584 → 3 reduction percentage: `ARITHMETIC_ONLY`;
- 150 mV → 36.269838631273764 THz: `UNIT_CONVERSION`;
- 700 nm photon / Landauer-bit quotient: `DERIVED_RATIO`.

These classifications are evidence boundaries, not claims that the underlying physical hypotheses are false.

### Compliance Guardrails

- Workflow run: `36352662548`
- Commit tested: `f36e188ce27cd2301e302cd959324cc3e6c0d577`
- Result: **SUCCESS**

### ReLiC plugin package

The grounding-skill package at this freeze is byte-identical to the package validated successfully in workflow run `36352533670`. No subsequent change to that skill file occurred before the tested freeze.

### Code Index Governance

At the time this manifest was first written, the exact-commit Code Index Governance run `36352662537` had not yet completed. No success is claimed here until a completed result exists.

## Frozen file identities

| Path | Git blob SHA |
|---|---|
| `docs/RELIC_CANON.md` | `db99ec440f78aa38218050416704cd1b3410419e` |
| `infra/aws/relic-canon.json` | `7a700a8d1a5db8cdc1f0fd04aa559491f71cc7c1` |
| `infra/aws/rist_relic_mcp.py` | `26559ac284d3b180aa131c86dbd0f619bb5cbbbb` |
| `plugins/relic/skills/relic-grounding/SKILL.md` | `cf8988377a56fc7b613602d61a26fc489f5a784b` |
| `relic_core.py` | `593f4fb7e1e3ef5e0854c313485c55d9870d5b94` |
| `relic_analyzer.py` | `ac72451db77db30789ec00b354b35ba952f85db0` |
| `tests/test_relic_core.py` | `fe33461a91c0c5f6c2e35c8936b6cdedd79cd88e` |
| `tests/test_relic_science.py` | `0897a2a09f82de5f41b0c508cf92e3f02047680f` |
| `.github/workflows/relic-science.yml` | `507c653bc3692d4dc4738a0ed473b6f6cc9eec93` |
| `research/relic_science/README.md` | `db425160c5af8258159bc439870ed7a60acb6b97` |
| `research/relic_science/benchmark.py` | `8e6a01a0af1f917bfe3659c5e514ccae6847ba03` |
| `research/relic_science/infoton_audit.py` | `0dcd094693936cab51729843d801f9c890df7255` |

## What this freeze proves

This freeze proves that the recorded source state exists and that the listed deterministic tests passed on that exact commit.

It does **not** prove:
- that ReLiC has changed AI globally;
- that all AI systems follow ReLiC canon;
- that ReLiC prevents every possible accidental harm;
- that ReLiC reduces real electrical energy without a measured baseline;
- that ReLiC outperforms neural models;
- that Infoton hypotheses are physically correct;
- that blind cellular predictions will succeed.

Those remain separate empirical questions.

## Governing audit rule

**Do not trust this manifest merely because it says the tests passed.**

The commit SHA, blob SHAs, workflow records, logs, test code, failures, and future independent reproductions are the evidence.
