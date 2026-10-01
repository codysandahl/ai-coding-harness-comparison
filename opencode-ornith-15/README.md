# Local AI Image Explorer

A lightweight app for fast, iterative visual exploration with AI-generated images.

## What it does

- Continuously generates image prompts and images from a base prompt
- Uses remix phrases to create variation across generations
- Lets you pause and resume the generation loop at any time
- Lets you click a generated image to promote its prompt into the new base prompt
- Shows images in a lightbox with full metadata
- Downloads images with attached metadata

## Getting started

```bash
cd src/backend
uv sync --extra dev

# Copy and edit the environment (provider URL, API key, models, etc.)
cp .env.example .env

# Run the app. Binds to 127.0.0.1:8191 by default; override with PORT.
PORT=8191 uv run python -m app
```

Then open http://127.0.0.1:8191 in your browser.

## Tests

```bash
cd src/backend
uv run pytest
```
