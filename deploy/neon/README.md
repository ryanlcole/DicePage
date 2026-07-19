# Neon Staging Notes

Create a dedicated Neon Free project:

```text
Project: Shaelvien Lite Staging
Database: shaelvien_lite_staging
Plan: Free
Connection: pooled PostgreSQL connection string with sslmode=require
```

Zero-cost requirements:

- Stay on the Free plan.
- Do not upgrade to Launch or Scale.
- Do not add paid read replicas.
- Do not create paid extra branches.
- Keep autosuspend/scale-to-zero enabled.
- Keep storage below free-plan limits.
- Review compute, storage, and transfer usage after each playtest.

After project creation, set `DATABASE_URL` only in Koyeb secrets or local shell environment. Never commit it.

Run migrations from a local trusted shell or through Koyeb startup only after confirming `DATABASE_URL` points at this staging database:

```powershell
$env:SHAELVIEN_STORAGE_BACKEND="postgres"
$env:DATABASE_URL="<secret>"
python scripts/shaelvien_db.py migrate
python scripts/shaelvien_db.py migration-status
```
