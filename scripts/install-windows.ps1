$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Set-Location "$Root\backend"
python -m venv .venv
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\pip.exe" install -r requirements-migration.txt
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }

Set-Location "$Root\frontend"
npm install

Write-Host "Installazione completata. Configura backend\.env e poi segui README_SUPABASE.md"
