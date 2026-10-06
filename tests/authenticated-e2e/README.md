# Isolated authenticated private-UI tests

This is a disposable local harness, **not a production login mechanism**. It runs the actual Discord-session and platform-authority Lambda handlers against Moto in-memory DynamoDB/S3. The real built Blazor application calls those handlers over loopback. All authenticated API requests still validate the real hashed-session schema, expiry, ownership, memberships and permissions. No private API response is mocked or replaced with an unconditional authorization result.

Production Discord OAuth requires an interactive Discord account ceremony and must not be bypassed. For automated local tests the harness seeds expiring normal session records out of band in disposable storage. Its two visibly named AINPC test identities are not real people, neither is the platform owner, and only the GM fixture receives the existing GM entitlement and a GM membership for `e2e-shared`. The ordinary user is a PC. Creation of a new sandbox world still uses the normal UI and existing ownership path.

## Architecture and authority

| Concern | Authoritative source |
| --- | --- |
| Discord OAuth, state, provider exchange, UUID identity, opaque session, single-use handoff, logout, storage namespace | `infra/aws/rist-discord-storage.yml` InlineCode |
| Session reaching browser | `wwwroot/rist.js` sessionStorage; `DiscordAuthClient.cs` verifies `/me` and loads private profile |
| Private application entry | `Components/AuthenticatedWorld.razor`; guests redirect to `/Play/index.html` |
| Server identity, GM/owner membership, platform owner and entitlements | `infra/aws/rist-platform-authority/app.py` |
| Frontend trusted authority | `WorldSession.WorldAuthority.cs`, `AwsAuthorityClient.cs` |
| Contextual permission system | `RecursiveAuthority.cs`, `AUTHORITY_SYSTEM.md` |
| Private screens | `/Game/`, `/Game/index.html`; universal role/environment/builder screens are component stages, not separate URL routes |
| Launcher | `/Launcher/index.html` and `/Game/Launcher/index.html`; release controls fail closed without release authority |

Existing automation includes C#/Python/Node contracts and a CDP tutorial script for Shaelvien Lite; none found provides an authenticated RIST browser session. This harness reuses existing AWS/session authority instead of adding a second identity provider to the application.

`Playwright.storageState` does not preserve sessionStorage. `auth-state.cjs` therefore restores only the existing three sessionStorage keys with an origin-scoped init script and verifies `/me` before opening the private application. It never creates a production cookie, URL bypass or query parameter.

## Run

Requirements: .NET 10 SDK, Python 3.12+, Node 22+, Playwright Chromium and its Linux dependencies. From the repository root:

```sh
python3 -m pip install -r tests/authenticated-e2e/requirements.txt
npm ci --prefix tests/authenticated-e2e
(cd tests/authenticated-e2e && npx playwright install --with-deps chromium)
python3 -m pytest tests/authenticated-e2e/test_security.py -q
export SHAELVIEN_TEST_AUTH=1 SHAELVIEN_ENVIRONMENT=test
export DOTNET_ENVIRONMENT=Development NODE_ENV=test
python3 tests/authenticated-e2e/build_local.py
npm test --prefix tests/authenticated-e2e
npm run audit --prefix tests/authenticated-e2e
```

The browser runner starts/stops the loopback server in the same process environment. This also works in environments where different shell invocations use different network namespaces. A separately installed compatible headless Chromium may be selected with `SHAELVIEN_E2E_CHROMIUM=/absolute/path/to/headless_shell`. That setting changes the test browser, not application authentication. For a sandbox that forbids MSBuild Unix-socket task hosts, set `SHAELVIEN_E2E_WASM_IN_PROCESS=1` before `build_local.py`; it uses the exact restored .NET WebAssembly SDK task assemblies in process and writes its override only into ignored test output. Normal environments and CI do not need this option.

`npm test` checks authenticated entry/reload, guest direct-route rejection, locked Launcher controls and private API rejection. `npm run audit` additionally drives the actual interface at 375×667 with mobile/touch context, captures important states, records controls/geometry, creates disposable data, checks owned-world persistence, and captures desktop state. It deliberately exits nonzero for detected UI/resource failures. An audit failure must not be described as a successful feature test. Extend journeys from observed normal UI controls as blockers are repaired; never force clicks, modify application state or weaken authorization to make the suite green. The keyboard-only diagnostic continuation is explicitly recorded when pointer creation is obstructed.

Evidence is written to `.e2e-runtime/evidence-public/`: screenshots and redacted JSON only. Query strings, session headers, response bodies, signed URLs and raw Playwright traces are not recorded. Do not upload the rest of `.e2e-runtime/`. The CI job has `contents: read`, no AWS role, no OIDC, no production credentials, and uploads only that evidence directory.

## Fail-closed boundaries

All four settings above, literal `127.0.0.1`, a Debug build, and the isolated test-build marker must match. A production environment or Release configuration is rejected before storage imports or socket binding. `SHAELVIEN_TEST_AUTH=1` alone is insufficient. Browser requests to any other origin are blocked. Host and Origin validation reject rebinding and cross-origin writes. The server exposes no session-minting route; state travels only through private files with mode 0600. Sessions expire after 15 minutes and are deleted from disk at runner shutdown. AWS credentials are overwritten with Moto-only dummy values before clients are constructed.

Fixture code exists only under `tests/`, outside frontend/CloudFormation publishing sources. Production handlers and frontend never read the test-auth flag. Removing the harness or unsetting its configuration restores ordinary authentication because application authentication was never changed. Authentication state, dependencies, build output and test results are Git-ignored. No reusable token or password is in source control.

Moto and the local capability transport emulate storage. They do **not** prove live AWS SigV4 enforcement, Discord OAuth, deployed CloudFront behavior, real iOS Safari rendering, or production functionality. Do not point this harness at AWS resources or deploy its files. The separate production authority fix only removes local-variable shadowing; it does not change permission decisions.

See `AUDIT.md`, `REPAIR_PROMPT.md`, and `baseline-evidence/` for the actual verified run and unresolved findings.
