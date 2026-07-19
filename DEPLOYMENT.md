# Deployment

## Current Targets

Local target: PC hosting with JSON storage.

Staging target: Koyeb Free Web Service plus Neon Free PostgreSQL on `staging.relicgamemaster.com`.

Implemented local URL:

```text
http://127.0.0.1:8790
```

Azure is not the intended host for this phase. Public DNS still appears to point somewhere that returns an Azure-style missing-site response, so production DNS/hosting must be corrected separately.

## Current Public Domain Observation

Observed on 2026-07-18:

- `relicgamemaster.com` resolves to A record `20.49.104.19`.
- `http://relicgamemaster.com` returns `HTTP/1.1 404 Site Not Found`.
- `https://relicgamemaster.com` fails certificate validation with a target-principal/certificate-name mismatch.

No repository deployment file such as `.openai/hosting.json`, reverse proxy config, IIS binding, nginx config, or production process supervisor configuration was found for Shaelvien Lite.

## Local Run

```powershell
cd <repo-root>
python -m pip install -r requirements.txt
python run_shaelvien_lite.py
```

Optional explicit state file:

```powershell
$env:SHAELVIEN_LITE_STATE="data\shaelvien_lite_state.json"
python run_shaelvien_lite.py
```

## Koyeb Staging Run

Koyeb must use the WSGI entrypoint, not the local `http.server` launcher:

```text
gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 45 shaelvien_lite.wsgi:app
```

Hosted staging storage must be PostgreSQL:

```text
SHAELVIEN_ENV=staging
SHAELVIEN_STORAGE_BACKEND=postgres
DATABASE_URL=<Neon pooled connection string>
```

The app fails startup if staging is configured without PostgreSQL, HTTPS settings, Owner bootstrap token, invite code, session secret, CSRF secret, or `DATABASE_URL`.

## LAN Hosting

For a trusted local network only:

```powershell
$env:SHAELVIEN_LITE_HOST="0.0.0.0"
$env:SHAELVIEN_LITE_PORT="8790"
python run_shaelvien_lite.py
```

Do not expose this directly to the internet. Use TLS, a reverse proxy, process supervision, backups, and production auth before public access.

## Environment Variables

- `SHAELVIEN_LITE_HOST`
- `SHAELVIEN_LITE_PORT`
- `SHAELVIEN_LITE_STATE`
- `SHAELVIEN_LITE_ENV`
- `SHAELVIEN_LITE_OWNER_BOOTSTRAP_TOKEN`
- `SHAELVIEN_LITE_OWNER_CODE`
- `SHAELVIEN_LITE_EXTERNAL_SCHEME`
- `SHAELVIEN_LITE_EXTERNAL_HOST`
- `SHAELVIEN_LITE_TRUST_PROXY_HEADERS`
- `SHAELVIEN_LITE_SECURE_COOKIES`
- `SHAELVIEN_LITE_MAX_REQUEST_BYTES`
- `SHAELVIEN_LITE_REQUEST_TIMEOUT_SECONDS`
- `SHAELVIEN_LITE_STORAGE_BACKEND`
- `SHAELVIEN_LITE_STAGING_ALLOW_JSON`
- `SHAELVIEN_LITE_BACKUP_PATH`
- `SHAELVIEN_LITE_VERBOSE_HTTP`
- `SHAELVIEN_ENV`
- `SHAELVIEN_STORAGE_BACKEND`
- `DATABASE_URL`
- `SHAELVIEN_INVITE_REQUIRED`
- `SHAELVIEN_INVITE_CODE`
- `SHAELVIEN_SESSION_SECRET`
- `SHAELVIEN_CSRF_SECRET`
- `SHAELVIEN_DEPLOYMENT_VERSION`
- `SHAELVIEN_RUN_MIGRATIONS_ON_STARTUP`
- `SHAELVIEN_MAX_STAGING_ACCOUNTS`
- `SHAELVIEN_MAX_CAMPAIGNS_PER_ACCOUNT`
- `SHAELVIEN_MAX_CHARACTERS_PER_ACCOUNT`

## Environment Modes

Development:

- local HTTP is permitted;
- first-account Owner bootstrap is enabled;
- deterministic AI fallback is enabled;
- local JSON state is permitted.

Testing:

- use isolated test state;
- no external services are required;
- deterministic random sources are injected by tests when needed.

Staging:

- startup requires HTTPS external scheme, external host, secure cookies, Owner bootstrap token, invite code, session secret, CSRF secret, and PostgreSQL storage;
- development first-account Owner bootstrap is disabled;
- JSON storage is rejected for hosted staging;
- registration is invite-gated server-side.

Production:

- requires PostgreSQL or a production database backend;
- first-account Owner bootstrap is disabled;
- HTTPS, secure cookies, explicit Owner setup, backups, and production data store are required.

## Reverse Proxy Readiness

Implemented configuration points:

- bind host: `SHAELVIEN_LITE_HOST`;
- internal port: `SHAELVIEN_LITE_PORT`;
- external scheme: `SHAELVIEN_LITE_EXTERNAL_SCHEME`;
- external host: `SHAELVIEN_LITE_EXTERNAL_HOST`;
- secure cookie mode: `SHAELVIEN_LITE_SECURE_COOKIES`;
- trusted proxy-header switch: `SHAELVIEN_LITE_TRUST_PROXY_HEADERS`;
- maximum request size: `SHAELVIEN_LITE_MAX_REQUEST_BYTES`;
- request timeout: `SHAELVIEN_LITE_REQUEST_TIMEOUT_SECONDS`;
- health check: `/health`;
- readiness check: `/ready`.

`/health` confirms the process responds. `/ready` confirms state initialization/storage access without exposing paths, accounts, sessions, or secrets.

## Recommended Deployment Path

Recommended now:

1. Continue local-only PC hosting for Owner review.
2. Create a staging host before production.
3. Prefer `staging.relicgamemaster.com` if DNS can be safely managed.
4. Keep the public root domain unchanged until staging is verified.
5. Add a reverse proxy with HTTPS.
6. Use Neon PostgreSQL for private staging; keep JSON only for local development.
7. Configure `SHAELVIEN_LITE_ENV=production`.
8. Configure Owner bootstrap through an environment secret.
9. Run automated and visible UI tests against staging.
10. Take a state backup before promoting production.

## Rollback

Local rollback:

- Stop `run_shaelvien_lite.py`.
- Restore the prior JSON state file from backup, if needed.
- Check out the backup branch `backup/shaelvien-lite-preverify-20260717-232622` if code rollback is required.

Production rollback is blocked until a real deployment target and versioned release procedure exist.
