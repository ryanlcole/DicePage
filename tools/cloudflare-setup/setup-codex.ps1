# Owner-controlled Cloudflare agent setup for Windows PowerShell.
# https://developers.cloudflare.com/agent-setup/prompt.md
param([switch]$SkipSkills)
$ErrorActionPreference = 'Stop'
foreach ($cmd in @('npx','codex')) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        throw "Missing $cmd. Install its official CLI and rerun."
    }
}
if (-not $SkipSkills) {
    & npx -y skills add cloudflare/skills --skill '*' --yes --global
    if ($LASTEXITCODE -ne 0) { throw 'Cloudflare skills installation failed.' }
}
$list = (& codex mcp list 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0) { throw 'Cannot read existing Codex MCP config.' }
if ($list -notmatch '(?m)^\s*cloudflare\s') {
    & codex mcp add cloudflare --url https://mcp.cloudflare.com/mcp
    if ($LASTEXITCODE -ne 0) { throw 'Cloudflare MCP registration failed.' }
} else { Write-Host 'Cloudflare MCP already registered; avoiding duplicate.' }
Write-Host 'Cloudflare OAuth will open in a browser. Approve required scopes only.'
& codex mcp login cloudflare
if ($LASTEXITCODE -ne 0) { throw 'Cloudflare OAuth login was not completed.' }
& codex mcp list
if ($LASTEXITCODE -ne 0) { throw 'Could not verify MCP registration.' }
Write-Host 'Restart Codex to load Cloudflare tools. No Worker, DNS, billing, or AWS was changed.'
