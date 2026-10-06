# Authenticated private-application implementation and audit

Verified against source commit `47e255c8f7e18a01b372a2f6fbc5584c1998d713` on `live-alpha-rist-blazor-world`, plus this change. Browser run: 2026-10-06 02:18:23–02:18:58 UTC (October 5 evening in New York). This is actual local runtime verification of the real Debug frontend and AWS handler source using disposable storage. It is not a production deployment or live Discord/AWS/Safari verification.

## Implemented result

Codex/Playwright can start directly in an authenticated private session without a human logging in. The test session passes the application's existing opaque-token/DynamoDB session validation. Production identity remains Discord OAuth. No production provider, flag check, bypass endpoint, cookie, query parameter or unconditional permission override was added.

Live provider authentication cannot be automated here without a dedicated permitted Discord login ceremony. Rather than weaken that boundary, the isolated loopback harness seeds normal session records in Moto storage and uses existing sessionStorage keys. See README for the complete authority trace, independent environment/build/host guards, transport limitations, and run commands.

A real backend defect was found and fixed: assignment to `owner_user_id` inside the deed-request branch shadowed the configured global throughout `handler`, causing `/authority/me` to raise UnboundLocalError. Renaming only that branch-local variable to `deed_owner_user_id` preserves all existing owner checks. A durable executable regression covers this.

## Verification facts

| Fact | Result |
| --- | --- |
| Python security regressions | 27 passed |
| Existing platform authority contract tests | 26 passed |
| Local .NET Debug publication | Success; nine existing compiler/analyzer warnings |
| Browser authentication/guest checks | All eight passed in the audit; standalone auth command also provided |
| Full private UI audit | Fails, correctly, on confirmed UI/resource defects |
| Production build/deployment | Not performed |
| Live Discord or AWS storage/signing | Not exercised |
| Actual iPhone Safari | Not exercised; Chromium mobile/touch emulation |

The normal SDK build initially hit this execution environment's MSBuild Unix-socket restriction. The opt-in build helper uses the exact restored SDK WebAssembly tasks in process, and the build then succeeded. Browser archive downloads for the package-matched Chromium returned empty archives here; a Microsoft Playwright Chromium 141 headless shell was successfully used with Playwright 1.58.2. CI uses the normal package-matched browser installation. This browser-version difference limits equivalence to CI and Safari.

## Actually exercised

| Route/screen or action | Observed result |
| --- | --- |
| Guest `/Game/index.html` and `/Game/` | Redirect to `/Play/index.html`; private start/interface absent |
| Guest private HTTP APIs | Normal 401 for missing session |
| Ordinary user and GM `/Game/index.html` | Private PRESS START screen; reload remains authenticated |
| `/Game/Launcher/index.html`, both identities | AUTHENTICATED; Promote/Revoke stay disabled with no release authority |
| `/Launcher/index.html` guest | LOCKED; release controls disabled |
| Start privacy choice and PRESS START | Essential-only selection enables start; environment selector opens |
| RIST → Roleplayer, ordinary user | View-only world reference/encounter surface opens; footer Character/Dice/Replay/Chat are marked Coming Soon, not tested functionality |
| RIST → GameMaster | World/path selector opens |
| World chooser and creation | Dialog is behind viewer and pointer-blocked; keyboard diagnostic creates AINPC E2E World through actual UI/normal save path |
| Owned-world selection and reopen | Created world appears; still appears after actual page reload and re-entry |
| World Builder, touch | Left-display taps reach World Home, Tier, Layer and hex selection |
| Region footprint/volume | Actual map tap selects a hex; region vertical-boundary controls reach SAVE AREA |
| Region save | Crashes before successful persistence; no region success claimed |
| Desktop-sized state | Resized 1280×800 mobile context reaches owned-world/builder views; this is not an independent desktop mouse test |
| Standalone Launcher, valid session | LOCKED due missing root `/rist.js`; nested Game Launcher validates the same session |

Earlier diagnostic mouse clicks in a mobile context failed to advance the left display, while native touch taps worked. They are not reported as touch failures. An earlier `U` shortcut image-tool attempt did not expose an image dialog in the embedded viewer; that is a failed reachability attempt, not proof that all image tools are broken.

## Confirmed failures and probable visibility issues

1. **World chooser hidden behind the universal viewer.** `WorldGate.razor` backdrop is z-index 2147482550, universal shell 2147483200. Element hit testing identifies the viewer iframe over the dialog. Its box fits the screen but its input/create/close controls are occluded. Keyboard diagnostic continuation is not evidence of usable touch creation. Screenshot `se-world-dialog.png`.
2. **Region save crashes the entire private interface.** After actual Tier/Layer/hex and vertical-boundary selection, Save Area renders “RIST startup error” and “The value 'prompt' is not a function.” Console captures the Blazor JSException stack at `BeginOrSaveVisibleSpatialSelectionAsync`, `PressLeft`, and `DispatchSemanticActionAsync`. `prototype/spatial-title-handoff.js` assigns an iframe-defined prompt proxy to the parent global; cross-realm interop is a suspected cause requiring investigation. No region save success or persistence was established. Screenshot `se-region-depth-2.png`.
3. **Crash recovery and mobile clipping.** The error screen has no recovery/navigation control and presents a long stack which extends beyond the visible screen. Important content is clipped in the screenshot. Refresh restores the normal private start screen, but is external browser recovery, not a working in-app cancel/back flow.
4. **Required CSS resources missing from the built UI.** `/Game/css/button-artwork-fit.css` and `/Game/css/character-universal.css` return 404, with `[RIST PLC] style failed` console messages.
5. **Standalone Launcher cannot validate a valid session in the source-aligned local layout.** `../rist.js` resolves to `/rist.js`, which returns 404. The nested `/Game/Launcher/` version works. Existing production objects could differ; no deployment claim is made. Screenshot `standalone-launcher.png`.
6. **Small active touch targets.** Viewer editing/navigation toolbar buttons measure about 29×28 px. Start and analog-mode controls are about 54–65×22 px. They are reachable but small for touch. This is a usability finding, not a claim of a specific accessibility-standard violation. Covered underlying footer controls are background controls while the universal shell is active and are not counted as missing foreground actions.

