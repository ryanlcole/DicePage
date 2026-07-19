# Data Models

## Persistence

Default local persistence:

```text
data/shaelvien_lite_state.json
```

This is an atomic JSON store suitable for the current PC-hosted MVP. It is not a production database. The store uses a process-local lock, parameter-free structured Python data mutation, temporary-file writes, and malformed JSON recovery into `*.corrupt.<timestamp>` files.

SQLite is not used. Local development remains on JSON; hosted staging uses PostgreSQL with migrations and transaction boundaries.

Hosted staging persistence:

```text
SHAELVIEN_STORAGE_BACKEND=postgres
DATABASE_URL=<Neon connection string>
```

PostgreSQL support is implemented for Koyeb/Neon staging. The storage adapter keeps the deterministic engine interface stable while persisting core records into relational tables:

- `accounts`
- `account_entitlements`
- `sessions`
- `characters`
- `character_inventory`
- `character_equipment`
- `campaigns`
- `campaign_characters`
- `campaign_quests`
- `campaign_camp_structures`
- `campaign_completed_encounters`
- `session_logs`
- `ai_validation_records`
- `validated_state_changes`
- `validation_failures`
- `admin_events`
- `rewards`
- `idempotency_records`
- `parties`
- `schema_migrations`

JSONB is used only for bounded flexible profile/configuration fields such as full character presentation, RPG item metadata, AI request/response payloads, scene metadata, and party metadata. Account ownership, credentials, inventory quantities, quest states, camp levels, completed encounters, and idempotency keys have relational columns and constraints.

## State Root

- `accounts`
- `sessions`
- `characters`
- `campaigns`
- `parties`
- `session_logs`
- `ai_proposals`
- `validated_state_changes`
- `validation_failures`
- `admin_events`
- `settings`
- `setup`
- `idempotency`
- `entitlements`
- `npc_templates`

## Account

Accounts include:

- account ID;
- handle;
- role;
- password hash;
- creation timestamp;
- owned character IDs;
- owned campaign IDs;
- party IDs.

Plain-text passwords are not stored.

## Session

Sessions include:

- secure random session token;
- account ID;
- CSRF token;
- creation timestamp;
- last-seen timestamp.

The browser receives the session only as an HttpOnly cookie. The browser stores only active character/campaign IDs in localStorage.

## Character

Character records include:

- character ID;
- player ID;
- name;
- portrait;
- ancestry or origin;
- role/class;
- progression tier;
- level;
- experience;
- biography;
- disposition;
- configurable attribute names;
- six starting attributes;
- vitals;
- flexible skills map;
- equipment slots;
- inventory;
- currency;
- resources;
- current assignment.

## Item

Every item includes:

- item ID;
- name;
- category;
- quantity in inventory;
- mass;
- quality;
- durability where applicable;
- description;
- mechanical effects;
- value;
- ownership status.

Durability is item-level for now. `mechanical_effects` and durability fields preserve room for later component-level Shaelvien equipment without replacing the inventory model.

## Campaign

Campaign records include:

- campaign ID;
- owner account ID;
- party ID;
- region ID;
- current location;
- unlocked locations;
- completed encounters;
- world state;
- scene state;
- assigned characters;
- secondary heroes;
- explicit quest state;
- NPC state and memory;
- camp progression;
- active combat;
- processed action idempotency keys;
- session log IDs.

## Party

Party records include:

- party ID;
- party owner;
- party members;
- invite status;
- character assignments;
- shared scene;
- turn ownership;
- party chat;
- action queue;
- group decisions;
- shared rewards;
- individual rewards;
- reconnection metadata.

The party model is persisted, but real-time cooperative behavior is not active.
