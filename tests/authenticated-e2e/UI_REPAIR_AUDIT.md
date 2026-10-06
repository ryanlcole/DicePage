# Authenticated private UI repair audit

Code base: `0f9aa9bcc0bef6ad5f088797e0869b99a92d84f3`, isolated branch `codex/private-ui-repairs`. The existing secure harness is retained. These are local runtime results, not AWS deployment or live-site verification.

## Authentication and safety

Discord OAuth is authoritative. The production Lambda validates provider/state/code and issues opaque, expiring sessions indexed in DynamoDB by SHA-256. `DiscordAuthClient` restores the existing sessionStorage keys, verifies `/me`, and obtains private storage capabilities. `AuthenticatedWorld` protects `/Game/` and `/Game/index.html`; the universal interface hosts private stages rather than distinct URLs. AWS authority handlers enforce memberships, ownership, roles, entitlements, and GM permissions. Frontend choice of GameMaster is not an authority grant.

The existing harness executes the real auth and authority handlers against Moto DynamoDB/S3. Sessions are generated out of band and verified by the real `/me`; browser setup restores the existing frontend keys. There is no login bypass endpoint, magic cookie, production token, authentication replacement, or production provider. Independent test/Development flags, loopback host restrictions, Debug marker and Release rejection remain. Test sessions, credentials and state stay in ignored `.e2e-runtime/.auth`, are mode 0600, and are deleted after runs. Production authorization source is unchanged by this repair.

## Verification

- Debug publish: passed, with the documented in-process SDK-task compatibility option for this sandbox.
- Release publish: passed; all five formerly missing canonical stylesheet sources occur in full in both published bundles. No production deployment performed.
- Security regressions: 27 passed. Existing platform-authority regressions: 26 passed. Compliance guardrails: passed. JavaScript syntax and Git whitespace checks: passed.
- Chromium mobile emulation: 375×667 and 320×568 with touch. Separate desktop context: 1280×800 with mouse. This is not physical iPhone/Safari verification.
- Auth-only verification: 8/8 checks passed, recorded in repair-evidence/authentication-report.json. Full audit: 14/15 checks passed. The full audit deliberately fails on the authoritative region-catalog rejection. HTTP 200, visual labels, and UI success text are not proof of authoritative persistence.

## Exercised flow

1. Guest direct `/Game/index.html` and `/Game/`: protected, redirected to `/Play/index.html`; private APIs returned 401. Guest Launcher controls remained locked.
2. Authenticated start and reload, normal user and GM: passed. Nested `/Game/Launcher/index.html`: authenticated, promotion/revocation disabled for both non-admin fixtures.
3. Roleplayer and GameMaster selection: reachable. Roleplayer showed the read-only encounter reference. Character/Dice/Replay/Chat placeholders are not verified implemented features.
4. World chooser: touch input created a disposable world, keyboard focus stayed in the dialog, and closing restored viewer input. World remained listed after reload.
5. Tier, layer, map-hex and vertical-boundary selection: reached through ordinary display controls and map touch.
6. Title editor: visible; Escape cancellation retained selection and retry succeeded without the old `prompt` crash. The UI reported a named region, but its authoritative catalog write failed (see below).
7. My Images: opened; its screenshot captures loading, not a confirmed completed library selection. The existing Add Image dialog opened. An existing repository PNG was uploaded through the normal file input, placed as a layer, resized through a touch control, and saved through Start → Save → Resume.
8. Reload in a separate desktop session: the world map source restored a committed region **label** and committed **image**. This proves source persistence, not persistence of region metadata. Editing a previously reloaded asset was not separately exercised.
9. 320×568: toolbar scrolled to Undo; its target measured at least 44×44 and was within the viewport. No document horizontal overflow was found in captured states. Embedded keyboard tabs remain visually small and need a complete touch-target audit.
10. Standalone `/Launcher/index.html`: authenticated after correcting its script path; release controls remained disabled. Release-control backend is absent in the fixture, so deployment functions were not exercised.

## Repairs and observed failures

