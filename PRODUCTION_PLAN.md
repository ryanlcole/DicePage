# Production Plan

Shaelvien Lite is not ready for public production. This plan defines the next engineering steps without changing the verified local gameplay scope.

## Database Plan

Preferred database: PostgreSQL.

Schema areas:

- users and account handles;
- password credentials and password history metadata;
- sessions with hashed token IDs;
- characters and character ownership;
- campaigns and party membership;
- quest state and objective state;
- inventory and equipment;
- combat state and completed encounters;
- camp structures and upgrades;
- session logs;
- audit logs;
- AI proposals, validation failures, and accepted state changes;
- entitlements and catalog records.

Migration approach:

- keep `GameStore` as the development adapter;
- define a storage interface used by API routes;
- implement a PostgreSQL adapter with migrations;
- use transactions for state-changing actions;
- add indexes for ownership, session lookup, campaign lookup, quest status, and audit timestamps;
- add backup and restore tests before public staging.

## Authentication Plan

Production auth must add:

- stronger password policy;
- email verification;
- password reset;
- account recovery;
- session expiration;
- session revocation;
- failed-login audit;
- login rate limiting backed by durable storage;
- secure cookies with HTTPS only;
- CSRF on browser state-changing requests;
- Owner recovery and role-assignment procedure;
- privacy and retention policy.

Email-dependent flows must wait for an Owner-approved email provider.

## Supervision Plan

Select only after the host type is known.

Required supervisor capabilities:

- automatic restart;
- startup on reboot;
- environment-variable injection;
- log capture;
- controlled shutdown;
- health monitoring;
- versioned deployment;
- rollback.

Candidate supervisors:

- Windows Service behind IIS reverse proxy;
- Azure App Service startup command if the Owner keeps Azure;
- Linux `systemd`;
- container service.

## HTTPS And Domain Plan

Tasks:

- identify the resource currently serving `20.49.104.19`;
- confirm Owner access or abandon the resource;
- create staging host before production;
- issue correct certificate for staging;
- configure HTTP-to-HTTPS redirect;
- set `SHAELVIEN_LITE_EXTERNAL_SCHEME=https`;
- enable secure cookies;
- verify `/health` and `/ready`;
- only then repeat for production;
- enable HSTS only after stable HTTPS.

## Backup And Rollback Plan

Application:

- tag releases;
- keep deployment packages;
- record startup command and environment;
- verify `/health`, `/ready`, and gameplay smoke test after deployment;
- document rollback command for the selected host.

Data:

- pre-deployment backup;
- encrypted scheduled backups;
- documented backup location;
- retention policy;
- restoration test.

Secrets:

- store outside Git;
- rotate on exposure;
- document replacement and revocation;
- restart supervised service after rotation.
