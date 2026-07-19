# Development Log

## 2026-07-18 - Initial Vertical Slice

Repository findings:

- `DicePage` is a Python/ShaelvienOS runtime repo, not a Node web app.
- No existing production website framework was found.
- Existing local web code is `shaelvien_web3d.py`, a stdlib WebGL viewer.
- The current Shaelvien Lite target is local PC hosting.
- `relicgamemaster.com` was observed returning an Azure-style `404 Site Not Found`, but Azure was explicitly ruled out for this phase.
- GitHub repo cloned from `https://github.com/ryanlcole/DicePage.git`.
- Chrome was opened to `https://github.com/login` for user-managed sign-in/autofill.

Implemented:

- isolated `shaelvien_lite/` module;
- local HTTP server;
- account entry and server-side sessions;
- primary character creation;
- hero cards and full character sheet;
- tutorial campaign;
- Emberhall Outpost and four adventure locations;
- six persistent NPC templates copied into campaign state;
- data-driven roles, items, equipment, enemies, quests, and camp structures;
- deterministic d20 checks;
- minimal turn-based combat;
- inventory, rewards, currency, resources;
- camp upgrades;
- session logs with visible roll records;
- AI-GM structured response schema;
- owner-only admin snapshot and toggles;
- placeholder entitlement catalog;
- cooperative party data model;
- local JSON persistence;
- automated tests.

## 2026-07-18 - Verification And Hardening

Hardening completed:

- Added password hashing and password-required account entry.
- Replaced browser-visible session token storage with HttpOnly cookie sessions.
- Added CSRF token validation for state-changing browser requests.
- Added persistent cookie lifetime so browser close/reopen resumes correctly.
- Added production owner-bootstrap fail-closed behavior with environment token support.
- Added auth rate limiting and retained game-action rate limiting.
- Added duplicate idempotency-key protection for player actions.
- Tightened combat turn enforcement and invalid target rejection.
- Confirmed rewards are server-issued and completed encounters cannot be farmed.
- Added malformed state recovery.
- Expanded AI response validation fixtures.
- Added visible Chrome UI journey verifier.
- Fixed mobile tab overflow and tab-change scroll position.

Verification commands:

```text
python -m unittest tests.test_shaelvien_lite -v
```

Result: 30 tests passing.

Visible UI evidence:

- Desktop journey passed: `verification/ui-journey-report.json`.
- Server restart/browser reconnect passed: `verification/ui-reconnect-report.json`.
- Mobile viewport journey passed: `verification/ui-mobile-report.json`.

Generated verification artifacts are ignored by Git.

## 2026-07-18 - Version Freeze Preparation

Baseline preservation:

- Tests passed before release-prep changes: 30/30.
- Local site returned HTTP 200 at `http://127.0.0.1:8790`.
- Git branch: `main`.
- Git remote: `origin https://github.com/ryanlcole/DicePage.git`.
- Git author identity source: existing repository commit metadata.
- Repository-local author configured: `ryanlcole <relic.gamemaster@gmail.com>`.

Release-prep changes:

- Added direct dependency pin in `requirements.txt`.
- Added non-secret `.env.example`.
- Added explicit environment modes: development, testing, staging, production.
- Added fail-closed staging/production startup validation.
- Added reverse-proxy configuration points.
- Added `/health` and `/ready`.
- Added staging readiness and staging deployment documentation.
- Added production persistence, authentication, supervision, HTTPS, backup, and rollback planning.

Release identifier planned after commit:

- Tag: `shaelvien-lite-v0.1.0-local`.
- Known blockers: production DNS/HTTPS mismatch, unconfirmed Microsoft/Azure-side resource ownership, no production database, no production identity provider, no process supervisor.

## 2026-07-18 - Koyeb/Neon Staging Preparation

Branch:

- `deployment/koyeb-neon-staging`

Baseline:

- Commit: `b7e8cf6c1e87f2b0aaed7f51291a623d747225b1`
- Tag: `shaelvien-lite-v0.1.0-local`

Work completed locally:

- Added PostgreSQL storage backend for Koyeb/Neon staging.
- Added ordered PostgreSQL migration `001_initial_postgres.sql`.
- Added JSON-to-PostgreSQL import command.
- Added manual PostgreSQL backup command.
- Added WSGI entrypoint for Gunicorn.
- Added invite-gated staging account registration.
- Added Koyeb/Neon environment variable documentation.
- Preserved JSON storage for local development.

External resource status:

- Koyeb and Neon resources were not created from this machine.
- No Koyeb CLI, Neon CLI, Koyeb token, Neon credentials, or `DATABASE_URL` were present locally.
- Owner dashboard/API access is required before generated-domain deployment can proceed.
