# Local AI Image Explorer — Backend Launcher
# Run from the source directory: .\run.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $scriptDir "src" "backend"
$venvPython = Join-Path $backendDir ".venv" "Scripts" "python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "ERROR: Virtual environment not found at $backendDir\.venv" -ForegroundColor Red
    Write-Host "Run 'uv venv src/backend' first." -ForegroundColor Yellow
    exit 1
}

Write-Host "Starting Local AI Image Explorer backend..." -ForegroundColor Cyan
Write-Host "  Venv: $venvPython" -ForegroundColor Gray
Write-Host "  Open http://127.0.0.1:8000 in your browser" -ForegroundColor Gray
Write-Host ""

& $venvPython -m uvicorn main:app --app-dir $backendDir --host 127.0.0.1 --port 8000 --reload
