param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"

$env:APP_ENV = "development"
$env:DATABASE_URL = "sqlite+aiosqlite:///./data/app.db"
$env:AUTO_CREATE_TABLES = "false"
$env:DEV_AUTH_ENABLED = "false"

Set-Location $projectRoot
& $pythonPath -m uvicorn src.main:app --host 127.0.0.1 --port $Port
