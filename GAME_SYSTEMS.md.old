# Game Systems

## Implemented Vertical Slice

Verified through unit/integration tests and visible Chrome UI tests:

1. Open landing page.
2. Create or enter account.
3. Create a primary hero.
4. Begin tutorial campaign.
5. Arrive at Emberhall Outpost.
6. Speak with the guild representative.
7. Accept the Forest Road quest.
8. Travel to Forest Road.
9. Resolve an investigation check.
10. Start and complete combat.
11. Receive server-issued rewards.
12. Return to Emberhall Outpost/camp.
13. Upgrade Quarters.
14. Close browser, restart server, reopen, and continue from saved state.

Evidence:

- `verification/ui-journey-report.json`
- `verification/ui-reconnect-report.json`
- `verification/ui-mobile-report.json`

These files are intentionally ignored by Git.

## Seeded Content

Implemented seed data:

- Region: Emberhall Reach.
- Settlement: Emberhall Outpost.
- Adventure locations: Forest Road, Abandoned Mine, Ruined Shrine, Bandit Camp.
- Persistent NPC templates: innkeeper, blacksmith, healer, merchant, guild representative, guard scout.
- Starting roles: Vanguard, Pathfinder, Arcanist.
- Items, weapons, armor, consumables, enemies, introductory boss, quests, and camp structures.

This is provisional Shaelvien Lite content, not expanded canon.

## Dice

Current rule:

```text
1d20 + Attribute Modifier + Skill Modifier + Situational Modifier
```

The server stores:

- original player action;
- selected rule;
- d20 roll;
- modifiers;
- total;
- difficulty;
- result band;
- resulting state changes;
- AI narration.

Result bands:

- Critical Failure;
- Failure;
- Partial Success;
- Success;
- Critical Success.

Rolls are server-generated. Browser-supplied roll claims are ignored.

## Combat

Implemented:

- initiative;
- player turn enforcement;
- enemy turn resolution;
- range bands: `Engaged`, `Near`, `Far`;
- basic attacks;
- defense action;
- healing item use;
- damage;
- defeat state;
- retreat state;
- reward issuance;
- duplicate encounter reward prevention.

Not implemented:

- tactical grid movement;
- multiple simultaneous players;
- complex status-condition system;
- repeatable encounter farming.

## Quests

Quest state uses explicit transitions:

```text
locked -> available -> active -> completed
active -> failed
failed -> available
```

The browser cannot directly set arbitrary quest status. Quest completion is derived from validated objectives.

## Camp

Implemented structures:

- Quarters;
- Storage;
- Workshop;
- Training Yard;
- Healing Tent;
- Planning Table.

Each has:

- level;
- max level;
- upgrade requirement;
- prerequisites;
- development-mode immediate completion;
- mechanical benefit text.

Resource costs and structure levels are mutated together in one server update. Failed upgrades do not consume resources. Duplicate idempotency keys do not double-apply upgrades.

## Free-To-Play And Revenue Preparation

Implemented:

- free-play entitlement flag;
- character slot and campaign slot data;
- disabled product catalog placeholders;
- development test entitlement structure.

Not implemented:

- real-money transactions;
- loot boxes;
- direct paid victory;
- subscriptions;
- product fulfillment.