No unintended document horizontal overflow was measured in captured states. Main touch displays are large and reachable. This does not certify every unvisited menu, dialog, nested scroll region or asset tool.

## Console and network record

The final audit recorded 80 console-error events, no Playwright `pageerror` events, and 106 failed/status-error network events. The region failure is a caught/rendered Blazor error logged to console, so zero `pageerror` does not mean zero JavaScript/interop errors. The redacted report contains full event detail and geometry.

| Class | Events | Interpretation |
| --- | ---: | --- |
| Missing required Game styles | 2 HTTP 404s | Confirmed built-source defects |
| Missing standalone `/rist.js` | 1 HTTP 404 | Confirmed local layout defect |
| Root translation-config | 21 HTTP 404s | Harness limitation: this config is normally generated by deployment; translation service not simulated |
| Signed object download | 41 HTTP 404s | Empty fixture storage/optional files; opaque URLs redacted; not proof of production missing assets |
| In-flight local requests aborted | 41 | Navigation/reload cancellations; includes config, storage and telemetry requests |
| External music/terrain requests blocked | 12 separate events | Intentional isolation; no conclusion about production resource health |

There were no unexpected private API 401/403 responses observed for valid test sessions in this audit. Explicit security tests separately prove missing/forged/expired/revoked sessions and forbidden role/owner actions remain rejected.

## Limits and next test work

Local creation, image/library selection, placement, scale/rotate/move, editing existing assets, and their save/cancel/persistence were not successfully exercised. Region saving crashes first. Do not count code implementing those features as working UI. Once that blocker is repaired, the harness must be extended with explicit positive normal-UI assertions for those journeys and separate desktop mouse contexts. Maps/owned zones in the live Shaelvien domain, deed purchases, tokens, admin/release changes and production data were not touched. Controller/gamepad, gesture beyond normal taps, VoiceOver, actual Safari safe areas and 320×568 were not verified.

`REPAIR_PROMPT.md` is the copyable instruction for the next chat. The screenshots and redacted report in baseline-evidence preserve observed failures; newly generated state and evidence stay under ignored `.e2e-runtime/`.

## Exact changed files

- `.gitignore`
- `infra/aws/rist-platform-authority/app.py`
- `.github/workflows/authenticated-e2e.yml`
- `tests/authenticated-e2e/AUDIT.md`
- `tests/authenticated-e2e/README.md`
- `tests/authenticated-e2e/REGRESSION_RULES.md`
- `tests/authenticated-e2e/REPAIR_PROMPT.md`
- `tests/authenticated-e2e/auth-state.cjs`
- `tests/authenticated-e2e/browser-tests.cjs`
- `tests/authenticated-e2e/build_local.py`
- `tests/authenticated-e2e/local_harness.py`
- `tests/authenticated-e2e/package-lock.json`
- `tests/authenticated-e2e/package.json`
- `tests/authenticated-e2e/requirements.txt`
- `tests/authenticated-e2e/test_security.py`
- `tests/authenticated-e2e/baseline-evidence/desktop-builder-entry.png`
- `tests/authenticated-e2e/baseline-evidence/desktop-owned-world.png`
- `tests/authenticated-e2e/baseline-evidence/report.json`
- `tests/authenticated-e2e/baseline-evidence/se-builder-0.png`
- `tests/authenticated-e2e/baseline-evidence/se-builder-1.png`
- `tests/authenticated-e2e/baseline-evidence/se-builder-2.png`
- `tests/authenticated-e2e/baseline-evidence/se-builder-3.png`
- `tests/authenticated-e2e/baseline-evidence/se-builder-4.png`
- `tests/authenticated-e2e/baseline-evidence/se-builder-5.png`
- `tests/authenticated-e2e/baseline-evidence/se-builder-6.png`
- `tests/authenticated-e2e/baseline-evidence/se-environment.png`
- `tests/authenticated-e2e/baseline-evidence/se-gamemaster.png`
- `tests/authenticated-e2e/baseline-evidence/se-normal-user-roles.png`
- `tests/authenticated-e2e/baseline-evidence/se-region-depth-0.png`
- `tests/authenticated-e2e/baseline-evidence/se-region-depth-1.png`
- `tests/authenticated-e2e/baseline-evidence/se-region-depth-2.png`
- `tests/authenticated-e2e/baseline-evidence/se-region-save-attempt.png`
- `tests/authenticated-e2e/baseline-evidence/se-region-select.png`
- `tests/authenticated-e2e/baseline-evidence/se-reloaded.png`
- `tests/authenticated-e2e/baseline-evidence/se-roleplayer.png`
- `tests/authenticated-e2e/baseline-evidence/se-roles.png`
- `tests/authenticated-e2e/baseline-evidence/se-start.png`
- `tests/authenticated-e2e/baseline-evidence/se-world-created.png`
- `tests/authenticated-e2e/baseline-evidence/se-world-dialog.png`
- `tests/authenticated-e2e/baseline-evidence/se-world-open.png`
- `tests/authenticated-e2e/baseline-evidence/standalone-launcher.png`
