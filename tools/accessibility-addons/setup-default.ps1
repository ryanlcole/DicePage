$ErrorActionPreference = "Stop"

function Need($name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    throw "Missing required command: $name"
  }
}

Need python
Need node
Need npx

if (-not (Get-Command uvx -ErrorAction SilentlyContinue)) {
  Write-Host "uvx is not installed. Install Astral uv, then run this script again."
  Write-Host "The repository does not execute a remote installer automatically."
  exit 2
}

Write-Host "Checking pinned accessibility add-ons..."
uvx --from a11y-toolkit==3.20.0 a11y-toolkit-mcp --help | Out-Null
npx -y @playwright/mcp@0.0.82 --help | Out-Null
npx -y wcag-guidelines-mcp@2.0.0 --help | Out-Null

if (Get-Command codex -ErrorAction SilentlyContinue) {
  Write-Host "Registering default accessibility MCP servers with Codex..."
  try { codex mcp remove a11y-toolkit 2>$null } catch {}
  try { codex mcp remove playwright 2>$null } catch {}
  try { codex mcp remove wcag 2>$null } catch {}

  codex mcp add a11y-toolkit -- uvx --from a11y-toolkit==3.20.0 a11y-toolkit-mcp
  codex mcp add playwright -- npx -y @playwright/mcp@0.0.82 --headless
  codex mcp add wcag -- npx -y wcag-guidelines-mcp@2.0.0
  Write-Host "Default Shaelvien accessibility MCP stack registered."
} else {
  Write-Host "Codex CLI is not on PATH. Use mcp/default.accessibility.json in your MCP client."
}

Write-Host "Privileged/local-model add-ons remain OFF until explicitly enabled."
