# Deployment

## Current Target

Current target: local PC hosting.

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

- startup requires HTTPS external scheme, external host, secure cookies, Owner bootstrap token, and explicit JSON-staging approval if using local JSON;
- development first-account Owner bootstrap is disabled;
- staging JSON requires a backup path and must remain private single-user.

Production:

- startup is intentionally blocked in this baseline until a production database backend is implemented and configured;
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
6. Move persistence to a production database.
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
