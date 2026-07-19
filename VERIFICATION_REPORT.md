# Verification Report

Date: 2026-07-18

## Result

Complete local vertical-slice gameplay loop: passed.

Evidence files:

- `verification/ui-journey-report.json`
- `verification/ui-reconnect-report.json`
- `verification/ui-mobile-report.json`
- `verification/ui-01-landing.png`
- `verification/ui-05-camp-upgrade.png`
- `verification/ui-06-reconnect.png`
- `verification/mobile-final2-05-camp-upgrade.png`

These files are ignored by Git because they include generated state or screenshots.

## Manual UI Journey

Observed through visible Chrome:

| Step | Result |
| --- | --- |
| Open landing page | Pass |
| Enter/create account | Pass |
| Create character | Pass |
| Begin tutorial | Pass |
| Meet initial NPC | Pass |
| Receive tutorial quest | Pass |
| Travel to Forest Road | Pass |
| Perform skill check | Pass |
| Enter combat | Pass |
| Complete combat | Pass |
| Receive item/resource reward | Pass |
| Return to camp | Pass |
| Upgrade Quarters | Pass |
| Restart server and reconnect | Pass |
| Mobile narrow viewport journey | Pass |

Console errors: none in final passing reports.

## Automated Tests

Command:

```text
python -m unittest tests.test_shaelvien_lite -v
```

Result: 31 tests passing after release-prep environment validation coverage was added. The verified gameplay baseline was originally confirmed with 30 tests before this directive.

Compile check:

```text
compiled 7 files
```

## Persistence

Persistence uses `GameStore`, a local atomic JSON store. Verification state survived:

- browser refresh through `/api/bootstrap`;
- Chrome close and reopen after persistent cookie fix;
- Python server stop/restart;
- campaign save/reload in automated tests;
- malformed JSON recovery test.

## State Authority

Covered by tests:

- invalid character access rejected;
- cross-account campaign/character access rejected;
- browser-supplied roll/reward payload ignored;
- CSRF-less state-changing request rejected;
- direct reward request ignored;
- impossible dev item quantity rejected;
- unauthorized admin access rejected;
- invalid combat target rejected;
- duplicate camp upgrade idempotency key does not double-apply;
- completed encounter cannot be farmed for repeat rewards.

## AI Boundary

Covered by tests:

- malformed JSON rejected;
- forbidden account/entitlement/stat mutations rejected;
- hidden-instruction disclosure rejected;
- invalid NPC IDs rejected;
- unknown actions rejected;
- impossible item references rejected;
- oversized narration rejected;
- HTML/script injection escaped;
- deterministic fallback keeps gameplay usable without external AI.

## Mobile And Accessibility Baseline

Verified:

- mobile account entry, character creation, natural-language actions, structured actions, combat, camp upgrade, and quest/camp navigation;
- no final horizontal tab overflow at 390px viewport;
- labels on forms, visible focus styling, meaningful image alt text, semantic headings, readable health/quest text, and `role="status"` toast announcements.

Remaining gaps:

- no formal accessibility audit;
- no screen-reader regression suite;
- no automated visual diffing.

## Corrections Made During Verification

- Added persistent session cookie `Max-Age`.
- Added mobile tab wrapping.
- Added scroll reset on tab change.
- Added action input label and input focus outline.
- Added combat turn enforcement.
- Fixed Chrome verifier DevTools target and close behavior.
