#!/usr/bin/env bash
# Start the Local AI Image Explorer.
#
# Usage:  ./run.sh
# Binds to 127.0.0.1:8191 by default; override with PORT (see src/backend/.env).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/src/backend"

# Create a local .env from the template on first run, without overwriting edits.
if [ ! -f "$BACKEND/.env" ] && [ -f "$BACKEND/.env.example" ]; then
  cp "$BACKEND/.env.example" "$BACKEND/.env"
  echo "Created $BACKEND/.env from .env.example"
fi

cd "$BACKEND"

# Ensure dependencies are installed (fast no-op when already in sync).
uv sync --extra dev

# Run the app; exec replaces this shell so Ctrl-C stops the server.
exec uv run python -m app
