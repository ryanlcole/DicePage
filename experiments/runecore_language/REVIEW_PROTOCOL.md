# RuneCore research and cross-model review protocol (experimental)

Source-of-truth code: https://github.com/ryanlcole/DicePage/pull/58
Status: proposed hypothesis and verified interpreter; not chemical truth, not a trained LLM.

## Independent reviewer brief — copy into Grok, Claude, or another assistant

Read the source and tests in draft PR #58, and the project's v0.9 generic ring-contact prototype if supplied separately. Examine the owner's example ring definitions: H inner CW 1000→0100→0010→0001; O inner CW 1010↔0101; O outer CCW 11101110→11011101→10111011→01110111. Atoms retain fixed RAM/storage identity while ring phases advance. User's oxygen-with-two-hydrogen observation alternates 11111111 with each raw oxygen outer ring phase.

Do NOT assume these encodings are correct quantum chemistry. Do NOT claim that a language parser constitutes a trained LLM or that a periodic bit sequence proves real atomic bonding.

Please return:
1. Exact algebraic invariants, redundancies and counterexamples, especially cases where the ring-matching heuristic accepts implausible combinations or rejects intended ones.
2. At least 5 new held-out ring instances (different widths, occupancy counts, direction combinations, phase offsets) and machine-reproducible expected test outputs.
3. A blinded comparison between a generic contact matcher, random matching, and a simple hand-coded baseline; require no chemical labels as inputs.
4. A falsifiable proposal for how START/STOP hardware opcodes encode ring boundaries, direction and zero locations without stopping rotation.
5. A benchmark for a separately trained symbolic predictor using unseen ring structures; identify possible train/test leakage from repeating cycles.
6. A physically honest critique: what additional assumptions and measurable predictions would distinguish the model from a cellular automaton or notation system?
7. Classify every conclusion as VERIFIED, CONTRADICTED, HYPOTHESIS or UNKNOWN and provide supporting source/code lines.

Avoid paid APIs, secrets, undisclosed uploads, and unfounded claims. Put code changes in a separate pull request or return a reproducible diff. Do not edit or merge PR #58 automatically.

## Proposed acceptance gates for future milestones

- LANGUAGE: tokenizer/parser/serializer round trip for at least 1,000 generated examples; invalid grammar rejected.
- ORBITAL RULES: rotation and recurrence invariants for all ring widths 1..32 and both direction types where applicable.
- VIEWER: frame pixel output limited to viewport; mobile Safari test with recorded device/browser.
- BONDING: zero-site capacity, stable relationship under phase advance, negative and adversarial control tests; no atom-name shortcuts.
- MODEL: trained model artifact, training provenance, held-out predictions on previously unseen ring layouts and meaningful improvement over baseline.
- SCIENCE: preregistered numerical predictions matched to independent experimental references; null hypotheses preserved.
- OPERATIONS: GitHub commit/CI + exact deployed URL verified; Drive archive pointer readback, ReLiC receipt only if true writer returns it.

Reviewer outputs are observations, never project canon by themselves.
