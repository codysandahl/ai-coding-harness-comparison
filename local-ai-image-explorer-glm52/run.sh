#!/usr/bin/env bash
# Run the Local AI Image Explorer via uv.
# uv manages the project venv automatically — no manual .venv creation.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
BE="$HERE/src/backend"

# .env is optional but recommended for a real provider.
export $(grep -v '^#' "$HERE/.env" 2>/dev/null | xargs -d '\n' 2>/dev/null || true)

exec uv run --project "$BE" uvicorn main:app --app-dir "$BE" --host 127.0.0.1 --port 8000