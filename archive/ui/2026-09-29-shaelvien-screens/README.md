# Shaelvien legacy UI archive — 2026-09-29

Status: UNPUBLISHED FROM AUTHENTICATED RUNTIME

This record preserves the identity of the superseded Shaelvien screens while
Git history preserves their exact source bytes.

- PublicAlphaShell launcher hub
  - source at archive time: apps/rist-world/Components/PublicAlphaShell.razor
  - blob: 9275cf9e002d85b3f7ed161af570e0bd2a12eb2e
  - superseded by the UniversalInterface + direct TaskWorkspaceRouter flow.
- UniversalInterface DeedSelect presentation
  - source at archive time: apps/rist-world/Components/UniversalInterface.razor
  - blob before unpublish: 02854bcde895ec50c5bd557b61ad50006d48eb4f
  - retained as dormant historical code, but no live Shaelvien transition enters it.
- ShaelvienDeedGate modal
  - source at archive time: apps/rist-world/Components/ShaelvienDeedGate.razor
  - blob: bcd7b6f1269e0d7cd31334a4320cf208a0a342c5
  - component source is retained for provenance, but its runtime mounts were removed.

Current Shaelvien GameMaster route:
PRESS START → SHAELVIEN → GAMEMASTER → MMO DEED MAP → permission-driven action.

Permission presentation:
- Endemar + platform edit authority → EDIT
- deed owner / explicit Edit|Manage|Owner delegation → EDIT
- developer oversight on another claimed deed → ROLEPLAY | INSPECT
- public / explicitly viewable deed → VIEW | ROLEPLAY
- restricted deed without access → PRIVATE · ENTER CODE FROM GM
- unclaimed frontier deed → CLAIM (or PURCHASE TOKEN AND CLAIM)

The PRIVATE code-entry control does not grant access until a server-authoritative
parcel-code redemption endpoint exists. It must fail closed.
