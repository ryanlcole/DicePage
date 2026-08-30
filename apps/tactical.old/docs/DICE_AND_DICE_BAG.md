# Dice And Dice Bag

The tabletop supports D100, D30, D20, D12, D10, D8, D6, D4, and Coin profiles.

## Authority

The authoritative result is generated through deterministic event logic and recorded in tabletop replay events. Visual throw motion is decorative and seeded from the authoritative result.

## Dice Bag

A card may define a Dice Bag action:

```json
{
  "actionId": "attack",
  "dice": ["d20", "d6"],
  "baseModifierSource": "character.baseAttack",
  "chipTargets": ["attack"]
}
```

Resolution records:

- selected card
- action ID
- dice results
- base modifier
- visible chips
- total
- replay event

Visual dice never become the source of authoritative randomness.

