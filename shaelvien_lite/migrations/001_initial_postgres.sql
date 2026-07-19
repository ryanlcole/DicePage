CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app_state_meta (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    handle TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('owner', 'player')),
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    profile JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_accounts_handle_lower ON accounts (lower(handle));

CREATE TABLE IF NOT EXISTS account_entitlements (
    account_id TEXT PRIMARY KEY REFERENCES accounts(account_id) ON DELETE CASCADE,
    free_play BOOLEAN NOT NULL DEFAULT true,
    character_slots INTEGER NOT NULL DEFAULT 2 CHECK (character_slots >= 0 AND character_slots <= 20),
    campaign_slots INTEGER NOT NULL DEFAULT 1 CHECK (campaign_slots >= 0 AND campaign_slots <= 20),
    cosmetics JSONB NOT NULL DEFAULT '[]'::jsonb,
    dev_flags JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    csrf_token TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL,
    profile JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_sessions_account_id ON sessions(account_id);

CREATE TABLE IF NOT EXISTS characters (
    character_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    role_name TEXT NOT NULL,
    level INTEGER NOT NULL CHECK (level >= 1),
    experience INTEGER NOT NULL CHECK (experience >= 0),
    health INTEGER NOT NULL CHECK (health >= 0),
    max_health INTEGER NOT NULL CHECK (max_health > 0),
    currency INTEGER NOT NULL CHECK (currency >= 0),
    active_campaign_id TEXT,
    profile JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_characters_account_id ON characters(account_id);

CREATE TABLE IF NOT EXISTS character_inventory (
    character_id TEXT NOT NULL REFERENCES characters(character_id) ON DELETE CASCADE,
    item_id TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity >= 0 AND quantity <= 9999),
    value INTEGER NOT NULL DEFAULT 0 CHECK (value >= 0),
    item_json JSONB NOT NULL,
    PRIMARY KEY (character_id, item_id)
);

CREATE TABLE IF NOT EXISTS character_equipment (
    character_id TEXT NOT NULL REFERENCES characters(character_id) ON DELETE CASCADE,
    slot TEXT NOT NULL,
    item_id TEXT,
    equipment_json JSONB NOT NULL,
    PRIMARY KEY (character_id, slot)
);

CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id TEXT PRIMARY KEY,
    owner_account_id TEXT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    party_id TEXT,
    primary_character_id TEXT REFERENCES characters(character_id) ON DELETE SET NULL,
    region_id TEXT NOT NULL,
    current_location TEXT NOT NULL,
    active_quest_id TEXT,
    combat_active BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    profile JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_campaigns_owner_account_id ON campaigns(owner_account_id);

CREATE TABLE IF NOT EXISTS campaign_characters (
    campaign_id TEXT NOT NULL REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    character_id TEXT NOT NULL REFERENCES characters(character_id) ON DELETE CASCADE,
    PRIMARY KEY (campaign_id, character_id)
);

CREATE TABLE IF NOT EXISTS campaign_quests (
    campaign_id TEXT NOT NULL REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    quest_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('locked', 'available', 'active', 'completed', 'failed')),
    completed_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    quest_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (campaign_id, quest_id)
);

CREATE INDEX IF NOT EXISTS idx_campaign_quests_status ON campaign_quests(campaign_id, status);

CREATE TABLE IF NOT EXISTS campaign_camp_structures (
    campaign_id TEXT NOT NULL REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    structure_id TEXT NOT NULL,
    level INTEGER NOT NULL CHECK (level >= 0),
    max_level INTEGER NOT NULL CHECK (max_level >= level),
    upgrade_state TEXT NOT NULL,
    upgrade_complete_at TIMESTAMPTZ,
    structure_json JSONB NOT NULL,
    PRIMARY KEY (campaign_id, structure_id)
);

CREATE TABLE IF NOT EXISTS campaign_completed_encounters (
    campaign_id TEXT NOT NULL REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    encounter_id TEXT NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (campaign_id, encounter_id)
);

CREATE TABLE IF NOT EXISTS session_logs (
    log_id TEXT PRIMARY KEY,
    campaign_id TEXT REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    entry_type TEXT NOT NULL,
    text TEXT NOT NULL,
    roll_result JSONB,
    created_at TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_session_logs_campaign_created ON session_logs(campaign_id, created_at);

CREATE TABLE IF NOT EXISTS ai_validation_records (
    proposal_id TEXT PRIMARY KEY,
    campaign_id TEXT REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    character_id TEXT REFERENCES characters(character_id) ON DELETE SET NULL,
    request_json JSONB NOT NULL,
    response_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS validated_state_changes (
    proposal_id TEXT PRIMARY KEY REFERENCES ai_validation_records(proposal_id) ON DELETE CASCADE,
    changes_json JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS validation_failures (
    failure_id BIGSERIAL PRIMARY KEY,
    at TIMESTAMPTZ NOT NULL,
    route TEXT,
    status INTEGER,
    message TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS admin_events (
    event_id BIGSERIAL PRIMARY KEY,
    at TIMESTAMPTZ NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS rewards (
    reward_id TEXT PRIMARY KEY,
    campaign_id TEXT REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    character_id TEXT REFERENCES characters(character_id) ON DELETE SET NULL,
    source TEXT NOT NULL,
    payload JSONB NOT NULL,
    granted_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS idempotency_records (
    campaign_id TEXT NOT NULL REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    idempotency_key TEXT NOT NULL,
    proposal_id TEXT,
    action_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (campaign_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS parties (
    party_id TEXT PRIMARY KEY,
    owner_account_id TEXT REFERENCES accounts(account_id) ON DELETE SET NULL,
    party_json JSONB NOT NULL
);
