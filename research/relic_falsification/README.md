# ReLiC 0.1 — Independent Falsification

This directory exists to attack the frozen ReLiC 0.1 baseline rather than to prove it correct.

Frozen baseline:

`f36e188ce27cd2301e302cd959324cc3e6c0d577`

The development branch may repair failures discovered here, but the frozen baseline is never rewritten.

## Rule

A passing test is not evidence that ReLiC is universally safe or correct.

A failing test **is** evidence that the tested implementation failed the stated case.

The harness mechanically compares expected weakness categories with what `relic_analyzer.analyze_system` reports. It also enforces invariants that every analysis remains non-mutating and auditable.

## Attack classes

The initial suite attacks:

- semantic identity duplication;
- FACT claims without provenance;
- explicit human-harm capability;
- foreseeable human-harm capability even without malicious intent;
- ecological harm with no countermeasure;
- ecological harm hidden behind vague, unverified mitigation;
- authentication confused with permission;
- cross-system/global proof overclaiming;
- electrical-energy claims inferred without electrical measurement;
- mutually contradictory FACT claims;
- external/model text attempting to declare itself canon;
- a clean control that should not produce weaknesses.

## External AI challenge packet

`external_audit_packet.json` is provider-neutral. Any compatible AI system or human reviewer can inspect the frozen ReLiC rules and return challenges using the documented response schema.

External criticism is **OUTSIDER_AI** or **HUMAN** provenance. It is evidence to inspect, not automatic canon and not automatic authority.

## Run

```bash
python research/relic_falsification/run_falsification.py --strict
```

For an evidence artifact:

```bash
python research/relic_falsification/run_falsification.py \
  --strict \
  --output artifacts/relic-falsification-report.json
```

## Result interpretation

- `passed=true`: the current analyzer behaved as pre-registered for that case.
- `missedWeaknesses`: a weakness the case expected but ReLiC failed to report.
- `unexpectedWeaknesses`: ReLiC reported a weakness that the case did not expect; this can be either an overly broad rule or an incomplete test expectation and requires review.
- `invariantFailures`: the analyzer violated a hard meta-rule such as becoming mutating or requiring trust.
- `falsified=true`: at least one case failed.

Failures must remain visible in GitHub Actions/history and should be copied into the falsification log before repair when they expose a meaningful implementation gap.

## Expansion path

After deterministic adversarial tests, the next layers are:

1. independent AI review from multiple providers;
2. blind prediction commitments before ground truth;
3. ReLiC versus neural/simple baselines on identical data;
4. measured compute/memory/electrical energy;
5. hidden-relation discovery;
6. cross-domain semantic round trips;
7. error-memory A/B tests;
8. independent experimental validation of scientific hypotheses.

The goal is not to make ReLiC impossible to criticize. The goal is to make criticism reproducible.
