# Durable regression constraints

- Never assign to the configured module `owner_user_id` inside authority `handler`. A deed recipient is a different identity; use a deed-scoped name. `/authority/me` must execute successfully for a normal valid session and must not manufacture platform-owner/developer authority.
- Never ship local fixture code, generated auth state or test environment activation paths in production frontend/Lambda artifacts. The test flag alone, production environments and Release builds must be rejected by the harness executable.
- Never bypass API authorization in UI tests. Seed the existing session/membership/profile schema in disposable storage and call the real handlers. Ordinary user hints must not become GM/owner authority.
- Never use force-clicks, direct application-state edits or unrestricted production requests to hide an interaction defect. Record pointer failure separately from a keyboard diagnostic continuation. Mobile interaction tests must use touch taps; mouse clicks are a distinct input mode.
- A modal rendered beneath an active iframe is not usable. Regression acceptance must include hit testing, normal pointer/touch activation, close/cancel and small-screen scrolling.
- A screenshot or HTTP 200 is not proof of persistence. Reopen/reload and observe the saved state through normal UI and authoritative storage where applicable.
- A caught Blazor interop exception may produce zero browser pageerror events. Capture console errors, rendered error surfaces, request failures and screen geometry separately.
- Region save must never turn a recoverable title/interop failure into an unrecoverable full-app stack screen. Preserve draft selection, authoritative commit gates and the existing in-map title composer.
- New browser evidence must redact session headers, query strings and signed URLs. Never commit/upload raw authentication state or traces containing private credentials.

## Private UI audit constraints

- Never replace a parent-window global function with an iframe-realm function for Blazor interop. Use a scoped explicit module bridge for the existing editor.
- World modal input must be above the viewer, trap focus while open, and restore inert state even after Blazor removes the modal element.
- Embedded tools must remain visible and usable when legitimately opened; passive summaries must not cover them.
- Labels are not images; image-size controls cannot assume every selected content node has size.
- Canonical styles must be published through the existing bundle, with no lazy requests for absent source-only CSS files.
- Separate committed map representation from authoritative region metadata. A null result after 401/403 is not a successful write. Keep the catalog persistence assertion failing until the actual authority contract is repaired; never bypass authorization to make the test green.
