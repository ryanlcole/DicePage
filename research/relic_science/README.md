# ReLiC Scientific Validation Harness

Status: **EXPERIMENTAL / FALSIFIABLE**

This folder converts the open scientific questions recorded in the 2026-09-27 ReLiC evidence packet into reproducible tests. It exists to prevent ReLiC, Shaelvien, or an external theory from being declared correct merely because its equations can restate known inputs.

## Governing rule

A result is not a prediction when the claimed output was used to define or derive the equation that produced it.

Every scientific claim must therefore identify:

- the input available before prediction;
- the target hidden from the predictor;
- the baseline(s) to beat;
- the metric selected before reveal;
- the compute/memory/energy measurement method;
- the timestamped prediction commitment;
- the later independent ground truth;
- the exact scope supported by the result.

Failure, contradiction, and null results are retained.

## Eight open questions from the evidence packet

### 1. Blind cellular perturbation prediction

**Question:** Can ReLiC predict an unseen cellular perturbation response before ground truth is revealed?

**Test:** Use the Arc Institute Virtual Cell Challenge protocol or an equivalent held-out Perturb-seq dataset. The prediction process receives only the allowed basal cell state, perturbation target, and public prior knowledge. Ground-truth post-perturbation expression is withheld until after the prediction is cryptographically committed.

**Pass condition:** Score the committed prediction with the benchmark's published metrics and compare against explicit simple baselines and published neural baselines. A single successful case is evidence only for that tested distribution.

### 2. Rune/Glyph/Shaep versus neural models

**Question:** Can the semantic method equal or outperform a neural model?

**Test:** Run the same examples, train/test split, target variables, and evaluation metric through:
- a simple baseline;
- a documented neural baseline;
- a ReLiC Rune/Glyph/Shaep method.

Do not give ReLiC privileged access to hidden labels or future state.

**Pass condition:** Report accuracy and resource use separately. No overall winner is declared without a pre-registered aggregation rule.

### 3. Computation, memory, and energy

**Question:** Can ReLiC obtain comparable useful results with substantially less resource use?

**Test:** Measure wall time, CPU time where available, peak allocated memory, serialized context bytes, and externally measured joules when a supported meter is present.

**Important:** byte reduction, operation-count reduction, elapsed time, and Landauer's theoretical lower bound are not substitutes for measured electrical energy.

### 4. Discovery of new relationships

**Question:** Can useful relationships emerge from atomic/cellular data without being manually supplied?

**Test:** Hide selected known relationships and allow the system to construct candidate typed relations from the remaining observations. Freeze candidates before revealing the hidden relations.

**Pass condition:** Evaluate precision/recall or ranking quality against the hidden relationships. Newly proposed relationships not present in the reference data remain HYPOTHESIS until independently tested.

### 5. Cross-domain semantic conservation

**Question:** Can one semantic framework represent biology, physics, software, world state, and NPC behavior without losing domain-specific meaning?

**Test:** Use stable Rune identities plus typed domain namespaces and explicit Glyph/Shaep composition. Round-trip each domain through encode -> semantic graph -> domain representation.

**Pass condition:** Identity, units, truth domain, provenance, authority, and domain-specific constraints survive the round trip. One universal vocabulary is not required; a shared semantic substrate with domain-specific types is sufficient.

### 6. Locked unseen predictions

**Question:** Can ReLiC make a timestamped prediction that is later confirmed by independent evidence?

Use `benchmark.py lock` before ground truth is available. It writes a SHA-256 commitment over canonical JSON. After reveal, use `benchmark.py verify` and then score the unchanged prediction.

A modified prediction fails verification.

### 7. Error memory without model retraining

**Question:** Do preserved failures measurably improve future reasoning?

**Test:** Run an A/B suite:
- A: identical solver with error memory disabled;
- B: identical solver with normalized prior failure constraints enabled.

Replay tasks containing previously seen failure patterns plus novel controls.

**Pass condition:** Compare regression rate, repeated-error rate, task success, and resource cost. Improvement on only memorized exact strings is insufficient; normalized failure identity must generalize to controlled variants.

### 8. January Walker / Infoton claims

The Infoton equation

`m(T) = k_B T ln(2) / c^2`

is mathematically equivalent to

`T = m c^2 / (k_B ln(2))`.

Therefore, if a particle's temperature coordinate is calculated from its already-known mass with that same equation, the later relation

`log10(T) = log10(m) + constant`

is an algebraic identity, not an independent prediction of particle mass.

The correct validation question is: **Does the framework predict an unseen independently measured quantity using inputs that did not contain that quantity?**

`infoton_audit.py` calculates the identities, makes the dependency explicit, and separates:
- arithmetic identities;
- physically measured quantities;
- independent predictions;
- hypotheses requiring experiment.

The same rule applies to the P30 claim. The arithmetic change from 584 operations/checks to 3 would be a 99.4863% count reduction, but this percentage is not evidence of a 99.4863% reduction in electrical energy. Operation definitions, executable implementations, workload equivalence, hardware, measurement method, and measured joules must be supplied.

## ReLiC scientific lifecycle

`Observe -> Normalize -> Rune -> Glyph -> Shaep -> Predict -> Lock -> Reveal -> Score -> Remember`

A failed prediction becomes durable evidence. It is never silently rewritten into a success.
