#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/src/backend"
VENV_DIR="$BACKEND_DIR/.venv"

# Copy .env.example to .env if .env doesn't exist
if [ ! -f "$BACKEND_DIR/.env" ]; then
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
  echo "Created .env from .env.example — please set your OPENAI_API_KEY"
fi

# Source .env to get PORT
set -a
source "$BACKEND_DIR/.env"
set +a

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install -q -r "$BACKEND_DIR/requirements.txt"

# Start the server
echo "Starting Local AI Image Explorer on http://0.0.0.0:${PORT}"
echo ""
echo "Before generating, set your OPENAI_API_KEY in src/backend/.env"
echo ""
cd "$BACKEND_DIR"
uvicorn app:app --host 0.0.0.0 --port "$PORT" --reload
