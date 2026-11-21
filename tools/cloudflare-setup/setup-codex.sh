#!/usr/bin/env bash
# Local Codex setup: https://developers.cloudflare.com/agent-setup/prompt.md
set -euo pipefail
for cmd in npx codex; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing $cmd. Install its official CLI and retry." >&2
    exit 1
  fi
done
if (( $# == 0 )) || [[ "$1" != "--skip-skills" ]]; then
  npx -y skills add cloudflare/skills --skill '*' --yes --global
fi
if ! codex mcp list | grep -Eq '^[[:space:]]*cloudflare[[:space:]]'; then
  codex mcp add cloudflare --url https://mcp.cloudflare.com/mcp
fi
codex mcp login cloudflare
codex mcp list
printf '%s\n' 'Restart Codex to load Cloudflare tools. No Worker, DNS, billing, or AWS was changed.'
