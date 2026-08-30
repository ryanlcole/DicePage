# AI Game Master

## Current Implementation

The current build uses deterministic fallback narration and structured AI-GM response objects. This proves the orchestration boundary without requiring an external AI service or API key.

Implemented:

- structured response format;
- schema validation;
- safe text rendering;
- rejected forbidden state domains;
- deterministic fallback narration when no external AI is available;
- storage of AI proposals separately from validated state changes.

Not implemented:

- external model calls;
- long-term AI memory summarization beyond local NPC conversation summaries;
- streaming narration;
- production AI rate-limit tiers.

## Required Response Shape

Every AI-GM response uses:

```json
{
  "narration": "Visible description for the players.",
  "scene_updates": [],
  "proposed_checks": [],
  "proposed_state_changes": [],
  "npc_actions": [],
  "combat_actions": [],
  "rewards": [],
  "follow_up_options": []
}
```

## Authority Rule

AI narration is not authoritative state. The AI may propose limited scene-facing changes, but the deterministic engine must validate and commit every actual mutation.

The AI layer cannot directly control:

- account permissions;
- player entitlements;
- random number generation;
- inventory ownership;
- currency balances;
- character statistics;
- payment status;
- authoritative world state.

## Validation Coverage

`shaelvien_lite/ai_gm.py` validates:

- exact top-level schema keys;
- expected list fields;
- narration type and length;
- allowed check attributes and skills;
- known NPC IDs and action types;
- known item IDs in proposals;
- contradictory scene updates;
- forbidden account, entitlement, character-stat, and payment mutations;
- hidden-instruction disclosure patterns;
- HTML/script injection is escaped before rendering.

Rejected fixture categories are covered by `tests/test_shaelvien_lite.py`.

## Future External AI Integration

External AI should be added behind the same schema. Requests should keep context separated:

- canon;
- world state;
- character state;
- scene state;
- recent session log;
- player intent.

External model output must pass schema validation before game-system functions see it. Validation failures should be logged and replaced with deterministic fallback narration so the tutorial remains playable.
