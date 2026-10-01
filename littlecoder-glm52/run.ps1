# Run the Local AI Image Explorer via uv.
# uv manages the project venv automatically — no manual .venv creation.
$ErrorActionPreference = "Stop"

$here = $PSScriptRoot
$be = Join-Path $here "src/backend"

# Load .env if present (PROVIDER_BASE_URL / PROVIDER_API_KEY).
$envFile = Join-Path $here ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $idx = $line.IndexOf("=")
            $key = $line.Substring(0, $idx).Trim()
            $val = $line.Substring($idx + 1).Trim()
            Set-Item -Path "Env:$key" -Value $val
        }
    }
}

uv run --project $be uvicorn main:app --app-dir $be --host 127.0.0.1 --port 8000