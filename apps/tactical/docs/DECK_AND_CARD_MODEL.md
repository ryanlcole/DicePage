# Deck And Card Model

Card definitions are static templates. Scene state tracks current use, sharing, discovery, stacks, and revealed state.

## Card Definition

```json
{
  "cardId": "card-weapon-sword-001",
  "cardType": "weapon",
  "title": "Practice Sword",
  "visibility": "player_private",
  "actionProfiles": []
}
```

## Deck Definition

```json
{
  "deckId": "deck-orcs-001",
  "deckType": "monster",
  "visibility": "gm_private",
  "cards": []
}
```

## Instance State

Scene state records:

- shared card IDs
- revealed card IDs
- card share state
- card discovery state
- card use counts
- active chip IDs

Definitions are not mutated for one player's current scene.

