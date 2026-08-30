# Perception System

Milestone: `SHAELVIEN-PERCEPTION-1`

The player view is derived from authoritative map state and an owned player character's active sensory profile.

Separated state layers:

- Authoritative map state
- GM-visible map state
- Player-known map state
- Current visible cells
- Current audible events
- Previously discovered cells
- Unknown cells

Perception profiles live in `data/perception_profiles.json`. The starter PC profile currently uses 120 ft vision and 140 ft hearing on maps whose scale converts those values into logical cells.

The public player snapshot is produced through `playerVisibleSnapshot()`, which now calls the perception filter. Hidden tiles, hidden triggers, GM notes, encounter setup, source identities for sounds, and out-of-perception terrain are not included in the public snapshot.

Derived perception state is not encounter replay state. Replay records authoritative movements, interaction, combat, and future perception-relevant state changes, but it does not record pulse animation frames or viewport pan/zoom.

