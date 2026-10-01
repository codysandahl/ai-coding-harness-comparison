# Implementation Plan: Local AI Image Explorer

## 1. Project Setup

- Initialize Python backend in `src/backend/` with venv at `src/backend/.venv`
- Use `uv` for dependency management
- Create FastAPI application structure
- Static HTML/CSS/JS frontend served by FastAPI
- Create `.env` file for `OPENAI_BASE_URL` and `OPENAI_API_KEY`

### 1.1 Startup Script
- `src/backend/run.sh` — launches the FastAPI app via `uvicorn` in the venv
- User runs this on demand; no persistent service

## 2. Backend Architecture (Python/FastAPI)

### 2.1 Configuration
- Load `OPENAI_BASE_URL` and `OPENAI_API_KEY` from environment
- Default to OpenAI's production endpoint if not overridden
- `/config` endpoint to inspect current settings

### 2.2 Model Management
- `/models` endpoint querying OpenAI for available text and image models
- Categorize models as text or image type

### 2.3 Text Generation (Prompt Remixing) — Creativity-Only
- `/generate-text` endpoint accepting: base prompt, remix phrases, creativity level, model selection
- **Creativity is prompt-based only** — no temperature manipulation, no programmatic remix step
- Creativity levels (3+) controlled by system prompt injected before generation:
  - **Low**: Minor word substitutions, preserves structure
  - **Medium**: Moderate rephrasing, adds/removes descriptive elements
  - **High**: Significant divergence, introduces new imagery while keeping core subject
- Creativity behavior defined in external config (e.g., `creativity.json`) — no code changes needed
- Returns generated prompt text

### 2.4 Image Generation
- `/generate-image` endpoint accepting: prompt, model, size, seed, creativity level
- Calls OpenAI's image generation endpoint
- **OpenAI constraints**: No seed parameter accepted, minimum size 1024×1024
- Returns image as base64-encoded data
- **No disk persistence** — images exist only in memory during session
- Each response includes metadata: model, size, seed, creativity level, prompt

### 2.5 Continuous Generation Loop
- `/generate-stream` endpoint using Server-Sent Events (SSE)
- Pushes new images to frontend at ~10s intervals
- Respects pause/resume state
- Pauses when lightbox is open

### 2.6 Download Endpoint
- `/download/{id}` returns image with metadata (attached as JSON sidecar or embedded data)

## 3. Frontend Architecture

### 3.1 Control Panel (Left Sidebar)
- **Text Model** dropdown (populated from `/models`)
- **Image Model** dropdown (populated from `/models`)
- **Base Prompt** textarea (editable, becomes new prompt when user clicks an image)
- **Remix Phrases** textarea (one per line, appended to base prompt)
- **Seed** input (optional, random if empty — display only, not sent to API)
- **Size** inputs (width/height, default 1024×1024, step 64)
- **Creativity Level** selector (3+ levels)
- **Play/Pause** button (ghost button style)
- **Status indicator** in nav bar (Generating / Paused)

### 3.2 Image Grid (Main Area)
- Responsive grid (3-column desktop, 1-column mobile)
- Each card shows:
  - Image thumbnail
  - Eyebrow: image number, model, size, seed
  - Prompt text (truncated to 2 lines)
  - "Use as Base Prompt" overlay on hover/click
- Clicking an image updates the base prompt and restarts generation

### 3.3 Lightbox
- Full-screen overlay when clicking an image
- Shows full-resolution image
- Displays all generation metadata
- Pauses the generation loop while open
- Close button dismisses and resumes generation

### 3.4 Download
- Clicking download on an image triggers the `/download/{id}` endpoint
- Metadata accompanies the downloaded file

## 4. Design System Implementation

- **Typography**: Playfair Display for headings, Fira Sans for body/UI text
- **Colors**: Primary `#1A1A1A`, Secondary `#666666`, Tertiary `#8A8A8A`, Neutral `#FFFFFF`, Surface `#EEEEEE`
- **Spacing**: 11-step scale (3xs through 2xl)
- **Corners**: Sharp (0px) by default, full circles for avatars/icons, 4px for one floating control
- **No elevation/shadows** in main content flow
- **Responsive**: Single-column mobile, 3-column desktop, breakpoints at 680px, 768px, 900px, 1024px

## 5. Creativity Level Configuration

Creativity behavior is defined in an external configuration file (e.g., `creativity.json` or `.env`), not hardcoded:

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

## 6. Spec Deviations — OpenAI Constraints

The original spec calls for 512×512 default size and seed support. OpenAI's API does not support either. The spec is **updated** to reflect this:

- **Default image size**: Changed from 512×512 to **1024×1024** (OpenAI minimum)
- **Seed**: Display-only in UI and metadata — not sent to API (OpenAI does not support seed parameter)
- **Creativity config**: Loaded from external file, not hardcoded

## 7. Failure Conditions Handling

- **No images produced**: Show explicit error message if provider fails or returns no image
- **Continues after pause**: Enforce pause state in both backend loop and frontend UI
- **Prompt not promoted**: Ensure clicking an image correctly updates the base prompt and resets the generation loop
- **Missing metadata**: Validate all required fields (model, size, seed, creativity, prompt) before displaying
- **Disk persistence**: Ensure images are never written to temporary files — use in-memory buffers
- **Lightbox doesn't pause**: Hook lightbox open/close to generation loop state
- **Creativity level adjustment**: Validate that creativity config is loaded from external file, not hardcoded

## 8. Development Workflow

1. Set up backend FastAPI app with configuration loading
2. Implement `/models` endpoint
3. Implement `/generate-text` with creativity levels
4. Implement `/generate-image` endpoint
5. Implement SSE-based `/generate-stream` for continuous generation
6. Build frontend control panel and image grid
7. Implement lightbox with pause/resume
8. Add download with metadata
9. Apply design system and responsive layout
10. Test against OpenAI with default settings
11. Verify all failure conditions are handled

## 9. Open Questions — Resolved

1. **Provider**: OpenAI only — confirmed
2. **Startup**: Bash script on demand — confirmed
3. **Creativity**: Prompt-based only, no temperature or remix step — confirmed
4. **Memory**: Truly unlimited images in memory — confirmed
5. **Text model default**: `chatgpt-5.6-luna` if available in the list, otherwise first available model — confirmed
6. **Image eviction**: Truly unlimited — confirmed
