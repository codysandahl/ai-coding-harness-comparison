param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$venvScripts = "C:\Source\envs\claude\Scripts"
$backend = Join-Path $PSScriptRoot "src\backend"

if (-not (Test-Path (Join-Path $venvScripts "Activate.ps1"))) {
    throw "Venv not found at $venvScripts"
}

# Activate the claude venv (required for all Python commands in this repo)
. (Join-Path $venvScripts "Activate.ps1")

Set-Location $backend
Write-Host "Serving on http://localhost:$Port (backend: $backend)"
python -m uvicorn main:app --host 127.0.0.1 --port $Port --reload
