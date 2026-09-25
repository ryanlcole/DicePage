#!/usr/bin/env bash
set -euo pipefail

for command in python3 node npx uvx; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "Missing required command: $command" >&2
    if [ "$command" = "uvx" ]; then
      echo "Install Astral uv, then run this script again. No remote installer is executed automatically." >&2
    fi
    exit 2
  fi
done

echo "Checking pinned accessibility add-ons..."
uvx --from a11y-toolkit==3.20.0 a11y-toolkit-mcp --help >/dev/null
npx -y @playwright/mcp@0.0.82 --help >/dev/null
npx -y wcag-guidelines-mcp@2.0.0 --help >/dev/null

if command -v codex >/dev/null 2>&1; then
  echo "Registering default accessibility MCP servers with Codex..."
  codex mcp remove a11y-toolkit >/dev/null 2>&1 || true
  codex mcp remove playwright >/dev/null 2>&1 || true
  codex mcp remove wcag >/dev/null 2>&1 || true
  codex mcp add a11y-toolkit -- uvx --from a11y-toolkit==3.20.0 a11y-toolkit-mcp
  codex mcp add playwright -- npx -y @playwright/mcp@0.0.82 --headless
  codex mcp add wcag -- npx -y wcag-guidelines-mcp@2.0.0
  echo "Default Shaelvien accessibility MCP stack registered."
else
  echo "Codex CLI is not on PATH. Use mcp/default.accessibility.json in your MCP client."
fi

echo "Privileged/local-model add-ons remain OFF until explicitly enabled."
