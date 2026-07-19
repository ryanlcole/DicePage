# Known Issues

- The app is not production-ready.
- Local password accounts are not production SSO.
- Development mode still allows first local account to become Owner; production mode fails closed unless the Owner bootstrap token is configured.
- Deleting local development state can reopen development Owner bootstrap.
- Local persistence is JSON. Hosted staging requires PostgreSQL through Neon; production database hardening remains future work.
- No HTTPS, reverse proxy, process supervisor, or production logging stack is configured.
- `relicgamemaster.com` currently appears to point at a host that returns `404 Site Not Found`; HTTPS certificate validation fails.
- External AI is not connected yet; current Game Master narration is deterministic fallback text.
- Multiplayer models exist, but real-time cooperative play is not active.
- Admin console is minimal and development-focused.
- Payment and monetization systems are placeholder data only.
- Placeholder SVG art is not final production artwork.
- The repository contains checked-in dependencies, binaries, build outputs, and existing runtime logs that should be reviewed before any public release.
- A single mobile verifier rerun had a transient browser `fetch` failure after combat; immediate rerun passed and the server remained healthy.
- Koyeb and Neon staging resources are not provisioned yet; local credentials and CLIs are absent.
- PostgreSQL tests are unit/migration-surface checks on this PC because no isolated local PostgreSQL service is available.
- Hosted staging must be verified through Koyeb's generated HTTPS domain before any DNS change for `staging.relicgamemaster.com`.