| Failure | Repair / current result |
|---|---|
| World modal behind universal viewer; pointer controls blocked | Modal raised above viewer; focus containment and inert cleanup added; touch world creation passes. |
| Parent `prompt` replaced by an iframe function; region naming crashed | Explicit parent-module/child-composer bridge; parent global prompt untouched; ordinary title UI works. |
| Embedded CSS hides the title keyboard | Scoped visibility for requested title editor. |
| Parent context/legend panels cover embedded tools | Read-only visibility observer hides passive summaries while tools are open. |
| Image tab with a selected label reads undefined size (`toFixed`) | Image renderer treats labels as non-image selections; final run has no JavaScript exceptions. |
| Embedded image/sprite upload dialogs hidden | Existing dialogs allowed to render when opened; image upload exercised, sprite upload not exercised. |
| Five missing stylesheet requests | Canonical button-artwork-fit, character-universal, art-studio, art-surface-controls and asset-credit sources added to existing generated bundle; redundant PLC loads removed. No missing stylesheet requests in final audit. |
| Standalone Launcher requests missing `/rist.js` | Uses existing `/Game/rist.js`; real session verification passes. |
| Toolbar and Start/mode targets too small | Mobile minimum 44px targets and horizontal toolbar scrolling; last toolbar control reachable at 320px. This does not certify every control. |
| Exception screen clipped long technical message without recovery | Scrollable generic error surface and Reload button implemented and compiled. An artificial crash was not injected to certify this fallback at runtime. |
| **Region creation appears successful despite authority failure** | **Unresolved. POST and GET `/api/authority/world/regions` return 403 for the newly UI-created sandbox world. `AwsAuthorityClient.SendAsync` returns null on 401/403; `SaveRegionsAsync` does not check the returned region. The map label/image persist, but authoritative region catalog verification fails. Authorization was preserved.** |

The world-creation path writes private world references/checkpoints and refreshes trusted authority; the authority handler requires a server membership for region access. A missing/mismatched registration is a source-grounded hypothesis, not a proven production diagnosis. Reconcile the intended sandbox/authority contract instead of assigning an owner role or weakening `can_view`/`can_manage`.

Local/Instance creation and durable nested metadata are not verified: proceeding from a rejected region catalog would not establish valid hierarchy persistence. No purchases, token/deed transfer, world deletion, live private data, production sessions, live AWS resources, or release promotion/revocation were modified. The test account and database were disposable. No secret backdoor was created.

## Console and network

Final audit: 91 console error entries, 128 failed/non-success local transport records, zero page exceptions. Two unexpected authorization failures remain: the region POST and GET, both 403. Console errors primarily reflect the same known fixture 404s and authority denials; they are not described as clean.

Empty optional private JSON objects return 404; missing deployment-generated translation config is a local fixture limitation; interrupted navigation fetches record ERR_ABORTED. The report retains every raw redacted record and separates these expected fixture records. Object-image failures are not excluded as optional JSON reads. Fourteen external requests were deliberately blocked to isolate tests (music/terrain); live CDN and translation services were not verified. No bearer headers, cookies, body dumps, query secrets or traces are committed.

Evidence: [report.json](repair-evidence/report.json), plus the screenshot set below. All screenshots were inspected; the My Images loading capture is explicitly not accepted as completed-library proof.

## Run

Install the documented dependencies in [README.md](README.md), then:

```sh
export SHAELVIEN_TEST_AUTH=1 SHAELVIEN_ENVIRONMENT=test DOTNET_ENVIRONMENT=Development NODE_ENV=test
python3 tests/authenticated-e2e/build_local.py
python3 -m pytest tests/authenticated-e2e/test_security.py -q
npm test --prefix tests/authenticated-e2e
npm run audit --prefix tests/authenticated-e2e
```

For this sandbox only, set `SHAELVIEN_E2E_WASM_IN_PROCESS=1` for the build and `SHAELVIEN_E2E_CHROMIUM=/tmp/shaelvien-headless/chrome-linux/headless_shell` for browser runs. Normal CI uses standard SDK tasks and its package-matched browser. Start the server through the runner; it creates and cleans up sessions. The audit is expected to exit nonzero until region catalog authorization/persistence is correctly repaired.

## Screenshots

- [se-normal-user-roles](repair-evidence/se-normal-user-roles.png)
- [se-roleplayer](repair-evidence/se-roleplayer.png)
- [se-start](repair-evidence/se-start.png)
- [se-environment](repair-evidence/se-environment.png)
- [se-roles](repair-evidence/se-roles.png)
- [se-gamemaster](repair-evidence/se-gamemaster.png)
- [se-world-dialog](repair-evidence/se-world-dialog.png)
- [se-world-created](repair-evidence/se-world-created.png)
- [se-world-open](repair-evidence/se-world-open.png)
- [se-builder-0](repair-evidence/se-builder-0.png)
- [se-builder-1](repair-evidence/se-builder-1.png)
- [se-builder-2](repair-evidence/se-builder-2.png)
- [se-builder-3](repair-evidence/se-builder-3.png)
- [se-builder-4](repair-evidence/se-builder-4.png)
- [se-builder-5](repair-evidence/se-builder-5.png)
- [se-builder-6](repair-evidence/se-builder-6.png)
- [se-region-select](repair-evidence/se-region-select.png)
- [se-region-save-attempt](repair-evidence/se-region-save-attempt.png)
- [se-region-depth-0](repair-evidence/se-region-depth-0.png)
- [se-region-depth-1](repair-evidence/se-region-depth-1.png)
- [se-title-editor](repair-evidence/se-title-editor.png)
- [se-region-depth-2](repair-evidence/se-region-depth-2.png)
- [se-my-images](repair-evidence/se-my-images.png)
- [se-image-upload](repair-evidence/se-image-upload.png)
- [se-image-edited](repair-evidence/se-image-edited.png)
- [se-image-save](repair-evidence/se-image-save.png)
- [se-320-builder](repair-evidence/se-320-builder.png)
- [se-320-toolbar-scrolled](repair-evidence/se-320-toolbar-scrolled.png)
- [se-reloaded](repair-evidence/se-reloaded.png)
- [desktop-owned-world](repair-evidence/desktop-owned-world.png)
- [desktop-builder-entry](repair-evidence/desktop-builder-entry.png)
- [standalone-launcher](repair-evidence/standalone-launcher.png)

