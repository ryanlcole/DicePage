# Security

## Current Scope

This is a local PC-hosted MVP. It is hardened enough for local vertical-slice testing, but it is not production-ready.

## Implemented Protections

- Passwords are hashed with `werkzeug.security.generate_password_hash`.
- Sessions use secure random server-side tokens.
- Session token is sent as an HttpOnly cookie.
- Cookie has `SameSite=Lax` and `Max-Age`.
- Cookie adds `Secure` automatically when `SHAELVIEN_LITE_ENV=production`.
- State-changing browser requests require `X-CSRF-Token`.
- Logout invalidates the server-side session and clears the cookie.
- Account ownership checks protect characters and campaigns.
- Owner-only routes protect admin functions.
- Production owner bootstrap fails closed unless a server-side token is configured and supplied once.
- Server generates dice rolls and combat results.
- Server validates quest transitions, rewards, inventory changes, camp upgrades, and combat targets.
- Duplicate idempotency keys do not double-apply state-changing actions.
- AI response schema validation rejects malformed or forbidden output.
- Rendered AI/user text is escaped or assigned with `textContent`.
- Request body size limit is enforced.
- Authentication and game-action routes are rate-limited in memory.
- Player-safe errors are returned to the browser.
- Internal exceptions are written to `logs/shaelvien_lite_errors.jsonl`.

## Owner Bootstrap

Development:

- First account becomes Owner.
- This is acceptable only for local PC hosting.
- Deleting local state reopens development bootstrap.

Production:

- Set `SHAELVIEN_LITE_ENV=production`.
- First visitor does not become Owner.
- Owner requires `SHAELVIEN_LITE_OWNER_BOOTSTRAP_TOKEN`.
- Token is compared server-side with constant-time comparison and then marked used.
- Do not embed the token in client code.
- Do not deploy a development state file unless existing Owner roles have been reviewed and explicitly approved.

The server update lock serializes local account creation, reducing simultaneous first-account risk for the single-process local server.

## Known Security Limits

- No TLS is provided by the Python dev server.
- JSON state is not a hardened production database.
- Sessions have no cleanup job or absolute server-side expiration yet.
- Rate limiting is in memory and resets on process restart.
- CORS is local-development oriented and must be restricted before public hosting.
- No external identity provider, email verification, password reset, or MFA exists.
- The repository includes many checked-in dependencies and binaries that need separate security review before public deployment.
- Production mode intentionally fails startup until a production database backend is implemented and configured.

## External AI Rules

When an external AI service is added:

- keep API keys server-side only;
- rate-limit AI calls;
- validate model output against the schema;
- never allow narration to mutate authoritative state;
- log validation failures without exposing prompts or internals to players;
- use deterministic fallback narration when the AI path fails.

## Before Internet Exposure

Required before public hosting:

- HTTPS through a real reverse proxy or hosting service;
- production database and backup/restore process;
- hardened session lifecycle and secret rotation;
- production Owner setup procedure;
- dependency and binary audit;
- stricter CORS and security headers;
- process supervision and structured log rotation;
- staging deployment and rollback procedure.
