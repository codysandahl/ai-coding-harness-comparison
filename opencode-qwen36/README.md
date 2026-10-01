# Local AI Image Explorer

A lightweight local app for fast, iterative visual exploration with AI-generated images.

## What It Does

The user sets a base prompt, the app continuously generates new image prompts (via remix phrases) and images, and the user can steer exploration by clicking promising images to promote their prompts as the new base prompt.

## Core Workflow

1. User starts with a base prompt
2. App combines the base prompt with remix phrases to generate prompt variations and images
3. New images appear continuously in the app (~10s interval target)
4. User clicks a generated image to make its prompt the new base prompt
5. User can pause/resume generation, open a lightbox, and download images

## Architecture

- **OpenAI API-compatible interface** — the app communicates with AI providers through an OpenAI-compatible endpoint
- **Two models** — separate text model (prompt generation) and image model (image generation)
- **Configurable provider** — base URL overridable via app environment file
- **No disk persistence** — generated images are displayed in-session only; saved to disk only on explicit user download
- **Generation metadata** — each image retains model, size, seed, creativity level, and prompt

## Getting Started

### Prerequisites

- Python 3.10+
- An OpenAI API key

### Installation

```bash
chmod +x start.sh
./start.sh
```

This will:
1. Create a Python virtual environment at `src/backend/.venv`
2. Install dependencies (FastAPI, uvicorn, httpx, python-dotenv)
3. Copy `.env.example` to `.env` (if not already present)
4. Start the server on `http://localhost:8000`

### Configuration

Edit `src/backend/.env`:

```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
TEXT_MODEL=          # empty = auto-detect first available text model
IMAGE_MODEL=dall-e-3
CREATIVITY_CONFIG=creativity.json
```

### Creativity Levels

Edit `src/backend/creativity.json` to customize how much generated prompts diverge from the base prompt:

```json
{
  "levels": {
    "low": {
      "divergence": "minimal",
      "system_prompt": "Make small word-level changes to the base prompt. Preserve the original structure and subject."
    },
    "medium": {
      "divergence": "moderate",
      "system_prompt": "Rephrase the prompt more substantially. Add or remove descriptive elements while keeping the core subject."
    },
    "high": {
      "divergence": "significant",
      "system_prompt": "Diverge noticeably from the base prompt. Introduce new imagery, settings, or styles while preserving the core subject."
    }
  }
}
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/models` | List available text and image models |
| GET | `/creativity` | Get creativity level configurations |
| POST | `/generate-text` | Generate a text prompt variation |
| POST | `/generate-image` | Generate a single image |
| POST | `/generate-stream` | SSE stream for continuous generation |
| GET | `/images` | List generated images |
| DELETE | `/images` | Clear all generated images |
| POST | `/pause` | Pause generation loop |
| POST | `/resume` | Resume generation loop |
| GET | `/pause/status` | Get current pause status |
| POST | `/images/{id}/use-as-prompt` | Use an image's prompt as the new base |
| GET | `/download/{id}` | Download an image with metadata |

## Development

### Manual Setup

```bash
cd src/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### File Structure

```
opencode-qwen36/
├── DESIGN.md                  # Design system tokens
├── README.md                  # This file
├── start.sh                   # Startup script
├── design-system/
│   ├── tokens.css             # CSS custom properties
│   └── tokens.json            # Design tokens (JSON)
├── docs/
│   ├── intent/
│   │   └── INTENT.md          # Intent specification
│   ├── plans/
│   │   └── implementation-plan.md
│   └── wireframes/
│       └── main.html          # Interactive wireframe
├── src/
│   ├── backend/
│   │   ├── .env               # Environment config
│   │   ├── .env.example       # Config template
│   │   ├── app.py             # FastAPI application
│   │   ├── creativity.json    # Creativity level config
│   │   └── requirements.txt   # Python dependencies
│   └── frontend/
│       └── index.html         # Single-page frontend
└── CLAUDE.md                  # Development guidance
```

## Constraints

- Default image size is **1024×1024** (OpenAI minimum)
- Seed is display-only — not sent to API (OpenAI does not support seed parameter)
- Creativity config is loaded from external file, not hardcoded
- Generated images are stored in memory only, never written to disk
- Opening the lightbox pauses the generation loop
- Each generation uses a different seed unless explicitly overridden
