# ReLiC Game Master - Shaelvien Lite

Shaelvien Lite is a local PC-hosted early vertical slice for an AI-operated tabletop RPG and virtual tabletop. The implementation is isolated under `shaelvien_lite/` so existing ShaelvienOS runtime files, checked-in dependency folders, build outputs, and executables are not replaced.

## Current Status

Implemented:

- Local PC hosting at `http://127.0.0.1:8790`.
- Public landing page, account entry, character creation, dashboard, game screen, character sheet, inventory, quest log, camp screen, party placeholder, settings, and owner console.
- One tutorial region, Emberhall Outpost, four adventure locations, six persistent NPC templates, five quests, starting roles, items, enemies, and camp structures.
- Deterministic server-side checks, combat, rewards, quest transitions, camp upgrades, session log persistence, and fallback AI-GM narration.
- Local JSON persistence with atomic file replacement.
- Password-hashed local accounts, server-side sessions, HttpOnly cookies, SameSite, CSRF token checks, and production owner-bootstrap fail-closed behavior.

Development-only or partial:

- Account auth is a local password account system, not production SSO.
- JSON persistence is acceptable for this PC-hosted MVP, but not for production concurrency.
- AI narration is deterministic fallback narration. No external AI provider is connected yet.
- Multiplayer data models exist, but real-time cooperative play is not active.
- Entitlements and product catalog records are placeholders only. No payments are active.
- Visual assets are licensed-safe SVG placeholders.

## Run Locally

```powershell
cd <repo-root>
python -m pip install -r requirements.txt
python run_shaelvien_lite.py
```

Open:

```text
http://127.0.0.1:8790
```

By default the app binds to `127.0.0.1` and uses `data/shaelvien_lite_state.json`.

## Koyeb/Neon Staging

Staging runs from branch `deployment/koyeb-neon-staging` with Koyeb Free Web Service and Neon Free PostgreSQL.

Start command:

```text
gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 45 shaelvien_lite.wsgi:app
```

Required staging settings are documented in `STAGING_DEPLOYMENT.md`. Hosted staging must use:

```text
SHAELVIEN_ENV=staging
SHAELVIEN_STORAGE_BACKEND=postgres
DATABASE_URL=<Neon pooled connection string>
```

Do not commit database URLs, invite codes, Owner bootstrap tokens, session secrets, CSRF secrets, or backups.

## Account And Owner Notes

Development mode:

- The first local account becomes Owner.
- Later local accounts are ordinary players.
- If local state is deleted, development owner bootstrap can happen again.

Production mode:

- Set `SHAELVIEN_LITE_ENV=production`.
- Owner status is not granted to the first visitor.
- Owner bootstrap requires `SHAELVIEN_LITE_OWNER_BOOTSTRAP_TOKEN` to be configured server-side and supplied once through the account-entry request.
- Do not put the Owner token in client code or the repository.

## Clean Checkout Startup

Requirements:

- Python 3.12 or newer. The verified local machine currently uses Python 3.14.2.
- Direct dependencies: `Werkzeug==3.1.3`, `gunicorn==26.0.0`, and `psycopg[binary]==3.3.4`.

From a clean checkout:

```powershell
cd <repo-root>
python -m pip install -r requirements.txt
Copy-Item .env.example .env.local -ErrorAction SilentlyContinue
python -m unittest tests.test_shaelvien_lite -v
python run_shaelvien_lite.py
```

Data-store initialization happens automatically when `GameStore` creates the configured JSON state file. Stop the app with `Ctrl+C` in the terminal running `python run_shaelvien_lite.py`, or stop the supervised process if running under a service wrapper.

## Test

Unit and integration tests:

```powershell
cd <repo-root>
python -m unittest tests.test_shaelvien_lite -v
```

Compile check:

```powershell
python -c "import pathlib, py_compile; files=[pathlib.Path('run_shaelvien_lite.py'), *pathlib.Path('shaelvien_lite').glob('*.py')]; [py_compile.compile(str(p), doraise=True) for p in files]; print('compiled', len(files), 'files')"
```

Visible Chrome journey test:

