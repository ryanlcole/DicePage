# Architecture

## Repository Assessment

`DicePage` is a Python-heavy ShaelvienOS runtime repository. It contains local scripts, launcher/runtime files, a stdlib WebGL status viewer, checked-in dependency folders, generated build outputs, and executable artifacts. It is not a conventional Node, React, Next, Vite, or static-site repository.

The safest integration path is the current isolated module:

```text
shaelvien_lite/
  ai_gm.py
  engine.py
  seed_data.py
  server.py
  store.py
  static/
```

No existing ShaelvienOS runtime file has been modified.

## Existing Technology Stack

- Backend: Python, standard-library `ThreadingHTTPServer`.
- Frontend: static HTML, CSS, vanilla JavaScript.
- Password hashing: `werkzeug.security`.
- Persistence: local JSON file through `GameStore`.
- Test runner: Python `unittest`.
- Browser verification: Chrome DevTools Protocol script run by local Node.

No existing production website framework, production web server config, database schema, or deployment automation was found in the repo.

## Runtime Shape

- Static SPA files live under `shaelvien_lite/static/`.
- JSON APIs are exposed under `/api/*`.
- The browser sends player intent and selected records.
- The server validates account/session/CSRF/ownership and commits deterministic game state.
- The store serializes state-changing actions through a process-local lock and atomically replaces the JSON state file.

## Authority Boundaries

The browser cannot authoritatively grant:

- levels, experience, currency, items, quest completion, camp upgrades, victory, health restoration, owner access, or entitlements.

The AI-GM layer cannot directly control:

- account permissions, entitlements, random number generation, inventory ownership, currency balances, character statistics, payment status, or canonical world state.

The deterministic engine owns:

- dice, checks, quest transitions, combat resolution, rewards, inventory mutation, camp upgrades, location unlocks, and admin authorization.

## Local Data Flow

1. Browser enters account handle and password.
2. Server creates or resumes the account.
3. Server stores a secure random session and CSRF token.
4. Server sends an HttpOnly session cookie and returns the CSRF token to the page.
5. Browser stores only active character/campaign IDs in localStorage.
6. State-changing requests send `X-CSRF-Token`.
7. Server validates session, CSRF, ownership, route semantics, and game rules.
8. Server commits state and appends logs/proposals/validated state changes.
9. Browser reboots from `/api/bootstrap` and renders committed state.

## Reusable Components

- Existing Python runtime style made stdlib Python the lowest-risk integration point.
- Existing checked-in Flask/Werkzeug package files are present, but no active Flask app was found.
- `werkzeug.security` is reused for password hashing because it is already available in the repo tree.

## Protected Files

Protected unless Owner-approved:

- ShaelvienOS runtime scripts such as `shaelvien_daemon.py`, `shaelvien_launcher.py`, `shaelvien_terminal*.bat`, `shaelvien_web3d.py`, and related runtime modules.
- Build and installer outputs under `build/`, `dist/`, `installer/`, and executable/binary artifacts.
- Checked-in third-party dependency folders.
- Existing logs and runtime state unrelated to Shaelvien Lite.

## Major Risks

- Local JSON persistence is not a multi-user production database.
- Local password accounts are not production identity.
- Production DNS/hosting for `relicgamemaster.com` is not configured for this app.
- External AI is not connected yet.
- The repository contains many generated and third-party files, so commits must be narrowly staged.
