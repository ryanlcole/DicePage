# Scene Model

A Scene is the playable table context around a map.

```json
{
  "sceneId": "scene-tavern-ambush-001",
  "mapId": "map-tavern-main-floor",
  "participants": [],
  "initiativeId": "initiative-tavern-ambush-001",
  "decks": [],
  "sharedCards": [],
  "activeChipIds": [],
  "permissions": {}
}
```

The Scene does not own terrain. It references the active map and adds tabletop play surfaces:

- player decks
- GM decks
- monster decks
- dice tray
- initiative strip
- chess clock
- lore scroll
- shared cards
- active effects
- permissions

Scene layout is separate from map data. Shared card placement may become authoritative only when campaign rules make it part of play.