```powershell
$env:SHAELVIEN_LITE_URL="http://127.0.0.1:8790"
$env:SHAELVIEN_LITE_UI_PROFILE="<temporary-browser-profile-path>"
$env:SHAELVIEN_LITE_UI_REPORT="verification\ui-journey-report.json"
$env:SHAELVIEN_LITE_UI_PHASE="journey"
node tests\ui_tutorial_journey.mjs
```

The UI test uses Chrome DevTools Protocol and writes ignored evidence files under `verification/`.

## Environment Variables

- `SHAELVIEN_LITE_HOST`: host bind address. Default: `127.0.0.1`.
- `SHAELVIEN_LITE_PORT`: local port. Default: `8790`.
- `SHAELVIEN_LITE_STATE`: custom JSON state file path.
- `SHAELVIEN_LITE_ENV`: `development`, `testing`, `staging`, or `production`. Default: `development`.
- `SHAELVIEN_LITE_OWNER_BOOTSTRAP_TOKEN`: one-time production Owner bootstrap token.
- `SHAELVIEN_LITE_OWNER_CODE`: backward-compatible alias for the Owner bootstrap token.
- `SHAELVIEN_LITE_EXTERNAL_SCHEME`: external scheme used behind a proxy. Must be `https` in staging and production.
- `SHAELVIEN_LITE_EXTERNAL_HOST`: external host used behind a proxy. Required in staging and production.
- `SHAELVIEN_LITE_TRUST_PROXY_HEADERS`: reserved proxy-header trust switch. Default: `0`.
- `SHAELVIEN_LITE_SECURE_COOKIES`: secure cookie override. Defaults on in staging and production.
- `SHAELVIEN_LITE_MAX_REQUEST_BYTES`: JSON request body limit. Default: `128000`.
- `SHAELVIEN_LITE_REQUEST_TIMEOUT_SECONDS`: socket request timeout. Default: `30`.
- `SHAELVIEN_LITE_STORAGE_BACKEND`: local alias for storage backend.
- `SHAELVIEN_STORAGE_BACKEND`: `json` locally or `postgres` on Koyeb staging.
- `DATABASE_URL`: Neon PostgreSQL connection string; secret, staging only.
- `SHAELVIEN_INVITE_CODE`: private staging registration code; secret.
- `SHAELVIEN_SESSION_SECRET`: staging/production session secret placeholder; secret.
- `SHAELVIEN_CSRF_SECRET`: staging/production CSRF secret placeholder; secret.
- `SHAELVIEN_LITE_STAGING_ALLOW_JSON`: set to `1` only for private single-user staging with documented backups.
- `SHAELVIEN_LITE_BACKUP_PATH`: required for JSON-backed staging.
- `SHAELVIEN_LITE_VERBOSE_HTTP`: set to `1` for HTTP request logs.

Do not commit secrets, local databases, verification state, screenshots, or logs.

## Main Files

- `shaelvien_lite/server.py`: local stdlib HTTP server, cookies, CSRF, API routes, rate limiting, and player-safe errors.
- `shaelvien_lite/wsgi.py`: Koyeb/Gunicorn WSGI entrypoint.
- `shaelvien_lite/engine.py`: deterministic game state transitions.
- `shaelvien_lite/ai_gm.py`: AI response schema, sanitization, and deterministic fallback.
- `shaelvien_lite/store.py`: storage interface, JSON persistence, and backend factory.
- `shaelvien_lite/postgres_store.py`: PostgreSQL storage adapter and migration runner.
- `shaelvien_lite/seed_data.py`: provisional data-driven region, NPCs, roles, quests, items, enemies, camp structures, and entitlement placeholders.
- `shaelvien_lite/static/`: player interface and placeholder art.
- `tests/test_shaelvien_lite.py`: automated server/engine tests.
- `tests/ui_tutorial_journey.mjs`: visible Chrome tutorial verifier.

## Protected Boundaries

Do not modify existing ShaelvienOS runtime files unless the Owner explicitly directs it. Treated as protected/generated:

- `.venv/`
- checked-in dependency folders such as `flask/`, `jinja2/`, `werkzeug/`, `click/`, `blinker/`, `markupsafe/`
- `dist/`
- `build/`
- `.exe`, `.pyd`, `.obj`, `.lib`, `.exp` artifacts
- existing ShaelvienOS launcher/runtime scripts
