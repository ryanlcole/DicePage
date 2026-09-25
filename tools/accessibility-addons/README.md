# Shaelvien Accessibility MCP Add-ons

These add-ons implement the project rule that normal development and accessibility development are one process. They are developer/assistive tools, not new authority.

## Default developer stack

The default local MCP profile is `mcp/default.accessibility.json`.

- **a11y-toolkit 3.20.0** — WCAG-oriented audit, keyboard, form, reflow, contrast, snapshot/diff and evidence tooling.
- **Playwright MCP 0.0.82** — browser interaction through structured accessibility snapshots.
- **WCAG MCP 2.0.0** — WCAG 2.2 criteria, techniques, glossary and implementation reference.

They are intentionally pinned. Upgrade them through an ordinary reviewed project change rather than silently following latest releases.

## Optional local assistive stack

These stay off by default because they carry additional local capability or local model requirements.

- **Munim Computer Use** — accessibility-tree desktop control. Explicit opt-in only because it can control applications on the user's machine.
- **mcp-whisper** — local speech-to-text/captions/transcripts backed by whisper.cpp. Keep the backend local by default and require authentication if exposed over HTTP.
- **Piper MCP Server** — local text-to-speech. Voice/model licenses are separate from the MCP server license and must be reviewed before redistribution.

Optional desktop MCP configuration is in `mcp/optional.accessibility.local.json`. Whisper/Piper are not auto-installed because their model/runtime paths are device-specific.

## Windows / Codex setup

Run from the repository root:

```powershell
pwsh -File tools/accessibility-addons/setup-default.ps1
```

The script checks prerequisites and registers the three default servers with Codex when `codex mcp add` is available. It does not install the privileged optional add-ons.

## POSIX / Codex setup

```bash
bash tools/accessibility-addons/setup-default.sh
```

## Audit evidence

`Accessibility Add-on Audit` is a manual GitHub Action. It installs the pinned A11y Toolkit + Playwright browser and captures an audit, keyboard pass, 320px reflow test, and accessibility snapshot of the public site as artifacts.

This evidence is useful for regression work. It is not a declaration of WCAG conformance. Human assistive-technology testing remains part of the accessibility contract.

## Authority boundary

All add-ons observe or invoke representations and semantic actions available to the user. They do not receive hidden world truth, credentials, moderation rights, GameMaster authority, or administrative authority merely because they are accessibility tools.
