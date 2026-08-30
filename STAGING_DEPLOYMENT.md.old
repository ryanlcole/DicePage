# Staging Deployment

This document intentionally avoids guessed provider-specific commands. Fill exact commands only after the staging host is identified and Owner access is confirmed.

## Preferred Staging Hostname

Preferred:

```text
staging.relicgamemaster.com
```

Acceptable alternative:

```text
playtest.relicgamemaster.com
```

Do not create DNS records until:

- the hosting target exists;
- HTTPS can be issued correctly;
- the staging app is running;
- rollback is documented.

## Current Evidence

Observed on 2026-07-18:

- `relicgamemaster.com` resolves to `20.49.104.19`.
- `20.49.104.19` is reported by public IP metadata as `AS8075 Microsoft Corporation`.
- HTTP and HTTPS direct checks return `404 Site Not Found`.
- HTTPS for `relicgamemaster.com` has a certificate-name mismatch.
- No repository deployment config for Shaelvien Lite was found.

Provider/resource type remains unresolved until the Owner checks the relevant hosting dashboard.

## Required Runtime

- Python 3.12 or newer.
- `pip install -r requirements.txt`.
- Startup command: `python run_shaelvien_lite.py`.
- Internal bind host/port from `SHAELVIEN_LITE_HOST` and `SHAELVIEN_LITE_PORT`.
- Reverse proxy terminates HTTPS and forwards to the internal port.

## Required Staging Environment

Example values only:

```text
SHAELVIEN_LITE_ENV=staging
SHAELVIEN_LITE_HOST=127.0.0.1
SHAELVIEN_LITE_PORT=8790
SHAELVIEN_LITE_STATE=<non-repository-state-path>
SHAELVIEN_LITE_EXTERNAL_SCHEME=https
SHAELVIEN_LITE_EXTERNAL_HOST=staging.relicgamemaster.com
SHAELVIEN_LITE_SECURE_COOKIES=1
SHAELVIEN_LITE_OWNER_BOOTSTRAP_TOKEN=<server-side-secret>
SHAELVIEN_LITE_STORAGE_BACKEND=json
SHAELVIEN_LITE_STAGING_ALLOW_JSON=1
SHAELVIEN_LITE_BACKUP_PATH=<staging-backup-path>
```

JSON storage is acceptable only for a private single-user staging demonstration. Multi-user staging should use the planned PostgreSQL adapter.

## Staging Smoke Test

After deployment:

```powershell
python -m unittest tests.test_shaelvien_lite -v
```

External checks:

```text
GET https://staging.relicgamemaster.com/health
GET https://staging.relicgamemaster.com/ready
```

Manual checks:

- create account;
- create character;
- begin tutorial;
- speak with Ilyra;
- accept quest;
- travel to Forest Road;
- complete check;
- complete combat;
- receive rewards;
- return to camp;
- upgrade Quarters;
- close browser;
- reopen and continue.

## Unresolved Provider-Specific Steps

Do not fill these until the actual host is confirmed:

- DNS record type and target.
- Certificate issuer and renewal mechanism.
- Reverse proxy configuration.
- Process supervisor.
- Log location.
- Backup command.
- Deployment package format.
- Restart command.
- Rollback command.
