# Production Readiness

## Status

Shaelvien Lite is not production-ready.

It is ready for local Owner review on the PC-hosted server and for planning a controlled staging deployment.

## Current Deployment Findings

Observed on 2026-07-18:

- `relicgamemaster.com` DNS resolves to `20.49.104.19`.
- HTTP returns `404 Site Not Found`.
- HTTPS certificate validation fails with target-principal mismatch.
- Public IP metadata reports `20.49.104.19` under `AS8075 Microsoft Corporation`.
- Direct HTTP/HTTPS requests to `20.49.104.19` return `404 Site Not Found`.
- PTR lookup did not return a resource name in the local check.
- No Shaelvien Lite production web server, reverse proxy, process supervisor, deployment credentials, or staging config was found in the repository.
- No `.openai/hosting.json` file was found.

This appears to be a Microsoft/Azure-side missing-site or abandoned host binding, but the exact resource type and Owner dashboard access are unconfirmed. It should not be treated as a working production deployment target.

## Production Blockers

- DNS and host binding are not configured for the PC-hosted Shaelvien Lite app.
- HTTPS is not configured for the domain.
- The current Python server is suitable for local development, not direct internet exposure.
- Persistence is JSON instead of a production database.
- Local password auth lacks password reset, email verification, MFA, account recovery, and mature session expiration.
- Owner bootstrap needs an Owner-controlled deployment secret and setup procedure.
- External AI provider integration is not implemented.
- The repository needs dependency and binary review before release.
- No production backup, restore, log rotation, monitoring, or rollback procedure exists.

## Recommended Next Deployment Action

Use a staging target before touching production.

Preferred staging options:

- `staging.relicgamemaster.com` if DNS can be safely updated; or
- a private LAN/VPN-only host path for Owner review.

Minimum staging requirements:

- reverse proxy with HTTPS;
- process supervisor for the Python app;
- explicit `SHAELVIEN_LITE_ENV=production`;
- server-side `SHAELVIEN_LITE_OWNER_BOOTSTRAP_TOKEN`;
- fresh or reviewed production state, not an unchecked development state file;
- non-repository state/database location;
- backup path for state;
- log retention path;
- rerun automated tests and visible UI journey against staging.

## Production Persistence Plan

Preferred public database: PostgreSQL.

Migration plan:

- keep the current storage boundary so JSON remains available for development/testing;
- add a database adapter behind the same engine-facing store contract;
- create migrations for users, password credentials, sessions, characters, campaigns, quest state, inventory, combat state, camp upgrades, audit logs, AI proposals, AI validation records, and admin events;
- use transactions for quest/combat/reward/camp mutations;
- index account handle, account ID, session token hash, character owner, campaign owner, quest state, and audit timestamps;
- store session tokens hashed at rest in production;
- create backup and restore jobs before public staging;
- test restoration before accepting staging sign-off.

## Production Authentication Plan

The local password account baseline should expand before public launch:

- enforce password policy and breached-password checks;
- add email verification;
- add password reset through a configured email provider;
- define session expiration and revocation;
- add account recovery and Owner recovery procedures;
- preserve login rate limiting and add failed-login audit records;
- use secure cookies, SameSite, CSRF, and HTTPS only;
- assign admin roles through Owner-approved server-side workflows;
- document privacy handling and data retention.

Do not add email flows until an Owner-approved email provider is configured.

## Process Supervision Plan

Do not rely on a manually launched terminal for staging or production.

The supervisor must provide:

- automatic restart;
- startup on reboot;
- environment-variable injection;
- log capture;
- controlled shutdown;
- health monitoring against `/health` and `/ready`;
- versioned deployment;
- rollback.

The exact supervisor remains unresolved until the host type is confirmed. Candidate approaches are Windows Service/IIS reverse proxy, Azure App Service startup command, Linux `systemd`, or a container service.

## HTTPS Remediation Plan

Required sequence:

1. Identify and gain Owner access to the resource currently behind `20.49.104.19`, or abandon it.
2. Create a staging host first.
3. Bind `staging.relicgamemaster.com` or `playtest.relicgamemaster.com`.
4. Issue a correct staging certificate.
5. Configure reverse proxy external scheme/host and secure cookies.
6. Verify HTTP-to-HTTPS redirect.
7. Run tests and manual smoke checks.
8. Repeat for production only after staging passes.
9. Enable HSTS only after correct HTTPS routing is stable.

Do not alter current DNS during this phase.

## Backup And Rollback Plan

Application rollback:

- preserve previous commit and tag;
- keep previous deployment package;
- verify `/health`, `/ready`, and tutorial smoke test after rollback;
- check database migration compatibility before downgrade.

Data backup:

- take a pre-deployment snapshot;
- schedule encrypted backups;
- retain backups according to Owner policy;
- document backup location;
- perform restoration testing before launch.

Secrets recovery:

- keep secrets out of Git;
- rotate leaked or suspect values;
- document replacement and revocation steps;
- restart services after rotation.

## Local PC Hosting

Local use remains:

```text
http://127.0.0.1:8790
```

LAN testing can bind to `0.0.0.0`, but should remain on a trusted network until TLS, production auth, and a hardened database are in place.
