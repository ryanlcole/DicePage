$ErrorActionPreference = 'Stop'

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker was not found. Install/start Docker Desktop with WSL2, then rerun this script.'
}

if (-not (Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
    Write-Host 'Created .env. Replace POSTGRES_PASSWORD with a long random local secret, then rerun.'
    exit 2
}

# Generate the SQL schema from the same Guacamole image we will run.
# This avoids checking version-specific Guacamole SQL into the repository.
$schemaPath = Join-Path $PSScriptRoot 'init\002-guacamole-schema.sql'
docker run --rm guacamole/guacamole:latest /opt/guacamole/bin/initdb.sh --postgresql | Set-Content -Encoding utf8 $schemaPath

Write-Host "Generated $schemaPath"
Write-Host 'Starting Guacamole on loopback only...'
docker compose up -d
Write-Host 'Open http://127.0.0.1:8080/guacamole/ after the containers become healthy.'
Write-Host 'Do NOT expose port 8080 directly to the public Internet.'
