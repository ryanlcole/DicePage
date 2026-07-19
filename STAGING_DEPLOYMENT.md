# Staging Deployment

Target staging architecture:

```text
Koyeb Free Web Service
Neon Free PostgreSQL
staging.relicgamemaster.com
```

This document is written for the `deployment/koyeb-neon-staging` branch. Do not alter `relicgamemaster.com` DNS during generated-domain testing.

## Zero-Cost Verification

Checked from official public docs on 2026-07-18:

- Koyeb Free Instance: free Web Service, 512 MB RAM, 0.1 vCPU, 2 GB SSD, one Free Instance per organization, Washington D.C. or Frankfurt, scales to zero after one hour without traffic, no persistent volumes.
- Neon Free: $0/month, no credit card required, 100 CU-hours/project/month, 0.5 GB storage/project, 5 GB public transfer, 6-hour restore window, scale-to-zero after five minutes, free limits suspend service rather than silently billing.

Stop before provisioning if either dashboard requires a paid instance, paid database, paid storage, automatic paid overages, or a trial that converts to paid.

## Current Blocker

No Koyeb CLI, Neon CLI, `DATABASE_URL`, Koyeb API token, or Neon credentials are present locally. The code and branch can be prepared and pushed, but resource creation requires Owner dashboard/API access.

## Koyeb Service

Planned names:

```text
App: shaelvien-lite-staging
Service: web
Branch: deployment/koyeb-neon-staging
Instance: Free
Region: Washington, D.C. when available
```

Repository source:

```text
https://github.com/ryanlcole/DicePage.git
```

Build:

```text
pip install -r requirements.txt
```

Start command:

```text
gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 45 shaelvien_lite.wsgi:app
```

Health check:

```text
/ready
```

Do not attach a persistent volume. Do not enable autoscaling beyond the single Free Instance.

## Neon Database

Planned project:

```text
Project: Shaelvien Lite Staging
Database: shaelvien_lite_staging
Connection: pooled PostgreSQL connection string with sslmode=require
```

Use a project dedicated to Shaelvien Lite staging. Do not share a database with another project. Do not commit or paste the connection string.

## Environment Variables

Set secrets through Koyeb secret/environment management. Values below are names and placeholders only:

```text
SHAELVIEN_ENV=staging
SHAELVIEN_STORAGE_BACKEND=postgres
SHAELVIEN_EXTERNAL_HOST=staging.relicgamemaster.com
SHAELVIEN_EXTERNAL_SCHEME=https
SHAELVIEN_SECURE_COOKIES=1
SHAELVIEN_TRUST_PROXY_HEADERS=1
SHAELVIEN_OWNER_BOOTSTRAP_TOKEN=<secret>
SHAELVIEN_INVITE_REQUIRED=1
SHAELVIEN_INVITE_CODE=<secret>
SHAELVIEN_SESSION_SECRET=<secret>
SHAELVIEN_CSRF_SECRET=<secret>
SHAELVIEN_DEPLOYMENT_VERSION=b7e8cf6-koyeb-neon
SHAELVIEN_RUN_MIGRATIONS_ON_STARTUP=1
SHAELVIEN_MAX_STAGING_ACCOUNTS=25
SHAELVIEN_MAX_CAMPAIGNS_PER_ACCOUNT=2
SHAELVIEN_MAX_CHARACTERS_PER_ACCOUNT=4
SHAELVIEN_MAX_RETAINED_COMBAT_LOGS=500
SHAELVIEN_MAX_RETAINED_AI_RECORDS=200
DATABASE_URL=<Neon pooled connection string with sslmode=require>
PYTHONUNBUFFERED=1
```

## Database Commands

Use these only with `SHAELVIEN_STORAGE_BACKEND=postgres` and `DATABASE_URL` set locally:

```powershell
python scripts/shaelvien_db.py migration-status
python scripts/shaelvien_db.py migrate
python scripts/import_json_to_postgres.py --source data/shaelvien_lite_state.json
```

The JSON import command refuses to overwrite an existing database unless `--allow-existing` is supplied after explicit Owner approval.

## Generated-Domain Verification

Deploy and verify the Koyeb-generated HTTPS hostname before DNS changes:

```text
GET /health
GET /ready
Landing page
Invite-gated account registration
Login and logout
Owner bootstrap
Character creation
Tutorial start
NPC interaction
Skill check
Combat victory
Reward issuance
Camp upgrade
Reconnect
Koyeb redeploy
State recovery from Neon
Sleep and wake
Mobile-width journey
```

## Custom Domain Preparation

Only after generated-domain verification passes, add `staging.relicgamemaster.com`.

Before DNS changes, report:

- exact DNS record type supplied by Koyeb;
- exact host/name;
- exact target;
- existing conflicting records, if any;
- expected Koyeb certificate behavior;
- rollback steps.

Do not guess the DNS target and do not modify root-domain records.

## Manual Backup

Backups must be created outside the repository:

```powershell
python scripts/export_staging_backup.py --output <outside-repo-path>\shaelvien-lite-staging.dump
```

Schedule:

- before each deployment;
- after major playtest sessions;
- before schema migrations.

A restoration test is required before public beta.