## Exact changed files

Generated CSS remains build output; the tracked stub is preserved. The source/file list below includes this report, prompt and redacted evidence.

- `apps/rist-world/App.razor`
- `apps/rist-world/Components/UniversalInterface.razor`
- `apps/rist-world/Components/WorldGate.razor`
- `apps/rist-world/rist_css_authority.py`
- `apps/rist-world/wwwroot/Launcher/index.html`
- `apps/rist-world/wwwroot/css/universal-interface.css`
- `apps/rist-world/wwwroot/prototype/prototype.css`
- `apps/rist-world/wwwroot/prototype/prototype.js`
- `apps/rist-world/wwwroot/prototype/spatial-title-handoff.js`
- `apps/rist-world/wwwroot/rist-plc.js`
- `apps/rist-world/wwwroot/world-gate-focus.js`
- `apps/rist-world/wwwroot/worldbuilder-source-host.js`
- `tests/authenticated-e2e/NEXT_REPAIR_PROMPT.md`
- `tests/authenticated-e2e/REGRESSION_RULES.md`
- `tests/authenticated-e2e/UI_REPAIR_AUDIT.md`
- `tests/authenticated-e2e/browser-tests.cjs`
- `tests/authenticated-e2e/repair-evidence/authentication-report.json`
- `tests/authenticated-e2e/repair-evidence/desktop-builder-entry.png`
- `tests/authenticated-e2e/repair-evidence/desktop-owned-world.png`
- `tests/authenticated-e2e/repair-evidence/report.json`
- `tests/authenticated-e2e/repair-evidence/se-320-builder.png`
- `tests/authenticated-e2e/repair-evidence/se-320-toolbar-scrolled.png`
- `tests/authenticated-e2e/repair-evidence/se-builder-0.png`
- `tests/authenticated-e2e/repair-evidence/se-builder-1.png`
- `tests/authenticated-e2e/repair-evidence/se-builder-2.png`
- `tests/authenticated-e2e/repair-evidence/se-builder-3.png`
- `tests/authenticated-e2e/repair-evidence/se-builder-4.png`
- `tests/authenticated-e2e/repair-evidence/se-builder-5.png`
- `tests/authenticated-e2e/repair-evidence/se-builder-6.png`
- `tests/authenticated-e2e/repair-evidence/se-environment.png`
- `tests/authenticated-e2e/repair-evidence/se-gamemaster.png`
- `tests/authenticated-e2e/repair-evidence/se-image-edited.png`
- `tests/authenticated-e2e/repair-evidence/se-image-save.png`
- `tests/authenticated-e2e/repair-evidence/se-image-upload.png`
- `tests/authenticated-e2e/repair-evidence/se-my-images.png`
- `tests/authenticated-e2e/repair-evidence/se-normal-user-roles.png`
- `tests/authenticated-e2e/repair-evidence/se-region-depth-0.png`
- `tests/authenticated-e2e/repair-evidence/se-region-depth-1.png`
- `tests/authenticated-e2e/repair-evidence/se-region-depth-2.png`
- `tests/authenticated-e2e/repair-evidence/se-region-save-attempt.png`
- `tests/authenticated-e2e/repair-evidence/se-region-select.png`
- `tests/authenticated-e2e/repair-evidence/se-reloaded.png`
- `tests/authenticated-e2e/repair-evidence/se-roleplayer.png`
- `tests/authenticated-e2e/repair-evidence/se-roles.png`
- `tests/authenticated-e2e/repair-evidence/se-start.png`
- `tests/authenticated-e2e/repair-evidence/se-title-editor.png`
- `tests/authenticated-e2e/repair-evidence/se-world-created.png`
- `tests/authenticated-e2e/repair-evidence/se-world-dialog.png`
- `tests/authenticated-e2e/repair-evidence/se-world-open.png`
- `tests/authenticated-e2e/repair-evidence/standalone-launcher.png`
