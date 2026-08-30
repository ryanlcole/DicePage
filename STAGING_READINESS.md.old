# Staging Readiness

Use this checklist before creating or changing any public DNS record.

- [ ] Verified Git commit exists.
- [ ] Release tag exists: `shaelvien-lite-v0.1.0-local`.
- [ ] Working tree is clean.
- [ ] No secret scan findings.
- [ ] Dependency pinning exists: `requirements.txt`.
- [ ] Environment modes implemented.
- [ ] Staging secrets are stored outside Git.
- [ ] Secure Owner bootstrap token is configured server-side.
- [ ] Staging database or approved private JSON state is configured.
- [ ] HTTPS is issued and valid for the staging hostname.
- [ ] Domain binding is configured for staging only.
- [ ] Reverse proxy passes requests to the internal Shaelvien Lite port.
- [ ] Process supervision is configured.
- [ ] `/health` and `/ready` pass from outside the host.
- [ ] Log capture is configured.
- [ ] Backup location is configured.
- [ ] Restoration procedure is documented.
- [ ] Rollback procedure is documented.
- [ ] Python test suite passes on staging build.
- [ ] Manual gameplay smoke test passes.
- [ ] Mobile smoke test passes.
- [ ] Accessibility baseline is rechecked.
- [ ] Owner deployment approval is recorded.

## Current Status

Ready locally:

- Shaelvien Lite source, tests, documentation, local JSON persistence, environment-mode validation, health checks, and staging planning.

Blocked:

- No staging host is identified.
- No staging DNS record exists.
- No staging certificate exists.
- No process supervisor is selected.
- No production-capable database exists.
- Current public domain points to a Microsoft/Azure-side missing-site response and must not be reused blindly.
