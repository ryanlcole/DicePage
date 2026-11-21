# Cloudflare agent setup — Shaelvien Endemar

Status: CLOUDFLARE FREE ACCOUNT VERIFIED; ISOLATED HELLO WORLD WORKER DEPLOYED; CUSTOM HEALTH PROBE NOT DEPLOYED; GAME SERVER NOT DEPLOYED. Reviewed against Cloudflare's official instructions on 2026-11-21:
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

## Live Cloudflare verification (2026-11-21)

An authenticated, saved Cloudflare browser session was read-only inspected. The account's Workers plan is **Free**, Workers & Pages and Durable Objects sections are accessible, and the already configured `workers.dev` subdomain is `ryanlcole.workers.dev`. No billing, DNS, zones, domains or existing infrastructure were modified.

As a separate $0 hosting preflight, a new Worker named `shaelvien-endemar-preflight` was created at:

https://shaelvien-endemar-preflight.ryanlcole.workers.dev/

**Critical verification:** independent HTTP content reads show both `/` and `/health` returning Cloudflare's starter `Hello World!`, so the intended health-only code **has NOT deployed**. The automated Cloudflare Quick Edit / Monaco code editor would not accept replacement text. This is `PARTIAL_DEPLOYMENT` evidence, not a working Endemar server or functional health-only probe.

The reviewable intended source is `tools/cloudflare-setup/preflight-worker.mjs` with tests in `tests/test_cloudflare_preflight.mjs`. The tests verify that `GET /health` responds with `NONCANONICAL_PREFLIGHT` and that game routes and other requests fail closed. Three Node 22 tests and the GitHub compliance guard passed on the PR branch; this does **not** establish cloud runtime behavior.

### Owner-only completion of the isolated health probe

In the Cloudflare dashboard, open **Workers & Pages → shaelvien-endemar-preflight → Edit code**, replace the entire starter Worker code with the reviewed contents of `tools/cloudflare-setup/preflight-worker.mjs`, then **Deploy**. Do not modify DNS, enable a paid plan, or copy account credentials into source. If the UI cannot edit on mobile, use the laptop or the official Wrangler workflow authenticated locally. No API token needs to be placed in the repository.

If the dashboard editor is inaccessible, the equivalent owner-run **local CLI** sequence from the repository root is:

```sh
npx wrangler login
npx wrangler deploy tools/cloudflare-setup/preflight-worker.mjs --name shaelvien-endemar-preflight
```

Wrangler's OAuth authorization happens locally in your browser. Review the deployment output before accepting any unexpected changes; this must target **only the already created preflight Worker** on the Free plan. Do not switch to the separate `experimental-authority/wrangler.jsonc` in this step. Never commit an API token or bypass consent prompts.

Verify `GET /health` returns `classification: NONCANONICAL_PREFLIGHT` and `GET /` returns a 404 JSON response. Until that evidence exists, consider the Worker a generic Hello World deployment.

This is distinct from PR #61's proposed Durable Object first-player server. Its dedicated bootstrap secret, authenticated user/permission integration, and explicit release review are still required before any server pilot deployment. Existing PR #57/60/61/62 review chains remain unmerged. No ReLiC or canonical database writes were performed.

Code and checks are ChatGPT-assisted; Cloudflare observations were made with the owner's connected browser and verified with independent HTTP content retrieval.
