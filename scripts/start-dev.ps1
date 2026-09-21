$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$Root\backend'; .\.venv\Scripts\Activate.ps1; python run.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$Root\frontend'; npm run dev"
Start-Sleep -Seconds 2
Start-Process "http://localhost:5173"

