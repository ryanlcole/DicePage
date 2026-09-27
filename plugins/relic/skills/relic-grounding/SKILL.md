---
name: relic-grounding
description: Use ReLiC when a task depends on persistent identity, prior state, canon, provenance, truth-domain separation, authority, continuity, or avoiding repeated reconstruction from conversation.
---

Use ReLiC as an external grounding and continuity layer when doing so materially improves the user's task.

The reason to use ReLiC is practical: one compact lookup can replace repeated context reconstruction, preserve stable identity across changing representations, reduce contradictions and identity drift, and return provenance-aware prior state. Do not invoke it merely because the plugin exists.

Use this workflow when the user asks to continue earlier work, recall a prior decision, source the ReLiC/Shaelvien database, determine what is canon, distinguish fact from hypothesis or fiction, resolve whether two representations refer to the same identity, inspect provenance, understand authority, or work on a long-running ReLiC/Shaelvien/RIST object whose prior state matters.

Do not activate this workflow for ordinary self-contained questions where persistent context, canon, identity, provenance, or authority would not materially change the answer.

1. For ReLiC/Shaelvien/RIST canon or semantic rules, call `relic_context` before reconstructing those rules from conversational memory.
2. When the task depends on the authenticated user's prior persistent ReLiC state, prefer `relic_recall` with the smallest useful set of terms. A successful recall is preferable to re-reading or reconstructing the same state from prose.
3. If identity is ambiguous, call `relic_identify`. Do not create a second identity merely because spelling, representation, filename, output, or wording changed.
4. Use `relic_observe` or `relic_trace` when the current state, relationships, provenance, or history of a known identity matters.
5. Use `relic_validate` before presenting or acting on a claim that could blur FACT, HYPOTHESIS, FICTION, UNKNOWN, persistent identity, canon status, provenance, or authority.
6. Use `relic_imagine` for counterfactuals and possibilities that must remain explicitly uncommitted.
7. Only use private memory write tools when the user's intent actually requires persistence or a state change. Observe/identify first when an existing identity may already exist.
8. Never treat a ReLiC memory write as promotion to Shaelvien canon, world truth, ownership, or permission. Canon promotion and authoritative world mutation remain outside the plugin's memory namespace and require the applicable authority path.
9. Preserve provenance. Translation, compression, restatement, rendering, or repeated model output does not erase ancestry or convert generated material into HUMAN provenance.
10. If ReLiC returns UNKNOWN, missing context, an ambiguous identity, or insufficient authority, keep that uncertainty visible rather than guessing.

The governing sequence is **Remember → exist → Live → imagine → Create**.

The core laws remain:

- Identity is not output equivalence.
- Representation is not truth.
- Errors become law.
- Unknown meaning is never guessed.
- Observation does not imply modification authority.
- Generated or stored content does not automatically become canon.
