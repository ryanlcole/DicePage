# Cloudflare agent setup — Shaelvien Endemar

Status: SETUP PREPARED; OAUTH AND DEPLOYMENT NOT CONFIRMED. Reviewed against Cloudflare's official instructions on 2026-11-21:
https://developers.cloudflare.com/agent-setup/prompt.md

## Scope

The scripts configure Cloudflare's official agent skills and MCP in Codex **on the machine where the scripts run**, using OAuth and the official endpoint https://mcp.cloudflare.com/mcp. They do not connect the ChatGPT app, make a Cloudflare account, modify DNS, create an API token, or deploy a Worker. Existing MCP entries are preserved.

This is the same noncanonical Endemar pilot from PR #61; it is not the authoritative Shaelvien database, the protected weather system, or production game authentication.

## Windows PowerShell — development PC

Node.js/npm and Codex CLI must already be installed and available on PATH.

From the repository root:

    ./tools/cloudflare-setup/setup-codex.ps1

To skip the skill download when already present:

    ./tools/cloudflare-setup/setup-codex.ps1 -SkipSkills

The script follows Cloudflare's published steps:
1. npx -y skills add cloudflare/skills --skill '*' --yes --global
2. codex mcp add cloudflare --url https://mcp.cloudflare.com/mcp (if not already configured)
3. codex mcp login cloudflare — opens interactive OAuth; owner chooses account and scopes
4. codex mcp list — confirms the MCP registration; restart Codex to load tools

If local PowerShell execution policy blocks scripts, do not weaken machine policy for this project. Run the official commands individually through an approved terminal.

## Linux / macOS / WSL

    bash tools/cloudflare-setup/setup-codex.sh

Use --skip-skills when already installed. Do not paste OAuth tokens or passwords into chat, scripts, GitHub Actions secrets or source files.

## Hosting remains a separate release

The proposed experimental Cloudflare Worker and SQLite-backed Durable Object configuration is in:
apps/rist-world/experimental-authority/wrangler.jsonc

This setup does NOT deploy it. Stay on Workers Free and use SQLite-backed Durable Objects. Free limits can cause requests to fail when exceeded. Confirm an existing Cloudflare account and plan, then require human review of bootstrap secret handling, authentication, privacy, permission gates and PR #57/#60/#61 before deployment.

Do not move the existing sourcerors.com or relicgamemaster.com DNS zones, touch AWS, grant RIOT or ReLiC mutation rights, or bypass the canonical project database. The pilot can eventually use a Cloudflare-generated workers.dev URL with explicit release approval. Do not place the deployment secret ENDEMAR_BOOTSTRAP_KEY in source, documentation, browser code, logs, public GitHub issues, or chat.

## Verification

Codex MCP list confirms a configured connection, not cloud permission or deployment. OAuth access must be verified through an authenticated read-only account/Workers query; permission errors need owner-approved OAuth scopes. Actual server functionality requires a deployed worker URL and authenticated external tests.

Installing skills in an isolated sandbox does not install them on the user's computer or in the ChatGPT app. The first attempt inside the ChatGPT sandbox failed because npm's registry was unreachable (DNS error). Running these scripts on an authorized networked machine is the remaining local-agent step.

Optional Cloudflare cf beta CLI is intentionally not installed. Do not auto-enroll in a paid plan, change domains, or deploy infrastructure during agent setup.

Code and documentation drafted with ChatGPT assistance for owner review.