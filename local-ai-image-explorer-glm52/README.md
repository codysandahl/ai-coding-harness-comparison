# Local AI Image Explorer

A lightweight app for fast, iterative visual exploration with AI-generated images.

## What it does

- Continuously generates image prompts and images from a base prompt
- Uses remix phrases to create variation across generations
- Lets you pause and resume the generation loop at any time
- Lets you click a generated image to promote its prompt into the new base prompt
- Shows images in a lightbox with full metadata
- Downloads images with attached metadata

## Run

1. Copy `.env.example` to `.env` and set your OpenAI-compatible provider:
   ```
   PROVIDER_BASE_URL=https://api.openai.com/v1
   PROVIDER_API_KEY=sk-...
   ```
2. Run it — Windows PowerShell: `./run.ps1`; macOS/Linux: `./run.sh`
   (uses `uv` to create and sync `src/backend/.venv`, serves on http://127.0.0.1:8000)

   Requires [uv](https://docs.astral.sh/uv/) installed. `uv run` syncs the
   project environment from `src/backend/pyproject.toml` automatically.

The creativity levels that govern how far prompts diverge from the base prompt
live in `src/backend/creativity.yaml` — edit them without touching code.
