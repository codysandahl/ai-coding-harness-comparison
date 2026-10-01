# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

Implementation is complete. The Local AI Image Explorer is a fully functional FastAPI application with a single-page frontend.

## What the App Does

Local AI Image Explorer is a lightweight local app for fast, iterative visual exploration with AI-generated images. The user sets a base prompt, the app continuously generates new image prompts (via remix phrases) and images, and the user can steer exploration by clicking promising images to promote their prompts as the new base prompt.

## Core Workflow

1. User starts with a base prompt
2. App combines the base prompt with remix phrases to generate prompt variations and images
3. New images appear continuously in the app (~10s interval target)
4. User clicks a generated image to make its prompt the new base prompt
5. User can pause/resume generation, open a lightbox, and download images

## Architecture Notes

- **OpenAI API-compatible interface** — the app communicates with AI providers through an OpenAI-compatible endpoint
- **Two models** — separate text model (prompt generation) and image model (image generation)
- **Configurable provider** — base URL overridable via app environment file
- **No disk persistence** — generated images are displayed in-session only; saved to disk only on explicit user download
- **Generation metadata** — each image retains model, size, seed, creativity level, and prompt

## Development Environment

- **Python virtual environment**: `src/backend/.venv`. Always use this venv for backend Python commands (`pip`, `uvicorn`, running scripts, etc.) — never the system Python.
  - Direct executables (works from any shell, no activation needed): `src/backend/.venv/bin/python`, `src/backend/.venv/bin/pip`, `src/backend/.venv/bin/uvicorn`
  - Or activate it first — Bash/Zsh: `source src/backend/.venv/bin/activate`

## Key Files

- `README.md` — project overview and feature summary
- `docs/intent/INTENT.md` — full intent spec with expectations, constraints, and failure conditions
- `docs/wireframes/main.svg` — wireframe for the main UI

## Development Guidance (pre-implementation)

When starting implementation, refer to `docs/intent/INTENT.md` as the single source of truth for requirements. The constraints and failure conditions sections define what must be built and what would constitute a bug. The intent doc is the authoritative spec — if anything in CLAUDE.md conflicts with it, the intent doc wins.
